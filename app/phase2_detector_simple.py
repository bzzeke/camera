import os
import sys
from threading import Thread
import pickledb
import time
import queue

from util import log
import shutil
from datetime import date
from api import Api
from notifier import Notifier
from phase1_detector_simple import clip_path

from math import exp as exp
from openvino.inference_engine import IENetwork, IECore
import cv2

class YoloParams:
    def __init__(self, param, side):
        self.num = 3 if 'num' not in param else int(param['num'])
        self.coords = 4 if 'coords' not in param else int(param['coords'])
        self.classes = 80 if 'classes' not in param else int(param['classes'])
        self.side = side
        self.anchors = [10.0, 13.0, 16.0, 30.0, 33.0, 23.0, 30.0, 61.0, 62.0, 45.0, 59.0, 119.0, 116.0, 90.0, 156.0, 198.0, 373.0, 326.0] if 'anchors' not in param else [float(a) for a in param['anchors'].split(',')]
        self.isYoloV3 = False

        if param.get('mask'):
            mask = [int(idx) for idx in param['mask'].split(',')]
            self.num = len(mask)

            maskedAnchors = []
            for idx in mask:
                maskedAnchors += [self.anchors[idx * 2], self.anchors[idx * 2 + 1]]
            self.anchors = maskedAnchors

            self.isYoloV3 = True

    def entry_index(self, side, coord, classes, location, entry):
        side_power_2 = side ** 2
        n = location // side_power_2
        loc = location % side_power_2
        return int(side_power_2 * (n * (coord + classes + 1) + entry) + loc)


    def scale_bbox(self, x, y, h, w, class_id, confidence, h_scale, w_scale):
        xmin = int((x - w / 2) * w_scale)
        ymin = int((y - h / 2) * h_scale)
        xmax = int(xmin + w * w_scale)
        ymax = int(ymin + h * h_scale)
        return dict(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, class_id=class_id, confidence=confidence)


    def parse_yolo_region(self, blob, resized_image_shape, original_im_shape, threshold):
        _, _, out_blob_h, out_blob_w = blob.shape
        assert out_blob_w == out_blob_h, "Invalid size of output blob. It sould be in NCHW layout and height should " \
                                        "be equal to width. Current height = {}, current width = {}" \
                                        "".format(out_blob_h, out_blob_w)

        orig_im_h, orig_im_w = original_im_shape
        resized_image_h, resized_image_w = resized_image_shape
        objects = list()
        predictions = blob.flatten()
        side_square = self.side * self.side

        for i in range(side_square):
            row = i // self.side
            col = i % self.side
            for n in range(self.num):
                obj_index = self.entry_index(self.side, self.coords, self.classes, n * side_square + i, self.coords)
                scale = predictions[obj_index]
                if scale < threshold:
                    continue
                box_index = self.entry_index(self.side, self.coords, self.classes, n * side_square + i, 0)
                x = (col + predictions[box_index + 0 * side_square]) / self.side
                y = (row + predictions[box_index + 1 * side_square]) / self.side

                try:
                    w_exp = exp(predictions[box_index + 2 * side_square])
                    h_exp = exp(predictions[box_index + 3 * side_square])
                except OverflowError:
                    continue

                w = w_exp * self.anchors[2 * n] / (resized_image_w if self.isYoloV3 else self.side)
                h = h_exp * self.anchors[2 * n + 1] / (resized_image_h if self.isYoloV3 else self.side)
                for j in range(self.classes):
                    class_index = self.entry_index(self.side, self.coords, self.classes, n * side_square + i,
                                            self.coords + 1 + j)
                    confidence = scale * predictions[class_index]
                    if confidence < threshold:
                        continue
                    objects.append(self.scale_bbox(x=x, y=y, h=h, w=w, class_id=j, confidence=confidence,
                                            h_scale=orig_im_h, w_scale=orig_im_w))
        return objects


def intersection_over_union(box_1, box_2):
    width_of_overlap_area = min(box_1['xmax'], box_2['xmax']) - max(box_1['xmin'], box_2['xmin'])
    height_of_overlap_area = min(box_1['ymax'], box_2['ymax']) - max(box_1['ymin'], box_2['ymin'])
    if width_of_overlap_area < 0 or height_of_overlap_area < 0:
        area_of_overlap = 0
    else:
        area_of_overlap = width_of_overlap_area * height_of_overlap_area
    box_1_area = (box_1['ymax'] - box_1['ymin']) * (box_1['xmax'] - box_1['xmin'])
    box_2_area = (box_2['ymax'] - box_2['ymin']) * (box_2['xmax'] - box_2['xmin'])
    area_of_union = box_1_area + box_2_area - area_of_overlap
    if area_of_union == 0:
        return 0
    return area_of_overlap / area_of_union


class Phase2Detector(Thread):

    PATH_TO_MODEL = ""
    PATH_TO_LABELS = ""
    DETECTION_CATEGORIES = ["person", "car", "truck", "bus", "motorcycle", "bicycle"]

    DEVICE = "CPU"
    PROB_THRESHOLD = 0.5
    IOU_THRESHOLD = 0.4

    meta = {}
    labels_map = []
    net = None
    exec_net = None
    queue = None
    stop = False

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, queue=None):
        super(Phase2Detector, self).__init__(group=group, target=target, name=name)
        self.PATH_TO_MODEL = os.environ["MODEL_PATH"]
        self.PATH_TO_LABELS = os.path.dirname(self.PATH_TO_MODEL) + "/coco_classes.txt"
        self.DEVICE = os.environ["INFERENCE_DEVICE"]
        self.queue = queue

        self.init_model()


    def init_model(self):
        model_bin = os.path.splitext(self.PATH_TO_MODEL)[0] + ".bin"
        ie = IECore()
        self.net = ie.read_network(model=self.PATH_TO_MODEL, weights=model_bin)
        assert len(self.net.inputs.keys()) == 1, "Sample supports only YOLO V3 based single input topologies"

        self.net.batch_size = 1

        with open(self.PATH_TO_LABELS, 'r') as f:
            self.labels_map = [x.strip() for x in f]

        self.exec_net = ie.load_network(network=self.net, num_requests=2, device_name=self.DEVICE)


    def run(self):
        api = Api()

        log("[phase2] Starting detector")

        cur_request_id = 0
        input_blob = next(iter(self.net.inputs))
        n, c, h, w = self.net.inputs[input_blob].shape

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

            request_id = cur_request_id
            in_frame = cv2.resize(frame_img, (w, h))
            in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
            in_frame = in_frame.reshape((n, c, h, w))

            s = time.time()
            self.exec_net.start_async(request_id=request_id, inputs={input_blob: in_frame})

            objects = list()
            if self.exec_net.requests[cur_request_id].wait(-1) == 0:
                output = self.exec_net.requests[cur_request_id].outputs
                for layer_name, out_blob in output.items():
                    out_blob = out_blob.reshape(self.net.layers[self.net.layers[layer_name].parents[0]].out_data[0].shape)
                    layer_params = YoloParams(self.net.layers[layer_name].params, out_blob.shape[2])
                    objects += layer_params.parse_yolo_region(out_blob, in_frame.shape[2:], frame_img.shape[:-1], self.PROB_THRESHOLD)

            objects = self.filter_objects(objects)

            log("[phase2] [{}] Frame processed for: {} seconds, queue length: {}".format(frame["camera"], (time.time() - s), self.queue.qsize()))

            if len(objects):
                for obj in objects:
                    self.meta[frame["camera"]][frame["start_time"]]["detections"].add(obj["category"])

                if self.meta[frame["camera"]][frame["start_time"]]["snapshot"] == False:

                    origin_im_size = frame_img.shape[:-1]
                    save = False
                    for obj in objects:
                        if obj['xmax'] > origin_im_size[1] or obj['ymax'] > origin_im_size[0] or obj['xmin'] < 0 or obj['ymin'] < 0:
                            continue
                        color = (int(min(obj['class_id'] * 12.5, 255)), min(obj['class_id'] * 7, 255), min(obj['class_id'] * 5, 255))
                        det_label = self.labels_map[obj['class_id']] if self.labels_map and len(self.labels_map) >= obj['class_id'] else str(obj['class_id'])

                        cv2.rectangle(frame_img, (obj['xmin'], obj['ymin']), (obj['xmax'], obj['ymax']), color, 2)
                        cv2.putText(frame_img, det_label + ' ' + str(round(obj['confidence'] * 100, 1)) + ' %', (obj['xmin'], obj['ymin'] - 7), cv2.FONT_HERSHEY_COMPLEX, 0.6, color, 1)
                        save = True

                    if save:
                        self.save_snapshot(frame_img, frame, api)

    def save_snapshot(self, frame_img, frame, api):
        snapshot_filename = api.path(frame["camera"], frame["start_time"], "jpeg")
        os.makedirs(os.path.dirname(snapshot_filename), exist_ok=True)
        cv2.imwrite(snapshot_filename, frame_img)

        notifier = Notifier()
        notifier.notify("Motion detected on camera {}".format(frame["camera"]), [snapshot_filename])

        self.meta[frame["camera"]][frame["start_time"]]["snapshot"] = True

    def filter_objects(self, objects):

        objects = sorted(objects, key=lambda obj : obj['confidence'], reverse=True)

        for i in range(len(objects)):
            objects[i]["category"] = self.labels_map[objects[i]['class_id']]
            if objects[i]['confidence'] == 0:
                continue
            for j in range(i + 1, len(objects)):
                if intersection_over_union(objects[i], objects[j]) > self.IOU_THRESHOLD:
                    objects[j]['confidence'] = 0

        objects = [obj for obj in objects if obj['confidence'] >= self.PROB_THRESHOLD and obj["category"] in self.DETECTION_CATEGORIES]

        return objects

