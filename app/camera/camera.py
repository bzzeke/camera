import requests
import os
import uuid

from urllib.parse import urlparse, urlunparse
from xml.etree import ElementTree
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from threading import Thread

from camera.onvif import Onvif
from camera.motion_detector import MotionDetector
from camera.streamer import CameraStream
from homekit import HomekitCamera
from util import log
from models.config import config, CameraModel, CameraType

class Camera():

    motion_detector = None
    object_detector_queue = None
    streamer = None
    notifier = None

    client = None
    name = ""
    id = ""
    stream_url = ""
    substream_url = ""
    meta = {
        "dtype": None,
        "shape": None,
        "width": 0,
        "height": 0,
        "fps": 0
    }
    detection = None

    def __init__(self, model: CameraModel, notifier = None, object_detector_queue = None):


        if model.type == CameraType.onvif:
            self.client = OnvifCamera(model.manage_url)
        else:
            self.client = TestCamera(model.manage_url)

        self.name = model.name
        self.detection = model.detection

        self.id = self.client.id
        self.stream_url = self.client.stream_url
        self.substream_url = self.client.substream_url

        self.notifier = notifier
        self.object_detector_queue = object_detector_queue
        self.start_streamer()
        self.restart_motion_detector()

    def restart_motion_detector(self):
        if not self.detection.enabled:
            return

        log("[camera] Restart detection for camera {}".format(self.name))
        if self.motion_detector != None:
            self.motion_detector.stop()

        self.motion_detector = MotionDetector(camera=self, object_detector_queue=self.object_detector_queue)
        self.motion_detector.start()

    def start_streamer(self):
        self.streamer = CameraStream(camera=self)
        self.streamer.start()

    def start_homekit(self, homekit_bridge):
        accessory = HomekitCamera(self, homekit_bridge.driver, self.name)
        homekit_bridge.add_accessory(accessory)

    def stop(self):
        self.streamer.stop()

        if self.motion_detector != None:
            self.motion_detector.stop()

    def get_features(self):
        return {
            "id": self.id,
            "name": self.name,
            "meta": self.meta,
            "detection": self.detection.dict(),
            "manage_url": self.client.manage_url,
            "stream_url": self.client.stream_url,
            "substream_url": self.client.substream_url,
            "ptz": self.client.ptz
        }

    def set_options(self, options):
        self.detection = options
        config.get_camera(self.id).detection = self.detection
        config.save()

    def set_meta(self, meta):
        self.meta = meta

    def make_snapshot(self):
        return self.client.make_snapshot()


class BaseCamera():
    id = ""
    manage_url = ""
    stream_url = ""
    substream_url = ""
    snapshot_url = ""
    ptz = {
        "zoom": False,
        "pan_tilt": False
    }

    def __init__(self, manage_url):
        self.manage_url = manage_url
        self.id = str(uuid.uuid5(uuid.NAMESPACE_DNS, manage_url))

    def make_snapshot(self):
        return b""

class OnvifCamera(BaseCamera):
    host = ""
    username = ""
    password = ""
    auth_type = ""

    main_stream_token = None
    substream_token = None

    def __init__(self, manage_url, cpath="/onvif/device_service"):

        super(OnvifCamera, self).__init__(manage_url)
        parts = urlparse(manage_url)
        self.username = parts.username or ""
        self.password = parts.password or ""
        self.host = "{}:{}".format(parts.hostname, parts.port) if parts.port else parts.hostname

        self.client = Onvif(self.host, cpath)
        self.client.set_auth(self.username, self.password)
        self.init_profile_tokens()

    def init_profile_tokens(self):
        response = self.client.getProfiles()
        names = self.search(response, ".//media:Profiles")
        tokens = list(map(lambda item: item.attrib["token"], names))

        self.main_stream_token = tokens[0]
        self.substream_token = tokens[1]

    def get_configuration_token(self, profile_token):
        response = self.client.getConfigurations(profile_token)
        names = self.search(response, ".//ptz:PTZConfiguration")

        return names[0].attrib["token"]

    def get_ptz_features(self):
        profile_token = self.get_configuration_token(self.main_stream_token)
        response = self.client.getConfigurationOptions(profile_token)

        has_zoom = self.search(response, ".//schema:ContinuousZoomVelocitySpace")
        has_pan_tilt = self.search(response, ".//schema:ContinuousPanTiltVelocitySpace")

        return {
            "zoom": len(has_zoom) > 0,
            "pan_tilt": len(has_pan_tilt) > 0
        }

    def get_stream_urls(self):
        urls = []
        for token in [self.main_stream_token, self.substream_token]:
            response = self.client.getStreamUri(token)
            uri = self.search(response, ".//schema:Uri")

            urls.append(uri[0].text)

        return urls

    def get_snapshot_urls(self):
        urls = []
        for token in [self.main_stream_token, self.substream_token]:
            response = self.client.getSnapshotUri(token)
            uri = self.search(response, ".//schema:Uri")

            urls.append(uri[0].text)

        return urls

    def move(self, direction):
        if direction == "zoom_in":
            self.client.continuousZoom(self.main_stream_token, 1)
        elif direction == "zoom_out":
            self.client.continuousZoom(self.main_stream_token, -1)
        elif direction == "move_up":
            self.client.continuousMove(self.main_stream_token, 0, 1)
        elif direction == "move_down":
            self.client.continuousMove(self.main_stream_token, 0, -1)
        elif direction == "move_left":
            self.client.continuousMove(self.main_stream_token, -1, 0)
        elif direction == "move_right":
            self.client.continuousMove(self.main_stream_token, 1, 0)
        elif direction == "stop":
            self.client.stopMove(self.main_stream_token, "true", "true")

        return True

    def search(self, response, search):
        dom = ElementTree.fromstring(response)
        return dom.findall(
            search,
            self.client.namespaces,
        )


    def setup_camera(self):
        streams = self.get_stream_urls()
        snapshots = self.get_snapshot_urls()

        parts = urlparse(streams[0])
        parts = parts._replace(netloc="{}:{}@{}:{}".format(username, password, parts.hostname, parts.port))
        self.stream_url = urlunparse(parts)

        parts = urlparse(streams[1])
        parts = parts._replace(netloc="{}:{}@{}:{}".format(username, password, parts.hostname, parts.port))
        self.substream_url = urlunparse(parts)

        parts = urlparse(snapshots[0])
        parts = parts._replace(netloc="{}:{}@{}:{}".format(username, password, parts.hostname, parts.port if parts.port != None else 80))
        self.snapshot_url = urlunparse(parts)
        self.ptz = self.get_ptz_features()

    def make_snapshot(self):
        parts = urlparse(self.snapshot_url)

        auth_type = HTTPBasicAuth(parts.username, parts.password) if self.auth_type == "basic" else HTTPDigestAuth(parts.username, parts.password)
        response = requests.get(self.snapshot_url, auth=auth_type)

        if response.status_code != 200:
            auth_type = HTTPBasicAuth(parts.username, parts.password) if self.auth_type != "basic" else HTTPDigestAuth(parts.username, parts.password)
            response = requests.get(self.snapshot_url, auth=auth_type)

        if response.status_code == 200:
            self.auth_type = "basic" if isinstance(auth_type, HTTPBasicAuth) else "digest"
            return response.content

        return b""

class TestCamera(BaseCamera):
    stream_url = "../ai/video/backyard.mp4"
    substream_url = "../ai/video/backyard.mp4"
    snapshot_url = ""
    ptz = {
        "zoom": False,
        "pan_tilt": False
    }

    def make_snapshot(self):
        with open("../ai/video/snapshot.jpeg", 'rb') as fp:
            content = fp.read()
            print("snap: {}".format(len(content)))
            return content

        return b""