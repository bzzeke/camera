import os
import queue

from camera.camera import Camera
# from camera.object_detector import ObjectDetector
from homekit import HomekitCamera, HomekitWorker
from adapters.pyhap import HomekitDriver

from pyhap.accessory import Bridge

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
        self.homekit_driver = HomekitDriver(address=os.environ["API_SERVER_HOST"], port=51826, persist_file="{}/data/bridge.state".format(os.environ["STORAGE_PATH"]))
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

    def add(self, props):

        try:
            camera = Camera(props["name"], props["onvif_url"], props["detection"], notifier=self.notifier, object_detector_queue=self.object_detector_queue)
            self.cameras[camera.name] = camera
            self.restart_homekit()
            return True
        except Exception as e:
            print(e)
            pass

        return False

    def stop(self):
        if self.homekit_worker:
            self.homekit_worker.stop()
        # self.object_detector.stop()

        for camera in self.get_all():
            camera.stop()

    def start(self):

        it = 0
        while True:
            props = self.get_props_from_env(it)
            if not props:
                break

            camera = Camera(props["name"], props["onvif_url"], props["detection"], notifier=self.notifier, object_detector_queue=self.object_detector_queue, homekit_bridge=self.homekit_bridge)
            if camera == None:
                log("[main] Failed to initialized camera {}".format(os.environ["CAM_NAME_{}".format(it)]))
                continue

            self.cameras[camera.name] = camera
            it += 1

    def get_props_from_env(self, it):

        if "CAM_NAME_{}".format(it) in os.environ:
            return {
                "name": os.environ["CAM_NAME_{}".format(id)],
                "onvif": os.environ["CAM_ONVIF_{}".format(id)],
                "codec": os.environ["CAM_CODEC_{}".format(id)] if "CAM_CODEC_{}".format(id) in os.environ else "",
                "detection": {
                    "enabled": os.environ["CAM_DETECTION_{}".format(id)] if "CAM_DETECTION_{}".format(id) in os.environ else False,
                    "valid_categories": os.environ["CAM_VALID_CATEGORIES_{}".format(id)] if "CAM_VALID_CATEGORIES_{}".format(id) in os.environ else [],
                    "zone": []
                }
            }

        return None


