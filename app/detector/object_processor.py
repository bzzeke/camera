import queue
import time
import cv2

from threading import Thread
from shapely.geometry import Polygon

from util import log

class ObjectProcessor(Thread):
    stop = False
    response_queue = None
    scene_state = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, response_queue=None, clip_writer=None):
        super(ObjectProcessor, self).__init__(group=group, target=target, name=name)
        self.response_queue = response_queue
        self.stop = False
        self.scene_state = SceneState(clip_writer=clip_writer)

    def run(self):
        while not self.stop:
            try:
                (frame, timestamp, objects) = self.response_queue.get(block=False)
            except queue.Empty:
                time.sleep(0.1)
                continue

            self.scene_state.check_state(objects, frame, timestamp)



class SceneState():
    FRAMES_WITH_NO_MOTION = 3
    SPOT_PERCENTAGE = 0.1

    categories = set()
    objects = None
    stale_counter = 0
    start_timestamp = 0
    clip_writer = None
    zone = None
    has_snapshot = False

    def __init__(self, clip_writer=None):
        self.clip_writer = clip_writer
        self.zone = self.convert_zone(clip_writer.camera["zone"])

    def check_state(self, objects, frame, timestamp):
        objects = list(filter(lambda obj: self.object_in_zone(obj) == True, objects))

        if self.objects == None:
            self.objects = self.generate_state(objects)
            return

        if len(objects) != len(self.objects):
            self.start_motion(objects, frame, timestamp)
        else:
            hit_spots = set()
            for obj in objects:
                hit_spots = self.in_spot(obj, self.objects, hit_spots)

            if len(hit_spots) != len(self.objects):
                self.start_motion(objects, frame, timestamp)
                if self.has_snapshot == False:
                    self.clip_writer.make_snapshot(objects, frame, self.start_timestamp)
                    self.has_snapshot = True
            else:
                self.stale_counter += 1

        # stop detection
        if self.stale_counter >= self.FRAMES_WITH_NO_MOTION:
            self.stale_counter = 0
            self.stop_motion(timestamp)

        self.objects = self.generate_state(objects)

    def start_motion(self, objects, frame, timestamp):
        self.stale_counter = 0
        if self.start_timestamp == 0:
            self.start_timestamp = timestamp
            self.clip_writer.start_timestamp = timestamp
            self.has_snapshot = False

    def stop_motion(self, timestamp):
        if self.start_timestamp > 0:
            log("[processor] Motion recorded from {} to {} frame".format(self.start_timestamp, timestamp))

            self.clip_writer.categories = self.categories
            self.clip_writer.start_timestamp = 0
            self.categories = set()
            self.start_timestamp = 0

    def in_spot(self, new_obj, objects, hit_spots):
        center_x = new_obj["xmin"] + int((new_obj["xmax"] - new_obj["xmin"]) / 2)
        center_y = new_obj["ymin"] + int((new_obj["ymax"] - new_obj["ymin"]) / 2)

        for obj in objects:
            (xmin, xmax, ymin, ymax) = obj["spot"]

            if xmin <= center_x <= xmax and ymin <= center_y <= ymax:
                hit_spots.add(obj["spot"])
                break

        return hit_spots

    def calculate_spot(self, obj):
        return (
            obj["center_x"] - int(obj["width"] * self.SPOT_PERCENTAGE),
            obj["center_x"] + int(obj["width"] * self.SPOT_PERCENTAGE),
            obj["center_y"] - int(obj["height"] * self.SPOT_PERCENTAGE),
            obj["center_y"] + int(obj["height"] * self.SPOT_PERCENTAGE),
        )

    def generate_state(self, objects):
        state = []
        for obj in objects:
            new_obj = {
                "center_x": obj["xmin"] + int((obj["xmax"] - obj["xmin"]) / 2),
                "center_y": obj["ymin"] + int((obj["ymax"] - obj["ymin"]) / 2),
                "left": obj["xmin"],
                "top": obj["ymin"],
                "width": obj["xmax"] - obj["xmin"],
                "height": obj["ymax"] - obj["ymin"],
                "class_id": obj["class_id"],
                "confidence": obj["confidence"]
            }

            new_obj["spot"] = self.calculate_spot(new_obj)

            self.categories.add(obj["category"])
            state.append(new_obj)

        return state

    def convert_zone(self, zone):
        vertex = []
        new_zone = zone.copy()
        while len(new_zone) > 0:
            x = new_zone.pop(0)
            y = new_zone.pop(0)
            vertex.append((x, y))

        return Polygon(vertex)

    def convert_object(self, obj):
        return Polygon([(obj["xmin"], obj["ymin"]), (obj["xmax"], obj["ymin"]), (obj["xmax"], obj["ymax"]), (obj["xmin"], obj["ymax"])])

    def object_in_zone(self, obj):
        if self.zone.is_empty:
            return True

        if self.convert_object(obj).intersects(self.zone):
            return True

        return False

