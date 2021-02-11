import cv2
import time
import queue
import os
import jdb
import zmq
import numpy as np
import collections
import datetime as dt

from threading import Thread

from api.timelapse import Timelapse
from models.config import storage_path
from util import log

class TimelapseWriter(Thread):

    FPS = 30
    FRAMES_PER_CHUNK = 30 * 30

    storage_path = "{}/timelapse".format(storage_path)
    stop_flag = False
    camera = None
    out = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None):
        super(TimelapseWriter, self).__init__(group=group, target=target, name=name)
        self.camera = camera

    def run(self):

        log("[timelapse_writer] [{}] Starting timelapse writer".format(self.camera.name))
        api = Timelapse()
        ctx = zmq.Context()
        s = ctx.socket(zmq.SUB)
        s.connect("ipc:///tmp/streamer_{}".format(self.camera.id))
        s.setsockopt(zmq.SUBSCRIBE, b"")
        s.setsockopt(zmq.RCVTIMEO, 2000)
        frame_idx = 0

        out_frame_counter = 0
        fourcc = cv2.VideoWriter_fourcc("a", "v", "c", "1")

        while not self.stop_flag:
            try:
                msg = s.recv()
            except:
                continue

            A = np.frombuffer(msg, dtype=self.camera.meta["dtype"])
            frame = A.reshape(self.camera.meta["shape"])
            del A
            frame_idx += 1

            if frame_idx % self.camera.meta["fps"] != 0:
                continue

            frame_idx = 0
            if out_frame_counter == 0:
                file_path = api.chunk_path(self.camera.id, int(time.time()))
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                self.out = cv2.VideoWriter(file_path, fourcc, self.FPS, (self.camera.meta["width"], self.camera.meta["height"]))

            out_frame_counter += 1
            self.out.write(frame)

            if out_frame_counter > self.FRAMES_PER_CHUNK:
                self.out.release()
                self.out = None
                out_frame_counter = 0

    def stop(self):
        self.stop_flag = True
        self.join()
        self.out.release()
        self.out = None


