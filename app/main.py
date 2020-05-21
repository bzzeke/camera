import os
import time
import sys
import threading
from threading import Thread, RLock
import queue
from util import import_env, log

from streamer import Streamer
from api import ApiServer
from phase1_detector_simple import Phase1Detector
from phase2_detector_simple import Phase2Detector
from cleanup import Cleanup

class State():
    cameras = {}
    lock = RLock()
    threads = []
    q = queue.Queue()

    def set_camera(self, camera):
        self.lock.acquire()
        try:
            self.cameras[camera["name"]] = camera

            if camera["detection"]:
                phase1 = Phase1Detector(camera=camera, queue=self.q)
                phase1.start()
                self.threads.append(phase1)

        finally:
            self.lock.release()



if __name__ == "__main__":
    import_env()

    state = State()

    object_detector = Phase2Detector(queue=state.q)
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
