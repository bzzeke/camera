import time
import sys
import threading
import queue
import os
import jdb

from threading import Thread, RLock
from urllib.parse import urlparse

from util import import_env, log
from streamer import Streamer
from api import ApiServer
from motion_detector import MotionDetector
from detector.object_detector import ObjectDetector
from cleanup import Cleanup

class State():
    CAMERA_CONFIG = "cameras.json"

    cameras = {}
    lock = RLock()
    threads = []
    q = queue.Queue()
    db = None

    def __init__(self):
        self.db = jdb.load(self.CAMERA_CONFIG, True)
        self.cameras = self.init_cameras()

    def init_cameras(self):
        it = 0
        cameras = {}

        while "CAM_NAME_{}".format(it) in os.environ:
            cam = os.environ["CAM_NAME_{}".format(it)]
            cameras[cam] = {
                "name": cam,
                "url": os.environ["CAM_URL_{}".format(it)],
                "detection": "CAM_DETECTION_{}".format(it) in os.environ,
                "codec": os.environ["CAM_CODEC_{}".format(it)],
                "meta": {
                    "dtype": None,
                    "shape": None
                }
            }

            if "CAM_ONVIF_{}".format(it) in os.environ:
                parts = urlparse(os.environ["CAM_ONVIF_{}".format(it)])
                cameras[cam]["onvif"] = {
                    "host": parts.hostname,
                    "port": parts.port,
                    "username": parts.username,
                    "password": parts.password
                }

            if "CAM_PTZ_FEATURES_{}".format(it) in os.environ:
                cameras[cam]["ptz_features"] = os.environ["CAM_PTZ_FEATURES_{}".format(it)]

            zone = []
            if self.db.exists(cam) and self.db.dexists(cam, "zone"):
                zone = self.db.dget(cam, "zone")
            cameras[cam]["zone"] = zone

            it += 1

        return cameras

    def set_camera(self, camera):
        self.lock.acquire()
        try:

            self.cameras[camera["name"]] = camera

            if not self.db.exists(camera["name"]):
                self.db.dcreate(camera["name"])

            self.db.dadd(camera["name"], ("zone", camera["zone"]))

            if camera["detection"]:
                self.restart_detection(camera)

        finally:
            self.lock.release()

    def restart_detection(self, camera):
        log("[state] Restart detection for camera {}".format(camera["name"]))
        for thread in self.threads:
            if thread.camera["name"] == camera["name"]:
                thread.stop = True
                thread.join()
                self.threads.remove(thread)

        motion_detector = MotionDetector(camera=camera, object_detector_queue=self.q)
        motion_detector.start()
        self.threads.append(motion_detector)

if __name__ == "__main__":
    import_env()

    state = State()

    object_detector = ObjectDetector(object_detector_queue=state.q)
    object_detector.start()

    cleanup = Cleanup()
    cleanup.start()

    streamer = Streamer(state=state)
    streamer.start()

    api_server = ApiServer(state=state)
    api_server.start()

    total_threads = threading.active_count()

    try:
        while True:
            time.sleep(1)
            if threading.active_count() < total_threads:
                log("[main] Some thread is dead")
                sys.exit(1)
    except KeyboardInterrupt:

        log("[main] Stopping all")
        cleanup.stop = True
        streamer.stop = True
        object_detector.stop = True
        api_server.stop()

        for thread in state.threads:
            thread.stop = True
            thread.join()

        cleanup.join()
        streamer.join()
        object_detector.join()
        api_server.join()
