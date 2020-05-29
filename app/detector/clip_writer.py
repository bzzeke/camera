import cv2
import time
import queue
import os
import pickledb

from threading import Thread

from api import Api
from notifier import Notifier

class ClipWriter(Thread):
    stop = False
    camera = None
    write_queue = None
    writing = 0
    api = Api()

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None, write_queue=None):
        super(ClipWriter, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.write_queue = write_queue

    def run(self):

        out = None
        while not self.stop:

            if self.writing > 0 and out == None:

                file_path = self.api.path(self.camera["name"], self.writing, "mp4")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                fourcc = cv2.VideoWriter_fourcc("a", "v", "c", "1")
                out = cv2.VideoWriter(file_path, fourcc, self.camera["meta"]["fps"], (self.camera["meta"]["width"], self.camera["meta"]["height"]))

            if self.writing == 0 and out != None:
                out.release()
                out = None

            try:
                frame = self.write_queue.get(block=False)
            except queue.Empty:
                time.sleep(0.01)
                continue

            if out:
                out.write(frame)


    def make_snapshot(self, objects, frame, timestamp):
        origin_im_size = frame.shape[:-1]
        if len(objects) > 0:
            for obj in objects:
                if obj["xmax"] > origin_im_size[1] or obj["ymax"] > origin_im_size[0] or obj["xmin"] < 0 or obj["ymin"] < 0:
                    continue
                color = (int(min(obj["class_id"] * 12.5, 255)), min(obj["class_id"] * 7, 255), min(obj["class_id"] * 5, 255))
                cv2.rectangle(frame, (obj["xmin"], obj["ymin"]), (obj["xmax"], obj["ymax"]), color, 2)
                cv2.putText(frame, "{}, {}%".format(obj["category"], round(obj["confidence"] * 100, 1)), (obj["xmin"], obj["ymin"] - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 1)


        file_path = self.api.path(self.camera["name"], timestamp, "jpeg")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        cv2.imwrite(file_path, frame)

        notifier = Notifier()
        notifier.notify("Motion detected on camera {}".format(self.camera["name"]), [file_path])

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



