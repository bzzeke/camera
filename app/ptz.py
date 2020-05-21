from onvif import Onvif
from xml.etree import ElementTree
from util import log

class PTZ():
    XMAX = 1
    XMIN = -1
    YMAX = 1
    YMIN = -1
    ZMIN = -1
    ZMAX = 1
    onvif = None

    def __init__(self, camera):
        self.onvif = Onvif()
        self.onvif.setup(camera["host"], camera["port"])
        self.onvif.setAuth(camera["username"], camera["password"])
        self.onvif.setProfileToken(self.get_profile_token())

    def zoom_in(self):
        log("[ptz] zoom in...")
        self.onvif.continuousZoom(self.ZMAX)

    def zoom_out(self, cam):
        log("[ptz] zoom out...")
        self.onvif.continuousZoom(self.ZMIN)

    def move_up(self):
        log("[ptz] move up...")
        self.onvif.continuousMove(0, self.YMAX)

    def move_down(self):
        log("[ptz] move down...")
        self.onvif.continuousMove(0, self.YMIN)

    def move_right(self):
        log("[ptz] move right...")
        self.onvif.continuousMove(self.XMAX, 0)

    def move_left(self):
        log("[ptz] move left...")
        self.onvif.continuousMove(self.XMIN, 0)

    def stop(self):
        log("[ptz] stop camera...")
        self.onvif.stopMove("true", "true")

    def move(self, direction):
        return getattr(self, direction)

    def get_profile_token(self):
        response = self.onvif.getProfiles()

        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'trt': 'http://www.onvif.org/ver10/media/wsdl'
        }
        dom = ElementTree.fromstring(response)

        names = dom.findall(
            './/trt:Profiles',
            namespaces,
        )

        return names[0].attrib['token']