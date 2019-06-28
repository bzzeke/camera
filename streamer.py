import socket, sys
import time
import cv2
from pynng import Bus0, Req0
import json
from threading import Thread
import os
from urllib.parse import urlparse

class Streamer():
    cameras = {}

    def __init__(self):
        it = 0
        while "CAM_NAME_%i" % it in os.environ:
            self.cameras[os.environ["CAM_NAME_%i" % it]] = {
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

            it += 1


    def send_meta(self):
        print("Checking if meta information is filled")
        for cam in self.cameras:
            if self.cameras[cam]["meta"]["dtype"] == None:
                return

        print("Sending meta information")
        s1 = Req0(dial=os.environ["META_SERVER_ADDRESS"], recv_timeout=2000)
        s1.send(json.dumps(self.cameras).encode("utf-8"))

    def stream(self, cam):
        video = self.get_capture(self.cameras[cam]["url"])
        print("Starting stream for camera %s" % cam)

        s0 = Bus0(listen=self.cameras[cam]["stream"], recv_timeout=100, recv_max_size=0, send_buffer_size=1, recv_buffer_size=1)
        while True:

            (grabbed, frame) = video.read()
            if self.cameras[cam]["meta"]["dtype"] == None:
                self.cameras[cam]["meta"]["dtype"]=str(frame.dtype)
                self.cameras[cam]["meta"]["shape"]=frame.shape
                self.send_meta()

            if not grabbed:
                print("Reconnecting to camera %s" % cam)
                video.release()
                video = self.get_capture(self.cameras[cam]["url"])
                continue

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
