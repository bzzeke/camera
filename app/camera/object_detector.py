import os
import time
import cv2
import queue
import ngraph

from threading import Thread
from openvino.inference_engine import IENetwork, IECore

from util import log
from models.config import config
from .yolo_params import YoloParams, intersection_over_union, parse_yolo_region

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
    yolo_layer_params = {}
    exec_net = None
    object_detector_queue = None
    stop_flag = False

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, object_detector_queue=None):
        super(ObjectDetector, self).__init__(group=group, target=target, name=name)
        self.PATH_TO_MODEL = config.detector.model_path
        self.PATH_TO_LABELS = os.path.dirname(self.PATH_TO_MODEL) + "/classes.txt"
        self.DEVICE = config.detector.inference_device.value
        self.object_detector_queue = object_detector_queue

        self.init_model()


    def init_model(self):
        model_bin = os.path.splitext(self.PATH_TO_MODEL)[0] + ".bin"
        ie = IECore()
        self.net = ie.read_network(model=self.PATH_TO_MODEL, weights=model_bin)
        # assert len(self.net.inputs.keys()) == 1, "Sample supports only YOLO V3 based single input topologies"

        self.net.batch_size = 1

        with open(self.PATH_TO_LABELS, "r") as f:
            self.labels_map = [x.strip() for x in f]


        ng_func = ngraph.function_from_cnn(self.net)
        for node in ng_func.get_ordered_ops():
            layer_name = node.get_friendly_name()
            if layer_name not in self.net.outputs:
                continue

            shape = list(node.inputs()[0].get_source_output().get_node().shape)
            yolo_params = YoloParams(node._get_attributes(), shape[2:4])
            self.yolo_layer_params[layer_name] = (shape, yolo_params)

        self.exec_net = ie.load_network(network=self.net, num_requests=2, device_name=self.DEVICE)

    def run(self):
        log("[object_detector] Starting detector")

        input_blob = next(iter(self.net.input_info))
        n, c, h, w = self.net.input_info[input_blob].input_data.shape

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
                layer_params = self.yolo_layer_params[layer_name]
                out_blob.shape = layer_params[0]
                objects += parse_yolo_region(out_blob, in_frame.shape[2:], frame.shape[0:2], layer_params[1], self.PROB_THRESHOLD)

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

