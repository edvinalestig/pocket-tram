from datetime import datetime
from pydantic import BaseModel, RootModel

class StopPoint(BaseModel):
    gid: str
    name: str
    shortName: str
    stopAreaGid: str
    stopAreaName: str
    stopAreaShortName: str
    municipalityName: str
    municipalityNumber: int

class Direction(BaseModel):
    gid: str
    directionCode: int
    name: str

class Municipality(BaseModel):
    municipalityNumber: int
    municipalityName: str

class Line(BaseModel):
    gid: str
    name: str
    technicalNumber: int
    designation: str
    defaultTransportModeCode: str
    transportAuthorityCode: str
    transportAuthorityName: str
    textColor: str
    backgroundColor: str
    directions: list[Direction]
    municipalities: list[Municipality]
    affectedStopPointGids: list[str]

class Journey(BaseModel):
    gid: str
    departureDateTime: datetime
    line: Line

class TrafficSituation(BaseModel):
    situationNumber: str
    creationTime: datetime
    startTime: datetime
    endTime: datetime
    severity: str
    title: str
    description: str
    affectedStopPoints: list[StopPoint]
    affectedLines: list[Line]
    affectedJourneys: list[Journey]

TrafficSituationList = RootModel[list[TrafficSituation]]