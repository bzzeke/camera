import os
import time
import cv2
import queue

from threading import Thread
from openvino.inference_engine import IENetwork, IECore

from util import log
from .yolo_params import YoloParams, intersection_over_union

class ObjectDetector(Thread):

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
    object_detector_queue = None
    stop = False

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, object_detector_queue=None):
        super(ObjectDetector, self).__init__(group=group, target=target, name=name)
        self.PATH_TO_MODEL = os.environ["MODEL_PATH"]
        self.PATH_TO_LABELS = os.path.dirname(self.PATH_TO_MODEL) + "/coco_classes.txt"
        self.DEVICE = os.environ["INFERENCE_DEVICE"]
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

        cur_request_id = 0
        input_blob = next(iter(self.net.inputs))
        n, c, h, w = self.net.inputs[input_blob].shape

        while not self.stop:
            try:
                (out_queue, frame, timestamp) = self.object_detector_queue.get(block=False)
                log("[object_detector] Queue length: {}".format(self.object_detector_queue.qsize()))
            except queue.Empty:
                time.sleep(0.01)
                continue

            request_id = cur_request_id
            in_frame = cv2.resize(frame, (w, h))
            in_frame = in_frame.transpose((2, 0, 1))  # Change data layout from HWC to CHW
            in_frame = in_frame.reshape((n, c, h, w))

            self.exec_net.start_async(request_id=request_id, inputs={input_blob: in_frame})

            objects = list()
            if self.exec_net.requests[cur_request_id].wait(-1) == 0:
                output = self.exec_net.requests[cur_request_id].outputs
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

