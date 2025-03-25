# coding: utf-8
import base64
from datetime import datetime, timezone
import requests
from requests import Response
from requests_futures.sessions import FuturesSession

from PTClasses import StopReq

class Auth():
    def __init__(self, key, secret, scope):
        if key == None or secret == None or scope == None:
            raise TypeError("Usage: Auth(<key>, <secret>, <scope>)")

        if type(key) != str:
            raise TypeError("Expected str [key]")
        if type(secret) != str:
            raise TypeError("Expected str [secret]")

        self.__credentials = base64.b64encode(str.encode(f'{key}:{secret}')).decode("utf-8")
        self.scope = scope

        self.__renewToken()


    def __renewToken(self):
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + self.__credentials
        }
        url = f'https://ext-api.vasttrafik.se/token?grant_type=client_credentials&scope={self.scope}'
        response = requests.post(url, headers=header)

        response.raise_for_status()

        responseDict = response.json()
        self.token = "Bearer " + responseDict.get("access_token")


    def checkResponse(self, response: Response):
        if response.status_code == 401:
            self.__renewToken()

            header = {"Authorization": self.token}
            response = requests.get(response.url, headers=header)

        response.raise_for_status()

        try:
            return response.json()
        except requests.exceptions.JSONDecodeError as e:
            print(e)
            with open("error.txt", "w") as f:
                f.write(str(response.content))
            raise Exception()


    def checkResponses(self, response_list: list[tuple[StopReq,Response]]) -> list[tuple[StopReq,dict]]:
        if all([r.status_code == 200 for (_,r) in response_list]):
            return [(sr,r.json()) for (sr,r) in response_list]
        else:
            print("Renewing token..")
            self.__renewToken()
            header = {"Authorization": self.token}

            # Retry!
            session = FuturesSession()
            reqs = []
            for (sr,resp) in response_list:
                # Send the new requests
                reqs.append((sr,session.get(resp.url, headers=header)))

            # Get the results
            resps = [(sr,req.result()) for (sr,req) in reqs]
            for (_,res) in resps:
                res.raise_for_status()

            return [(sr,r.json()) for (sr,r) in resps]


class Reseplaneraren():
    def __init__(self, auth: Auth):
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth

    def locations_by_text(self, name: str) -> dict:
        header = {"Authorization": self.auth.token}
        url = "https://ext-api.vasttrafik.se/pr/v4/locations/by-text"

        response = requests.get(url, headers=header, params={"types":["stoparea"], "q": name})
        return self.auth.checkResponse(response)

    def positions(self, lowerLeftLat, lowerLeftLon, upperRightLat, upperRightLon, 
                  detailsReferences=[], lineDesignations=[], limit=100):
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
        response = requests.get(url, headers=header, params=params)
        return self.auth.checkResponse(response)


    def departureBoard(self, gid: str, date_time: datetime, offset: int = 0) -> dict:
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
        return self.auth.checkResponse(response)


    def asyncDepartureBoards(self, request_list: list[StopReq]) -> list[tuple[StopReq,dict]]:
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
        return self.auth.checkResponses(responses)


    def arrivalBoard(self, gid: str, date_time: datetime, offset: int = 0) -> dict:
        header = {"Authorization": self.auth.token}
        url = f"https://ext-api.vasttrafik.se/pr/v4/stop-areas/{gid}/arrivals"
        if date_time.tzinfo is None or date_time.tzinfo.utcoffset(date_time) is None:
            date_time = date_time.astimezone(timezone.utc)

        response = requests.get(url, headers=header, params={
            "startDateTime": date_time.isoformat(),
            "limit": 25,
            "timeSpanInMinutes": 1339,
            "offset": offset
        })
        return self.auth.checkResponse(response)



    def request(self, ref: str, gid: str, ank: bool, geo: bool = False):
        base_url = "https://ext-api.vasttrafik.se/pr/v4/stop-areas"
        url = f"{base_url}/{gid}/{'arrivals' if ank else 'departures'}/{ref}/details?includes=servicejourneycalls"
        if geo: url += "&includes=servicejourneycoordinates"
        header = {"Authorization": self.auth.token}
        response = requests.get(url, headers=header)
        return self.auth.checkResponse(response)


class TrafficSituations():
    def __init__(self, auth):
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth
        self.url = "https://ext-api.vasttrafik.se/ts/v1/traffic-situations"

    
    def __get(self, url):
        header = {"Authorization": self.auth.token}
        response = requests.get(url, headers=header)
        return self.auth.checkResponse(response)

    
    def trafficsituations(self):
        url = self.url
        return self.__get(url)


    def stoppoint(self, gid):
        url = self.url + f'/stoppoint/{gid}'
        return self.__get(url)


    def situation(self, gid):
        url = self.url + f'/{gid}'
        return self.__get(url)


    def line(self, gid):
        url = self.url + f'/line/{gid}'
        return self.__get(url)


    def journey(self, gid):
        url = self.url + f'/journey/{gid}'
        return self.__get(url)


    def stoparea(self, gid):
        url = self.url + f'/stoparea/{gid}'
        return self.__get(url)


if __name__ == "__main__":
    print("Import using 'import vasttrafik'")
    print("or by importing selected classes only:")
    print("'from vasttrafik import Auth, Reseplaneraren, TrafficSituations'")
