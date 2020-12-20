import os
import json

from pydantic import BaseModel
from typing import List, Optional, Any
from enum import Enum

class CameraDetectionModel(BaseModel):
    enabled = False
    valid_categories: List[str] = []
    zone: List[int] = []

class CameraModel(BaseModel):
    name: str
    onvif_url: str
    detection = CameraDetectionModel()

class CapturerType(str, Enum):
    ffmpeg = 'ffmpeg'
    gstreamer = 'gstreamer'

class HardwareType(str, Enum):
    cpu = 'cpu'
    gpu = 'gpu'

class CapturerModel(BaseModel):
    type: CapturerType = CapturerType.ffmpeg
    hardware: HardwareType = HardwareType.cpu

class NotificationsModel(BaseModel):
    enabled = False
    url = ""

class DetectorModel(BaseModel):
    model_path: str
    clips_max_size = 500
    inference_device: HardwareType = HardwareType.cpu

class UserModel(BaseModel):
    username: str
    password: str

class Config(BaseModel):
    cameras: List[CameraModel]
    capturer: CapturerModel
    notifications: NotificationsModel
    detector: DetectorModel
    user: UserModel
    storage_path: str

    def save(self):
        loco = os.environ['CONFIG_PATH']
        tmp_file = "{}.tmp".format(loco)
        json.dump(self.dict(), open(tmp_file, 'wt'), indent=4)

        os.rename(tmp_file, loco)

        return True

    def get_camera(self, name):
        return list(filter(lambda item: item.name == name, self.cameras)).pop()

config = Config.parse_file(os.environ['CONFIG_PATH'])
