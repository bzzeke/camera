import requests
import os
import jdb

from urllib.parse import urlparse, urlunparse
from xml.etree import ElementTree
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
from threading import Thread

from camera.onvif import Onvif
from camera.motion_detector import MotionDetector
from camera.streamer import CameraStream
from homekit import HomekitCamera
from util import log

class Camera():

    client = None
    main_stream_token = None
    substream_token = None
    db = None
    motion_detector = None
    object_detector_queue = None
    streamer = None
    notifier = None
    auth_type = ""

    name = ""
    meta = {
        "dtype": None,
        "shape": None,
        "width": 0,
        "height": 0,
        "fps": 0
    }
    detection = {
        "enabled": False,
        "valid_categories": [],
        "zone": []
    }
    stream_url = ""
    substream_url = ""
    snapshot_url = ""
    ptz = {}

    def __init__(self, name, onvif_url, detection = None, cpath="/onvif/device_service", notifier = None, object_detector_queue = None):

        self.name = name
        if detection != None:
            self.detection = detection

        self.notifier = notifier
        self.object_detector_queue = object_detector_queue
        self.db = jdb.load("{}/data/cameras.json".format(os.environ["STORAGE_PATH"]), True)

        parts = urlparse(onvif_url)
        hostname = "{}:{}".format(parts.hostname, parts.port) if parts.port else parts.hostname
        self.client = Onvif(hostname, cpath)
        self.client.set_auth(parts.username, parts.password)
        self.init_profile_tokens()
        self.setup_camera(parts.username, parts.password)

        self.start_streamer()
        self.restart_motion_detector()

    def restart_motion_detector(self):
        if not self.detection["enabled"]:
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

    def setup_camera(self, username, password):
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

        if self.db.exists(self.name) and self.db.dexists(self.name, "zone"):
            self.detection["zone"] = self.db.dget(self.name, "zone")

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

    def get_features(self):
        return {
            "name": self.name,
            "detection": self.detection,
            "stream_url": self.stream_url,
            "substream_url": self.substream_url,
            "ptz": self.ptz,
            "meta": self.meta
        }

    def set_zone(self, zone):
        if not self.db.exists(self.name):
            self.db.dcreate(self.name)

        self.db.dadd(self.name, ("zone", zone))
        self.detection["zone"] = zone

    def set_meta(self, meta):
        self.meta = meta

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
