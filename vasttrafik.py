# coding: utf-8
import base64
from datetime import datetime, timezone, timedelta
import requests
from requests import Response
from requests_futures.sessions import FuturesSession

from models.PR4.DeparturesAndArrivals import GetDeparturesResponse, GetArrivalsResponse, DepartureDetails
from models.ErrorModel import ErrorModel
import models.PR4.Positions as PR4Positions
import models.PR4.Locations as PR4Locations
import models.TrafficSituations.TrafficSituations as TSModels
from PTClasses import StopReq, Result

class Auth():
    __credentials: str
    scope: str
    token: str
    tokenExpiry: datetime

    def __init__(self, key: str, secret: str, scope: str) -> None:
        if key is None or secret is None or scope is None:
            raise TypeError("Usage: Auth(<key>, <secret>, <scope>)")

        if type(key) != str:
            raise TypeError("Expected str [key]")
        if type(secret) != str:
            raise TypeError("Expected str [secret]")

        self.__credentials = base64.b64encode(str.encode(f'{key}:{secret}')).decode("utf-8")
        self.scope = scope

        self.__renewToken()


    def __renewToken(self) -> None:
        header: dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + self.__credentials
        }
        url: str = f'https://ext-api.vasttrafik.se/token?grant_type=client_credentials&scope={self.scope}'
        response: Response = requests.post(url, headers=header)

        response.raise_for_status()

        responseDict: dict[str, str] = response.json()
        self.token = "Bearer " + responseDict["access_token"]
        self.tokenExpiry = datetime.now() + timedelta(seconds=int(responseDict["expires_in"]))


    def ensureValidToken(self) -> None:
        if self.tokenExpiry is None or self.tokenExpiry + timedelta(seconds=10) < datetime.now():
            self.__renewToken()


class PR4():
    def __init__(self, auth: Auth) -> None:
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth


    def __getAuthHeader(self) -> dict[str,str]:
        self.auth.ensureValidToken()
        return {"Authorization": self.auth.token}


    def locations_by_text(self, name: str) -> Result[PR4Locations.GetLocationsResponse, ErrorModel]:
        header = self.__getAuthHeader()
        url = "https://ext-api.vasttrafik.se/pr/v4/locations/by-text"

        response = requests.get(url, headers=header, params={"types": ["stoparea"], "q": name})
        if response.status_code == 200:
            return Result.Ok(PR4Locations.GetLocationsResponse.model_validate_json(response.text))
        else:
            return Result.Err(ErrorModel.model_validate_json(response.text))


    def positions(self, 
                  lowerLeftLat: float, 
                  lowerLeftLon: float, 
                  upperRightLat: float, 
                  upperRightLon: float, 
                  detailsReferences: list[str] = [], 
                  lineDesignations: list[str] = [], 
                  limit: int = 100
                  ) -> Result[list[PR4Positions.JourneyPosition], ErrorModel]: 
        if not 1 <= limit <= 200: raise ValueError("Limit must be between 1 and 200")

        header = self.__getAuthHeader()
        url = "https://ext-api.vasttrafik.se/pr/v4/positions"
        params = {
            "lowerLeftLat": lowerLeftLat,
            "lowerLeftLong": lowerLeftLon,
            "upperRightLat": upperRightLat,
            "upperRightLong": upperRightLon,
            "limit": limit,
            "detailsReferences": detailsReferences,
            "lineDesignations": lineDesignations
        }
        response: Response = requests.get(url, headers=header, params=params)
        if response.status_code == 200:
            return Result.Ok(PR4Positions.JourneyPositionList.model_validate_json(response.text).root)
        else:
            return Result.Err(ErrorModel.model_validate_json(response.text))


    def departureBoard(self, gid: str, date_time: datetime, offset: int = 0) -> Result[GetDeparturesResponse,ErrorModel]:
        header = self.__getAuthHeader()
        url = f"https://ext-api.vasttrafik.se/pr/v4/stop-areas/{gid}/departures"
        if date_time.tzinfo is None or date_time.tzinfo.utcoffset(date_time) is None:
            date_time = date_time.astimezone(timezone.utc)

        response = requests.get(url, headers=header, params={
            "startDateTime": date_time.isoformat(), 
            "limit": 25,
            "timeSpanInMinutes": 720, # 12h
            "maxDeparturesPerLineAndDirection": 25,
            "offset": offset
        })

        if response.status_code == 200:
            return Result.Ok(GetDeparturesResponse.model_validate_json(response.text))
        else:
            return Result.Err(ErrorModel.model_validate_json(response.text))


    def asyncDepartureBoards(self, request_list: list[StopReq]) -> list[tuple[StopReq,Result[GetDeparturesResponse,ErrorModel]]]:
        header = self.__getAuthHeader()
        url = "https://ext-api.vasttrafik.se/pr/v4/stop-areas"

        # Start a session for the async requests
        reqs = []
        with FuturesSession() as session:
            for req in request_list:
                # Send the requests
                future = session.get(f"{url}/{req.stop.value}/departures", headers=header, params=req.getParams())
                reqs.append((req,future))

            responses: list[tuple[StopReq,Response]] = [(sr,req.result()) for (sr,req) in reqs]

        # Check for errors
        return [(s,
                 Result.Ok(GetDeparturesResponse.model_validate_json(r.text)) if r.status_code == 200 else
                 Result.Err(ErrorModel.model_validate_json(r.text))
                 ) for (s,r) in responses]


    def arrivalBoard(self, gid: str, date_time: datetime, offset: int = 0) -> Result[GetArrivalsResponse,ErrorModel]:
        header = self.__getAuthHeader()
        url = f"https://ext-api.vasttrafik.se/pr/v4/stop-areas/{gid}/arrivals"
        if date_time.tzinfo is None or date_time.tzinfo.utcoffset(date_time) is None:
            date_time = date_time.astimezone(timezone.utc)

        response = requests.get(url, headers=header, params={
            "startDateTime": date_time.isoformat(),
            "limit": 25,
            "timeSpanInMinutes": 1339,
            "maxArrivalsPerLineAndDirection": 100,
            "offset": offset
        })
        if response.status_code == 200:
            return Result.Ok(GetArrivalsResponse(**response.json()))
        else:
            return Result.Err(ErrorModel.model_validate_json(response.text))


    def request(self, ref: str, gid: str, ank: bool, geo: bool = False) -> Result[DepartureDetails, ErrorModel]:
        base_url = "https://ext-api.vasttrafik.se/pr/v4/stop-areas"
        url = f"{base_url}/{gid}/{'arrivals' if ank else 'departures'}/{ref}/details?includes=servicejourneycalls"
        if geo:
            url += "&includes=servicejourneycoordinates"
        header = self.__getAuthHeader()
        response: Response = requests.get(url, headers=header)
        if response.status_code == 200:
            return Result.Ok(DepartureDetails.model_validate_json(response.text))
        else:
            return Result.Err(ErrorModel.model_validate_json(response.text))


class TrafficSituations():
    def __init__(self, auth) -> None:
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth
        self.url = "https://ext-api.vasttrafik.se/ts/v1/traffic-situations"


    def __getAuthHeader(self) -> dict[str,str]:
        self.auth.ensureValidToken()
        return {"Authorization": self.auth.token}
    
    
    def __get(self, url) -> Response:
        header = self.__getAuthHeader()
        return requests.get(url, headers=header)

    
    def trafficsituations(self) -> list[TSModels.TrafficSituation]:
        return TSModels.TrafficSituationList.model_validate_json(self.__get(self.url).text).root


    def stoppoint(self, gid) -> list[TSModels.TrafficSituation]:
        resp: Response = self.__get(self.url + f'/stoppoint/{gid}')
        return TSModels.TrafficSituationList.model_validate_json(resp.text).root


    def situation(self, gid) -> TSModels.TrafficSituation:
        resp: Response = self.__get(self.url + f'/{gid}')
        return TSModels.TrafficSituation.model_validate_json(resp.text)


    def line(self, gid) -> list[TSModels.TrafficSituation]:
        resp: Response = self.__get(self.url + f'/line/{gid}')
        return TSModels.TrafficSituationList.model_validate_json(resp.text).root


    def journey(self, gid) -> list[TSModels.TrafficSituation]:
        resp: Response = self.__get(self.url + f'/journey/{gid}')
        return TSModels.TrafficSituationList.model_validate_json(resp.text).root


    def stoparea(self, gid) -> list[TSModels.TrafficSituation]:
        resp: Response = self.__get(self.url + f'/stoparea/{gid}')
        return TSModels.TrafficSituationList.model_validate_json(resp.text).root
    

    def asyncStoparea(self, gid_list: list[int]) -> list[TSModels.TrafficSituation]:
        header = self.__getAuthHeader()
        url = f"{self.url}/stoparea"

        # Start a session for the async requests
        reqs = []
        with FuturesSession() as session:
            for gid in gid_list:
                # Send the requests
                future = session.get(f"{url}/{gid}", headers=header)
                reqs.append((None,future))

            responses = [(_,req.result()) for (_,req) in reqs]

        trafficSituations = map(lambda r: TSModels.TrafficSituationList.model_validate_json(r[1].text).root, responses)
        return [item for sublist in trafficSituations for item in sublist]


if __name__ == "__main__":
    print("Import using 'import vasttrafik'")
    print("or by importing selected classes only:")
    print("'from vasttrafik import Auth, Reseplaneraren, TrafficSituations'")
