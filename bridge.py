import json
import os
from enum import Enum
import requests
from requests import Response

class AudienceEnum(Enum):
    Car = "Car"
    Maritime = "Maritime"
    GC = "GC"

class Bridge:
    _headers: dict[str,str]
    _baseURL: str = "https://itsh-apim-prod-6576l5amgavgg.azure-api.net/openapidriver/v1/"

    def __init__(self) -> None:
        apiKey: str | None = os.environ.get("BRIDGE_KEY")
        if apiKey is None: raise ValueError("No API key for bridge provided")
        self._headers = {
            "Ocp-Apim-Subscription-Key": apiKey
        }

    def bridgeMessages(self) -> dict[str,str]:
        r: Response = requests.get(self._baseURL + "bridgemessages", headers=self._headers)
        r.raise_for_status()
        return r.json()
    
    def riverSignals(self) -> str:
        r: Response = requests.get(self._baseURL + "riversignals", headers=self._headers)
        r.raise_for_status()
        return r.json().get("status")
    
    def roadSignals(self) -> str:
        r: Response = requests.get(self._baseURL + "roadsignals", headers=self._headers)
        r.raise_for_status()
        return r.json().get("status")
    
    def sharedPathwaySignals(self) -> str:
        r: Response = requests.get(self._baseURL + "sharedpathwaysignals", headers=self._headers)
        r.raise_for_status()
        return r.json().get("status")
    
    def historySignals(self, fromDate: str, toDate: str, audienceName: AudienceEnum) -> list[dict]:
        body: dict[str,str] = {
            "fromDate": fromDate,
            "toDate": toDate,
            "audienceName": audienceName.value
        }
        r: Response = requests.post(self._baseURL + "historysignals", json=body, headers=self._headers)
        r.raise_for_status()
        print(r.json() == r.text)
        return json.loads(r.json())
