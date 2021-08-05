import os
import queue
from typing import Any

from util import log

class Publisher(object):
    subscribers = []

    def attach(self, subscriber):
        if subscriber not in self.subscribers:
            self.subscribers.append(subscriber)

    def detach(self, subscriber):
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)

    def pub(self, msg):
        for subscriber in self.subscribers:
            subscriber.put(msg)


class Subscriber(object):

    q = None
    QSIZE = 5

    def __init__(self) -> None:
        self.q = queue.Queue()

    def put(self, msg) -> None:
        if self.q.qsize() == self.QSIZE:
            log("[publisher] Queue is too big, clearing")
            with self.q.mutex:
                self.q.queue.clear()

        self.q.put(msg)

    def sub(self, block = False) -> Any:
        try:
            return self.q.get(block=block, timeout=1)
        except queue.Empty:
            pass

        return None
