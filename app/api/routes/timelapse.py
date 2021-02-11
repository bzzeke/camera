import io, os, time
import datetime as dt

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse, HTMLResponse
from starlette.requests import Request

from api.timelapse import Timelapse
from adapters.fastapi import MediaResponse

router = APIRouter()
public_router = APIRouter()

@router.get("/timelapse")
def timelapse(request: Request, date: str = ""):

    api = Timelapse()
    timestamp = int(time.time())
    if len(date) > 0:
        ts = dt.datetime(year=int(date[:4]), month=int(date[4:6]), day=int(date[6:]))
        timestamp = int(time.mktime(ts.timetuple()))

    chunks = list(map(lambda chunk: "http://{}:{}/api/timelapse/{}".format(os.environ["API_SERVER_HOST"], os.environ["API_SERVER_PORT"], chunk), api.list(timestamp)))

    return {
        "success": True,
        "results": chunks
    }

@public_router.get("/timelapse/{timestamp}.mp4")
def timelapse(request: Request, timestamp: int):
    api = Timelapse()
    return MediaResponse(path=api.chunk_path(timestamp), status_code=206, request_headers=request.headers)
