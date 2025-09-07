from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum
from models.APIResponse import APIResponseModel

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

class Occupancy(BaseModel):
    level: OccupancyLevel
    source: OccupancySource

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

class Line(BaseModel):
    gid: Optional[str] = None
    name: Optional[str] = None
    shortName: Optional[str] = None
    designation: Optional[str] = None
    backgroundColor: Optional[str] = None
    foregroundColor: Optional[str] = None
    borderColor: Optional[str] = None
    transportMode: TransportMode
    transportSubMode: TransportSubMode
    isWheelchairAccessible: bool

class ServiceJourney(BaseModel):
    gid: str
    origin: Optional[str] = None
    direction: Optional[str] = None
    directionDetails: DirectionDetails
    line: Line

class StopPoint(BaseModel):
    gid: str
    name: str
    platform: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DepartureAPIModel(BaseModel):
    detailsReference: Optional[str] = None
    serviceJourney: ServiceJourney
    stopPoint: StopPoint
    plannedTime: datetime
    estimatedTime: Optional[datetime] = None
    estimatedOtherwisePlannedTime: datetime
    isCancelled: bool
    isPartCancelled: bool
    occupancy: Optional[Occupancy] = None

class GetDeparturesResponse(APIResponseModel, BaseModel):
    results: list[DepartureAPIModel]
    pagination: PaginationProperties
    links: PaginationLinks

class ArrivalsAPIModel(BaseModel):
    detailsReference: Optional[str] = None
    serviceJourney: ServiceJourney
    stopPoint: StopPoint
    plannedTime: datetime
    estimatedTime: Optional[datetime] = None
    estimatedOtherwisePlannedTime: datetime
    isCancelled: bool
    isPartCancelled: bool

class GetArrivalsResponse(APIResponseModel, BaseModel):
    results: ArrivalsAPIModel
    pagination: PaginationProperties
    links: PaginationLinks
