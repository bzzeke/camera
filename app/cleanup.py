import os
from os.path import join, getsize
import re
import time
from threading import Thread

class Cleanup(Thread):

    current_size = 0
    max_size = 0
    clips_directory = ""
    period = 5 * 60 * 60 # seconds
    stop = False
    regex = re.compile("/[0-9]\.(jpeg|mp4)/")

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        super(Cleanup, self).__init__(group=group, target=target, name=name)
        self.max_size = int(os.environ["CLIPS_MAX_SIZE"])
        self.clips_directory = os.environ["DETECTOR_STORAGE_PATH"]


    def run(self):
        print("[cleanup] Starting service")
        last_check = 0
        while not self.stop:
            if time.time() - last_check >= self.period:
                print("[cleanup] Checking space")
                self.calculate_total_space()
                if self.current_size >= self.max_size:
                    print("[cleanup] Free space was exceed, need to clean up old files")
                    self.remove_oldest()
                last_check = time.time()

            time.sleep(1)


    def remove_oldest(self):
        total_size = 0

        for root, dirs, files in os.walk(self.clips_directory, topdown=False):
            for filename in files:
                if not self.regex.match(filename):
                    continue

                filepath = join(root, filename)
                total_size += getsize(filepath)
                print("[cleanup] Removing file: {}".format(filepath))
                os.remove(filepath)

                if self.current_size - total_size <= self.max_size:
                    break

    def calculate_total_space(self):
        self.current_size = 0
        for root, dirs, files in os.walk(self.clips_directory, topdown=False):
            for filename in files:
                filepath = join(root, filename)
                self.current_size += getsize(filepath)
