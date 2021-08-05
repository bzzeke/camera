from app.broker import Subscriber
import cv2
import numpy as np
import time
import queue

from threading import Thread

from util import log
from broker import Subscriber
from camera.clip_writer import ClipWriter
from camera.object_processor import ObjectProcessor

#
#
# [frame] -> ObjectDetector -> [objects] -> ObjectProcessor -> [timestamp] -> ClipWriter
#
#

class MotionDetector(Thread):
    RATE = 5 # each N frame, move to config?

    stop_flag = False
    camera = None

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
        log("[motion_detector] [{}] Starting detector".format(self.camera.name))

        subscriber = Subscriber()
        self.camera.publisher.attach(subscriber)
        frame_idx = 0

        while not self.stop_flag:

            frame = subscriber.sub()
            if not frame:
                continue

            frame_idx += 1
            self.writer_queue.put(frame)

            if frame_idx % self.RATE == 0:
                self.object_detector_queue.put((self.response_queue, frame, int(time.time())))
                frame_idx = 0

        self.camera.publisher.detach(subscriber)
        self.object_processor.stop()
        self.clip_writer.stop()

    def stop(self):
        self.stop_flag = True
        self.join()


