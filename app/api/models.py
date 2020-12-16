from pydantic import BaseModel
from typing import List, Optional, Any

class ResponseModel(BaseModel):
    status: str
    results: Optional[Any]


class ZoneModel(BaseModel):
    zone: List[int]
