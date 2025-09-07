from typing import Optional
from pydantic import BaseModel
from models.PR4.PR4 import *

class Location(BaseModel):
    gid: Optional[str] = None
    name: str
    locationType: LocationType
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    platform: Optional[str] = None
    straightLineDistanceInMeters: Optional[int] = None
    hasLocalService: Optional[bool] = None

class GetLocationsResponse(BaseModel):
    results: list[Location] = []
    pagination: PaginationProperties
    links: PaginationLinks
