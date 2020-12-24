import io, os, time
import datetime as dt
import uuid

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from util import log, resize_image, build_url
from api.models import ResponseModel, ZoneModel, CameraModel
from adapters.fastapi import MediaResponse, APIException
from models.config import config, CameraModel as ConfigCameraModel, CameraType, CameraDetectionModel

router = APIRouter()
public_router = APIRouter()

@public_router.get("/{id}/snapshot")
def snapshot(request: Request, id: str, resize_to: int = 0):

    camera = request.app.camera_manager.get(id)
    if camera:
        try:
            image = camera.make_snapshot()

            if resize_to > 0:
                image = resize_image(image, resize_to)

            return StreamingResponse(io.BytesIO(image), media_type="image/jpeg")

        except Exception as e:
            log("[api] Failed to get image from stream: {}".format(str(e)))
            raise APIException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    raise APIException(
        status_code=HTTP_404_NOT_FOUND, detail="Camera not found"
    )

@router.post("/{id}/ptz/{direction}", response_model=ResponseModel)
def ptz(request: Request, id: str, direction: str):

    camera = request.app.camera_manager.get(id)
    if camera and camera.move(direction):
        return {
            "success": True
        }

    raise APIException(
        status_code=HTTP_400_BAD_REQUEST, detail="Camera not found"
    )

@router.post("/{id}/options", response_model=ResponseModel)
def detection_zone(request: Request, id: str, options: CameraDetectionModel):

    camera = request.app.camera_manager.get(id)
    if camera:
        success = True
        try:
            camera.set_options(options)
        except Exception as e:
            raise APIException(
                status_code=HTTP_400_BAD_REQUEST, detail=str(e)
            )

        return {
            "success": success
        }

    raise APIException(
        status_code=HTTP_400_BAD_REQUEST, detail="Camera not found"
    )

@router.get("/list", response_model=ResponseModel)
def camera_list(request: Request):
    cameras = []

    for camera in request.app.camera_manager.get_all():
        features = camera.get_features()
        features["snapshot_url"] = "http://{}:{}/camera/{}/snapshot".format(os.environ["API_SERVER_HOST"], os.environ["API_SERVER_PORT"], camera.id)
        cameras.append(features)

    return {
        "success": True,
        "results": cameras
    }

@router.post("/add", response_model=ResponseModel)
def add_camera(request: Request, camera: CameraModel):

    try:
        model = ConfigCameraModel.parse_obj({
            "name": camera.name,
            "type": CameraType.onvif,
            "manage_url": build_url({
                "scheme": "http",
                "host": camera.host,
                "username": camera.username,
                "password": camera.password
            })
        })

        camera = request.app.camera_manager.add(model)
        config.cameras[camera.id] = model
        config.save()

        return {
            "success": True
        }

    except Exception as e:
        raise APIException(
            status_code=HTTP_400_BAD_REQUEST, detail=str(e)
        )

@router.delete("/{id}", response_model=ResponseModel)
def remove_camera(request: Request, id: str):

    try:
        request.app.camera_manager.remove(id)
        del config.cameras[id]
        config.save()

    except Exception as e:
        log("[api] Failed to remove camera: {}".format(str(e)))
        raise APIException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
