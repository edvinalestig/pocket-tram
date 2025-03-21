from flask import Flask, request, send_file
from vasttrafik import Auth, Reseplaneraren, TrafficSituations
import json
import dateutil.tz as tz
from datetime import datetime, timedelta, timezone
import math
from os import environ
from enum import Enum

from utilityPages import UtilityPages

app = Flask(__name__)

auth = Auth(environ["VTClient"], environ["VTSecret"], "app")
rp = Reseplaneraren(auth)
ts = TrafficSituations(auth)
utilPages = UtilityPages(rp)

# Stop IDs (GID)
class S(Enum):
    """Enum of stop GIDs"""

    Bjurslättstorget        = 9021014001475000
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
    Ålandsgatan             = 9021014007440000

@app.route("/")
def index():
    return send_file("static/index.html")

@app.route("/favicon.ico")
def favicon():
    return send_file("static/favicon.ico")

# "Hidden" page: displays response from VT when searching for a stop
# Usage: <url>/searchstop?stop=<name>
@app.route("/searchstop")
def seachStop():
    return json.dumps(rp.locations_by_text(request.args.get("stop")))

@app.route("/utilities")
def utilities():
    return utilPages.mainPage()

@app.route("/findDepartures")
def findDepartures():
    if request.args.get("moreInfo") == "on":
        return utilPages.searchStop(request.args)
    else:
        return utilPages.simpleSearchStop(request.args)

@app.route("/findArrivals")
def findArrivals():
    return utilPages.simpleStopArrivals(request.args)

@app.route("/depInfo")
def depInfo():
    return utilPages.depInfo(request.args)

@app.route("/simpleDepInfo")
def simpleDepInfo():
    return utilPages.simpleDepInfo(request.args)

@app.route("/getgeometry")
def getgeometry():
    return utilPages.getGeometry(request.args)

@app.route("/map")
def routemap():
    return send_file("static/map.html")

@app.route("/mapdata")
def routedata():
    return utilPages.routemap(request.args)

@app.route("/position")
def position():
    return utilPages.position(request.args)

@app.route("/request")
def req():
    place = request.args.get("place")
    timeNow = datetime.now(tz.gettz("Europe/Stockholm")).strftime("%H:%M:%S")

    if place == "lgh":
        deps = getDepartures([
            compileDict(S.UlleviNorra, S.Chalmers, countdown=False, first=True),
            compileDict(S.Svingeln, S.HjalmarBrantingsplatsen, countdown=False, first=True, dest="Hjalmar Brantingspl.", excludeLines=["6"]),
            compileDict(S.Svingeln, S.Lindholmen, countdown=False, first=True),
            compileDict(S.UlleviNorra, S.Centralstationen)
        ])

        return json.dumps({
            "stops": {
                "Mot Chalmers": deps[0],
                "Mot Hjalmar Brantingsplatsen": deps[1],
                "Mot Lindholmen": deps[2],
                "Mot Centralstationen": deps[3]
            },
            "ts": getTrafficSituation(place),
            "time": timeNow
        })

    elif place == "huset":
        deps = getDepartures([
            compileDict(S.NyaVarvetsTorg, S.Järnvågen, countdown=False),
            compileDict(S.NyaVarvsallén, S.Kungssten, countdown=False)
        ])

        return json.dumps({
            "stops": {
                "Nya Varvets Torg": deps[0],
                "Nya Varvsallén": deps[1]
            },
            "ts": getTrafficSituation(place),
            "time": timeNow
        })

    elif place == "jt":
        deps = getDepartures([
            compileDict(S.Järntorget, S.Chalmers),
            compileDict(S.Järntorget, S.HjalmarBrantingsplatsen),
            compileDict(S.Järntorget, S.Käringberget),
            compileDict(S.Järntorget, S.UlleviNorra, excludeLines=["6"])
        ])

        return json.dumps({
            "stops": {
                "Mot Chalmers": deps[0],
                "Mot Hjalmar Brantingsplatsen": deps[1],
                "Mot Pappa": deps[2],
                "Mot Mamma": deps[3]
            },
            "ts": getTrafficSituation(place),
            "time": timeNow
        })

    elif place == "domkyrkan":
        deps = getDepartures([
            compileDict(S.Domkyrkan, S.Bjurslättstorget),
            compileDict(S.Domkyrkan, S.Kapellplatsen)
        ])

        return json.dumps({
            "stops": {
                "Mot Bjurslätts torg": deps[0],
                "Mot Kapellplatsen": deps[1]
            },
            "ts": getTrafficSituation(place),
            "time": timeNow
        })

    elif place == "bjurslatt":
        deps = getDepartures([
            compileDict(S.Bjurslättstorget, S.HjalmarBrantingsplatsen, first=True, dest="Hjalmar Brantingspl.", excludeLines=["31"], excludeDestinations=["Kippholmen"]),
            compileDict(S.Bjurslättstorget, S.Lindholmen)
        ])

        return json.dumps({
            "stops": {
                "Mot Hjalmar Brantingsplatsen": deps[0],
                "Mot Lindholmen": deps[1]
            },
            "ts": getTrafficSituation(place),
            "time": timeNow
        })

    elif place == "hjalmar":
        deps = getDepartures([
            compileDict(S.HjalmarBrantingsplatsen, S.Wieselgrensgatan, first=True, excludeLines=["31"]),
            compileDict(S.HjalmarBrantingsplatsen, S.Chalmers, excludeLines=["6"]),
            compileDict(S.HjalmarBrantingsplatsen, S.Svingeln, first=True)
        ])

        return json.dumps({
            "stops": {
                "Mot Wieselgrensgatan": deps[0],
                "Mot Chalmers": deps[1],
                "Mot Svingeln": deps[2],
            },
            "ts": getTrafficSituation(place),
            "time": timeNow
        })

    elif place == "chalmers":
        deps = getDepartures([
            compileDict(S.Chalmers, S.Domkyrkan, excludeLines=["6"]),
            compileDict(S.Chalmers, S.Brunnsparken, first=True, dest="Brunnsparken", excludeLines=["6"]),
            compileDict(S.Chalmers, S.UlleviNorra, first=True, dest="Ullevi Norra"),
            compileDict(S.Chalmers, S.Lindholmen)
        ])

        return json.dumps({
            "stops": {
                "Mot Domkyrkan": deps[0],
                "Mot Brunnsparken": deps[1],
                "Mot Ullevi Norra": deps[2],
                "Mot Lindholmen": deps[3],
            },
            "ts": getTrafficSituation(place),
            "time": timeNow
        })

    elif place == "lindholmen":
        deps = getDepartures([
            compileDict(S.Lindholmen, S.Bjurslättstorget),
            compileDict(S.Lindholmen, S.Svingeln, first=True),
            compileDict(S.Lindholmspiren, S.Stenpiren),
        ])

        return json.dumps({
            "stops": {
                "Mot Bjurslätts torg": deps[0],
                "Mot Svingeln": deps[1],
                "Båt": deps[2],
            },
            "ts": getTrafficSituation(place),
            "time": timeNow
        })
        
    elif place == "brunnsparken":
        deps = getDepartures([
            compileDict(S.Brunnsparken, S.Chalmers, excludeLines=["6"]),
            compileDict(S.Brunnsparken, S.Bjurslättstorget),
            compileDict(S.Brunnsparken, S.HjalmarBrantingsplatsen, first=True, dest="Hjalmar Brantingspl.")
        ])

        return json.dumps({
            "stops": {
                "Mot Chalmers": deps[0],
                "Mot Bjurslätts torg": deps[1],
                "Mot Hjalmar Brantingsplatsen": deps[2]
            },
            "ts": getTrafficSituation("centrum"),
            "time": timeNow
        })


    return json.dumps({
        "test":"test2",
        "time": timeNow
    })


def compileDict(fr: S, to: S, countdown=True, first=False, dest=None, offset=0, excludeLines=[], excludeDestinations=[]):
    """Compiles a dict with all info for getDeparture() so it can be sent asynchronously
    
    Parameters
    ----------
    fr: Stop enum
        From stop

    to: Stop enum
        To stop   

    countdown: bool, optional
        If time left (countdown) or the timetable time with offset should be displayed

    first: bool, optional
        Show combined row of all departures toward a stop (first 3)

    dest: str, optional
        Destination showed for the combined row

    offset: int, optional
        Time offset in minutes to not show unnecessary departures

    excludeLines: list[str], optional
        Line numbers to exclude from the result

    excludeDestinations: list[str], optional
        Line destinations to exclude from the result
    """

    timeNow = datetime.now(tz.gettz("Europe/Stockholm")) + timedelta(minutes=offset)
    # timeNow = datetime(year=2023, month=6, day=28, hour=8, minute=0) + timedelta(minutes=offset)
    return {
        "request": {
            "gid": fr.value,
            "params": {
                "maxDeparturesPerLineAndDirection": 3,
                "directionGid": to.value,
                "startDateTime": timeNow.astimezone(timezone.utc).isoformat(),
                "limit": 100
            }
        },
        "countdown": countdown,
        "first": first,
        "dest": dest or to.name,
        "excludeLines": excludeLines,
        "excludeDestinations": excludeDestinations
    }

# Takes a list of compiled dicts and returns a list of cleaned results
# Does what getDeparture() does but with many at the same time
def getDepartures(reqList):
    reqs = [req["request"] for req in reqList]
    responses = rp.asyncDepartureBoards(reqs)
    returnList = []
    for i, resp in enumerate(responses):
        returnList.append(clean(resp, reqList[i]["countdown"], reqList[i]["first"], reqList[i]["dest"], reqList[i]["excludeLines"], reqList[i]["excludeDestinations"]))
    return returnList

# obj: Object received from VT API
# countdown, first, dest: same as getDeparture()
def clean(obj, countdown, first, dest, excludeLines, excludeDestinations):
    deps = obj.get("results")

    if deps == None:
        # No departures found
        return []

    firstDeps = {
        "line": "🚋",
        "dest": dest,
        "time": [],
        "fgColor": "blue",
        "bgColor": "white"
    }

    outArr = []
    for dep in deps:
        sj = dep.get("serviceJourney")
        line = sj.get("line").get("shortName")
        if line in excludeLines: continue

        dest = sj.get("directionDetails").get("shortDirection").replace("Brantingsplatsen", "Brantingspl.")
        if dest in excludeDestinations: continue

        ctdown = calculateCountdown(dep)

        # If the time left or the time+delay should be shown
        if countdown:
            time = ctdown
        else:
            t = datetime.fromisoformat("".join(dep.get("plannedTime").split(".0000000")))
            time = t.strftime("%H:%M") + getDelay(dep)

        i = 0
        while i < len(outArr):
            # Check if that line & destination is already present.
            # Put all departures in one list
            if outArr[i].get("line") == line and outArr[i].get("dest") == dest:
                outArr[i]["time"].append(time)
                break
            i += 1
        else:
            # The line & destination is not in the list
            vitals = {
                "line": line,
                "dest": dest,
                "time": [time],
                "bgColor": sj.get("line").get("backgroundColor"),
                "fgColor": sj.get("line").get("foregroundColor")
            }
            outArr.append(vitals)
        
        if (type(ctdown) == int) or (ctdown == "Nu"):
            # Add countdowns to a list of all departures toward a stop if 
            # they aren't cancelled or not having realtime info.
            firstDeps["time"].append(ctdown)

    if first:
        # All departures toward a stop
        # Get only the first three after sorting
        if len(firstDeps["time"]) > 0:
            sort = sortDepartures([firstDeps])[0]
            sort["time"] = sort["time"][:3]
            outArr.append(sort)

    return sortDepartures(outArr)

def getDelay(dep):
    if dep.get("isCancelled"):
        return " X"

    # Check if real time info is available
    tttime = dep.get("plannedTime")
    rttime = dep.get("estimatedTime")
    if rttime == None:
        return ""

    ttdt = datetime.fromisoformat("".join(tttime.split(".0000000")))
    rtdt = datetime.fromisoformat("".join(rttime.split(".0000000")))
    delta = rtdt - ttdt

    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    delay = delta.days * 1440 + math.floor(delta.seconds/60)

    if delay >= 0:
        return f"+{delay}"
    else:
        return str(delay)

def calculateCountdown(departure):
    if departure.get("isCancelled"):
        return "❌"

    # Check if real time info is available
    dTime = departure.get("estimatedTime")
    if dTime == None:
        realtime = False
        dTime = departure.get("plannedTime")
    else:
        realtime = True

    depTime = datetime.fromisoformat("".join(dTime.split(".0000000")))
    timeNow = datetime.now(tz.gettz("Europe/Stockholm"))

    # Time left:
    countdown = depTime - timeNow
    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    countdown = countdown.days * 1440 + math.ceil(countdown.seconds/60)


    if realtime:
        if countdown <= 0:
            return "Nu"
        else:
            return countdown
    else:
        return f'Ca {countdown}'

def sortDepartures(arr):
    # Get the departures in the correct order in case the one behind is actually in front
    for i, dep in enumerate(arr):
        # Do not sort the list if there are strings in it (except 'Nu'), they  
        # might be "00:12+1" and "23:56-2" which would then be swapped.
        skip = False
        for t in arr[i]["time"]:
            if type(t) == str and t != "Nu":
                skip = True
        if skip: 
            continue

        try:
            arr[i]["time"] = sorted(arr[i]["time"], key=lambda t: prioTimes(t))
        except TypeError:
            # One departure was a string and it doesn't like mixing strings and numbers
            pass

    # Sort firstly by line number and secondly by destination
    sortedByDestination = sorted(arr, key=lambda dep: dep["dest"])
    sortedByLine = sorted(sortedByDestination, key=lambda dep: prioritise(dep["line"]))
    return sortedByLine

def prioritise(value):
    if value == "🚋":
        return "0"

    # 65 should become before 184 -> sort by 065 and 184 instead.
    return (3 - len(value)) * "0" + value

def prioTimes(t):
    if type(t) == int:
        return t
    if t == "Nu":
        return 0
    if "Ca " in t:
        return int(t.split("Ca ")[1])
    return 99999999


def getTrafficSituation(place):
    # Stops to check for each place
    placeStops = {
        "lgh":          [S.UlleviNorra, S.Svingeln, S.Chalmers, S.HjalmarBrantingsplatsen],
        "chalmers":     [S.Chalmers, S.UlleviNorra, S.Domkyrkan],
        "huset":        [S.NyaVarvetsTorg, S.NyaVarvsallén, S.Järntorget],
        "lindholmen":   [S.Lindholmen, S.Lindholmspiren, S.Svingeln, S.Stenpiren, S.Bjurslättstorget],
        "jt":           [S.Järntorget, S.Kungssten, S.NyaVarvetsTorg, S.NyaVarvsallén, S.Chalmers, S.UlleviNorra, S.HjalmarBrantingsplatsen],
        "centrum":      [S.Brunnsparken, S.Centralstationen, S.Nordstan],
        "domkyrkan":    [S.Brunnsparken, S.Domkyrkan, S.Chalmers, S.HjalmarBrantingsplatsen, S.Bjurslättstorget],
        "brunnsparken": [S.Brunnsparken, S.Domkyrkan, S.Chalmers, S.HjalmarBrantingsplatsen, S.Bjurslättstorget],
        "bjurslatt":    [S.Brunnsparken, S.Domkyrkan, S.Chalmers, S.HjalmarBrantingsplatsen, S.Bjurslättstorget],
        "hjalmar":      [S.Brunnsparken, S.Domkyrkan, S.Chalmers, S.HjalmarBrantingsplatsen, S.Bjurslättstorget, S.Svingeln]
    }

    traffic = [ts.stoparea(stop.value) for stop in placeStops[place]]
    arr = [x for xs in traffic for x in xs] # Flatten list
    
    with open("ts.json", "w") as f:
        f.write(json.dumps(traffic))

    outarr = []
    for situation in arr:
        # Get the start time and current time
        timeformat = "%Y-%m-%dT%H%M%S%z" # Format from västtrafik
        time = situation.get("startTime").replace(":", "")
        time = datetime.strptime(time, timeformat)
        now = datetime.now(tz.UTC)
        # Add it to the output array only if the disruption has started
        if time <= now:
            relevant = {
                "title": situation.get("title"), 
                "description": situation.get("description")
            }
            # Skip duplicates
            if relevant not in outarr:
                outarr.append(relevant)

    return outarr
