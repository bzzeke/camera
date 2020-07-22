from onvif import Onvif
from xml.etree import ElementTree

from util import log

class PTZ():

    directions = {
        "zoom_in": {
            "method": "continuousZoom",
            "params": [1]
        },
        "zoom_out": {
            "method": "continuousZoom",
            "params": [-1]
        },
        "move_up": {
            "method": "continuousMove",
            "params": [0, 1]
        },
        "move_down": {
            "method": "continuousMove",
            "params": [0, -1]
        },
        "move_left": {
            "method": "continuousMove",
            "params": [-1, 0]
        },
        "move_right": {
            "method": "continuousMove",
            "params": [1, 0]
        },
        "stop": {
            "method": "stopMove",
            "params": ["true", "true"]
        }
    }
    onvif = None


    def __init__(self, camera):
        self.onvif = Onvif()
        self.onvif.setup(camera["host"], camera["port"])
        self.onvif.setAuth(camera["username"], camera["password"])
        self.onvif.setProfileToken(self.get_profile_token())

    def move(self, direction):
        if direction in self.directions:
            return getattr(self.onvif, self.directions[direction]["method"])(*self.directions[direction]["params"])

    def get_profile_token(self):
        response = self.onvif.getProfiles()

        namespaces = {
            "soap": "http://schemas.xmlsoap.org/soap/envelope/",
            "trt": "http://www.onvif.org/ver10/media/wsdl"
        }
        dom = ElementTree.fromstring(response)

        names = dom.findall(
            ".//trt:Profiles",
            namespaces,
        )

        return names[0].attrib["token"]