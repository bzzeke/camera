import cv2
import time
import queue
import os
import pickledb
import numpy as np

from threading import Thread

from api import Api
from notifier import Notifier

class ClipWriter(Thread):

    COLOR = (153, 255, 51)
    stop = False
    camera = None
    circular_queue = None
    writing = 0
    api = Api()

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None, circular_queue=None):
        super(ClipWriter, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.circular_queue = circular_queue

    def run(self):

        out = None
        while not self.stop:

            if self.writing > 0 and out == None:

                self.circular_queue.drop = False
                file_path = self.api.path(self.camera["name"], self.writing, "mp4")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                fourcc = cv2.VideoWriter_fourcc("a", "v", "c", "1")
                out = cv2.VideoWriter(file_path, fourcc, self.camera["meta"]["fps"], (self.camera["meta"]["width"], self.camera["meta"]["height"]))

            if self.writing == 0 and out != None:
                out.release()
                out = None
                self.circular_queue.drop = True

            if self.writing > 0:
                frame = self.circular_queue.get()
            else:
                time.sleep(0.01)
                continue

            if out:
                out.write(frame)

    def make_snapshot(self, objects, frame, timestamp):

        origin_im_size = frame.shape[:-1]
        snapshot_frame = np.array(frame, copy=True)
        fontface = cv2.FONT_HERSHEY_COMPLEX
        scale = 0.6
        thickness = 1
        labels = []

        if len(objects) > 0:
            for obj in objects:
                if obj["xmax"] > origin_im_size[1] or obj["ymax"] > origin_im_size[0] or obj["xmin"] < 0 or obj["ymin"] < 0:
                    continue

                cv2.rectangle(snapshot_frame, (obj["xmin"], obj["ymin"]), (obj["xmax"], obj["ymax"]), self.COLOR, 2)

                labels.append(obj["category"])
                label = "{}, {}%".format(obj["category"], round(obj["confidence"] * 100, 1))
                (text_width, text_height) = cv2.getTextSize(label, fontface, fontScale=scale, thickness=thickness)[0]
                text_offset_x = obj["xmin"]
                text_offset_y = obj["ymin"] - 7

                box_coords = ((obj["xmin"], obj["ymin"]), (obj["xmin"] + text_width + 2, text_offset_y - text_height - 2))
                cv2.rectangle(snapshot_frame, box_coords[0], box_coords[1], self.COLOR, cv2.FILLED)
                cv2.putText(snapshot_frame, label, (text_offset_x, text_offset_y), cv2.FONT_HERSHEY_COMPLEX, 0.6, (0, 0, 0), 1)

        file_path = self.api.path(self.camera["name"], timestamp, "jpeg")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        cv2.imwrite(file_path, snapshot_frame)
        del snapshot_frame

        notifier = Notifier()
        notifier.notify("Motion detected on camera {}: {}, frame size: {}".format(self.camera["name"], ", ".join(labels), frame.nbytes), [(file_path, "{}_{}.jpeg".format(self.camera["name"], timestamp))])

    def save_meta(self, categories, timestamp):
        file_path = self.api.db_path(timestamp)

        db = pickledb.load(file_path, True, sig=False)

        if not db.exists("clips"):
            db.lcreate("clips")

        db.ladd("clips", {
            "camera": self.camera["name"],
            "start_time": timestamp,
            "objects": list(categories)
        })



