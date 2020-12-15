import os
import sys
import asyncio
import threading
import queue
import pyhap.tlv as tlv
import json

from pyhap import camera
from pyhap.hap_server import HAPServerHandler
from pyhap.accessory_driver import AccessoryDriver
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from zeroconf import ServiceInfo, Zeroconf
from pyhap.encoder import AccessoryEncoder
from pyhap.loader import Loader
from pyhap.state import State
from pyhap.hap_server import HAPServer
from pyhap.const import CATEGORY_BRIDGE

class HomekitCamera(camera.Camera):
    cameraObj = None
    default_options = {
        "video": {
            "codec": {
                "profiles": [
                    camera.VIDEO_CODEC_PARAM_PROFILE_ID_TYPES["BASELINE"],
                    camera.VIDEO_CODEC_PARAM_PROFILE_ID_TYPES["MAIN"],
                    camera.VIDEO_CODEC_PARAM_PROFILE_ID_TYPES["HIGH"]
                ],
                "levels": [
                    camera.VIDEO_CODEC_PARAM_LEVEL_TYPES['TYPE3_1'],
                    camera.VIDEO_CODEC_PARAM_LEVEL_TYPES['TYPE3_2'],
                    camera.VIDEO_CODEC_PARAM_LEVEL_TYPES['TYPE4_0'],
                ],
            },
            "resolutions": [
                [320, 240, 10],
                [1920, 1080, 10],
                [1024, 768, 10],
                [640, 480, 10],
                [640, 360, 10],
                [480, 360, 10],
                [480, 270, 10],
                [320, 240, 10],
                [320, 180, 10],
            ],
        },
        "audio": {
            "codecs": [
                {
                    'type': 'OPUS',
                    'samplerate': 24,
                },
                {
                    'type': 'AAC-eld',
                    'samplerate': 16
                }
            ],
        },
        "srtp": True,
        "start_stream_cmd":  (
        'ffmpeg -re -i {stream} '
        '-probesize 32 -analyzeduration 0 '
        '-vcodec copy -r 10 '
        '-payload_type 99 -ssrc {v_ssrc} -f rtp '
        '-srtp_out_suite AES_CM_128_HMAC_SHA1_80 -srtp_out_params {v_srtp_key} '
        'srtp://{address}:{v_port}?rtcpport={v_port}&'
        'localrtcpport={v_port}&pkt_size=1316'),
    }

    def __init__(self, camera, *args, **kwargs):

        self.cameraObj = camera

        options = self.default_options.copy()
        options["address"] = os.environ["API_SERVER_HOST"]

        super(HomekitCamera, self).__init__(options, *args, **kwargs)


    async def start_stream(self, session_info, stream_config):

        stream_config["stream"] = self.cameraObj.stream_url if stream_config["height"] >= 720 else self.cameraObj.substream_url
        return await super().start_stream(session_info, stream_config)

    def get_snapshot(self, image_size):
        return self.cameraObj.make_snapshot()


class HomekitWorker(Thread):
    driver = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, driver=None):
        super(HomekitWorker, self).__init__(group=group, target=target, name=name)
        self.driver = driver

    def run(self):
        self.driver.start()

    def stop(self):
        self.driver.stop()
        self.join()


class HomekitDriver(AccessoryDriver):


    def __init__(self, *, address=None, port=51234,
                 persist_file='accessory.state', pincode=None,
                 encoder=None, loader=None, loop=None, mac=None,
                 listen_address=None, advertised_address=None, interface_choice=None,
                 zeroconf_instance=None):

        if loop is None:
            if sys.platform == 'win32':
                loop = asyncio.ProactorEventLoop()
            else:
                loop = asyncio.new_event_loop()

            executor_opts = {'max_workers': None}
            if sys.version_info >= (3, 6):
                executor_opts['thread_name_prefix'] = 'SyncWorker'

            self.executor = ThreadPoolExecutor(**executor_opts)
            loop.set_default_executor(self.executor)
        else:
            self.executor = None

        self.loop = loop

        self.accessory = None
        self.http_server_thread = None
        if zeroconf_instance is not None:
            self.advertiser = zeroconf_instance
        elif interface_choice is not None:
            self.advertiser = Zeroconf(interfaces=interface_choice)
        else:
            self.advertiser = Zeroconf()
        self.persist_file = os.path.expanduser(persist_file)
        self.encoder = encoder or AccessoryEncoder()
        self.topics = {}  # topic: set of (address, port) of subscribed clients
        self.topic_lock = threading.Lock()  # for exclusive access to the topics
        self.loader = loader or Loader()
        self.aio_stop_event = asyncio.Event(loop=loop)
        self.stop_event = threading.Event()
        self.event_queue = (
            queue.SimpleQueue() if hasattr(queue, "SimpleQueue") else queue.Queue()  # pylint: disable=no-member
        )
        self.send_event_thread = None  # the event dispatch thread
        self.sent_events = 0
        self.accumulated_qsize = 0

        self.safe_mode = False

        self.mdns_service_info = None
        self.srp_verifier = None

        address = address or util.get_local_address()
        advertised_address = advertised_address or address
        self.state = State(address=advertised_address, mac=mac, pincode=pincode, port=port)

        listen_address = listen_address or address
        network_tuple = (listen_address, self.state.port)
        self.http_server = HAPServer(network_tuple, self, handler_type=ServerHandler)

class ServerHandler(HAPServerHandler):
    def handle_resource(self):
        """Get a snapshot from the camera."""

        data_len = int(self.headers["Content-Length"])
        request_body = self.rfile.read(data_len)
        data = json.loads(request_body.decode("utf-8"))

        if self.accessory_handler.accessory.category == CATEGORY_BRIDGE:
            accessory = self.accessory_handler.accessory.accessories.get(data['aid'])
            if not accessory:
                raise ValueError('Accessory with aid == {} not found'.format(data['aid']))
        else:
            accessory = self.accessory_handler.accessory

        if not hasattr(accessory, 'get_snapshot'):
            raise ValueError('Got a request for snapshot, but the Accessory '
                             'does not define a "get_snapshot" method')

        image = accessory.get_snapshot(data)
        self.send_response(200)
        self.send_header('Content-Type', 'image/jpeg')
        self.end_response(image)
