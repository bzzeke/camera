import cv2, sys
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from pynng import Bus0, Rep0
import numpy, json
import ptz
import os
import copy
import urllib, urllib.request
import shutil, ssl, base64
from sighthound import Sighthound

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class HttpServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.respond()

    def respond(self):
        path = urllib.parse.unquote(self.path).strip("/")
        path = path.split("/")
        method = path[0]
        if hasattr(self, method):
            del path[0]
            response = getattr(self, method)(path)
        else:
            response = b""
            self.send_response(404)
            self.end_headers()

        self.wfile.write(response)

class ApiServer(HttpServer):
    cameras = {}

    def snapshot(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'image/jpeg')
        self.end_headers()
        cam = args[0]
        if self.cameras:
            if cam in self.cameras:

                try:
                    s2 = Bus0(dial=self.cameras[cam]['stream'], recv_timeout=2000 , recv_max_size=0, send_buffer_size=1, recv_buffer_size=1)
                    msg = s2.recv()
                    s2.close()
                    A = numpy.frombuffer(msg, dtype=self.cameras[cam]["meta"]["dtype"])
                    frame = A.reshape(self.cameras[cam]["meta"]['shape'])

                    del A
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    return jpeg.tobytes()

                except Exception:
                    print("Failed to get image from stream")

        return b""

    def ptz(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        cam = args[0]
        direction = args[1]

        if not "onvif" in self.cameras[cam]:
            return b""

        ptz.continuous_move(self.cameras[cam]["onvif"], direction)
        return b'"OK"'

    def camera_list(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        cameras = []
        for cam in self.cameras:
            camera = copy.deepcopy(self.cameras[cam])
            del camera["meta"]
            camera["name"] = cam
            camera["snapshot_url"] = "http://%s:%s/snapshot/%s" % (os.environ["API_SERVER_HOST"], os.environ["API_SERVER_HOST"], cam)
            camera["ptz_url"] = "http://%s:%s/ptz/%s" % (os.environ["API_SERVER_HOST"], os.environ["API_SERVER_HOST"], cam)

            cameras.append(camera)

        return json.dumps(cameras).encode("utf-8")

    def clips_list(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        sy = Sighthound(os.environ["SIGHTHOUND_HOST"], os.environ["SIGHTHOUND_USER"], os.environ["SIGHTHOUND_PASSWORD"])
        camera = args[0] if len(args) >= 1 else ""
        rule = args[1] if len(args) >= 2 else ""
        date = int(args[2]) if len(args) >= 3 else None

        clips = sy.get_clips(camera, rule, date)
        result = []
        if (clips):
            for ts in clips:
                result.append({
                    "timestamp": ts,
                    "camera": clips[ts]["camera"],
                    "thumbnail_url": generate_video_url(clips[ts], "thumbnail"),
                    "video_url": generate_video_url(clips[ts], "video"),
                    "objects": clips[ts]["objects"]
                })

        return json.dumps(result).encode("utf-8")

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

        return b""

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

        return b""

    def mapping(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        mapping = {
            "cameras": {}
        }

        it = 0
        while "MAPPING_%i" % it in os.environ:
            hosts = os.environ["MAPPING_%i" % it].split("|")
            mapping[hosts[0]] = hosts[1]
            it += 1

        for cam in self.cameras:
            mapping["cameras"][self.cameras[cam]["url"]] = os.environ["MAPPING_CAMERA"] % cam

        return json.dumps(mapping).encode("utf-8")


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

def get_cams_meta():

    cameras = {}
    print("Waiting for meta information")
    s1 = Rep0(listen=os.environ["META_SERVER_ADDRESS"], recv_timeout=1000)
    while True:
        try:
            msg = s1.recv()
            if msg:
                cameras = json.loads(msg.decode("utf-8"))
                print("Meta information was received successfully")
                break

        except Exception as e:
            pass
        time.sleep(1)

    print("Closing meta information listener")
    s1.close()

    return cameras

def run():

    cameras = get_cams_meta()
    print("Starting API server")
    httpd = ThreadingHTTPServer(("", int(os.environ["API_SERVER_PORT"])), ApiServer)
    httpd.RequestHandlerClass.cameras = cameras

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
