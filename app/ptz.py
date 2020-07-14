from onvif import Onvif
from xml.etree import ElementTree

from util import log

class PTZ():

    directions = {
        "zoom_in": [1],
        "zoom_out": [-1],
        "move_up": [0, 1],
        "move_down": [0, -1],
        "move_left": [-1, 0],
        "move_right": [1, 0],
    }
    onvif = None


    def __init__(self, camera):
        self.onvif = Onvif()
        self.onvif.setup(camera["host"], camera["port"])
        self.onvif.setAuth(camera["username"], camera["password"])
        self.onvif.setProfileToken(self.get_profile_token())

    def move(self, direction):

        if direction == "stop":
            return self.onvif.stopMove("true", "true")

        return self.onvif.continuousZoom(*self.directions[direction])

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