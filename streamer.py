import socket, sys
import time
import cv2
from pynng import Bus0, Rep0
import json
from threading import Thread

CAMS= {
    "street": {
        "url": "rtsp://10.10.10.10:554/Streaming/Channels/1",
        "stream": "tcp://127.0.0.1:5556",
        "meta": {
            "dtype": None,
            "shape": None
        }
    },
    "backyard": {
        "url": "rtsp://10.10.10.11:554/Streaming/Channels/1",
        "stream": "tcp://127.0.0.1:5557",
        "meta": {
            "dtype": None,
            "shape": None
        }
    },
    "boiler": {
        "url": "rtsp://10.10.10.12:554/ch01.264?ptype=udp",
        "stream": "tcp://127.0.0.1:5558",
        "meta": {
            "dtype": None,
            "shape": None
        }
    }
}

meta_server_address="tcp://127.0.0.1:5555"

def meta_server():
    print("Starting meta server")
    s1 = Rep0(listen=meta_server_address, recv_timeout=100)
    while True:
        try:
            msg = s1.recv()
            if msg == b"cams":
                s1.send(json.dumps(CAMS).encode('utf-8'))
            else:
                s1.send(b"Unknown message")
        except Exception as e:
            pass
        time.sleep(0.05)

def run():
    for cam in CAMS:
        p = Thread(target = stream, args=[cam])
        p.daemon = True
        p.start()

    meta_server()

def stream(cam):
    video = get_capture(CAMS[cam]["url"])
    print("Starting stream for camera %s" % cam)

    s0 = Bus0(listen=CAMS[cam]["stream"], recv_timeout=100, recv_max_size=0, send_buffer_size=1, recv_buffer_size=1)
    while True:

        (grabbed, frame) = video.read()
        if CAMS[cam]["meta"]["dtype"] == None:
            CAMS[cam]["meta"]["dtype"]=str(frame.dtype)
            CAMS[cam]["meta"]["shape"]=frame.shape

        if not grabbed:
            print("Reconnecting to camera %s" % cam)
            video.release()
            video = get_capture(CAMS[cam]["url"])
            continue

        s0.send(frame.tostring())
        del frame
        time.sleep(0.1)

def get_capture(url):
    return cv2.VideoCapture(url)
