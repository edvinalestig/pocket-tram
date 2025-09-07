from typing import Optional
from pydantic import BaseModel, RootModel
from models.PR4.PR4 import *

class LineDetails(BaseModel):
    name: Optional[str] = None
    detailName: Optional[str] = None
    backgroundColor: Optional[str] = None
    foregroundColor: Optional[str] = None
    borderColor: Optional[str] = None
    transportMode: TransportMode
    transportSubMode: TransportSubMode

class JourneyPosition(BaseModel):
    detailsReference: Optional[str] = None
    line: LineDetails
    notes: list[Note] = []
    name: Optional[str] = None
    direction: Optional[str] = None
    directionDetails: DirectionDetails
    latitude: Optional[float] = None
    longitude: Optional[float] = None

JourneyPositionList = RootModel[list[JourneyPosition]]