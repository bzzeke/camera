import syslog
import os
import cv2

import datetime as dt
import numpy as np

def log(text, log_level=None):
    print("[{}] {}".format(dt.datetime.now().strftime("%H:%M:%S"), text))
    if (log_level == None):
        log_level = syslog.LOG_NOTICE

    syslog.syslog(log_level, text)

def import_env():
    filepath = os.path.dirname(os.path.realpath(__file__)) + "/../.env"
    if not os.path.isfile(filepath):
        return

    with open(filepath) as fp:
        for cnt, line in enumerate(fp):
            parts = line.split("=", 1)
            if len(parts) == 2:
                os.environ[parts[0].strip()] = parts[1].strip()


def resize_image(image, new_width):

    nparr = np.frombuffer(image, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    (h, w) = frame.shape[:2]
    new_height = int(new_width * h / float(w))
    ret, jpeg = cv2.imencode(".jpg", cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA))

    return jpeg.tostring()

def build_url(parts):
    url = ""
    if "scheme" in parts and parts["scheme"] != "":
        url = "{}://".format(parts["scheme"])

    if "username" in parts and parts["username"] != "":
        url = "{}{}:{}@".format(url, parts["username"], parts["password"])

    if "host" in parts and parts["host"] != "":
        url = "{}{}".format(url, parts["host"])

    if "path" in parts and parts["path"] != "":
        url = "{}{}".format(url, parts["path"])

    if "query" in parts and parts["query"] != "":
        url = "{}?{}".format(url, parts["query"])

    return url