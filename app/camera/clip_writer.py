import cv2
import time
import queue
import os
import jdb
import numpy as np
import collections

from threading import Thread

from api.clips import Clips
from util import log

class ClipWriter(Thread):

    COLOR = (153, 255, 51)
    CIRCULAR_BUFFER = 5 # seconds

    stop_flag = False
    camera = None
    writer_queue = None
    start_timestamp = 0
    api = Clips()
    categories = []

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None, writer_queue=None):
        super(ClipWriter, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.writer_queue = writer_queue

    def run(self):

        out = None
        frame = None
        last_timestamp = 0
        circular_queue = collections.deque(maxlen=self.CIRCULAR_BUFFER * self.camera.meta["fps"])

        while not self.stop_flag:

            frame = self.writer_queue.get()
            circular_queue.append(frame)

            if self.start_timestamp > 0 and out == None:
                last_timestamp = self.start_timestamp
                self.categories = []
                file_path = self.api.path(self.camera.id, self.start_timestamp, self.api.video_format)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                fourcc = cv2.VideoWriter_fourcc("a", "v", "c", "1")
                out = cv2.VideoWriter(file_path, fourcc, self.camera.meta["fps"], (self.camera.meta["width"], self.camera.meta["height"]))

                while True:
                    try:
                        out.write(circular_queue.popleft())
                    except Exception:
                        break
                continue

            if self.start_timestamp == 0 and out != None:
                out.release()
                out = None
                self.finish_clip(last_timestamp)
                last_timestamp = 0

            if out:
                out.write(frame)

    def finish_clip(self, timestamp):
        file_path = self.api.path(self.camera.id, timestamp, self.api.image_format)
        if os.path.isfile(file_path):
            self.save_meta(self.categories, timestamp)
        else:
            log("[clip writer] Cleanup flickering for timestamp {}".format(timestamp))
            self.cleanup(timestamp)

    def make_snapshot(self, objects, frame, timestamp):

        origin_im_size = frame.shape[:-1]
        snapshot_frame = np.array(frame, copy=True)
        fontface = cv2.FONT_HERSHEY_COMPLEX
        scale = 0.6
        thickness = 1
        labels = []

        if len(objects) > 0:
            for obj in objects:
                obj["xmin"] = max(0, obj["xmin"])
                obj["ymin"] = max(0, obj["ymin"])
                obj["xmax"] = min(origin_im_size[1], obj["xmax"])
                obj["ymax"] = min(origin_im_size[0], obj["ymax"])

                cv2.rectangle(snapshot_frame, (obj["xmin"], obj["ymin"]), (obj["xmax"], obj["ymax"]), self.COLOR, 2)

                labels.append(obj["category"])
                label = "{}, {}%".format(obj["category"], round(obj["confidence"] * 100, 1))
                (text_width, text_height) = cv2.getTextSize(label, fontface, fontScale=scale, thickness=thickness)[0]
                text_offset_x = obj["xmin"]
                text_offset_y = obj["ymin"] - 7

                box_coords = ((obj["xmin"], obj["ymin"]), (obj["xmin"] + text_width + 2, text_offset_y - text_height - 2))
                cv2.rectangle(snapshot_frame, box_coords[0], box_coords[1], self.COLOR, cv2.FILLED)
                cv2.putText(snapshot_frame, label, (text_offset_x, text_offset_y), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 0, 0), 1)

        file_path = self.api.path(self.camera.id, timestamp, self.api.image_format)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        cv2.imwrite(file_path, snapshot_frame)
        del snapshot_frame

        self.camera.notifier.notify("Motion detected on camera {}: {}".format(self.camera.name, ", ".join(labels)), [(file_path, [self.camera.id, timestamp])])

    def save_meta(self, categories, timestamp):
        file_path = self.api.db_path(timestamp)

        db = jdb.load(file_path, True)

        if not db.exists("clips"):
            db.lcreate("clips")

        db.ladd("clips", {
            "camera": self.camera.id,
            "start_time": timestamp,
            "objects": list(categories)
        })

    def cleanup(self, timestamp):
        file_path = self.api.path(self.camera.id, timestamp, "mp4")
        os.remove(file_path)

    def stop(self):
        self.stop_flag = True
        self.join()


