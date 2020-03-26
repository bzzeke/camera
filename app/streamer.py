import socket, sys
import time
import cv2
from pynng import Bus0, Req0
import json
from threading import Thread
import os
from urllib.parse import urlparse
from urllib import request
import cv2
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

class SensorFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, camera, **properties):
        super(SensorFactory, self).__init__(**properties)
        self.camera = camera
        self.s2 = Bus0(dial=self.camera['stream'], recv_timeout=2000 , recv_max_size=0, send_buffer_size=1, recv_buffer_size=1)
        self.number_frames = 0
        self.fps = 10
        self.duration = 1 / self.fps * Gst.SECOND  # duration of a frame in nanoseconds
        self.launch_string = 'appsrc name=source is-live=true block=true format=GST_FORMAT_TIME ' \
                             'caps=video/x-raw,format=BGR,width=1920,height=1080,framerate={}/1 ' \
                             '! videoconvert ! video/x-raw,format=I420 ' \
                             '! x264enc speed-preset=ultrafast tune=zerolatency ' \
                             '! rtph264pay config-interval=1 name=pay0 pt=96'.format(self.fps)

    def on_need_data(self, src, lenght):

        try:
            data = self.s2.recv()
            if len(data) > 0:
                buf = Gst.Buffer.new_allocate(None, len(data), None)
                buf.fill(0, data)
                buf.duration = self.duration
                timestamp = self.number_frames * self.duration
                buf.pts = buf.dts = int(timestamp)
                buf.offset = timestamp
                self.number_frames += 1
                retval = src.emit('push-buffer', buf)
                # print('pushed buffer, frame {}, duration {} ns, durations {} s'.format(self.number_frames,
                                                                                        # self.duration,
                                                                                        # self.duration / Gst.SECOND))
                if retval != Gst.FlowReturn.OK:
                    print(retval)
        except Exception:
            pass


    def do_create_element(self, url):
        return Gst.parse_launch(self.launch_string)

    def do_configure(self, rtsp_media):
        print("gst configure")
        self.number_frames = 0
        appsrc = rtsp_media.get_element().get_child_by_name('source')
        appsrc.connect('need-data', self.on_need_data)

class GstServer(GstRtspServer.RTSPServer):

    def attach_stream(self, camera):
        factory = SensorFactory(camera)
        factory.set_shared(True)
        self.get_mount_points().add_factory("/%s" % camera["name"], factory)
        self.attach(None)



class Streamer(Thread):
    camera = {}
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None):
        super(Streamer, self).__init__(group=group, target=target, name=name)
        self.camera = camera
        self.stop = False

    def send_meta(self):

        print("Sending meta information for camera %s" % self.camera["name"])

        params = json.dumps(self.camera).encode("utf8")
        url = "http://%s:%s" % (os.environ["API_SERVER_HOST"], os.environ["API_SERVER_PORT"])
        req = request.Request(url, data=params, headers={'content-type': 'application/json'})
        response = request.urlopen(req)
        print("Got response: %s" % response.read().decode())

    def run(self):
        video = self.get_capture(self.camera["url"])

        print("Starting stream for camera %s" % self.camera["name"])

        s0 = Bus0(listen=self.camera["stream"], recv_timeout=100, recv_max_size=0, send_buffer_size=1, recv_buffer_size=1)
        while True:
            if self.stop:
                break

            (grabbed, frame) = video.read()

            if not grabbed:
                print("Reconnecting to camera %s" % self.camera["name"])
                video.release()
                video = self.get_capture(self.camera["url"])
                time.sleep(5)
                continue

            if self.camera["meta"]["dtype"] == None:
                self.camera["meta"]["dtype"]=str(frame.dtype)
                self.camera["meta"]["shape"]=frame.shape
                self.send_meta()

            s0.send(frame.tostring())
            del frame

    def get_capture(self, url):
        return cv2.VideoCapture(url)


def get_camera():
    it = 0
    cameras = {}
    while "CAM_NAME_%i" % it in os.environ:
        cameras[os.environ["CAM_NAME_%i" % it]] = {
            "name": os.environ["CAM_NAME_%i" % it],
            "url": os.environ["CAM_URL_%i" % it],
            "stream": os.environ["CAM_STREAM_%i" % it],
            "meta": {
                "dtype": None,
                "shape": None
            }
        }

        if "CAM_ONVIF_%i" % it in os.environ:
            parts = urlparse(os.environ["CAM_ONVIF_%i" % it])
            cameras[os.environ["CAM_NAME_%i" % it]]["onvif"] = {
                "host": parts.hostname,
                "port": parts.port,
                "username": parts.username,
                "password": parts.password
            }

        if "CAM_PTZ_FEATURES_%i" % it in os.environ:
            cameras[os.environ["CAM_NAME_%i" % it]]["ptz_features"] = os.environ["CAM_PTZ_FEATURES_%i" % it]

        it += 1

    return cameras.items()

def run():
    GObject.threads_init()
    Gst.init(None)
    server = GstServer()

    threads = []
    for cam, camera in get_camera():
        thread = Streamer(camera=camera)
        thread.start()
        server.attach_stream(camera)
        threads.append(thread)


    loop = GObject.MainLoop()

    try:
        while True:
            loop.run()
    except KeyboardInterrupt:
        loop.quit()
        for thread in threads:
            thread.stop = True

