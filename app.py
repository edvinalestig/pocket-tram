from flask import Flask, request, send_file
from jinja2 import Environment, FileSystemLoader
from vasttrafik import Auth, Reseplaneraren, TrafficSituations
import json
import dateutil.tz as tz
from dateutil.parser import isoparse
from datetime import datetime, timedelta
import math
from os import environ

from bridge import Bridge, AudienceEnum
from PTClasses import Stop, StopReq
from utilityPages import UtilityPages

app = Flask(__name__)

auth = Auth(environ["VTClient"], environ["VTSecret"], "app")
rp = Reseplaneraren(auth)
ts = TrafficSituations(auth)
utilPages = UtilityPages(rp)

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
    if (stop := request.args.get("stop")) is None:
        return "Add ?stop=xxx to the url"
    return json.dumps(rp.locations_by_text(stop))

@app.route("/utilities")
def utilities():
    return utilPages.mainPage()

@app.route("/findDepartures")
def findDepartures():
    if request.args.get("moreInfo") == "on":
        return utilPages.searchStop(request.args)
    else:
        return utilPages.stopDepartures(request.args)

@app.route("/findArrivals")
def findArrivals():
    return utilPages.simpleStopArrivals(request.args)

@app.route("/depInfo")
def depInfo():
    return utilPages.depInfo(request.args)

@app.route("/simpleDepInfo")
def simpleDepInfo():
    return utilPages.simpleDepInfo(request.args)

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
    place = request.args.get("place", "")
    timeNow = datetime.now(tz.gettz("Europe/Stockholm")).strftime("%H:%M:%S")
    deps = mapStops(place)

    return json.dumps({
                "stops": {sr.title: dep for (sr,dep) in deps},
                "ts": getTrafficSituation(place),
                "time": timeNow
            })

@app.route("/bridge")
def bridge():
    bridge = Bridge()
    car: str = bridge.roadSignals()
    gc: str = bridge.sharedPathwaySignals()
    boat: str = bridge.riverSignals()
    message: str = bridge.bridgeMessages().get("message", "")

    now = datetime.now(tz.UTC)
    openings = bridge.historySignals(
        fromDate=(now - timedelta(days=1)).strftime("%Y-%m-%d"),
        toDate=(now + timedelta(days=1)).strftime("%Y-%m-%d"),
        audienceName=AudienceEnum.Car
    )
    lastOpeningISO: str = max(openings, key=lambda x: x.get("Timestamp", "")).get("Timestamp", "-")
    lastOpeningDT: datetime = isoparse(lastOpeningISO)
    lastOpening: str = lastOpeningDT.astimezone(tz.gettz("Europe/Stockholm")).strftime("%d %b %Y kl. %H:%M")

    # Generate html using jinja2
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("bridge.html.j2")

    return template.render(
        car = car,
        gc = gc,
        boat = boat,
        message = message,
        lastOpening = lastOpening
    )

@app.route("/bridge2")
def bridge2():
    bridge = Bridge()
    return bridge.historySignals("2025-08-24", "2025-08-26", AudienceEnum.Car)


def mapStops(place: str) -> list[tuple[StopReq,list]]:
    match place:
        case "lgh":
            return getDepartures([
                compileStopReq("Mot Chalmers", Stop.UlleviNorra, Stop.Chalmers, showCountdown=False, compileFirst=True),
                compileStopReq("Mot Hjalmar Brantingsplatsen", Stop.Svingeln, Stop.HjalmarBrantingsplatsen, showCountdown=False, compileFirst=True, dest="Hjalmar Brantingspl.", excludeLines=["6"]),
                compileStopReq("Mot Lindholmen", Stop.Svingeln, Stop.Lindholmen, showCountdown=False, compileFirst=True),
                compileStopReq("Mot Centralstationen", Stop.UlleviNorra, Stop.Centralstationen)
            ])

        case "huset":
            return getDepartures([
                compileStopReq("Nya Varvets Torg", Stop.NyaVarvetsTorg, Stop.Järnvågen, showCountdown=False),
                compileStopReq("Nya Varvsallén", Stop.NyaVarvsallén, Stop.Kungssten, showCountdown=False)
            ])

        case "jt":
            return getDepartures([
                compileStopReq("Mot Chalmers", Stop.Järntorget, Stop.Chalmers),
                compileStopReq("Mot Hjalmar Brantingsplatsen", Stop.Järntorget, Stop.HjalmarBrantingsplatsen),
                compileStopReq("Mot Pappa", Stop.Järntorget, Stop.Käringberget),
                compileStopReq("Mot Mamma", Stop.Järntorget, Stop.UlleviNorra, excludeLines=["6"])
            ])

        case "domkyrkan":
            return getDepartures([
                compileStopReq("Mot Bjurslätts torg", Stop.Domkyrkan, Stop.Bjurslättstorget),
                compileStopReq("Mot Kapellplatsen", Stop.Domkyrkan, Stop.Kapellplatsen)
            ])

        case "bjurslatt":
            return getDepartures([
                compileStopReq("Mot Hjalmar Brantingsplatsen", Stop.Bjurslättstorget, Stop.HjalmarBrantingsplatsen, compileFirst=True, dest="Hjalmar Brantingspl.", excludeLines=["31"], excludeDestinations=["Kippholmen"]),
                compileStopReq("Mot Lindholmen", Stop.Bjurslättstorget, Stop.Lindholmen)
            ])

        case "hjalmar":
            return getDepartures([
                compileStopReq("Mot Wieselgrensgatan", Stop.HjalmarBrantingsplatsen, Stop.Wieselgrensgatan, compileFirst=True, excludeLines=["31"]),
                compileStopReq("Mot Chalmers", Stop.HjalmarBrantingsplatsen, Stop.Chalmers, excludeLines=["6"]),
                compileStopReq("Mot Brunnsparken", Stop.HjalmarBrantingsplatsen, Stop.Brunnsparken, compileFirst=True),
                compileStopReq("Mot Svingeln", Stop.HjalmarBrantingsplatsen, Stop.Svingeln, compileFirst=True, excludeLines=["6"])
            ])

        case "chalmers":
            return getDepartures([
                compileStopReq("Mot Domkyrkan", Stop.Chalmers, Stop.Domkyrkan, excludeLines=["6"]),
                compileStopReq("Mot Brunnsparken", Stop.Chalmers, Stop.Brunnsparken, compileFirst=True, dest="Brunnsparken", excludeLines=["6"]),
                compileStopReq("Mot Hjalmar Brantingsplatsen", Stop.Chalmers, Stop.HjalmarBrantingsplatsen, excludeLines=["6"]),
                compileStopReq("Mot Ullevi Norra", Stop.Chalmers, Stop.UlleviNorra, compileFirst=True, dest="Ullevi Norra")
            ])

        case "lindholmen":
            return getDepartures([
                compileStopReq("Mot Bjurslätts torg", Stop.Lindholmen, Stop.Bjurslättstorget),
                compileStopReq("Mot Svingeln", Stop.Lindholmen, Stop.Svingeln, compileFirst=True),
                compileStopReq("Båt", Stop.Lindholmspiren, Stop.Stenpiren),
            ])
        
        case "brunnsparken":
            return getDepartures([
                compileStopReq("Mot Chalmers", Stop.Brunnsparken, Stop.Chalmers, excludeLines=["6"]),
                compileStopReq("Mot Bjurslätts torg", Stop.Brunnsparken, Stop.Bjurslättstorget),
                compileStopReq("Mot Hjalmar Brantingsplatsen", Stop.Brunnsparken, Stop.HjalmarBrantingsplatsen, compileFirst=True, dest="Hjalmar Brantingspl.")
            ])
        
        case "wieselgrensplatsen":
            return getDepartures([
                compileStopReq("Mot Bjurslätts torg", Stop.Wieselgrensplatsen, Stop.Bjurslättstorget, compileFirst=True),
                compileStopReq("Mot Wieselgrensgatan", Stop.Wieselgrensplatsen, Stop.Wieselgrensgatan, excludeLines=["25","31"]),
                compileStopReq("Mot Brunnsparken", Stop.Wieselgrensplatsen, Stop.Brunnsparken, compileFirst=True)
            ])
        
        case _:
            return []
            

def compileStopReq(title: str,
                   fr: Stop,
                   to: Stop,
                   showCountdown: bool = True,
                   compileFirst: bool = False, 
                   dest: str | None = None, 
                   offset: int = 0, 
                   excludeLines: list[str] = [], 
                   excludeDestinations: list[str] = []
                   ) -> StopReq:
    timeNow = datetime.now(tz.gettz("Europe/Stockholm")) + timedelta(minutes=offset)
    return StopReq(title, showCountdown, compileFirst, dest or to.name, excludeLines, excludeDestinations, fr, to, timeNow) 

# Takes a list of compiled dicts and returns a list of cleaned results
def getDepartures(reqList: list[StopReq]) -> list[tuple[StopReq,list]]:
    responses = rp.asyncDepartureBoards(reqList)
    return [clean(*resp) for resp in responses]

# obj: Object received from VT API
def clean(sr: StopReq, obj: dict) -> tuple[StopReq, list]:
    deps = obj.get("results")

    if deps == None:
        # No departures found
        return (sr, [])

    firstDeps = {
        "line": "🚋",
        "dest": sr.dest,
        "time": [],
        "fgColor": "blue",
        "bgColor": "white"
    }

    outArr = []
    for dep in deps:
        sj = dep.get("serviceJourney")
        line = sj.get("line").get("shortName")
        if line in sr.excludeLines: continue

        dest = sj.get("directionDetails").get("shortDirection").replace("Brantingsplatsen", "Brantingspl.")
        if dest in sr.excludeDestinations: continue

        ctdown = calculateCountdown(dep)

        # If the time left or the time+delay should be shown
        if sr.showCountdown:
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

    if sr.compileFirst:
        # All departures toward a stop
        # Get only the first three after sorting
        if len(firstDeps["time"]) > 0:
            sort = sortDepartures([firstDeps])[0]
            sort["time"] = sort["time"][:3]
            outArr.append(sort)

    return (sr, sortDepartures(outArr))

def getDelay(dep: dict) -> str:
    if dep.get("isCancelled"):
        return " X"

    # Check if real time info is available
    tttime = dep.get("plannedTime", "")
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

def calculateCountdown(departure: dict) -> str | int:
    if departure.get("isCancelled"):
        return "❌"

    # Check if real time info is available
    dTime = departure.get("estimatedTime")
    if dTime == None:
        realtime = False
        dTime = departure.get("plannedTime", "")
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
        for t in dep["time"]:
            if type(t) == str and t != "Nu":
                skip = True
                break
        if skip: 
            continue

        try:
            arr[i]["time"] = sorted(dep["time"], key=lambda t: prioTimes(t))
        except TypeError:
            # One departure was a string and it doesn't like mixing strings and numbers
            pass

    # Sort firstly by line number and secondly by destination
    sortedByDestination = sorted(arr, key=lambda dep: dep["dest"])
    sortedByLine = sorted(sortedByDestination, key=lambda dep: prioritise(dep["line"]))
    return sortedByLine

def prioritise(value: str) -> str:
    if value == "🚋":
        return "0"

    # 65 should become before 184 -> sort by 065 and 184 instead.
    return (3 - len(value)) * "0" + value

def prioTimes(t: int | str) -> int:
    if type(t) == int:
        return t
    if t == "Nu":
        return 0
    if "Ca " in t: # type: ignore
        return int(t.split("Ca ")[1]) # type: ignore
    return 99999999


def getTrafficSituation(place: str) -> list[dict[str, str]]:
    # Stops to check for each place
    defaultStops: list[Stop] = [Stop.Brunnsparken, Stop.Domkyrkan, Stop.Chalmers, Stop.HjalmarBrantingsplatsen, Stop.Bjurslättstorget]
    placeStops: dict[str, list[Stop]] = {
        "lgh":          [Stop.UlleviNorra, Stop.Svingeln, Stop.Chalmers, Stop.HjalmarBrantingsplatsen],
        "chalmers":     [Stop.Chalmers, Stop.UlleviNorra, Stop.Domkyrkan],
        "huset":        [Stop.NyaVarvetsTorg, Stop.NyaVarvsallén, Stop.Järntorget],
        "lindholmen":   [Stop.Lindholmen, Stop.Lindholmspiren, Stop.Svingeln, Stop.Stenpiren, Stop.Bjurslättstorget],
        "jt":           [Stop.Järntorget, Stop.Kungssten, Stop.NyaVarvetsTorg, Stop.NyaVarvsallén, Stop.Chalmers, Stop.UlleviNorra, Stop.HjalmarBrantingsplatsen],
        "hjalmar":      defaultStops + [Stop.Svingeln]
    }

    traffic = [ts.stoparea(stop.value) for stop in placeStops.get(place, defaultStops)]
    arr = [x for xs in traffic for x in xs] # Flatten list
    
    # with open("ts.json", "w") as f:
    #     f.write(json.dumps(traffic))

    outarr: list[dict[str,str]] = []
    for situation in arr:
        # Get the start time and current time
        timeformat = "%Y-%m-%dT%H%M%S%z" # Format from västtrafik
        timeStr: str = situation.get("startTime").replace(":", "")
        time: datetime = datetime.strptime(timeStr, timeformat)
        now: datetime = datetime.now(tz.UTC)
        # Add it to the output array only if the disruption has started
        if time <= now:
            relevant: dict[str, str] = {
                "title": situation.get("title"), 
                "description": situation.get("description")
            }
            # Skip duplicates
            if relevant not in outarr:
                outarr.append(relevant)

    return outarr
