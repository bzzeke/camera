import os
import queue

from pyhap.accessory import Bridge
from urllib.parse import urlparse

from camera.camera import Camera
from camera.object_detector import ObjectDetector
from homekit import HomekitCamera, HomekitWorker
from adapters.pyhap import HomekitDriver
from models.config import config, storage_path
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
        self.object_detector = ObjectDetector(object_detector_queue=self.object_detector_queue)
        self.object_detector.start()

        self.start_homekit()


    def start_homekit(self):
        self.homekit_driver = HomekitDriver(address=os.environ["API_SERVER_HOST"], port=51826, persist_file="{}/data/bridge.state".format(storage_path))
        self.homekit_bridge = Bridge(self.homekit_driver, 'Camera bridge')
        self.homekit_driver.add_accessory(accessory=self.homekit_bridge)
        self.homekit_worker = HomekitWorker(driver=self.homekit_driver)
        self.homekit_worker.start()

    def get(self, id):
        if id in self.cameras:
            return self.cameras[id]

        return None

    def get_all(self):
        return self.cameras.values()

    def is_exist(self, manage_url):
        return len(list(filter(lambda camera: camera.client.manage_url == manage_url, self.get_all()))) > 0

    def add(self, model):

        if self.is_exist(model.manage_url):
            return False

        camera = Camera(model, notifier=self.notifier, object_detector_queue=self.object_detector_queue)
        camera.add_to_homekit(self.homekit_bridge)

        self.cameras[camera.id] = camera

        return camera

    def remove(self, id):
        camera = self.get(id)
        if camera:
            camera.stop()
            del self.cameras[camera.id]
            return True

        return False

    def stop(self):
        if self.homekit_worker:
            self.homekit_worker.stop()

        if self.object_detector:
            self.object_detector.stop()

        for camera in self.get_all():
            camera.stop()

    def start(self):
        for camera in config.cameras.values():
            self.add(camera)
