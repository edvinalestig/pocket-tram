# coding: utf-8
import base64
from datetime import datetime, timezone
import requests
from requests import Response
from requests_futures.sessions import FuturesSession

from models.PR4.DeparturesAndArrivals import GetDeparturesResponse, GetArrivalsResponse, DepartureDetails
import models.PR4.Positions as PR4Positions
import models.PR4.Locations as PR4Locations
import models.TrafficSituations.TrafficSituations as TSModels
from PTClasses import StopReq

class Auth():
    __credentials: str
    scope: str
    token: str

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


    def checkResponse(self, response: Response) -> Response:
        if response.status_code == 401:
            self.__renewToken()

            header: dict[str, str] = {"Authorization": self.token}
            response = requests.get(response.url, headers=header)

        response.raise_for_status()
        return response


    def checkResponses(self, response_list: list[tuple[StopReq,Response]]) -> list[tuple[StopReq,Response]]:
        if all([r.status_code == 200 for (_,r) in response_list]):
            return response_list
        else:
            print("Renewing token..")
            self.__renewToken()
            header: dict[str, str] = {"Authorization": self.token}

            # Retry!
            session = FuturesSession()
            reqs = []
            for (sr,resp) in response_list:
                # Send the new requests
                reqs.append((sr,session.get(resp.url, headers=header)))

            # Get the results
            resps: list[tuple[StopReq,Response]] = [(sr,req.result()) for (sr,req) in reqs]
            for (_,res) in resps:
                res.raise_for_status()

            return resps


class PR4():
    def __init__(self, auth: Auth) -> None:
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth


    def locations_by_text(self, name: str) -> PR4Locations.GetLocationsResponse:
        header = {"Authorization": self.auth.token}
        url = "https://ext-api.vasttrafik.se/pr/v4/locations/by-text"

        response = requests.get(url, headers=header, params={"types":["stoparea"], "q": name})
        return PR4Locations.GetLocationsResponse.model_validate_json(self.auth.checkResponse(response).text)


    def positions(self, 
                  lowerLeftLat: float, 
                  lowerLeftLon: float, 
                  upperRightLat: float, 
                  upperRightLon: float, 
                  detailsReferences: list[str] = [], 
                  lineDesignations: list[str] = [], 
                  limit: int = 100
                  ) -> list[PR4Positions.JourneyPosition]: 
        if not 1 <= limit <= 200: raise ValueError("Limit must be between 1 and 200")

        header = {"Authorization": self.auth.token}
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
        return PR4Positions.JourneyPositionList.model_validate_json(self.auth.checkResponse(response).text).root


    def departureBoard(self, gid: str, date_time: datetime, offset: int = 0) -> GetDeparturesResponse:
        header = {"Authorization": self.auth.token}
        url = f"https://ext-api.vasttrafik.se/pr/v4/stop-areas/{gid}/departures"
        if date_time.tzinfo is None or date_time.tzinfo.utcoffset(date_time) is None:
            date_time = date_time.astimezone(timezone.utc)

        response = requests.get(url, headers=header, params={
            "startDateTime": date_time.isoformat(), 
            "limit": 25,
            "timeSpanInMinutes": 1339,
            "maxDeparturesPerLineAndDirection": 100,
            "offset": offset
        })
        return GetDeparturesResponse.model_validate_json(self.auth.checkResponse(response).text)


    def asyncDepartureBoards(self, request_list: list[StopReq]) -> list[tuple[StopReq,GetDeparturesResponse]]:
        header = {"Authorization": self.auth.token}
        url = "https://ext-api.vasttrafik.se/pr/v4/stop-areas"

        # Start a session for the async requests
        session = FuturesSession()
        reqs = []
        for req in request_list:
            # Send the requests
            future = session.get(f"{url}/{req.stop.value}/departures", headers=header, params=req.getParams())
            reqs.append((req,future))

        responses = [(sr,req.result()) for (sr,req) in reqs]

        # Check for errors
        return [(s, GetDeparturesResponse.model_validate_json(r.text)) for (s,r) in self.auth.checkResponses(responses)]


    def arrivalBoard(self, gid: str, date_time: datetime, offset: int = 0) -> GetArrivalsResponse:
        header = {"Authorization": self.auth.token}
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
        return GetArrivalsResponse(**self.auth.checkResponse(response).json())


    def request(self, ref: str, gid: str, ank: bool, geo: bool = False) -> DepartureDetails:
        base_url = "https://ext-api.vasttrafik.se/pr/v4/stop-areas"
        url = f"{base_url}/{gid}/{'arrivals' if ank else 'departures'}/{ref}/details?includes=servicejourneycalls"
        if geo: url += "&includes=servicejourneycoordinates"
        header = {"Authorization": self.auth.token}
        response: Response = requests.get(url, headers=header)
        return DepartureDetails.model_validate_json(self.auth.checkResponse(response).text)


class TrafficSituations():
    def __init__(self, auth) -> None:
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth
        self.url = "https://ext-api.vasttrafik.se/ts/v1/traffic-situations"

    
    def __get(self, url) -> Response:
        header = {"Authorization": self.auth.token}
        response = requests.get(url, headers=header)
        return self.auth.checkResponse(response)

    
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


if __name__ == "__main__":
    print("Import using 'import vasttrafik'")
    print("or by importing selected classes only:")
    print("'from vasttrafik import Auth, Reseplaneraren, TrafficSituations'")
