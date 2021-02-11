import os
import sys
import asyncio
import threading
import queue
import json
import itertools
import warnings
import logging

from pyhap.hap_handler import HAPServerHandler, SNAPSHOT_TIMEOUT
from pyhap.hap_protocol import HAPServerProtocol

from pyhap.accessory_driver import AccessoryDriver
from concurrent.futures import ThreadPoolExecutor
from zeroconf import ServiceInfo, Zeroconf
from pyhap.encoder import AccessoryEncoder
from pyhap.loader import Loader
from pyhap.state import State
from pyhap.hap_server import HAPServer
from pyhap.const import CATEGORY_BRIDGE

logger = logging.getLogger("pyhap")

class HomekitDriver(AccessoryDriver):

    def __init__(
        self,
        *,
        address=None,
        port=51234,
        persist_file="accessory.state",
        pincode=None,
        encoder=None,
        loader=None,
        loop=None,
        mac=None,
        listen_address=None,
        advertised_address=None,
        interface_choice=None,
        zeroconf_instance=None
    ):
        if loop is None:
            if sys.platform == "win32":
                loop = asyncio.ProactorEventLoop()
            else:
                loop = asyncio.new_event_loop()

            executor_opts = {"max_workers": None}
            if sys.version_info >= (3, 6):
                executor_opts["thread_name_prefix"] = "SyncWorker"

            self.executor = ThreadPoolExecutor(**executor_opts)
            loop.set_default_executor(self.executor)
            self.tid = threading.current_thread()
        else:
            self.tid = threading.main_thread()
            self.executor = None

        self.loop = loop

        self.accessory = None
        if zeroconf_instance is not None:
            self.advertiser = zeroconf_instance
        elif interface_choice is not None:
            self.advertiser = Zeroconf(interfaces=interface_choice)
        else:
            self.advertiser = Zeroconf()
        self.persist_file = os.path.expanduser(persist_file)
        self.encoder = encoder or AccessoryEncoder()
        self.topics = {}  # topic: set of (address, port) of subscribed clients
        self.loader = loader or Loader()
        self.aio_stop_event = asyncio.Event(loop=loop)
        self.stop_event = threading.Event()

        self.safe_mode = False

        self.mdns_service_info = None
        self.srp_verifier = None

        address = address or util.get_local_address()
        advertised_address = advertised_address or address
        self.state = State(
            address=advertised_address, mac=mac, pincode=pincode, port=port
        )

        listen_address = listen_address or address
        network_tuple = (listen_address, self.state.port)
        self.http_server = Server(network_tuple, self)

class Server(HAPServer):
    async def async_start(self, loop):
        self.server = await loop.create_server(
            lambda: ServerProtocol(loop, self.connections, self.accessory_handler),
            self._addr_port[0],
            self._addr_port[1],
        )

class ServerProtocol(HAPServerProtocol):
    def connection_made(self, transport: asyncio.Transport) -> None:
        """Handle incoming connection."""
        peername = transport.get_extra_info("peername")
        logger.info("%s: Connection made", peername)
        self.transport = transport
        self.peername = peername
        self.connections[peername] = self
        self.handler = ServerHandler(self.accessory_driver, peername)

class ServerHandler(HAPServerHandler):
    def handle_resource(self):
        """Get a snapshot from the camera."""

        data = json.loads(self.request_body.decode("utf-8"))

        if self.accessory_handler.accessory.category == CATEGORY_BRIDGE:
            accessory = self.accessory_handler.accessory.accessories.get(data['aid'])
            if not accessory:
                raise ValueError('Accessory with aid == {} not found'.format(data['aid']))
        else:
            accessory = self.accessory_handler.accessory

        loop = asyncio.get_event_loop()
        if hasattr(accessory, "async_get_snapshot"):
            coro = accessory.async_get_snapshot(data)
        elif hasattr(accessory, "get_snapshot"):
            coro = asyncio.wait_for(
                loop.run_in_executor(
                    None, accessory.get_snapshot, data
                ),
                SNAPSHOT_TIMEOUT,
            )
        else:
            raise ValueError(
                "Got a request for snapshot, but the Accessory "
                'does not define a "get_snapshot" or "async_get_snapshot" method'
            )

        task = asyncio.ensure_future(coro)
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.response.task = task
