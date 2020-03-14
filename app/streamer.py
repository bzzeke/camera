import socket, sys
import time
import cv2
from pynng import Bus0, Req0
import json
from threading import Thread
import os
from urllib.parse import urlparse
from urllib import request

class Streamer():
    cameras = {}

    def __init__(self):
        it = 0
        while "CAM_NAME_%i" % it in os.environ:
            self.cameras[os.environ["CAM_NAME_%i" % it]] = {
                "name": os.environ["CAM_NAME_%i" % it],
                "url": os.environ["CAM_URL_%i" % it],
                "stream": os.environ["CAM_STREAM_%i" % it],
                "meta": {
                    "dtype": None,
                    "shape": None
                }
            }

            if "CAM_ONVIF_%i" % it in os.environ:
                parts = urlparse(os.environ["CAM_ONVIF_%i" % it])
                self.cameras[os.environ["CAM_NAME_%i" % it]]["onvif"] = {
                    "host": parts.hostname,
                    "port": parts.port,
                    "username": parts.username,
                    "password": parts.password
                }

            if "CAM_PTZ_FEATURES_%i" % it in os.environ:
                self.cameras[os.environ["CAM_NAME_%i" % it]]["ptz_features"] = os.environ["CAM_PTZ_FEATURES_%i" % it]

            it += 1


    def send_meta(self, cam):

        print("Sending meta information for camera %s" % cam)

        params = json.dumps(self.cameras[cam]).encode("utf8")
        url = "http://%s:%s" % (os.environ["API_SERVER_HOST"], os.environ["API_SERVER_PORT"])
        req = request.Request(url, data=params, headers={'content-type': 'application/json'})
        response = request.urlopen(req)
        print("Got response: %s" % response.read().decode())

    def stream(self, cam):
        video = self.get_capture(self.cameras[cam]["url"])
        print("Starting stream for camera %s" % cam)

        s0 = Bus0(listen=self.cameras[cam]["stream"], recv_timeout=100, recv_max_size=0, send_buffer_size=1, recv_buffer_size=1)
        while True:

            (grabbed, frame) = video.read()

            if not grabbed:
                print("Reconnecting to camera %s" % cam)
                video.release()
                video = self.get_capture(self.cameras[cam]["url"])
                time.sleep(5)
                continue

            if self.cameras[cam]["meta"]["dtype"] == None:
                self.cameras[cam]["meta"]["dtype"]=str(frame.dtype)
                self.cameras[cam]["meta"]["shape"]=frame.shape
                self.send_meta(cam)

            s0.send(frame.tostring())
            del frame
            time.sleep(0.1)

    def get_capture(self, url):
        return cv2.VideoCapture(url)


def run():
    streamer = Streamer()

    for cam in streamer.cameras:
        p = Thread(target = streamer.stream, args=[cam])
        p.daemon = True
        p.start()
