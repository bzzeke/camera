import os
import sys
import asyncio
import threading
import queue
import json
import itertools
import warnings
import logging

from pyhap.hap_server import HAPServerHandler
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

    def __init__(self, *, address=None, port=51234,
                 persist_file='accessory.state', pincode=None,
                 encoder=None, loader=None, loop=None, mac=None,
                 listen_address=None, advertised_address=None, interface_choice=None,
                 zeroconf_instance=None):

        if loop is None:
            if sys.platform == 'win32':
                loop = asyncio.ProactorEventLoop()
            else:
                loop = asyncio.new_event_loop()

            executor_opts = {'max_workers': None}
            if sys.version_info >= (3, 6):
                executor_opts['thread_name_prefix'] = 'SyncWorker'

            self.executor = ThreadPoolExecutor(**executor_opts)
            loop.set_default_executor(self.executor)
        else:
            self.executor = None

        self.loop = loop

        self.accessory = None
        self.http_server_thread = None
        if zeroconf_instance is not None:
            self.advertiser = zeroconf_instance
        elif interface_choice is not None:
            self.advertiser = Zeroconf(interfaces=interface_choice)
        else:
            self.advertiser = Zeroconf()
        self.persist_file = os.path.expanduser(persist_file)
        self.encoder = encoder or AccessoryEncoder()
        self.topics = {}  # topic: set of (address, port) of subscribed clients
        self.topic_lock = threading.Lock()  # for exclusive access to the topics
        self.loader = loader or Loader()
        self.aio_stop_event = asyncio.Event(loop=loop)
        self.stop_event = threading.Event()
        self.event_queue = (
            queue.SimpleQueue() if hasattr(queue, "SimpleQueue") else queue.Queue()  # pylint: disable=no-member
        )
        self.send_event_thread = None  # the event dispatch thread
        self.sent_events = 0
        self.accumulated_qsize = 0

        self.safe_mode = False

        self.mdns_service_info = None
        self.srp_verifier = None

        address = address or util.get_local_address()
        advertised_address = advertised_address or address
        self.state = State(address=advertised_address, mac=mac, pincode=pincode, port=port)

        listen_address = listen_address or address
        network_tuple = (listen_address, self.state.port)
        self.http_server = HAPServer(network_tuple, self, handler_type=ServerHandler)

    def start(self):
        """Start the event loop and call `start_service`.
        Pyhap will be stopped gracefully on a KeyBoardInterrupt.
        """
        try:
            logger.info('Starting the event loop')
            if threading.current_thread() is threading.main_thread():
                logger.debug('Setting child watcher')
                watcher = ThreadedChildWatcher()
                watcher.attach_loop(self.loop)
                asyncio.set_child_watcher(watcher)
            else:
                logger.debug('Not setting a child watcher. Set one if '
                             'subprocesses will be started outside the main thread.')
            self.add_job(self.start_service)
            self.loop.run_forever()
        except KeyboardInterrupt:
            logger.debug('Got a KeyboardInterrupt, stopping driver')
            self.loop.call_soon_threadsafe(
                self.loop.create_task, self.async_stop())
            self.loop.run_forever()
        finally:
            self.loop.close()
            logger.info('Closed the event loop')

class ServerHandler(HAPServerHandler):
    def handle_resource(self):
        """Get a snapshot from the camera."""

        data_len = int(self.headers["Content-Length"])
        request_body = self.rfile.read(data_len)
        data = json.loads(request_body.decode("utf-8"))

        if self.accessory_handler.accessory.category == CATEGORY_BRIDGE:
            accessory = self.accessory_handler.accessory.accessories.get(data['aid'])
            if not accessory:
                raise ValueError('Accessory with aid == {} not found'.format(data['aid']))
        else:
            accessory = self.accessory_handler.accessory

        if not hasattr(accessory, 'get_snapshot'):
            raise ValueError('Got a request for snapshot, but the Accessory '
                             'does not define a "get_snapshot" method')

        image = accessory.get_snapshot(data)
        self.send_response(200)
        self.send_header('Content-Type', 'image/jpeg')
        self.end_response(image)


class ThreadedChildWatcher(asyncio.AbstractChildWatcher):
    """Threaded child watcher implementation.
    The watcher uses a thread per process
    for waiting for the process finish.
    It doesn't require subscription on POSIX signal
    but a thread creation is not free.
    The watcher has O(1) complexity, its performance doesn't depend
    on amount of spawn processes.
    """

    def __init__(self):
        self._pid_counter = itertools.count(0)
        self._threads = {}

    def is_active(self):
        return True

    def close(self):
        self._join_threads()

    def _join_threads(self):
        """Internal: Join all non-daemon threads"""
        threads = [thread for thread in list(self._threads.values())
                   if thread.is_alive() and not thread.daemon]
        for thread in threads:
            thread.join()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __del__(self, _warn=warnings.warn):
        threads = [thread for thread in list(self._threads.values())
                   if thread.is_alive()]
        if threads:
            _warn(f"{self.__class__} has registered but not finished child processes",
                  ResourceWarning,
                  source=self)

    def add_child_handler(self, pid, callback, *args):
        loop = events.get_running_loop()
        thread = threading.Thread(target=self._do_waitpid,
                                  name=f"waitpid-{next(self._pid_counter)}",
                                  args=(loop, pid, callback, args),
                                  daemon=True)
        self._threads[pid] = thread
        thread.start()

    def remove_child_handler(self, pid):
        # asyncio never calls remove_child_handler() !!!
        # The method is no-op but is implemented because
        # abstract base classe requires it
        return True

    def attach_loop(self, loop):
        pass

    def _do_waitpid(self, loop, expected_pid, callback, args):
        assert expected_pid > 0

        try:
            pid, status = os.waitpid(expected_pid, 0)
        except ChildProcessError:
            # The child process is already reaped
            # (may happen if waitpid() is called elsewhere).
            pid = expected_pid
            returncode = 255
            logger.warning(
                "Unknown child process pid %d, will report returncode 255",
                pid)
        else:
            returncode = _compute_returncode(status)
            if loop.get_debug():
                logger.debug('process %s exited with returncode %s',
                             expected_pid, returncode)

        if loop.is_closed():
            logger.warning("Loop %r that handles pid %r is closed", loop, pid)
        else:
            loop.call_soon_threadsafe(callback, pid, returncode, *args)

        self._threads.pop(expected_pid)
