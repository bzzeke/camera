import logging
import socket
import time

from urllib.parse import urlparse, urlunparse

from wsdiscovery.discovery import Discovery
from wsdiscovery.actions import *
from wsdiscovery.message import parseSOAPMessage
from wsdiscovery.daemon import Daemon
from wsdiscovery.threaded import ThreadedNetworking, NetworkingThread, AddressMonitorThread, BUFFER_SIZE


logger = logging.getLogger("threading")
daemon_logger = logging.getLogger("daemon")
daemon_logger.setLevel(logging.ERROR)

class DI(Discovery):
    def _addRemoteService(self, service):
        x = service.getXAddrs()[0]
        self._remoteServices[x] = service

class TN(ThreadedNetworking):
    def _startThreads(self):
        if self._networkingThread is not None:
            return

        self._networkingThread = NT(self)
        self._networkingThread.start()
        logger.debug("networking thread started")
        self._addrsMonitorThread = AddressMonitorThread(self)
        self._addrsMonitorThread.start()
        logger.debug("address monitoring thread started")

class NT(NetworkingThread):

    def _recvMessages(self):
        for key, events in self._selector.select(0):
            sock = socket.fromfd(key.fd, socket.AF_INET, socket.SOCK_DGRAM)
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
            except socket.error as e:
                time.sleep(0.01)
                continue

            env = parseSOAPMessage(data, addr[0])

            if env is None: # fault or failed to parse
                continue

            _own_addrs = self._observer._addrsMonitorThread._addrs
            if addr[0] not in _own_addrs:
                if env.getAction() == NS_ACTION_PROBE_MATCH:
                    prms = "\n ".join((str(prm) for prm in env.getProbeResolveMatches()))
                    msg = "probe response from %s:\n --- begin ---\n%s\n--- end ---\n"
                    logger.debug(msg, addr[0], prms)

                if self._capture:
                    self._capture.write("%i RECV %s:%s\n" % (self._seqnum, addr[0], addr[1]))
                    self._capture.write(data.decode("utf-8") + "\n")
                    self._seqnum += 1

            mid = env.getMessageId()
            if mid in self._knownMessageIds:
                pass # continue
            else:
                self._knownMessageIds.add(mid)

            iid = env.getInstanceId()
            if len(iid) > 0 and int(iid) >= 0:
                mnum = env.getMessageNumber()
                key = addr[0] + ":" + str(addr[1]) + ":" + str(iid)
                if mid is not None and len(mid) > 0:
                    key = key + ":" + mid
                if key not in self._iidMap:
                    self._iidMap[key] = iid
                else:
                    tmnum = self._iidMap[key]
                    if mnum > tmnum:
                        self._iidMap[key] = mnum
                    else:
                        continue

            self._observer.envReceived(env, addr)

class WSDiscovery(Daemon, DI, TN):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def stop(self):
        super().stop()


    def getHosts(self):
        services = self.searchServices()
        hosts = []
        for service in services:
            parts = urlparse(service.getXAddrs()[0])
            if parts.port:
                hosts.append("{}:{}".format(parts.hostname, parts.port))
            else:
                hosts.append(parts.hostname)

        return hosts
