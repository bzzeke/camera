import zmq
import cv2
import numpy as np
import time
import queue

from threading import Thread

from util import log
from detector.clip_writer import ClipWriter
from detector.object_processor import ObjectProcessor

#
#
# [frame] -> ObjectDetector -> [objects] -> ObjectProcessor -> [timestamp] -> ClipWriter
#
#

class MotionDetector(Thread):
    RATE = 10 # each N frame

    stop = False
    camera = {}

    response_queue = None
    object_detector_queue = None
    writer_queue = None

    object_processor = None
    clip_writer = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None, object_detector_queue=None):
        super(MotionDetector, self).__init__(group=group, target=target, name=name)
        self.camera = camera

        self.object_detector_queue = object_detector_queue
        self.response_queue = queue.Queue()
        self.writer_queue = queue.Queue()

        self.clip_writer = ClipWriter(camera=camera, writer_queue=self.writer_queue)
        self.clip_writer.start()

        self.object_processor = ObjectProcessor(response_queue=self.response_queue, clip_writer=self.clip_writer)
        self.object_processor.start()

    def run(self):
        log("[motion_detector] [{}] Starting detector".format(self.camera["name"]))
        ctx = zmq.Context()
        s = ctx.socket(zmq.SUB)
        s.connect("ipc:///tmp/streamer_{}".format(self.camera["name"]))
        s.setsockopt(zmq.SUBSCRIBE, b"")
        s.setsockopt(zmq.RCVTIMEO, 2000)
        frame_idx = 0

        while not self.stop:
            try:
                msg = s.recv()
            except:
                continue

            A = np.frombuffer(msg, dtype=self.camera["meta"]["dtype"])
            frame = A.reshape(self.camera["meta"]["shape"])
            del A
            frame_idx += 1
            self.writer_queue.put(frame)

            if frame_idx % self.RATE == 0:
                self.object_detector_queue.put((self.response_queue, frame, int(time.time())))
                frame_idx = 0

        s.close()
        self.object_processor.stop = True
        self.object_processor.join()

        self.clip_writer.stop = True
        self.clip_writer.join()


