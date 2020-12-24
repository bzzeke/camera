import os
import json

from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum

class CameraDetectionModel(BaseModel):
    enabled = False
    valid_categories: List[str] = []
    zone: List[int] = []

class CameraType(str, Enum):
    onvif = 'onvif'
    test = 'test'

class CameraModel(BaseModel):
    name: str
    manage_url: str
    type: CameraType = CameraType.onvif
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
    cameras: Dict[str, CameraModel]
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

    def get_camera(self, id):
        return self.cameras[id] if id in self.cameras else None

config = Config.parse_file(os.environ['CONFIG_PATH'])
