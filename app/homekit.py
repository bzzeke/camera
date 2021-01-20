import os

from pyhap import camera
from threading import Thread

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

