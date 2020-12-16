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

    nparr = np.fromstring(image, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    (h, w) = frame.shape[:2]
    new_height = int(new_width * h / float(w))
    ret, jpeg = cv2.imencode(".jpg", cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA))

    return jpeg.tostring()


def read_config():
    pass
'''
{
"cameras": [
    {
        "name": "front",
        "valid_categories": ["person", "car"],
        "detection": true,
        "onvif": "onvif://admin:admin@10.10.10.10",
        "codec" - REMOVE
    }
],
"server": {
    "host": "10.10.10.10.",
    "port": 80
},
"capturer": {
    "type": "ffmpeg|gstreamer",
    "hardware": "cpu|gpu"
},
"notifications": {
    "enable": true,
    "url": ""
},
"detector": {
    "storage_path": "",
    "clips_max_size": 100,
    "model_path": "",
    "inference_device": "cpu|gpu"
}
}
'''
