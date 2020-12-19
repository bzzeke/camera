from pydantic import BaseModel
from typing import List, Optional, Any

class ResponseModel(BaseModel):
    success: bool
    results: Optional[Any]

class ZoneModel(BaseModel):
    zone: List[int]

class CredentialsModel(BaseModel):
    username: str
    password: str

class CameraModel(BaseModel):
    name: str
    username: str
    password: str
    hostname: str
