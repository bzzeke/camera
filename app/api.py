import cv2, sys
import socket
import time
import numpy
import json
import zmq
import os
import copy
import urllib, urllib.request
import shutil, ssl, base64
import re
import jdb
import datetime as dt

from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

from util import log

class Api:
    def get_clips(self, camera, rule, date):
        filepath = self.db_path(date)
        if os.path.isfile(filepath):
            db = jdb.load(filepath, True)
            clips = db.lgetall("clips")
            if camera != "":
                clips = list(filter(lambda item: item["camera"] == camera, clips))
            if rule != "":
                clips = list(filter(lambda item: rule in item["objects"], clips))

            return sorted(clips, key = lambda item: item["start_time"], reverse=True)

        return False

    def get_video(self, camera, timestamp):
        filepath = self.path(camera, timestamp, "mp4")
        if os.path.isfile(filepath):
            return filepath

        return False

    def get_thumbnail(self, camera, timestamp):
        filepath = self.path(camera, timestamp, "jpeg")
        if os.path.isfile(filepath):
            return filepath

        return False

    def db_path(self, timestamp):
        clip_date = dt.date.fromtimestamp(timestamp)
        return "{}/{}/{}/{}/meta.json".format(os.environ["DETECTOR_STORAGE_PATH"], clip_date.year, clip_date.month, clip_date.day)

    def path(self, camera, timestamp, ext):
        clip_date = dt.date.fromtimestamp(timestamp)
        return "{}/{}/{}/{}/{}/{}.{}".format(os.environ["DETECTOR_STORAGE_PATH"], clip_date.year, clip_date.month, clip_date.day, camera, timestamp, ext)

class ApiHTTPServer(ThreadingMixIn, HTTPServer):
    cameras = None
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True, cameras=cameras):
        super(ApiHTTPServer, self).__init__(server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)
        self.cameras = cameras

class HTTPHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.respond()

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        request_body = self.rfile.read(content_length)
        self.respond(request_body.decode("utf-8"))

    def respond(self, request_body=None):
        path = urllib.parse.unquote(self.path).strip("/")
        path = path.split("/")
        method = path[0]
        del path[0]

        if method == "":
            method = "index"

        if hasattr(self, method):
            if request_body == None:
                response = getattr(self, method)(path)
            else:
                response = getattr(self, method)(path, request_body)

            if response != None:
                try:
                    if type(response) == str:
                        response = response.encode("utf-8")
                    self.wfile.write(response)
                except:
                    pass
        else:
            self.send_response(404)
            self.end_headers()

class ApiHandler(HTTPHandler):

    def snapshot(self, args):
        self.send_response(200)
        self.send_header("Content-type", "image/jpeg")
        self.end_headers()
        cam = args[0]
        if cam in self.server.cameras:
            try:
                camera = self.server.cameras[cam]
                frame = camera.make_snapshot()

                if len(args) == 2:
                    frame = self.resize_image(frame, int(args[1]))

                ret, jpeg = cv2.imencode(".jpg", frame)
                return jpeg.tobytes()

            except Exception as e:
                log("[api] Failed to get image from stream: {}".format(str(e)))


    def ptz(self, args, body):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        cam = args[0]
        direction = args[1]

        status = "failed"

        if cam in self.server.cameras:
            camera = self.server.cameras[cam]
            if camera.move(direction):
                status = "ok"

        return json.dumps({
            "status": status
        })

    def index(self, args):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-type", "text/html")
        self.download("zone.html")

    def detection_zone(self, args, body):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-type", "application/json")
        self.end_headers()

        cam = args[0]
        status = "failed"

        data = json.loads(body)
        if "zone" in data and cam in self.server.cameras[cam]:
            status = "ok"

            camera = self.server.cameras[cam]
            camera.set_zone(data["zone"])
            camera.restart_motion_detector()

        return json.dumps({
            "status": status
        })

    def camera_list(self, args):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-type", "application/json")
        self.end_headers()

        cameras = []

        for cam in self.server.cameras:
            camera = self.server.cameras[cam]
            features = camera.get_features()
            features["snapshot_url"] = "http://%s:%s/snapshot/%s" % (os.environ["API_SERVER_HOST"], os.environ["API_SERVER_PORT"], cam)
            cameras.append(features)

        return json.dumps({
            "status": "ok",
            "results": cameras
        })

    def clips_list(self, args):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        api = Api()
        # format: /clips_list
        # format: /clips_list/Any camera/All objects/20200620
        # format: /clips_list/Any camera/person
        camera = args[0] if len(args) >= 1 else ""
        rule = args[1] if len(args) >= 2 else ""
        date = int(time.time())
        if len(args) >=3:
            date_str = str(args[2])
            ts = dt.datetime(year=int(date_str[:4]), month=int(date_str[4:6]), day=int(date_str[6:]))
            date = int(time.mktime(ts.timetuple()))

        if camera == "Any camera":
            camera = ""
        if rule == "All objects":
            rule = ""

        status = "ok"
        description = ""
        results = []

        clips = api.get_clips(camera, rule, date)
        if clips:
            for clip in clips:
                results.append({
                    "timestamp": clip["start_time"],
                    "camera": clip["camera"],
                    "thumbnail_url": self.generate_video_url(clip, "thumbnail"),
                    "video_url": self.generate_video_url(clip, "video"),
                    "objects": clip["objects"]
                })

        return json.dumps({
            "status": status,
            "description": description,
            "results": results
        })


    def video(self, args):
        api = Api()
        filepath = api.get_video(args[0], int(args[1]))
        if filepath == False:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "video/mp4")
        self.download(filepath)

    def thumbnail(self, args):
        api = Api()
        filepath = api.get_thumbnail(args[0], int(args[1]))
        if filepath == False:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-type", "image/jpeg")

        if len(args) == 3:
            self.end_headers()
            frame = cv2.imread(filepath)
            frame = self.resize_image(frame, int(args[2]))
            ret, jpeg = cv2.imencode(".jpg", frame)
            return jpeg.tobytes()
        else:
            self.download(filepath)

    def download(self, filepath):
        with open(filepath, "rb") as handle:

            if "Range" in self.headers:
                self.download_range(handle)
            else:
                self.send_header("Content-length", os.stat(filepath).st_size)
                self.end_headers()
                try:
                    shutil.copyfileobj(handle, self.wfile)
                except:
                    pass

    def download_range(self, handle):
        start, stop = self.parse_byte_range(self.headers["Range"])
        fs = os.fstat(handle.fileno())
        file_len = fs[6]
        if start >= file_len:
            return None

        self.send_response(206)
        self.send_header("Accept-Ranges", "bytes")

        if stop is None or stop >= file_len:
            stop = file_len - 1
        response_length = stop - start + 1

        self.send_header("Content-Range", "bytes {}-{}/{}".format(start, stop, file_len))
        self.send_header("Content-Length", str(response_length))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()

        bufsize = 1024 * 1024
        handle.seek(start)
        while True:
            to_read = min(bufsize, stop + 1 - handle.tell() if stop else bufsize)
            buf = handle.read(to_read)
            if not buf:
                break

            try:
                self.wfile.write(buf)
            except:
                break

    def parse_byte_range(self, byte_range):

        if byte_range.strip() == "":
            return None, None

        m = re.compile(r"bytes=(\d+)-(\d+)?$").match(byte_range)
        if not m:
            return None, None

        start, stop = [x and int(x) for x in m.groups()]
        if stop and stop < start:
            return None, None

        return start, stop

    def generate_video_url(self, clip, type = ""):

        url = "http://{}:{}/{}/{}/{}".format(
            os.environ["API_SERVER_HOST"],
            os.environ["API_SERVER_PORT"],
            type,
            clip["camera"],
            clip["start_time"]
            )

        return url

    def resize_image(self, image, new_width):
        (h, w) = image.shape[:2]
        new_height = int(new_width * h / float(w))
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)


class ApiServer(Thread):
    cameras = None
    httpd = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, cameras=None):
        super(ApiServer,self).__init__(group=group, target=target, name=name)
        self.cameras = cameras

    def run(self):
        log("[api] Starting service")
        self.httpd = ApiHTTPServer(("", int(os.environ["API_SERVER_PORT"])), ApiHandler, cameras=self.cameras)
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass

        self.httpd.server_close()

    def stop(self):
        self.httpd.shutdown()
        self.join()
