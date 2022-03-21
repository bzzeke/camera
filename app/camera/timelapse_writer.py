import cv2
import time
import queue
import os
import jdb
import numpy as np
import collections
import datetime as dt
import ffmpeg

from threading import Thread

from api.timelapse import Timelapse
from models.config import storage_path
from util import log
from broker import Subscriber

class TimelapseWriter(Thread):

    FPS = 30

    storage_path = "{}/timelapse".format(storage_path)
    stop_flag = False
    camera = None
    out = None

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, camera=None):
        super(TimelapseWriter, self).__init__(group=group, target=target, name=name)
        self.camera = camera

    def run(self):

        log("[timelapse_writer] [{}] Starting timelapse writer".format(self.camera.name))
        api = Timelapse()
        frame_idx = 0
        previous_path = api.hls_path(self.camera.id, int(time.time()))
        out_filename = "playlist.m3u8"

        subscriber = Subscriber()
        self.camera.publisher.attach(subscriber)

        while not self.stop_flag:

            frame = subscriber.sub()
            if frame is None:
                continue

            frame_idx += 1
            if frame_idx % self.camera.meta["fps"] != 0:
                continue

            frame_idx = 0

            current_path = api.hls_path(self.camera.id, int(time.time()))
            if not self.out or previous_path != current_path:
                if self.out:
                    self.out.stdin.close()
                    self.out.wait()

                os.makedirs(current_path, exist_ok=True)
                self.out = (
                    ffmpeg
                    .input('pipe:', format='rawvideo', pix_fmt='rgb24', s='{}x{}'.format(int(self.camera.meta["width"]), int(self.camera.meta["height"])))
                    .output("{}/{}".format(current_path, out_filename), vcodec='libx264', pix_fmt='yuv420p', use_localtime='1', hls_segment_filename="{}/{}".format(current_path, '%Y%m%d-%s.ts'), hls_flags='append_list')
                    .overwrite_output()
                    .global_args('-loglevel', 'quiet')
                    .run_async(pipe_stdin=True)
                )

            self.out.stdin.write(frame
                .astype(np.uint8)
                .tobytes()
            )

        self.camera.publisher.detach(subscriber)

    def stop(self):
        self.stop_flag = True
        self.join()
        if self.out:
            self.out.stdin.close()
            self.out.wait()


