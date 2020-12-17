import io, os, time
import datetime as dt

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse, FileResponse

from util import log, resize_image
from api.models import ResponseModel, ZoneModel
from api.clips import Clips
from adapters.fastapi import MediaResponse, APIException


router = APIRouter()

@router.get("/snapshot/{cam}")
def snapshot(request: Request, cam: str, resize_to: int = 0):

    if cam in request.app.cameras:
        try:
            camera = request.app.cameras[cam]
            image = camera.make_snapshot()

            if resize_to > 0:
                image = resize_image(image, resize_to)

            return StreamingResponse(io.BytesIO(image), media_type="image/jpeg")

        except Exception as e:
            log("[api] Failed to get image from stream: {}".format(str(e)))

@router.post("/ptz/{cam}/{direction}", response_model=ResponseModel)
def ptz(request: Request, cam: str, direction: str):

    success = False

    if cam in request.app.cameras:
        camera = request.app.cameras[cam]
        if camera.move(direction):
            success = True

    return {
        "success": success
    }

@router.post("/detection-zone/{cam}", response_model=ResponseModel)
def detection_zone(request: Request, cam: str, zone: ZoneModel):

    success = False

    if cam in request.app.cameras:
        camera = request.app.cameras[cam]
        success = True

        camera.set_zone(zone.dict())

    return {
        "success": success
    }

@router.get("/cameras", response_model=ResponseModel)
def camera_list(request: Request):
    cameras = []

    for cam in request.app.cameras:
        camera = request.app.cameras[cam]

        features = camera.get_features()
        features["snapshot_url"] = "http://%s:%s/snapshot/%s" % (os.environ["API_SERVER_HOST"], os.environ["API_SERVER_PORT"], cam)
        cameras.append(features)

    return {
        "success": True,
        "results": cameras
    }

@router.get("/clips-list", response_model=ResponseModel)
def clips_list(request: Request, camera: str = "", rule: str = "", date: str = ""):

    api = Clips()
    # format: /clips_list
    # format: /clips_list/Any camera/All objects/20200620
    # format: /clips_list/Any camera/person
    timestamp = int(time.time())
    if len(date) > 0:
        ts = dt.datetime(year=int(date[:4]), month=int(date[4:6]), day=int(date[6:]))
        timestamp = int(time.mktime(ts.timetuple()))

    if camera == "Any camera":
        camera = ""
    if rule == "All objects":
        rule = ""

    success = True
    results = []

    clips = api.get_clips(camera, rule, timestamp)
    if clips:
        for clip in clips:
            results.append({
                "timestamp": clip["start_time"],
                "camera": clip["camera"],
                "thumbnail_url": api.generate_video_url(clip, "thumbnail"),
                "video_url": api.generate_video_url(clip, "video"),
                "objects": clip["objects"]
            })

    return {
        "success": True,
        "results": results
    }

@router.get("/video/{cam}/{timestamp}", response_model=ResponseModel)
def video(request: Request, cam: str, timestamp: int):

    api = Clips()
    filepath = api.get_video(cam, timestamp)

    if filepath == False:
        raise APIException(status_code=404)

    return MediaResponse(path=filepath, status_code=206, request_headers=request.headers)

@router.get("/thumbnail/{cam}/{timestamp}", response_model=ResponseModel)
def thumbnail(request: Request, cam: str, timestamp: int, resize_to: int = 0):

    api = Clips()
    filepath = api.get_thumbnail(cam, timestamp)
    if filepath == False:
        raise APIException(status_code=404)

    if resize_to > 0:
        with open(filepath, "rb") as handle:
            image = handle.read()
            return StreamingResponse(io.BytesIO(resize_image(image, resize_to)), media_type="image/jpeg")

    return FileResponse(filepath, media_type="image/jpeg")
