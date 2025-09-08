from dataclasses import dataclass
from pydantic import BaseModel, RootModel
from enum import Enum
from datetime import datetime

class AudienceEnum(Enum):
    Car = "Car"
    Maritime = "Maritime"
    GC = "GC"

class StatusEnum(Enum):
    Open = "Open"
    Closed = "Closed"

class MessageModel(BaseModel):
    timeStamp: datetime
    message: str

class SignalsModel(BaseModel):
    status: StatusEnum

class HistorySignalsModel(BaseModel):
    SignState: bool
    TimeSincePreviousState: int
    AudienceName: AudienceEnum
    PartitionKey: str
    RowKey: str
    Timestamp: datetime
    ETag: str

HistorySignalsModelList = RootModel[list[HistorySignalsModel]]

@dataclass
class AllBridgeDataModel:
    message: MessageModel
    boat: SignalsModel
    car: SignalsModel
    gc: SignalsModel
    openings: list[HistorySignalsModel]
