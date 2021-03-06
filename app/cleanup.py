import os
import re
import time

from threading import Thread
from os.path import join, getsize

from util import log
from api.clips import Clips
from models.config import config

class Cleanup(Thread):

    current_size = 0
    max_size = 0
    api = None
    period = 5 * 60 * 60 # seconds
    stop_flag = False
    regex = re.compile("[0-9]+\\.(jpeg|mp4)")

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        super(Cleanup, self).__init__(group=group, target=target, name=name)
        self.api = Clips()
        self.max_size = config.detector.clips_max_size * 1024 * 1024


    def run(self):
        log("[cleanup] Starting service")
        last_check = 0
        while not self.stop_flag:
            if time.time() - last_check >= self.period:
                log("[cleanup] Checking space")
                self.calculate_total_space()
                if self.current_size >= self.max_size:
                    log("[cleanup] Free space was exceed, need to clean up old files")
                    self.remove_oldest()
                last_check = time.time()

            time.sleep(1)

    def remove_oldest(self):
        total_size = 0

        for root, dirs, files in os.walk(self.api.storage_path, topdown=False):
            for filename in files:
                if not self.regex.match(filename):
                    continue

                filepath = join(root, filename)
                total_size += getsize(filepath)
                log("[cleanup] Removing file: {}".format(filepath))
                os.remove(filepath)

                if self.current_size - total_size <= self.max_size:
                    break

    def calculate_total_space(self):
        self.current_size = 0
        for root, dirs, files in os.walk(self.api.storage_path, topdown=False):
            for filename in files:
                filepath = join(root, filename)
                self.current_size += getsize(filepath)

    def stop(self):
        self.stop_flag = True
        self.join()
