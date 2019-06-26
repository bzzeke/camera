import cv2, sys
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pynng import Bus0, Req0
import numpy, json


meta_server_address="tcp://127.0.0.1:5555"
api_server_port=9000

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
    def snapshot(self, args):
        self.send_response(200)
        self.send_header('Content-type', 'image/jpeg')
        self.end_headers()

        cam = args[0]
        s1 = Req0(dial=meta_server_address, recv_timeout=500)
        s1.send(b'cams')
        cams = json.loads(s1.recv().decode("utf-8"))
        s1.close()

        if cams:
            if cam in cams:
                s2 = Bus0(dial=cams[cam]['stream'], recv_timeout=2000 , recv_max_size=0, send_buffer_size=1, recv_buffer_size=1)
                msg = s2.recv()
                s2.close()

                A = numpy.frombuffer(msg, dtype=cams[cam]["meta"]["dtype"])
                frame = A.reshape(cams[cam]["meta"]['shape'])

                del A
                ret, jpeg = cv2.imencode('.jpg', frame)

                return jpeg.tobytes()

        return b""

def run():

    print("Starting API server")
    httpd = HTTPServer(("", api_server_port), ApiServer)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
