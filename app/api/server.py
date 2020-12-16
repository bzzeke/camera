import os
import uvicorn

from threading import Thread
from fastapi import FastAPI
from uvicorn.server import Server, ServerState  # noqa: F401  # Used to be defined here.
from uvicorn.supervisors import ChangeReload, Multiprocess
from uvicorn.config import Config

from api import routes
from util import log

class ApiServer(Thread):
    cameras = None
    server = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, cameras=None):
        super(ApiServer,self).__init__(group=group, target=target, name=name)
        self.cameras = cameras

    def run(self):
        log("[api] Starting service")

        try:
            app = FastAPI()
            app.cameras = self.cameras
            app.include_router(routes.router)

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
