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

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class HttpServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.respond()

    def respond(self):
        path = self.path.strip("/")
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

                except Exeception:
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
        ip = get_ip()
        for cam in self.cameras:
            camera = copy.deepcopy(self.cameras[cam])
            del camera["meta"]
            camera["name"] = cam
            camera["snapshot_url"] = "http://%s:%s/snapshot/%s" % (ip, os.environ["API_SERVER_PORT"], cam)
            camera["ptz_url"] = "http://%s:%s/ptz/%s" % (ip, os.environ["API_SERVER_PORT"], cam)

            cameras.append(camera)

        return json.dumps(cameras).encode("utf-8")


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

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.connect(('<broadcast>', 0))
    return s.getsockname()[0]

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
