import os
import requests
from requests import Response
from bridge.bridgeModels import *

class Bridge:
    _headers: dict[str,str]
    _baseURL: str = "https://itsh-apim-prod-6576l5amgavgg.azure-api.net/openapidriver/v1/"

    def __init__(self) -> None:
        apiKey: str | None = os.environ.get("BRIDGE_KEY")
        if apiKey is None: raise ValueError("No API key for bridge provided")
        self._headers = {
            "Ocp-Apim-Subscription-Key": apiKey
        }

    def bridgeMessages(self) -> MessageModel:
        r: Response = requests.get(self._baseURL + "bridgemessages", headers=self._headers)
        r.raise_for_status()
        return MessageModel.model_validate_json(r.text)
    
    def riverSignals(self) -> SignalsModel:
        r: Response = requests.get(self._baseURL + "riversignals", headers=self._headers)
        r.raise_for_status()
        return SignalsModel.model_validate_json(r.text)
    
    def roadSignals(self) -> SignalsModel:
        r: Response = requests.get(self._baseURL + "roadsignals", headers=self._headers)
        r.raise_for_status()
        return SignalsModel.model_validate_json(r.text)
    
    def sharedPathwaySignals(self) -> SignalsModel:
        r: Response = requests.get(self._baseURL + "sharedpathwaysignals", headers=self._headers)
        r.raise_for_status()
        return SignalsModel.model_validate_json(r.text)
    
    def historySignals(self, fromDate: str, toDate: str, audienceName: AudienceEnum) -> list[HistorySignalsModel]:
        body: dict[str,str] = {
            "fromDate": fromDate,
            "toDate": toDate,
            "audienceName": audienceName.value
        }
        r: Response = requests.post(self._baseURL + "historysignals", json=body, headers=self._headers)
        r.raise_for_status()
        return HistorySignalsModelList.model_validate_json(r.json()).root
