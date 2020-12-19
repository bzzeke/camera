from fastapi import APIRouter
from starlette.requests import Request

from api.models import ResponseModel
from adapters.wsdiscovery import WSDiscovery

router = APIRouter()

@router.get("/discovery", response_model=ResponseModel)
def discovery(request: Request):

    wsd = WSDiscovery()
    wsd.start()
    hosts = wsd.getHosts()
    wsd.stop()

    return {
        "success": True,
        "results": hosts
    }
