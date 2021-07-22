import time
import sys
import threading
import os
import asyncio

from util import import_env, log
import_env()

from api.server import ApiServer
from cleanup import Cleanup
from camera.manager import CameraManager
from notifier import Notifier

if __name__ == "__main__":
    try:
        asyncio.get_event_loop()
        asyncio.get_child_watcher()

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

    except (KeyboardInterrupt, Exception) as e:
        log("[main] Caught exception: {}".format(str(e)))
        log("[main] Stopping all")
        if "notifier" in locals():
            notifier.stop()

        if "cleanup" in locals():
            cleanup.stop()

        if "api_server" in locals():
            api_server.stop()

        if "camera_manager" in locals():
            camera_manager.stop()
