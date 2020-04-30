import cv2, sys
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import numpy, json
import zmq
import ptz
import os
import copy
import urllib, urllib.request
import shutil, ssl, base64
from sighthound import Sighthound
from threading import RLock

lock = RLock()

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class HttpServer(BaseHTTPRequestHandler):

    def do_GET(self):
        self.respond()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request_body = self.rfile.read(content_length)
        self.respond(request_body.decode("utf-8"))

    def respond(self, request_body=None):
        path = urllib.parse.unquote(self.path).strip("/")
        path = path.split("/")
        method = path[0]
        del path[0]

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

class ApiServer(HttpServer):
    cameras = {}

    def camera(self, args, body):

        status = "failed"
        lock.acquire()
        try:
            camera = json.loads(body)
            self.cameras[camera["name"]] = camera
            status = "ok"
        finally:
            lock.release()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        return json.dumps({
            "status": status
        })

    def snapshot(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'image/jpeg')
        self.end_headers()
        cam = args[0]
        if self.cameras and cam in self.cameras:
            try:
                ctx = zmq.Context()
                s = ctx.socket(zmq.SUB)
                s.connect("ipc:///tmp/streamer_%s" % cam)
                s.setsockopt(zmq.SUBSCRIBE, b"")

                msg = s.recv()
                s.close()
                A = numpy.frombuffer(msg, dtype=self.cameras[cam]["meta"]["dtype"])
                frame = A.reshape(self.cameras[cam]["meta"]['shape'])
                del A
                ret, jpeg = cv2.imencode('.jpg', frame)
                return jpeg.tobytes()

            except Exception as e:
                print("Failed to get image from stream")
                print(str(e))


    def ptz(self, args, body):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        cam = args[0]
        direction = args[1]

        status = "failed"
        if "onvif" in self.cameras[cam]:
            ptz.continuous_move(self.cameras[cam]["onvif"], direction)
            status = "ok"

        return json.dumps({
            "status": status
        })

    def camera_list(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        cameras = []
        for cam in self.cameras:
            camera = copy.deepcopy(self.cameras[cam])
            del camera["meta"]
            camera["name"] = cam
            camera["snapshot_url"] = "http://%s:%s/snapshot/%s" % (os.environ["API_SERVER_HOST"], os.environ["API_SERVER_PORT"], cam)

            cameras.append(camera)

        return json.dumps({
            "status": "ok",
            "results": cameras
        })

    def clips_list(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        sy = Sighthound(os.environ["SIGHTHOUND_HOST"], os.environ["SIGHTHOUND_USER"], os.environ["SIGHTHOUND_PASSWORD"])
        camera = args[0] if len(args) >= 1 else ""
        rule = args[1] if len(args) >= 2 else ""
        date = int(args[2]) if len(args) >= 3 else None

        status = "ok"
        description = ""
        results = []
        try:
            clips = sy.get_clips(camera, rule, date)
            if clips:
                for ts in clips:
                    results.append({
                        "timestamp": ts,
                        "camera": clips[ts]["camera"],
                        "thumbnail_url": generate_video_url(clips[ts], "thumbnail"),
                        "video_url": generate_video_url(clips[ts], "video"),
                        "objects": clips[ts]["objects"]
                    })
        except Exception as e:
            status = "failed"
            description = str(e)

        return json.dumps({
            "status": status,
            "description": description,
            "results": results
        })


    def video(self, args):
        self.send_response(200)

        sy = Sighthound(os.environ["SIGHTHOUND_HOST"], os.environ["SIGHTHOUND_USER"], os.environ["SIGHTHOUND_PASSWORD"])

        url = sy.get_download_url({
            "camera": args[0],
            "first_timestamp": int(args[1]),
            "first_id": int(args[2]),
            "second_timestamp": int(args[3]),
            "second_id": int(args[4]),
            "object_ids": args[5]
        })

        request = urllib.request.Request(url)
        base64string = base64.b64encode(b'%s:%s' % (os.environ["SIGHTHOUND_USER"].encode("utf-8"), os.environ["SIGHTHOUND_PASSWORD"].encode("utf-8")))
        request.add_header("Authorization", "Basic %s" % base64string.decode("utf-8"))
        if self.headers.get("Range"):
            request.add_header("Range", self.headers.get("Range"))
        handle = urllib.request.urlopen(request, context=ssl._create_unverified_context())
        headers = dict(handle.headers)
        for hname in headers:
            if hname in ["Connection", "Date", "Server"]:
                continue
            self.send_header(hname, headers[hname])
        self.end_headers()

        shutil.copyfileobj(handle, self.wfile)

    def thumbnail(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'image/jpeg')
        self.end_headers()

        sy = Sighthound(os.environ["SIGHTHOUND_HOST"], os.environ["SIGHTHOUND_USER"], os.environ["SIGHTHOUND_PASSWORD"])

        url = sy.get_thumbnail_url({
            "camera": args[0],
            "first_timestamp": int(args[1]),
            "first_id": int(args[2]),
            "second_timestamp": int(args[3]),
            "second_id": int(args[4]),
            "object_ids": args[5]
        })

        request = urllib.request.Request(url)
        base64string = base64.b64encode(b'%s:%s' % (os.environ["SIGHTHOUND_USER"].encode("utf-8"), os.environ["SIGHTHOUND_PASSWORD"].encode("utf-8")))
        request.add_header("Authorization", "Basic %s" % base64string.decode("utf-8"))
        shutil.copyfileobj(urllib.request.urlopen(request, context=ssl._create_unverified_context()), self.wfile)

def generate_video_url(clip, type = ""):

    url = "http://%s:%s/%s/%s/%s/%s/%s/%s/%s" % (
        os.environ["API_SERVER_HOST"],
        os.environ["API_SERVER_PORT"],
        type,
        clip["camera"],
        clip["first_timestamp"],
        clip["first_id"],
        clip["second_timestamp"],
        clip["second_id"],
        clip["object_ids"]
        )

    return url

def run():

    print("Starting API server")
    httpd = ThreadingHTTPServer(("", int(os.environ["API_SERVER_PORT"])), ApiServer)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
