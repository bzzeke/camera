import socket, sys
import time
import cv2
import zmq
import json
import os

from threading import Thread

from util import log
from models.config import config, HardwareType, CapturerType

class CameraStream(Thread):
    camera = None
    video = None
    stop_flag = False

    ts_pregrab = 0
    ts_postgrab = 0
    ts_prezmq = 0
    ts_postzmq = 0

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None):
        super(CameraStream, self).__init__(group=group, target=target, name=name)
        self.camera = camera

    def run(self):
        self.video = self.get_capture(self.camera.stream_url)

        log("[streamer] [{}] Starting stream".format(self.camera.name))

        ctx = zmq.Context()
        s = ctx.socket(zmq.PUB)
        s.bind("ipc:///tmp/streamer_{}".format(self.camera.name))

        stream_watcher = StreamWatcher(camera_stream=self)
        stream_watcher.start()

        while not self.stop_flag:

            self.ts_pregrab = time.time()
            (grabbed, frame) = self.video.read()
            self.ts_postgrab = time.time()

            if not grabbed:
                # log("[streamer] [{}] Reconnecting to camera".format(self.camera.name))
                self.video.release()
                self.video = self.get_capture(self.camera.stream_url)
                time.sleep(5)
                continue

            if self.camera.meta["dtype"] == None:
                self.camera.set_meta({
                    "dtype": str(frame.dtype),
                    "shape": frame.shape,
                    "width": int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "fps": int(self.video.get(cv2.CAP_PROP_FPS)),
                })
                log("[streamer] [{}] Save meta information".format(self.camera.name))

            self.ts_prezmq = time.time()
            s.send(frame)
            self.ts_postzmq = time.time()
            del frame
        s.close()
        stream_watcher.stop()

    def get_capture(self, url):
        if config.capturer.type == CapturerType.gstreamer:
            codec = "h264"
            decoder = "avdec_{}".format(codec) if config.capturer.hardware == HardwareType.cpu else "vaapidecodebin"
            return cv2.VideoCapture('rtspsrc location="{}" latency=0 protocols=GST_RTSP_LOWER_TRANS_TCP ! rtp{}depay ! {}parse ! {} ! videoconvert ! appsink'.format(url, codec, codec, decoder), cv2.CAP_GSTREAMER)
        else:
            return cv2.VideoCapture(url)

    def stop(self):
        self.stop_flag = True
        self.join()


class StreamWatcher(Thread):
    stop_flag = False
    camera_stream = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera_stream=None):
        super(StreamWatcher, self).__init__(group=group, target=target, name=name)
        self.camera_stream = camera_stream

    def run(self):
        log("[stream_watcher] Starting service for {}".format(self.camera_stream.camera.name))

        while not self.stop_flag:
            time.sleep(1)
            self.watch_stream()

    def watch_stream(self):
        TIMEOUT = 20
        if self.camera_stream.ts_pregrab == 0:
            return

        if time.time() - self.camera_stream.ts_pregrab > TIMEOUT:
            log("[stream_watcher] Looks like thread is hang up: {} - {}, {}, {}, {}".format(self.camera_stream.camera.name, self.camera_stream.ts_pregrab, self.camera_stream.ts_postgrab, self.camera_stream.ts_prezmq, self.camera_stream.ts_postzmq))
            self.camera_stream.video.release()

    def stop(self):
        self.stop_flag = True
        self.join()

