import zmq
import cv2
from threading import Thread
import numpy as np
import os

import time
from detectors.phase1 import MotionDetector

def clip_path(camera, timestamp):
    return "/dev/shm/{}_{}.mp4".format(camera, timestamp)

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
            bg_history=10,
            brightness_discard_level=50,
            bg_subs_scale_percent=0.1,
            group_boxes=True,
            expansion_step=5
        )

    def run(self):
        print("[phase1] [{}] Starting detector".format(self.camera["name"]))
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
                    print("[phase1] [{}] Finished: reader timeout".format(self.camera["name"]))
                    self.finish_detection()
                continue

            A = np.frombuffer(msg, dtype=self.camera["meta"]["dtype"])
            frame = A.reshape(self.camera["meta"]['shape'])
            del A

            boxes = self.detector.detect(frame)

            if self.detection_start == 0 and len(boxes) > 0:
                print("[phase1] [{}] Start detection".format(self.camera["name"]))
                self.start_detection()

            if self.detection_start > 0:

                if self.current_frame_index % self.RATE == 0:
                    self.queue.put({
                        "camera": self.camera["name"],
                        "start_time": self.detection_start,
                        "frame": frame,
                        "status": "progress"
                    })

                self.out.write(frame)
                self.current_frame_index += 1

                if time.time() - self.detection_start > self.MAX_LENGTH:
                    print("[phase1] [{}] Finished: max length".format(self.camera["name"]))
                    self.finish_detection()
                else:
                    if len(boxes) == 0:
                        if self.silence_start > 0:
                            if time.time() - self.silence_start > self.MAX_SILENCE:
                                print("[phase1] [{}] Finished: silence length".format(self.camera["name"]))
                                self.finish_detection()
                        else:
                            self.silence_start = int(time.time())
                    else:
                        self.silence_start = 0



        s.close()

    def start_detection(self):
        self.detection_start = int(time.time())
        self.current_frame_index = 0
        self.queue.put({
            "camera": self.camera["name"],
            "width": self.camera["meta"]["width"],
            "height": self.camera["meta"]["height"],
            "fps": self.camera["meta"]["fps"],
            "status": "start",
            "start_time": self.detection_start
        })

        filepath = clip_path(self.camera["name"], self.detection_start)

        fourcc = cv2.VideoWriter_fourcc('a', 'v', 'c', '1')
        if os.environ["CAPTURER_TYPE"] == "gstreamer":
            encoder = "x264enc" if os.environ["CAPTURER_HARDWARE"] == "cpu" else "vaapih264enc"
            command = "appsrc ! queue ! videoconvert ! video/x-raw ! {} ! video/x-h264,profile=baseline ! mp4mux ! filesink location={}".format(encoder, filepath)
        else:
            command = filepath


        self.out = cv2.VideoWriter(command, fourcc, self.camera["meta"]["fps"], (self.camera["meta"]["width"], self.camera["meta"]["height"]))


    def finish_detection(self):
        self.queue.put({
            "camera": self.camera["name"],
            "status": "done",
            "start_time": self.detection_start
        })

        self.out = None
        self.detection_start = 0
        self.silence_start = 0
