import zmq
import cv2
from threading import Thread
import numpy as np
import os

from time import time
from detectors.phase1 import MotionDetector
from api import Api

class Phase1Detector(Thread):
    MAX_LENGTH = 30 # seconds
    MAX_SILENCE = 3 # seconds
    RATE = 10 # each N frame

    stop = False
    camera = {}
    detector = None
    detection_start = 0
    silence_start = 0
    queue = None
    current_frame_index = 0
    out = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None, queue=None):
        super(Phase1Detector, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.queue = queue
        self.stop = False
        self.detector = MotionDetector(
            bg_history=20,
            brightness_discard_level=25,
            bg_subs_scale_percent=0.1,
            group_boxes=True,
            expansion_step=5
        )

    def run(self):
        ctx = zmq.Context()
        s = ctx.socket(zmq.SUB)
        s.connect("ipc:///tmp/streamer_%s" % self.camera["name"])
        s.setsockopt(zmq.SUBSCRIBE, b"")
        s.setsockopt(zmq.RCVTIMEO, 2000)

        while not self.stop:
            try:
                msg = s.recv()
            except:
                if self.detection_start > 0:
                    print("Finished phase 1: reader timeout")
                    self.finish_detection()
                continue

            A = np.frombuffer(msg, dtype=self.camera["meta"]["dtype"])
            frame = A.reshape(self.camera["meta"]['shape'])
            del A

            boxes = self.detector.detect(frame)

            if self.detection_start == 0 and len(boxes) > 0:
                print("Start phase 1 detection")
                self.start_detection()

            if self.detection_start > 0:
                if self.current_frame_index % self.RATE == 0:
                    print("Sending frame: %s" % self.current_frame_index)
                    self.queue.put({
                        "camera": self.camera["name"],
                        "start_time": self.detection_start,
                        "frame": frame,
                        "status": "progress"
                    })

                self.out.write(frame)
                self.current_frame_index += 1

                if time() - self.detection_start > self.MAX_LENGTH:
                    print("Finished phase 1: max length reached")
                    self.finish_detection()
                else:
                    if len(boxes) == 0:
                        if self.silence_start > 0:
                            if time() - self.silence_start > self.MAX_SILENCE:
                                print("Finished phase 1: silence length reached")
                                self.finish_detection()
                        else:
                            self.silence_start = int(time())
                    else:
                        self.silence_start = 0



        s.close()

    def start_detection(self):
        self.detection_start = int(time())
        self.current_frame_index = 0
        self.queue.put({
            "camera": self.camera["name"],
            "width": self.camera["meta"]["width"],
            "height": self.camera["meta"]["height"],
            "fps": self.camera["meta"]["fps"],
            "status": "start",
            "start_time": self.detection_start
        })

        api = Api()
        filepath =  api.path(self.camera["name"], self.detection_start, "mp4")
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        # fourcc = cv2.VideoWriter_fourcc('a', 'v', 'c', '1')
        self.out = cv2.VideoWriter(filepath, fourcc, self.camera["meta"]["fps"], (self.camera["meta"]["width"], self.camera["meta"]["height"]))


    def finish_detection(self):
        self.queue.put({
            "camera": self.camera["name"],
            "status": "done",
            "start_time": self.detection_start
        })

        self.out = None
        self.detection_start = 0
        self.silence_start = 0
