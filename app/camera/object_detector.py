import os
import time
import cv2
import queue

from threading import Thread
from openvino.inference_engine import IENetwork, IECore

from util import log
from models.config import config
from .yolo_params import YoloParams, intersection_over_union

class ObjectDetector(Thread):

    PATH_TO_MODEL = ""
    PATH_TO_LABELS = ""
    DETECTION_CATEGORIES = ["person", "car", "truck", "bus", "motorcycle", "bicycle"]

    DEVICE = "CPU"
    PROB_THRESHOLD = 0.5
    IOU_THRESHOLD = 0.4
    MAX_QUEUE_LENGTH = 5

    meta = {}
    labels_map = []
    net = None
    exec_net = None
    object_detector_queue = None
    stop = False

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, object_detector_queue=None):
        super(ObjectDetector, self).__init__(group=group, target=target, name=name)
        self.PATH_TO_MODEL = config.detector.model_path
        self.PATH_TO_LABELS = os.path.dirname(self.PATH_TO_MODEL) + "/classes.txt"
        self.DEVICE = config.detector.inference_device
        self.object_detector_queue = object_detector_queue

        self.init_model()


    def init_model(self):
        model_bin = os.path.splitext(self.PATH_TO_MODEL)[0] + ".bin"
        ie = IECore()
        self.net = ie.read_network(model=self.PATH_TO_MODEL, weights=model_bin)
        assert len(self.net.inputs.keys()) == 1, "Sample supports only YOLO V3 based single input topologies"

        self.net.batch_size = 1

        with open(self.PATH_TO_LABELS, "r") as f:
            self.labels_map = [x.strip() for x in f]

        self.exec_net = ie.load_network(network=self.net, num_requests=2, device_name=self.DEVICE)


    def run(self):
        log("[object_detector] Starting detector")

        input_blob = next(iter(self.net.inputs))
        n, c, h, w = self.net.inputs[input_blob].shape

        while not self.stop_flag:
            try:
                (out_queue, frame, timestamp) = self.object_detector_queue.get(block=False)
                if self.object_detector_queue.qsize() >= self.MAX_QUEUE_LENGTH:
                    log("[object_detector] Queue length - {} is too big, clearing".format(self.object_detector_queue.qsize()))
                    self.object_detector_queue.queue.clear()

            except queue.Empty:
                time.sleep(0.01)
                continue

            in_frame = cv2.resize(frame, (w, h))
            in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
            in_frame = in_frame.reshape((n, c, h, w))

            output = self.exec_net.infer(inputs={input_blob: in_frame})

            objects = list()
            for layer_name, out_blob in output.items():
                out_blob = out_blob.reshape(self.net.layers[self.net.layers[layer_name].parents[0]].out_data[0].shape)
                layer_params = YoloParams(self.net.layers[layer_name].params, out_blob.shape[2])
                objects += layer_params.parse_yolo_region(out_blob, in_frame.shape[2:], frame.shape[:-1], self.PROB_THRESHOLD)

            objects = self.filter_objects(objects)
            out_queue.put((frame, timestamp, objects))

    def filter_objects(self, objects):

        objects = sorted(objects, key=lambda obj : obj["confidence"], reverse=True)

        for i in range(len(objects)):
            objects[i]["category"] = self.labels_map[objects[i]["class_id"]]
            if objects[i]["confidence"] == 0:
                continue
            for j in range(i + 1, len(objects)):
                if intersection_over_union(objects[i], objects[j]) > self.IOU_THRESHOLD:
                    objects[j]["confidence"] = 0

        objects = [obj for obj in objects if obj["confidence"] >= self.PROB_THRESHOLD and obj["category"] in self.DETECTION_CATEGORIES]

        return objects

    def stop(self):
        self.stop_flag = True
        self.join()
