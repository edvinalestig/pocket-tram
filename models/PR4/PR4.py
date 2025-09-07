from pydantic import BaseModel
from typing import Optional
from enum import Enum

class PaginationProperties(BaseModel):
    limit: int
    offset: int
    size: int

class PaginationLinks(BaseModel):
    previous: Optional[str] = None
    next: Optional[str] = None
    current: Optional[str] = None

class OccupancyLevel(Enum):
    low = "low"
    medium = "medium"
    high = "high"
    incomplete = "incomplete"
    missing = "missing"
    notpublictransport = "notpublictransport"

class OccupancySource(Enum):
    prediction = "prediction"
    realtime = "realtime"

class OccupancyInformation(BaseModel):
    level: OccupancyLevel
    source: OccupancySource

class SeverityEnum(Enum):
    unknown = "unknown"
    low = "low"
    normal = "normal"
    high = "high"

class Note(BaseModel):
    type: Optional[str] = None
    severity: SeverityEnum
    text: Optional[str] = None

class DirectionDetails(BaseModel):
    fullDirection: Optional[str] = None
    shortDirection: Optional[str] = None
    replaces: Optional[str] = None
    via: Optional[str] = None
    isFreeService: Optional[bool] = None
    isPaidService: Optional[bool] = None
    isSwimmingService: Optional[bool] = None
    isDirectDestinationBus: Optional[bool] = None
    isFrontEntry: Optional[bool] = None
    isExtraBus: Optional[bool] = None
    isExtraBoat: Optional[bool] = None
    isExtraTram: Optional[bool] = None
    isSchoolBus: Optional[bool] = None
    isExpressBus: Optional[bool] = None
    fortifiesLine: Optional[str] = None

class TransportMode(Enum):
    unknown = "unknown"
    none = "none"
    tram = "tram"
    bus = "bus"
    ferry = "ferry"
    train = "train"
    taxi = "taxi"
    walk = "walk"
    bike = "bike"
    car = "car"
    teletaxi = "teletaxi"

class TransportSubMode(Enum):
    unknown = "unknown"
    none = "none"
    vasttagen = "vasttagen"
    longdistancetrain = "longdistancetrain"
    regionaltrain = "regionaltrain"
    flygbussarna = "flygbussarna"

class LocationType(Enum):
    unknown = "unknown"
    stoparea = "stoparea"
    stoppoint = "stoppoint"
    address = "address"
    pointofinterest = "pointofinterest"
    metastation = "metastation"
