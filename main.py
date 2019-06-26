import streamer
import api

import time
import threading
from threading import Thread



if __name__ == "__main__":

    p = Thread(target = streamer.run)
    p.daemon = True
    p.start()

    s = Thread(target = api.run)
    s.daemon = True
    s.start()

    while True:
        time.sleep(1)