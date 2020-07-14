import socket, sys
import time
import cv2
import zmq
import json
import os

from threading import Thread

from util import log

class CameraStream(Thread):
    camera = {}
    state = None
    video = None

    ts_pregrab = 0
    ts_postgrab = 0
    ts_prezmq = 0
    ts_postzmq = 0

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None, state=None):
        super(CameraStream, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.state = state
        self.stop = False

    def set_meta(self):

        log("[streamer] [{}] Save meta information".format(self.camera["name"]))
        self.state.set_camera(self.camera)

    def run(self):
        self.video = self.get_capture(self.camera["url"])

        log("[streamer] [{}] Starting stream".format(self.camera["name"]))

        ctx = zmq.Context()
        s = ctx.socket(zmq.PUB)
        s.bind("ipc:///tmp/streamer_%s" % self.camera["name"])

        while True:
            if self.stop:
                break

            self.ts_pregrab = time.time()
            (grabbed, frame) = self.video.read()
            self.ts_postgrab = time.time()

            if not grabbed:
                # log("[streamer] [{}] Reconnecting to camera".format(self.camera["name"]))
                self.video.release()
                self.video = self.get_capture(self.camera["url"])
                time.sleep(5)
                continue

            if self.camera["meta"]["dtype"] == None:
                self.camera["meta"]["dtype"] = str(frame.dtype)
                self.camera["meta"]["shape"] = frame.shape
                self.camera["meta"]["width"] = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
                self.camera["meta"]["height"] = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.camera["meta"]["fps"] = int(self.video.get(cv2.CAP_PROP_FPS))
                self.set_meta()

            self.ts_prezmq = time.time()
            s.send(frame)
            self.ts_postzmq = time.time()
            del frame
        s.close()

    def get_capture(self, url):
        if os.environ["CAPTURER_TYPE"] == "gstreamer":
            decoder = "avdec_{}".format(self.camera["codec"]) if os.environ["CAPTURER_HARDWARE"] == "cpu" else "vaapidecodebin"
            return cv2.VideoCapture('rtspsrc location="{}" latency=0 protocols=GST_RTSP_LOWER_TRANS_TCP ! rtp{}depay ! {}parse ! {} ! videoconvert ! appsink'.format(url, self.camera["codec"], self.camera["codec"], decoder), cv2.CAP_GSTREAMER)
        else:
            return cv2.VideoCapture(url)


class Streamer(Thread):
    stop = False
    state = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, state=None):
        super(Streamer, self).__init__(group=group, target=target, name=name)
        self.state = state

    def run(self):
        log("[streamer] Starting service")
        threads = []
        for cam, camera in self.state.cameras.items():
            thread = CameraStream(camera=camera, state=self.state)
            thread.start()
            threads.append(thread)

        while not self.stop:
            time.sleep(1)
            self.watch_stream(threads)

        for thread in threads:
            thread.stop = True
            thread.join()

    def watch_stream(self, threads):
        TIMEOUT = 20
        for thread in threads:
            if thread.ts_pregrab == 0:
                continue

            if time.time() - thread.ts_pregrab > TIMEOUT:
                log("[streamer] Looks like thread is hang up: {} - {}, {}, {}, {}".format(thread.camera["name"], thread.ts_pregrab, thread.ts_postgrab, thread.ts_prezmq, thread.ts_postzmq))
                thread.video.release()

