import socket, sys
import time
import cv2
import zmq
import json
from threading import Thread
import os
from urllib.parse import urlparse
from urllib import request


class Streamer(Thread):
    camera = {}
    state = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None, state=None):
        super(Streamer, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.state = state
        self.stop = False

    def set_meta(self):

        print("Put meta information for camera %s to state" % self.camera["name"])
        self.state.set_camera(self.camera)

    def run(self):
        video = self.get_capture(self.camera["url"])

        print("Starting stream for camera %s" % self.camera["name"])

        ctx = zmq.Context()
        s = ctx.socket(zmq.PUB)
        s.bind("ipc:///tmp/streamer_%s" % self.camera["name"])

        while True:
            if self.stop:
                break

            (grabbed, frame) = video.read()

            if not grabbed:
                print("Reconnecting to camera %s" % self.camera["name"])
                video.release()
                video = self.get_capture(self.camera["url"])
                time.sleep(5)
                continue

            if self.camera["meta"]["dtype"] == None:
                self.camera["meta"]["dtype"] = str(frame.dtype)
                self.camera["meta"]["shape"] = frame.shape
                self.camera["meta"]["width"] = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.camera["meta"]["height"] = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.camera["meta"]["fps"] = int(video.get(cv2.CAP_PROP_FPS))
                self.set_meta()

            s.send(frame)
            del frame
        s.close()

    def get_capture(self, url):
        return cv2.VideoCapture(url)


def get_camera():
    it = 0
    cameras = {}
    while "CAM_NAME_%i" % it in os.environ:
        cameras[os.environ["CAM_NAME_%i" % it]] = {
            "name": os.environ["CAM_NAME_%i" % it],
            "url": os.environ["CAM_URL_%i" % it],
            "meta": {
                "dtype": None,
                "shape": None
            }
        }

        if "CAM_ONVIF_%i" % it in os.environ:
            parts = urlparse(os.environ["CAM_ONVIF_%i" % it])
            cameras[os.environ["CAM_NAME_%i" % it]]["onvif"] = {
                "host": parts.hostname,
                "port": parts.port,
                "username": parts.username,
                "password": parts.password
            }

        if "CAM_PTZ_FEATURES_%i" % it in os.environ:
            cameras[os.environ["CAM_NAME_%i" % it]]["ptz_features"] = os.environ["CAM_PTZ_FEATURES_%i" % it]

        it += 1

    return cameras.items()

def run(state):

    threads = []
    for cam, camera in get_camera():
        thread = Streamer(camera=camera, state=state)
        thread.start()
        threads.append(thread)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for thread in threads:
            thread.stop = True

