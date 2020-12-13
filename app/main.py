import time
import sys
import threading
import queue
import os

from threading import Thread
from pyhap.accessory_driver import AccessoryDriver

from util import import_env, log
from api import ApiServer
# from detector.object_detector import ObjectDetector
from cleanup import Cleanup
from camera import Camera
from homekit import HAPDriver

if __name__ == "__main__":
    import_env()

    cameras = {}
    object_detector_queue = queue.Queue()
    homekit_accessory_driver = AccessoryDriver(address=os.environ["API_SERVER_HOST"], port=51826, persist_file=FILE_PERSISTENT)

    it = 0
    while "CAM_NAME_{}".format(it) in os.environ:
        camera = Camera.setup(it, object_detector_queue, homekit_accessory_driver)
        cameras[camera.name] = camera
        it += 1

    # object_detector = ObjectDetector(object_detector_queue=object_detector_queue)
    # object_detector.start()

    homekit_driver = HAPDriver(driver=homekit_accessory_driver)
    homekit_driver.start()

    cleanup = Cleanup()
    cleanup.start()

    api_server = ApiServer(cameras=cameras)
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
        cleanup.stop()
        # object_detector.stop()
        api_server.stop()

        for camera in cameras.values():
            camera.stop()

        homekit_driver.stop()
