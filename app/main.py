import time
import sys
import threading
import os

from util import import_env, log
from api.server import ApiServer
from cleanup import Cleanup
from camera.manager import CameraManager
from notifier import Notifier

if __name__ == "__main__":
    import_env()

    try:
        notifier = Notifier()
        notifier.start()

        camera_manager = CameraManager(notifier=notifier)
        camera_manager.start()

        cleanup = Cleanup()
        cleanup.start()

        api_server = ApiServer(camera_manager=camera_manager)
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
        api_server.stop()
        camera_manager.stop()
