from flask import Flask, request, send_file
from jinja2 import Environment, FileSystemLoader
from vasttrafik import Auth, PR4, TrafficSituations
import json
import dateutil.tz as tz
from datetime import datetime, timedelta
import math
from os import environ

from bridge.bridge import Bridge
from bridge.bridgeModels import *
from PTClasses import Stop, StopReq, Departure
from models.PR4.DeparturesAndArrivals import DepartureAPIModel, GetDeparturesResponse
from models.PR4.Positions import JourneyPositionList
from models.TrafficSituations.TrafficSituations import TrafficSituation
from utilityPages import UtilityPages

app = Flask(__name__)

auth = Auth(environ["VTClient"], environ["VTSecret"], "app2")
pr4 = PR4(auth)
ts = TrafficSituations(auth)
utilPages = UtilityPages(pr4)

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
    return pr4.locations_by_text(stop).model_dump_json()

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
    return JourneyPositionList(utilPages.position(request.args)).model_dump_json()

@app.route("/request")
def req():
    place: str = request.args.get("place", "")
    timeNow: str = datetime.now(tz.gettz("Europe/Stockholm")).strftime("%H:%M:%S")
    deps = mapStops(place)

    return json.dumps({
                "stops": {sr.title: [d.model_dump() for d in dep] for (sr,dep) in deps},
                "ts": getTrafficSituation(place),
                "time": timeNow
            })

@app.route("/bridge")
def bridge():
    bridge = Bridge()
    car: StatusEnum = bridge.roadSignals().status
    gc: StatusEnum = bridge.sharedPathwaySignals().status
    boat: StatusEnum = bridge.riverSignals().status
    message: MessageModel = bridge.bridgeMessages()

    now: datetime = datetime.now(tz.UTC)
    openings: list[HistorySignalsModel] = bridge.historySignals(
        fromDate=(now - timedelta(days=1)).strftime("%Y-%m-%d"),
        toDate=(now + timedelta(days=1)).strftime("%Y-%m-%d"),
        audienceName=AudienceEnum.GC
    )
    openings.sort(reverse=True, key=lambda x: x.Timestamp)
    
    lastChange: str = openings[0].Timestamp.astimezone(tz.gettz("Europe/Stockholm")).strftime("%H:%M")
    penultimateChange: str = openings[1].Timestamp.astimezone(tz.gettz("Europe/Stockholm")).strftime("%d %b %Y kl. %H:%M")

    lastOpening: str
    if gc == StatusEnum.Closed:
        lastOpening = f"Nu (sedan {lastChange})"
    else:
        lastOpening = f"{penultimateChange} - {lastChange}"

    # Generate html using jinja2
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("bridge.html.j2")

    return template.render(
        car = car.value,
        gc = gc.value,
        boat = boat.value,
        message = "-" if message.message == "" else f'{message.message} (utfärdat {message.timeStamp.strftime("%d %b %Y kl. %H:%M")})',
        lastOpening = lastOpening
    )

def mapStops(place: str) -> list[tuple[StopReq,list[Departure]]]:
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
                compileStopReq("Mot Bjurslätts torg", Stop.Domkyrkan, Stop.BjurslättsTorg),
                compileStopReq("Mot Kapellplatsen", Stop.Domkyrkan, Stop.Kapellplatsen)
            ])

        case "bjurslatt":
            return getDepartures([
                compileStopReq("Mot Hjalmar Brantingsplatsen", Stop.BjurslättsTorg, Stop.HjalmarBrantingsplatsen, compileFirst=True, dest="Hjalmar Brantingspl.", excludeLines=["31"]),
                compileStopReq("Mot Lindholmen", Stop.BjurslättsTorg, Stop.Lindholmen)
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
                compileStopReq("Mot Bjurslätts torg", Stop.Lindholmen, Stop.BjurslättsTorg),
                compileStopReq("Mot Svingeln", Stop.Lindholmen, Stop.Svingeln, compileFirst=True),
                compileStopReq("Båt", Stop.Lindholmspiren, Stop.Stenpiren),
            ])
        
        case "brunnsparken":
            return getDepartures([
                compileStopReq("Mot Chalmers", Stop.Brunnsparken, Stop.Chalmers, excludeLines=["6"]),
                compileStopReq("Mot Bjurslätts torg", Stop.Brunnsparken, Stop.BjurslättsTorg),
                compileStopReq("Mot Hjalmar Brantingsplatsen", Stop.Brunnsparken, Stop.HjalmarBrantingsplatsen, compileFirst=True, dest="Hjalmar Brantingspl.")
            ])
        
        case "wieselgrensplatsen":
            return getDepartures([
                compileStopReq("Mot Bjurslätts torg", Stop.Wieselgrensplatsen, Stop.BjurslättsTorg, compileFirst=True),
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
    return StopReq(title=title, showCountdown=showCountdown, compileFirst=compileFirst, dest=dest or to.name, excludeLines=excludeLines, excludeDestinations=excludeDestinations, stop=fr, direction=to, startDateTime=timeNow) 

# Takes a list of compiled dicts and returns a list of cleaned results
def getDepartures(reqList: list[StopReq]) -> list[tuple[StopReq,list[Departure]]]:
    responses = pr4.asyncDepartureBoards(reqList)
    return [clean(*resp) for resp in responses]

def clean(sr: StopReq, resp: GetDeparturesResponse) -> tuple[StopReq, list[Departure]]:
    deps: list[DepartureAPIModel] = resp.results

    if deps == None or deps == []:
        # No departures found
        return (sr, [])

    firstDeps = Departure(
        line="🚋",
        dest=sr.dest,
        time=[],
        fgColor="blue",
        bgColor="white"
    )

    outArr: list[Departure] = []
    for dep in deps:
        line: str = dep.serviceJourney.line.shortName or "?"
        if line in sr.excludeLines: continue

        dest: str = (dep.serviceJourney.directionDetails.shortDirection).replace("Brantingsplatsen", "Brantingspl.") # type: ignore
        if dest in sr.excludeDestinations: continue

        ctdown: str | int = calculateCountdown(dep)

        # If the time left or the time+delay should be shown
        time: str | int
        if sr.showCountdown:
            time = ctdown
        else:
            time = dep.plannedTime.strftime("%H:%M") + getDelay(dep)

        i = 0
        while i < len(outArr):
            # Check if that line & destination is already present.
            # Put all departures in one list
            if outArr[i].line == line and outArr[i].dest == dest:
                outArr[i].time.append(time)
                break
            i += 1
        else:
            # The line & destination is not in the list
            outArr.append(Departure(
                line=line,
                dest=dest,
                time=[time],
                bgColor=dep.serviceJourney.line.backgroundColor or "blue",
                fgColor=dep.serviceJourney.line.foregroundColor or "white"
            ))
        
        if (type(ctdown) == int) or (ctdown == "Nu"):
            # Add countdowns to a list of all departures toward a stop if 
            # they aren't cancelled or not having realtime info.
            firstDeps.time.append(ctdown)

    if sr.compileFirst:
        # All departures toward a stop
        # Get only the first three after sorting
        if len(firstDeps.time) > 0:
            sort: Departure = sortDepartures([firstDeps])[0]
            sort.time = sort.time[:3]
            outArr.append(sort)

    return (sr, sortDepartures(outArr))

def getDelay(dep: DepartureAPIModel) -> str:
    if dep.isCancelled:
        return " X"

    # Check if real time info is available
    if dep.estimatedTime is None:
        return ""

    delta: timedelta = dep.estimatedTime - dep.plannedTime

    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    delay: int = delta.days * 1440 + math.floor(delta.seconds/60)

    if delay >= 0:
        return f"+{delay}"
    else:
        return str(delay)

def calculateCountdown(departure: DepartureAPIModel) -> str | int:
    if departure.isCancelled:
        return "❌"

    depTime: datetime = departure.estimatedOtherwisePlannedTime
    realtime: bool = departure.estimatedTime is not None
    timeNow: datetime = datetime.now(tz.gettz("Europe/Stockholm"))

    # Time left:
    delta: timedelta = depTime - timeNow
    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    countdown: int = delta.days * 1440 + math.ceil(delta.seconds/60)

    if realtime:
        if countdown <= 0:
            return "Nu"
        else:
            return countdown
    else:
        return f'Ca {countdown}'

def sortDepartures(departures: list[Departure]) -> list[Departure]:
    # Get the departures in the correct order in case the one behind is actually in front
    for i, dep in enumerate(departures):
        # Do not sort the list if there are strings in it (except 'Nu'), they  
        # might be "00:12+1" and "23:56-2" which would then be swapped.
        skip = False
        for t in dep.time:
            if type(t) == str and t != "Nu":
                skip = True
                break
        if skip: 
            continue

        try:
            departures[i].time = sorted(dep.time, key=lambda t: prioTimes(t))
        except TypeError:
            # One departure was a string and it doesn't like mixing strings and numbers
            pass

    # Sort firstly by line number and secondly by destination
    sortedByDestination: list[Departure] = sorted(departures, key=lambda dep: dep.dest)
    sortedByLine: list[Departure] = sorted(sortedByDestination, key=lambda dep: prioritise(dep.line))
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
    defaultStops: list[Stop] = [Stop.Brunnsparken, Stop.Domkyrkan, Stop.Chalmers, Stop.HjalmarBrantingsplatsen, Stop.BjurslättsTorg]
    placeStops: dict[str, list[Stop]] = {
        "lgh":          [Stop.UlleviNorra, Stop.Svingeln, Stop.Chalmers, Stop.HjalmarBrantingsplatsen],
        "chalmers":     [Stop.Chalmers, Stop.UlleviNorra, Stop.Domkyrkan],
        "huset":        [Stop.NyaVarvetsTorg, Stop.NyaVarvsallén, Stop.Järntorget],
        "lindholmen":   [Stop.Lindholmen, Stop.Lindholmspiren, Stop.Svingeln, Stop.Stenpiren, Stop.BjurslättsTorg],
        "jt":           [Stop.Järntorget, Stop.Kungssten, Stop.NyaVarvetsTorg, Stop.NyaVarvsallén, Stop.Chalmers, Stop.UlleviNorra, Stop.HjalmarBrantingsplatsen],
        "hjalmar":      defaultStops + [Stop.Svingeln]
    }

    traffic: list[list[TrafficSituation]] = [ts.stoparea(stop.value) for stop in placeStops.get(place, defaultStops)]
    arr: list[TrafficSituation] = [x for xs in traffic for x in xs] # Flatten list

    outarr: list[dict[str,str]] = []
    for situation in arr:
        now: datetime = datetime.now(tz.UTC)
        # Add it to the output array only if the disruption has started
        if situation.startTime <= now:
            relevant: dict[str, str] = {
                "title": situation.title, 
                "description": situation.description
            }
            # Skip duplicates
            if relevant not in outarr:
                outarr.append(relevant)

    return outarr
