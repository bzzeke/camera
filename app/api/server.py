import os
import uvicorn

from threading import Thread
from fastapi import FastAPI, Depends
from uvicorn.server import Server, ServerState  # noqa: F401  # Used to be defined here.
from uvicorn.supervisors import ChangeReload, Multiprocess
from uvicorn.config import Config
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.auth import HTTPHeaderAuthentication
from api.routes import auth, camera, clips, system, timelapse
from util import log
from adapters.fastapi import APIException

class ApiServer(Thread):
    camera_manager = None
    server = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera_manager=None):
        super(ApiServer,self).__init__(group=group, target=target, name=name)
        self.camera_manager = camera_manager

    def run(self):
        log("[api] Starting service")

        try:
            app = FastAPI(exception_handlers={APIException: http_exception_handler})
            app.camera_manager = self.camera_manager

            protected = Depends(HTTPHeaderAuthentication())
            app.include_router(camera.router, prefix="/api", dependencies=[protected])
            app.include_router(clips.router, prefix="/api", dependencies=[protected])
            app.include_router(system.router, prefix="/api", dependencies=[protected])
            app.include_router(timelapse.router, prefix="/api", dependencies=[protected])

            app.include_router(camera.public_router, prefix="/api")
            app.include_router(clips.public_router, prefix="/api")
            app.include_router(timelapse.public_router, prefix="/api")
            app.include_router(auth.router, prefix="/api")

            app.mount("/", StaticFiles(directory="../web/dist", html=True), name="public")

            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

            config = Config(app, host=os.environ["API_SERVER_HOST"], port=int(os.environ["API_SERVER_PORT"]))
            self.server = Server(config=config)

            if config.should_reload:
                sock = config.bind_socket()
                supervisor = ChangeReload(config, target=self.server.run, sockets=[sock])
                supervisor.run()
            elif config.workers > 1:
                sock = config.bind_socket()
                supervisor = Multiprocess(config, target=self.server.run, sockets=[sock])
                supervisor.run()
            else:
                self.server.run()

        except KeyboardInterrupt:
            pass

    def stop(self):

        self.server.handle_exit(None, None)
        self.join()


async def http_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    headers = getattr(exc, "headers", None)
    if headers:
        return JSONResponse(
            {"success": False, "message": exc.detail}, status_code=exc.status_code, headers=headers
        )
    else:
        return JSONResponse({"success": False, "message": exc.detail}, status_code=exc.status_code)
