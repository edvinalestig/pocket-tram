from pydantic import BaseModel
from typing import Optional
from models.PR4.PR4 import *

class TariffZone(BaseModel):
    gid: Optional[str] = None
    name: Optional[str] = None
    number: int
    shortName: Optional[str] = None

class StopArea(BaseModel):
    gid: Optional[str] = None
    name: Optional[str] = None
    latitude: float
    longitude: float
    tariffZone1: TariffZone
    tariffZone2: Optional[TariffZone] = None

class StopPoint(BaseModel):
    gid: str
    name: str
    platform: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    stopArea: StopArea
