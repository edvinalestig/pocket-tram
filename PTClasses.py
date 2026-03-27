from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Generic, TypeVar, Union, Any

from models.PR4.DeparturesAndArrivals import ServiceJourneyDetails
from models.PR4.Positions import JourneyPosition

# Stop IDs (GID)
class Stop(Enum):
    """Enum of stop GIDs"""

    Bergsprängaregatan      = 9021014001390000
    BjurslättsTorg          = 9021014001475000
    Brunnsparken            = 9021014001760000
    Centralstationen        = 9021014001950000
    Chalmers                = 9021014001960000
    Domkyrkan               = 9021014002130000
    Engdahlsgatan           = 9021014002230000
    Frihamnen               = 9021014002470000
    Frihamnsporten          = 9021014002472000
    Grönsakstorget          = 9021014002850000
    HjalmarBrantingsplatsen = 9021014003180000
    Järntorget              = 9021014003640000
    Järnvågen               = 9021014003645000
    Kapellplatsen           = 9021014003760000
    Korsvägen               = 9021014003980000
    Kungsportsplatsen       = 9021014004090000
    Kungssten               = 9021014004100000
    Käringberget            = 9021014004230000
    LillaBommen             = 9021014004380000
    Lindholmen              = 9021014004490000
    Lindholmspiren          = 9021014004493000
    Mariaplan               = 9021014004730000
    Marklandsgatan          = 9021014004760000
    Nordstan                = 9021014004945000
    NyaVarvetsTorg          = 9021014005105000
    NyaVarvsallén           = 9021014005100000
    Regnbågsgatan           = 9021014005465000
    Stenpiren               = 9021014006242000
    Svingeln                = 9021014006480000
    Tolvskillingsgatan      = 9021014006790000
    UlleviNorra             = 9021014007171000
    Valand                  = 9021014007220000
    Varbergsgatan           = 9021014007270000
    Vasaplatsen             = 9021014007300000
    Vidblicksgatan          = 9021014007400000
    Wieselgrensgatan        = 9021014007420000
    Wieselgrensplatsen      = 9021014007430000
    Ålandsgatan             = 9021014007440000

class StopReq(BaseModel):
    title: str
    showCountdown: bool
    compileFirst: bool
    dest: str
    excludeLines: list[str]
    excludeDestinations: list[str]
    stop: Stop
    direction: Stop
    startDateTime: datetime

    def getParams(self) -> dict[str, int | str]:
        return {
            "maxDeparturesPerLineAndDirection": 3,
            "directionGid": self.direction.value,
            "startDateTime": self.startDateTime.astimezone(timezone.utc).isoformat(),
            "limit": 100
        }

class Departure(BaseModel):
    line: str
    dest: str
    time: list[int | str]
    bgColor: str
    fgColor: str

class RouteMapData(BaseModel):
    geo: list[ServiceJourneyDetails]
    positions: list[JourneyPosition]

T1 = TypeVar('T1')
T2 = TypeVar('T2')

class Result(Generic[T1, T2]):
    """
    Polymorphic Result type, similar to Rust's Result enum.
    Use Result.Ok(value) or Result.Err(error) to construct.
    """
    def __init__(self, is_ok: bool, value: Any):
        self._is_ok = is_ok
        self._value = value

    @classmethod
    def Ok(cls, value: T1) -> 'Result[T1, T2]':
        return cls(True, value)

    @classmethod
    def Err(cls, error: T2) -> 'Result[T1, T2]':
        return cls(False, error)

    def is_ok(self) -> bool:
        return self._is_ok

    def is_err(self) -> bool:
        return not self._is_ok

    def ok(self) -> Union[T1, None]:
        return self._value if self._is_ok else None

    def err(self) -> Union[T2, None]:
        return self._value if not self._is_ok else None

    def unwrap(self) -> T1:
        if self._is_ok:
            return self._value
        raise ValueError(f"Called unwrap on Err: {self._value}")

    def unwrap_err(self) -> T2:
        if not self._is_ok:
            return self._value
        raise ValueError(f"Called unwrap_err on Ok: {self._value}")

    def __repr__(self):
        if self._is_ok:
            return f"Ok({self._value!r})"
        else:
            return f"Err({self._value!r})"
