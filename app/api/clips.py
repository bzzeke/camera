import os
import jdb
import datetime as dt

from models.config import config

class Clips:
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
        filepath = self.path(camera, timestamp, "mp4")

        if os.path.isfile(filepath):
            return filepath

        return False

    def get_thumbnail(self, camera, timestamp):
        filepath = self.path(camera, timestamp, "jpeg")
        if os.path.isfile(filepath):
            return filepath

        return False

    def db_path(self, timestamp):
        clip_date = dt.date.fromtimestamp(timestamp)
        return "{}/clips/{}/{}/{}/meta.json".format(config.storage_path, clip_date.year, clip_date.month, clip_date.day)

    def path(self, camera, timestamp, ext):
        clip_date = dt.date.fromtimestamp(timestamp)
        return "{}/clips/{}/{}/{}/{}/{}.{}".format(config.storage_path, clip_date.year, clip_date.month, clip_date.day, camera, timestamp, ext)

    def generate_video_url(self, clip, type = ""):

        url = "http://{}:{}/clips/{}/{}/{}".format(
            os.environ["API_SERVER_HOST"],
            os.environ["API_SERVER_PORT"],
            clip["camera"],
            type,
            clip["start_time"]
            )

        return url