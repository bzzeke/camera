import os


from uuid import UUID
from pyhap import camera
from pyhap import tlv
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
        'ffmpeg -i {stream} '
        '-rtsp_transport tcp '
        '-probesize 32 -analyzeduration 0 '
        '-an ' # disable audio
        '-vcodec copy -r 10 '
        '-payload_type 99 -ssrc {v_ssrc} -f rtp '
        '-srtp_out_suite AES_CM_128_HMAC_SHA1_80 -srtp_out_params {v_srtp_key} '
        'srtp://{address}:{v_port}?rtcpport={v_port}&'
        'localrtcpport={v_port}&pkt_size=1316')
    }

    def __init__(self, camera, *args, **kwargs):

        self.cameraObj = camera

        options = self.default_options.copy()
        options["address"] = os.environ["API_SERVER_HOST"]
        # options["stream"] = self.cameraObj.stream_url

        super(HomekitCamera, self).__init__(options, *args, **kwargs)

    async def start_stream(self, session_info, stream_config):

        stream_config["stream"] = self.cameraObj.stream_url
        return await super().start_stream(session_info, stream_config)

    def get_snapshot(self, image_size):
        return self.cameraObj.make_snapshot()

    # remove when https://github.com/ikalchev/HAP-python/pull/358 will be merged
    async def _stop_stream(self, objs):
        """Stop the stream for the specified session.
        Schedules ``self.stop_stream``.
        :param objs: TLV-decoded SelectedRTPStreamConfiguration value.
        :param objs: ``dict``
        """
        session_objs = tlv.decode(objs[camera.SELECTED_STREAM_CONFIGURATION_TYPES['SESSION']])
        session_id = UUID(bytes=session_objs[camera.SETUP_TYPES['SESSION_ID']])
        session_info = self.sessions.get(session_id)

        if not session_info:
            camera.logger.error(
                'Requested to stop stream for session %s, but no '
                'such session was found',
                session_id
            )
            return

        stream_idx = session_info['stream_idx']
        await self.stop_stream(session_info)
        del self.sessions[session_id]

        self._streaming_status[stream_idx] = camera.STREAMING_STATUS['AVAILABLE']


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

