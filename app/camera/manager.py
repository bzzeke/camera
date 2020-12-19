import os
import queue

from pyhap.accessory import Bridge

from camera.camera import Camera
# from camera.object_detector import ObjectDetector
from homekit import HomekitCamera, HomekitWorker
from adapters.pyhap import HomekitDriver
from models.config import config, CameraModel
from util import log

class CameraManager:
    cameras = {}
    object_detector_queue = None
    object_detector = None
    homekit_driver = None
    homekit_bridge = None
    homekit_worker = None
    notifier = None

    def __init__(self, notifier=None):
        self.notifier = notifier
        self.object_detector_queue = queue.Queue()
        # self.object_detector = ObjectDetector(object_detector_queue=self.object_detector_queue)
        # self.object_detector.start()


    def start_homekit(self):
        self.homekit_driver = HomekitDriver(address=os.environ["API_SERVER_HOST"], port=51826, persist_file="{}/data/bridge.state".format(config.storage_path))
        self.homekit_bridge = Bridge(self.homekit_driver, 'Camera bridge')
        self.homekit_driver.add_accessory(accessory=self.homekit_bridge)
        self.homekit_worker = HomekitWorker(driver=self.homekit_driver)
        self.homekit_worker.start()

    def restart_homekit(self):
        if self.homekit_worker:
            self.homekit_worker.stop()

        self.start_homekit()
        for camera in self.get_all():
            camera.start_homekit(self.homekit_bridge)

    def get(self, name):
        if name in self.cameras:
            return self.cameras[name]

        return None

    def get_all(self):
        return self.cameras.values()

    def add(self, model):

        try:
            camera = Camera(model, notifier=self.notifier, object_detector_queue=self.object_detector_queue)
            self.cameras[camera.name] = camera
            self.restart_homekit()

            return True
        except Exception as e:
            log("[manager] Failed to initialize camera: {}".format(str(e)))

        return False

    def stop(self):
        if self.homekit_worker:
            self.homekit_worker.stop()
        # self.object_detector.stop()

        for camera in self.get_all():
            camera.stop()

    def start(self):
        for camera in config.cameras:
            self.add(camera)
