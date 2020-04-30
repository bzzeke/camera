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
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None):
        super(Streamer, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.stop = False

    def send_meta(self):

        print("Sending meta information for camera %s" % self.camera["name"])

        params = json.dumps(self.camera).encode("utf8")
        url = "http://%s:%s/camera" % (os.environ["API_SERVER_HOST"], os.environ["API_SERVER_PORT"])
        req = request.Request(url, data=params, headers={'content-type': 'application/json'})
        response = request.urlopen(req)
        print("Got response: %s" % response.read().decode())

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
                self.camera["meta"]["dtype"]=str(frame.dtype)
                self.camera["meta"]["shape"]=frame.shape
                self.send_meta()

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

def run():

    threads = []
    for cam, camera in get_camera():
        thread = Streamer(camera=camera)
        thread.start()
        threads.append(thread)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for thread in threads:
            thread.stop = True

