import os
import jdb
import time
import datetime as dt

from models.config import config, storage_path

class Clips:
    storage_path = "{}/clips".format(storage_path)
    video_format = "mp4"
    image_format = "jpeg"

    def get_clips(self, camera, category, date):
        filepath = self.db_path(date)
        if os.path.isfile(filepath):
            db = jdb.load(filepath, True)
            clips = db.lgetall("clips")
            if camera != "":
                clips = list(filter(lambda item: item["camera"] == camera, clips))
            if category != "":
                clips = list(filter(lambda item: category in item["objects"], clips))

            return sorted(clips, key = lambda item: item["start_time"], reverse=True)

        return False

    def get_video(self, camera, timestamp):
        filepath = self.path(camera, timestamp, self.video_format)

        if os.path.isfile(filepath):
            return filepath

        return False

    def get_thumbnail(self, camera, timestamp):
        filepath = self.path(camera, timestamp, self.image_format)
        if os.path.isfile(filepath):
            return filepath

        return False

    def db_path(self, timestamp):
        clip_date = dt.date.fromtimestamp(timestamp)
        return "{}/{}/{}/{}/meta.json".format(self.storage_path, clip_date.year, clip_date.month, clip_date.day)

    def path(self, camera, timestamp, ext):
        clip_date = dt.date.fromtimestamp(timestamp)
        return "{}/{}/{}/{}/{}/{}.{}".format(self.storage_path, clip_date.year, clip_date.month, clip_date.day, camera, timestamp, ext)

    def generate_video_url(self, clip, type = ""):

        url = "http://{}:{}/api/clips/{}/{}/{}".format(
            os.environ["API_SERVER_HOST"],
            os.environ["API_SERVER_PORT"],
            clip["camera"],
            type,
            clip["start_time"]
            )

        return url

    def get_timezone(self):
        utc_offset = int(time.localtime().tm_gmtoff / (60 * 60))

        if utc_offset == 0:
            return "UTC"
        elif utc_offset > 0:
            return "UTC+{}".format(utc_offset)
        else:
            return "UTC{}".format(utc_offset)