import io, os, time
import datetime as dt

from fastapi import APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse, FileResponse

from util import log, resize_image
from api.models import ResponseModel
from api.clips import Clips
from adapters.fastapi import MediaResponse, APIException

router = APIRouter()
public_router = APIRouter()

@router.get("/list", response_model=ResponseModel)
def clips_list(request: Request, camera: str = "", category: str = "", date: str = ""):

    api = Clips()
    # format: /clips/list?camera=&category=&date=20200620
    timestamp = int(time.time())
    if len(date) > 0:
        ts = dt.datetime(year=int(date[:4]), month=int(date[4:6]), day=int(date[6:]))
        timestamp = int(time.mktime(ts.timetuple()))

    success = True
    results = []

    clips = api.get_clips(camera, category, timestamp)
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

@public_router.get("/{id}/video/{timestamp}", response_model=ResponseModel)
def video(request: Request, id: str, timestamp: int):

    api = Clips()
    filepath = api.get_video(id, timestamp)

    if filepath == False:
        raise APIException(status_code=404)

    return MediaResponse(path=filepath, status_code=206, request_headers=request.headers)

@public_router.get("/{id}/thumbnail/{timestamp}", response_model=ResponseModel)
def thumbnail(request: Request, id: str, timestamp: int, resize_to: int = 0):

    api = Clips()
    filepath = api.get_thumbnail(id, timestamp)
    if filepath == False:
        raise APIException(status_code=404)

    if resize_to > 0:
        with open(filepath, "rb") as handle:
            image = handle.read()
            return StreamingResponse(io.BytesIO(resize_image(image, resize_to)), media_type="image/jpeg")

    return FileResponse(filepath, media_type="image/jpeg")
