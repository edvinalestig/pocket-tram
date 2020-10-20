# coding: utf-8
import base64
import time
import requests
from requests_futures.sessions import FuturesSession

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
        url = f'https://api.vasttrafik.se/token?grant_type=client_credentials&scope={self.scope}'
        response = requests.post(url, headers=header)
        responseDict = response.json()

        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f'{response.status_code} {responseDict.get("error_description")}')

        self.token = "Bearer " + responseDict.get("access_token")


    def checkResponse(self, response):
        if response.status_code == 401:
            self.__renewToken()

            header = {"Authorization": self.token}
            response = requests.get(response.url, headers=header)

        responseDict = response.json()
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f'{response.status_code} {responseDict.get("error_description")}')

        return response

    def checkResponses(self, response_list):
        fine = True
        for resp in response_list:
            # Check for any errors
            if resp.status_code != 200:
                fine = False

        if fine:
            return response_list
        else:
            print("Renewing token..")
            self.__renewToken()
            header = {"Authorization": self.token}

            # Retry!
            session = FuturesSession()
            reqs = []
            for resp in response_list:
                # Send the new requests
                url = resp.url
                reqs.append(session.get(url, headers=header))
                time.sleep(0.01)

            # Get the results
            resps = []
            for req in reqs:
                resps.append(req.result())

            if resps[0].status_code != 200:
                raise requests.exceptions.HTTPError(f'{resps[0].status_code} {resps[0].reason}')

            return resps


class Reseplaneraren():
    def __init__(self, auth):
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth


    def trip(self, **kwargs):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/trip"
        kwargs["format"] = "json"

        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.checkResponse(response)

        return response.json()


    def location_nearbyaddress(self, **kwargs):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/location.nearbyaddress"
        kwargs["format"] = "json"
 
        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.checkResponse(response)

        return response.json()


    def location_nearbystops(self, **kwargs):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/location.nearbystops"
        kwargs["format"] = "json"

        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.checkResponse(response)

        return response.json()


    def location_allstops(self, **kwargs):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/location.allstops"
        kwargs["format"] = "json"

        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.checkResponse(response)

        return response.json()


    def location_name(self, **kwargs):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/location.name"
        kwargs["format"] = "json"

        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.checkResponse(response)

        return response.json()


    def systeminfo(self, **kwargs):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/systeminfo"
        kwargs["format"] = "json"

        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.checkResponse(response)

        return response.json()


    def livemap(self, **kwargs):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/livemap"
        kwargs["format"] = "json"

        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.checkResponse(response)

        return response.json()


    def journeyDetail(self, ref):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/journeyDetail"

        response = requests.get(url, headers=header, params={"ref":ref})
        response = self.auth.checkResponse(response)

        return response.json()


    def geometry(self, ref):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/geometry"

        response = requests.get(url, headers=header, params={"ref":ref})
        response = self.auth.checkResponse(response)

        return response.json()


    def departureBoard(self, **kwargs):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/departureBoard"
        kwargs["format"] = "json"

        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.checkResponse(response)

        return response.json()


    def asyncDepartureBoards(self, request_list):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/departureBoard"

        # Start a session for the async requests
        session = FuturesSession()
        reqs = []
        for req in request_list:
            # Send the requests
            req["format"] = "json"
            future = session.get(url, headers=header, params=req)
            reqs.append(future)
            time.sleep(0.02) # Without this everything breaks

        responses = []
        for req in reqs:
            # Get the results
            r = req.result()
            responses.append(r)

        # Check for errors
        resp = self.auth.checkResponses(responses)

        output = []
        for response in resp:
            output.append(response.json())

        return output


    def arrivalBoard(self, **kwargs):
        header = {"Authorization": self.auth.token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/arrivalBoard"
        kwargs["format"] = "json"

        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.checkResponse(response)

        return response.json()


    def request(self, url):
        header = {"Authorization": self.auth.token}
        response = requests.get(url, headers=header)
        response = self.auth.checkResponse(response)

        return response.json()


class TrafficSituations():
    def __init__(self, auth):
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth
        self.url = "https://api.vasttrafik.se/ts/v1/traffic-situations"

    
    def __get(self, url):
        header = {"Authorization": self.auth.token}
        response = requests.get(url, headers=header)
        response = self.auth.checkResponse(response)

        return response.json()

    
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