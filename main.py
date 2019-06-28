import streamer
import api

import os
import time
import threading
from threading import Thread


def import_env():
    filepath = os.path.dirname(os.path.realpath(__file__)) + '/.env'
    with open(filepath) as fp:
        for cnt, line in enumerate(fp):
            parts = line.split('=', 1)
            if len(parts) == 2:
                os.environ[parts[0].strip()] = parts[1].strip()

if __name__ == "__main__":

    import_env()

    p = Thread(target = streamer.run)
    p.daemon = True
    p.start()

    s = Thread(target = api.run)
    s.daemon = True
    s.start()

    while True:
        time.sleep(1)