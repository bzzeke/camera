from fastapi import APIRouter
from starlette.requests import Request
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from api.models import ResponseModel
from adapters.wsdiscovery import WSDiscovery
from adapters.fastapi import APIException
from models.config import config, CapturerModel, NotificationsModel, DetectorModel

router = APIRouter()

@router.get("/discovery")
def discovery(request: Request):

    wsd = WSDiscovery()
    wsd.start()
    hosts = wsd.getHosts()
    wsd.stop()

    return {
        "success": True,
        "results": hosts
    }

@router.get("/settings")
def settings(request: Request):

    return {
        "success": True,
        "results": [
            {
                "title": "Capturer",
                "type": "header",
            },
            {
                "name": "capturer.type",
                "title": "Type",
                "type": "select",
                "value": config.capturer.type,
                "items": [
                    {"text": "FFMPEG", "value": "ffmpeg"},
                    {"text": "GStreamer", "value": "gstreamer"}
                ]
            },
            {
                "name": "capturer.hardware",
                "title": "Hardware",
                "type": "select",
                "value": config.capturer.hardware,
                "items": [
                    {"text": "CPU", "value": "cpu"},
                    {"text": "GPU", "value": "gpu"}
                ]
            },
            {
                "title": "Notifications",
                "type": "header",
            },
            {
                "name": "notifications.enabled",
                "title": "Enabled",
                "value": config.notifications.enabled,
                "type": "checkbox",
            },
            {
                "name": "notifications.url",
                "title": "Notify URL",
                "value": config.notifications.url,
                "type": "input",
            },
            {
                "title": "Detector",
                "type": "header",
            },
            {
                "name": "detector.clips_max_size",
                "title": "Clips max size",
                "value": config.detector.clips_max_size,
                "type": "input",
            },
            {
                "name": "detector.model_path",
                "title": "Model path",
                "value": config.detector.model_path,
                "type": "input",
            },
            {
                "name": "detector.inference_device",
                "title": "Hardware",
                "type": "select",
                "value": config.detector.inference_device,
                "items": [
                    {"text": "CPU", "value": "cpu"},
                    {"text": "GPU", "value": "gpu"}
                ]
            }
        ]
    }

@router.post("/settings")
def save_settings(request: Request, settings: list):

    try:
        for option in settings:
            group, option_name = tuple(option["name"].split("."))
            option_object = getattr(config, group)
            setattr(option_object, option_name, option["value"])

        config.save()

        return {
            "success": True
        }

    except Exception as e:
        raise APIException(
            status_code=HTTP_400_BAD_REQUEST, detail=str(e)
        )