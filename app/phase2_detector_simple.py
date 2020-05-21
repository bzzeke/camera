import numpy as np
import os
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
import zipfile
from threading import Thread
from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image
import cv2
import pickledb
import time
import queue

from util import log
import shutil
from datetime import date
from api import Api
from notifier import Notifier
from phase1_detector_simple import clip_path

sys.path.append("detectors")

from detectors.object_detection.utils import label_map_util
from detectors.object_detection.utils import visualization_utils as vis_util

# tf.get_logger().setLevel('INFO')

class Phase2Detector(Thread):

    PATH_TO_MODEL = ""
    PATH_TO_LABELS = "detectors/object_detection/data/mscoco_label_map.pbtxt"
    NUM_CLASSES = 90
    DETECTION_CATEGORIES = ["person", "car", "truck", "bus", "motorcycle", "bicycle"]
    RATE = 10

    detection_graph = None
    category_index = None
    meta = {}
    queue = None
    stop = False

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, queue=None):
        super(Phase2Detector, self).__init__(group=group, target=target, name=name)
        self.PATH_TO_MODEL = os.environ["MODEL_PATH"]
        self.queue = queue

        self.init_detection_graph()
        self.init_labels()

    def init_detection_graph(self):
        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(self.PATH_TO_MODEL, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name="")

    def init_labels(self):
        label_map = label_map_util.load_labelmap(self.PATH_TO_LABELS)
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=self.NUM_CLASSES, use_display_name=True)
        self.category_index = label_map_util.create_category_index(categories)

    def run(self):
        api = Api()

        log("[phase2] Starting detector")
        with self.detection_graph.as_default():
            with tf.compat.v1.Session(graph=self.detection_graph) as sess:
                while not self.stop:
                    try:
                        frame = self.queue.get(block=False)
                    except queue.Empty:
                        time.sleep(0.1)
                        continue

                    if frame["status"] == "done":
                        clip_filename = clip_path(frame["camera"], frame["start_time"])
                        if len(self.meta[frame["camera"]][frame["start_time"]]["detections"]) > 0:
                            log("[phase2] [{}] Finished, timestamp: {}, detections: {}".format(frame["camera"], frame["start_time"], ", ".join(self.meta[frame["camera"]][frame["start_time"]]["detections"])))
                            db_filename = api.db_path(frame["start_time"])
                            os.makedirs(os.path.dirname(db_filename), exist_ok=True)
                            db = pickledb.load(db_filename, True, sig=False)

                            if not db.exists("clips"):
                                db.lcreate("clips")

                            db.ladd("clips", {
                                "camera": frame["camera"],
                                "start_time": frame["start_time"],
                                "objects": list(self.meta[frame["camera"]][frame["start_time"]]["detections"])
                            })

                            target_filename = api.path(frame["camera"], frame["start_time"], "mp4")
                            os.makedirs(os.path.dirname(target_filename), exist_ok=True)
                            shutil.move(clip_filename, target_filename)
                        else:
                            log("[phase2] [{}] Finished, timestamp: {}, no detections, removing clip".format(frame["camera"], frame["start_time"]))
                            os.remove(clip_filename)

                        del self.meta[frame["camera"]][frame["start_time"]]
                        continue
                    elif frame["status"] == "start":
                        log("[phase2] [{}] Start detection, timestamp: {}".format(frame["camera"], frame["start_time"]))

                        if frame["camera"] not in self.meta:
                            self.meta[frame["camera"]] = {}

                        self.meta[frame["camera"]][frame["start_time"]] = {
                            "detections": set(),
                            "snapshot": False,
                            "width": frame["width"],
                            "height": frame["height"]
                        }
                        continue
                    else:
                        frame_img = frame["frame"]


                    small_frame = cv2.resize(frame_img, (640, int(640 * self.meta[frame["camera"]][frame["start_time"]]["height"] / self.meta[frame["camera"]][frame["start_time"]]["width"])), interpolation = cv2.INTER_AREA)
                    image_np_expanded = np.expand_dims(small_frame, axis=0)

                    image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
                    boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
                    scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
                    classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
                    num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

                    s = time.time()
                    (boxes, scores, classes, num_detections) = sess.run(
                        [boxes, scores, classes, num_detections],
                        feed_dict={image_tensor: image_np_expanded}
                    )
                    log("[phase2] [{}] Frame processed for: {} seconds, queue length: {}".format(frame["camera"], (time.time() - s), self.queue.qsize()))

                    boxes = np.squeeze(boxes)
                    classes = np.squeeze(classes).astype(np.int32)
                    scores = np.squeeze(scores)

                    (boxes, scores, classes) = self.filter_boxes(0.5, boxes, scores, classes, self.DETECTION_CATEGORIES)

                    if len(boxes):


                        for i in range(classes.shape[0]):
                            if classes[i] in self.category_index.keys():
                                self.meta[frame["camera"]][frame["start_time"]]["detections"].add(self.category_index[classes[i]]['name'])

                        if self.meta[frame["camera"]][frame["start_time"]]["snapshot"] == False:
                            frame_img = vis_util.visualize_boxes_and_labels_on_image_array(
                                np.array(frame_img),
                                boxes,
                                classes,
                                scores,
                                self.category_index,
                                use_normalized_coordinates=True,
                                line_thickness=3)

                            self.save_snapshot(frame_img, frame, api)

    def save_snapshot(self, frame_img, frame, api):
        snapshot_filename = api.path(frame["camera"], frame["start_time"], "jpeg")
        os.makedirs(os.path.dirname(snapshot_filename), exist_ok=True)
        cv2.imwrite(snapshot_filename, frame_img)

        notifier = Notifier()
        notifier.notify("Motion detected on camera {}".format(frame["camera"]), [snapshot_filename])

        self.meta[frame["camera"]][frame["start_time"]]["snapshot"] = True

    def filter_boxes(self, min_score, boxes, scores, classes, categories):
        n = len(classes)
        idxs = []

        for i in range(n):
            if self.category_index[classes[i]]['name'] in categories and scores[i] >= min_score:
                idxs.append(i)

        filtered_boxes = boxes[idxs, ...]
        filtered_scores = scores[idxs, ...]
        filtered_classes = classes[idxs, ...]
        return filtered_boxes, filtered_scores, filtered_classes