import os
import json

from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum

storage_path = os.path.realpath(os.path.dirname(os.path.realpath(__file__) + "/../../../storage/"))
config_path = "{}/data/config.json".format(storage_path)

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
    CPU = 'CPU'
    GPU = 'GPU'

class CapturerModel(BaseModel):
    type: CapturerType = CapturerType.ffmpeg
    hardware: HardwareType = HardwareType.CPU

class NotificationsModel(BaseModel):
    enabled = False
    url = ""

class DetectorModel(BaseModel):
    model_path: str = "{}/models/yolo-v2-tf.xml".format(storage_path)
    clips_max_size = 500
    inference_device: HardwareType = HardwareType.CPU

class UserModel(BaseModel):
    username: str = ""
    password: str = ""

class Config(BaseModel):
    cameras: Dict[str, CameraModel] = {}
    capturer: CapturerModel = CapturerModel()
    notifications: NotificationsModel = NotificationsModel()
    detector: DetectorModel = DetectorModel()
    user: UserModel = UserModel()

    def save(self):
        tmp_file = "{}.tmp".format(config_path)
        json.dump(self.dict(), open(tmp_file, 'wt'), indent=4)

        os.rename(tmp_file, config_path)

        return True

    def get_camera(self, id):
        return self.cameras[id] if id in self.cameras else None


if os.path.isfile(config_path):
    config = Config.parse_file(config_path)
else:
    config = Config()
    config.save()
