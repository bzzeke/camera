from onvif import Onvif
from xml.etree import ElementTree
from util import log

XMAX = 1
XMIN = -1
YMAX = 1
YMIN = -1
ZMIN = -1
ZMAX = 1

def zoom_in(cam):
    log("[ptz] zoom in...")
    cam.continuousZoom(ZMAX)

def zoom_out(cam):
    log("[ptz] zoom out...")
    cam.continuousZoom(ZMIN)

def move_up(cam):
    log("[ptz] move up...")
    cam.continuousMove(0, YMAX)

def move_down(cam):
    log("[ptz] move down...")
    cam.continuousMove(0, YMIN)

def move_right(cam):
    log("[ptz] move right...")
    cam.continuousMove(XMAX, 0)

def move_left(cam):
    log("[ptz] move left...")
    cam.continuousMove(XMIN, 0)

def stop(cam):
    log("[ptz] stop camera...")
    cam.stopMove("true", "true")

def continuous_move(camera, direction):
    cam = Onvif()
    cam.setup(camera["host"], camera["port"])
    cam.setAuth(camera["username"], camera["password"])
    cam.setProfileToken(get_profile_token(cam))

    globals()[direction](cam)

def get_profile_token(cam):
    response = cam.getProfiles()

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