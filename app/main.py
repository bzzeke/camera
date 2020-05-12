import streamer
import api
import os
import time
import sys
import threading
from threading import Thread, RLock
import queue
from phase1_detector_simple import Phase1Detector
from phase2_detector_simple import Phase2Detector

def import_env():
    filepath = os.path.dirname(os.path.realpath(__file__)) + '/../.env'
    if not os.path.isfile(filepath):
        return

    with open(filepath) as fp:
        for cnt, line in enumerate(fp):
            parts = line.split('=', 1)
            if len(parts) == 2:
                os.environ[parts[0].strip()] = parts[1].strip()

class State():
    cameras = {}
    lock = RLock()
    phase1 = None
    object_detector = None

    def set_camera(self, camera):
        self.lock.acquire()
        try:
            self.cameras[camera["name"]] = camera

            q = queue.Queue()
            self.phase1 = Phase1Detector(camera=camera, queue=q)
            self.object_detector = Phase2Detector(queue=q)

            self.object_detector.start()
            self.phase1.start()


        finally:
            self.lock.release()


if __name__ == "__main__":

    import_env()

    state = State()


    p = Thread(target = streamer.run, args=(state,))
    p.daemon = True
    p.start()

    p = Thread(target = api.run, args=(state,))
    p.daemon = True
    p.start()

    # detector = Detector(state=state)
    # detector.start()

    total_threads = threading.active_count()

    try:
        while True:
            time.sleep(1)
            if threading.active_count() < total_threads:
                print("Some thread is dead")
                sys.exit(1)
    except KeyboardInterrupt:
        pass
