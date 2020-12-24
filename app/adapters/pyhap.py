import os
import sys
import asyncio
import threading
import queue
import json

from pyhap.hap_server import HAPServerHandler
from pyhap.accessory_driver import AccessoryDriver
from concurrent.futures import ThreadPoolExecutor
from zeroconf import ServiceInfo, Zeroconf
from pyhap.encoder import AccessoryEncoder
from pyhap.loader import Loader
from pyhap.state import State
from pyhap.hap_server import HAPServer
from pyhap.const import CATEGORY_BRIDGE

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