from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from models.PR4.PR4 import *
import models.PR4.JourneyDetails as JourneyDetails

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
    directionDetails: Optional[DirectionDetails] = None
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
    occupancy: Optional[OccupancyInformation] = None

class GetDeparturesResponse(BaseModel):
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

class GetArrivalsResponse(BaseModel):
    results: list[ArrivalsAPIModel]
    pagination: PaginationProperties
    links: PaginationLinks

class LineDetails(BaseModel):
    name: Optional[str] = None
    detailName: Optional[str] = None
    backgroundColor: Optional[str] = None
    foregroundColor: Optional[str] = None
    borderColor: Optional[str] = None
    transportMode: TransportMode
    transportSubMode: TransportSubMode

class Coordinate(BaseModel):
    latitude: float
    longitude: float
    elevation: Optional[float] = None

class CallDetails(BaseModel):
    stopPoint: JourneyDetails.StopPoint
    plannedArrivalTime: Optional[datetime] = None
    estimatedArrivalTime: Optional[datetime] = None
    plannedDepartureTime: Optional[datetime] = None
    estimatedDepartureTime: Optional[datetime] = None
    estimatedOtherwisePlannedArrivalTime: Optional[datetime] = None
    estimatedOtherwisePlannedDepartureTime: Optional[datetime] = None
    plannedPlatform: Optional[str] = None
    estimatedPlatform: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    index: Optional[str] = None
    occupancy: Optional[OccupancyInformation] = None
    isCancelled: bool
    isDepartureCancelled: Optional[bool] = None
    isArrivalCancelled: Optional[bool] = None

class ServiceJourneyDetails(BaseModel):
    gid: Optional[str] = None
    direction: Optional[str] = None
    directionDetails: DirectionDetails
    line: LineDetails
    serviceJourneyCoordinates: list[Coordinate] = []
    callsOnServiceJourney: list[CallDetails] = []

class DepartureDetails(BaseModel):
    serviceJourneys: list[ServiceJourneyDetails] = []
    occupancy: Optional[OccupancyInformation] = None
