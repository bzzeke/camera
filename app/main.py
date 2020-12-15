import time
import sys
import threading
import queue
import os

from threading import Thread
from pyhap.accessory_driver import AccessoryDriver
from pyhap.accessory import Bridge

from util import import_env, log
from api import ApiServer
# from detector.object_detector import ObjectDetector
from cleanup import Cleanup
from camera import Camera
from homekit import HomekitDriver, HomekitCamera, HomekitWorker
from notifier import Notifier

FILE_PERSISTENT = "accessory.state"

if __name__ == "__main__":
    import_env()

    cameras = {}
    object_detector_queue = queue.Queue()

    try:
        notifier = Notifier()
        notifier.start()

        homekit_driver = HomekitDriver(address=os.environ["API_SERVER_HOST"], port=51826, persist_file=FILE_PERSISTENT)
        homekit_bridge = Bridge(homekit_driver, 'Camera bridge')
        it = 0
        while "CAM_NAME_{}".format(it) in os.environ:
            camera = Camera.setup(it, object_detector_queue, homekit_bridge, notifier)
            if camera == None:
                log("[main] Failed to initialized camera {}".format(os.environ["CAM_NAME_{}".format(it)]))
                raise KeyboardInterrupt

            cameras[camera.name] = camera
            it += 1

        homekit_driver.add_accessory(accessory=homekit_bridge)

        # object_detector = ObjectDetector(object_detector_queue=object_detector_queue)
        # object_detector.start()

        homekit_worker = HomekitWorker(driver=homekit_driver)
        homekit_worker.start()

        cleanup = Cleanup()
        cleanup.start()

        api_server = ApiServer(cameras=cameras)
        api_server.start()

        total_threads = threading.active_count()

        while True:
            time.sleep(1)
            if threading.active_count() < total_threads:
                log("[main] Some thread is dead")
                raise KeyboardInterrupt

    except KeyboardInterrupt:

        log("[main] Stopping all")
        notifier.stop()
        cleanup.stop()
        # object_detector.stop()
        api_server.stop()

        for camera in cameras.values():
            camera.stop()

        homekit_worker.stop()
