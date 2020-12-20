import io, os, time
import datetime as dt

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse

from util import log, resize_image
from api.models import ResponseModel, ZoneModel, CameraModel
from adapters.fastapi import MediaResponse, APIException
from models.config import config, CameraModel as ConfigCameraModel

router = APIRouter()
public_router = APIRouter()

@public_router.get("/{cam}/snapshot")
def snapshot(request: Request, cam: str, resize_to: int = 0):

    camera = request.app.camera_manager.get(cam)
    if camera:
        try:
            image = camera.make_snapshot()

            if resize_to > 0:
                image = resize_image(image, resize_to)

            return StreamingResponse(io.BytesIO(image), media_type="image/jpeg")

        except Exception as e:
            log("[api] Failed to get image from stream: {}".format(str(e)))

@router.post("/{cam}/ptz/{direction}", response_model=ResponseModel)
def ptz(request: Request, cam: str, direction: str):

    success = False

    camera = request.app.camera_manager.get(cam)
    if camera and camera.move(direction):
        success = True

    return {
        "success": success
    }

@router.post("/{cam}/detection-zone", response_model=ResponseModel)
def detection_zone(request: Request, cam: str, zone: ZoneModel):

    success = False

    camera = request.app.camera_manager.get(cam)
    if camera:
        success = True
        camera.set_zone(zone.zone.dict())

    return {
        "success": success
    }

@router.get("/list", response_model=ResponseModel)
def camera_list(request: Request):
    cameras = []

    for camera in request.app.camera_manager.get_all():
        features = camera.get_features()
        features["snapshot_url"] = "http://{}:{}/camera/{}/snapshot".format(os.environ["API_SERVER_HOST"], os.environ["API_SERVER_PORT"], camera.name)
        cameras.append(features)

    return {
        "success": True,
        "results": cameras
    }

@router.post("/add", response_model=ResponseModel)
def add_camera(request: Request, camera: CameraModel):

    success = False
    try:
        model = ConfigCameraModel.parse_obj({
            "name": camera.name,
            "onvif_url": "onvif://{}:{}@{}".format(camera.username, camera.password, camera.hostname),
        })

        success = request.app.camera_manager.add(model)
        if success:
            config.cameras.append(model)
            config.save()

    except Exception as e:
        pass

    return {
        "success": success
    }
