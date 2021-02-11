import os
import glob
import datetime as dt

from models.config import config, storage_path

class Timelapse:
    storage_path = "{}/timelapse".format(storage_path)
    video_format = "mp4"

    def path(self, timestamp):
        chunk_date = dt.date.fromtimestamp(timestamp)
        return "{}/{}/{}/{}".format(self.storage_path, chunk_date.year, chunk_date.month, chunk_date.day)

    def chunk_path(self, timestamp):
        return "{}/{}.{}".format(self.path(timestamp), timestamp, self.video_format)

    def list(self, timestamp):
        chunks = sorted(glob.iglob("{}/*.{}".format(self.path(timestamp), self.video_format)))
        return list(map(lambda chunk: os.path.basename(chunk), chunks))
