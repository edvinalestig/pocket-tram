from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel

from models.PR4.DeparturesAndArrivals import ServiceJourneyDetails
from models.PR4.Positions import JourneyPosition

# Stop IDs (GID)
class Stop(Enum):
    """Enum of stop GIDs"""

    BjurslättsTorg        = 9021014001475000
    Brunnsparken            = 9021014001760000
    Centralstationen        = 9021014001950000
    Chalmers                = 9021014001960000
    Domkyrkan               = 9021014002130000
    Frihamnen               = 9021014002470000
    Frihamnsporten          = 9021014002472000
    Grönsakstorget          = 9021014002850000
    HjalmarBrantingsplatsen = 9021014003180000
    Järntorget              = 9021014003640000
    Järnvågen               = 9021014003645000
    Kapellplatsen           = 9021014003760000
    Korsvägen               = 9021014003980000
    Kungssten               = 9021014004100000
    Käringberget            = 9021014004230000
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