from flask import Flask, request, send_file
from vasttrafik import Auth, Reseplaneraren, TrafficSituations
import json
import dateutil.tz as tz
from datetime import datetime, timedelta, timezone
import math
from os import environ

from utilityPages import UtilityPages

app = Flask(__name__)

auth = Auth(environ["VTClient"], environ["VTSecret"], "app")
rp = Reseplaneraren(auth)
ts = TrafficSituations(auth)
utilPages = UtilityPages(rp)

stopIDs = {
    "chalmers": 9021014001960000,
    "lgh": 9021014007171000,
    "markland": 9021014004760000,
    "huset1": 9021014005105000,
    "huset2": 9021014005100000,
    "jt": 9021014003640000,
    "mariaplan": 9021014004730000,
    "kungssten": 9021014004100000,
    "vasaplatsen": 9021014007300000,
    "kberget": 9021014004230000,
    "lindholmen": 9021014004490000,
    "lpiren": 9021014004493000,
    "svingeln": 9021014006480000,
    "stenpiren": 9021014006242000,
    "brunnsparken": 9021014001760000,
    "centralstn": 9021014001950000,
    "kapellplatsen": 9021014003760000,
    "tolvskilling": 9021014006790000,
    "korsvägen": 9021014003980000,
    "varbergsgatan": 9021014007270000,
    "valand": 9021014007220000,
    "regnbågsgatan": 9021014005465000,
    "nordstan": 9021014004945000,
    "frihamnen": 9021014002470000,
    "frihamnsporten": 9021014002472000,
    "vidblicksgatan": 9021014007400000,
    "ålandsgatan": 9021014007440000,
    "järnvågen": 9021014003645000,
    "bjurslättstorget": 9021014001475000,
    "hjalmar": 9021014003180000,
    "domkyrkan": 9021014002130000
}

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
            compileDict("lgh", "chalmers", countdown=False, first=True, dest="Chalmers"),
            compileDict("svingeln", "hjalmar", countdown=False, first=True, dest="Hjalmar", excludeLines=["6"]),
            compileDict("svingeln", "lindholmen", countdown=False, first=True, dest="Lindholmen"),
            compileDict("lgh", "centralstn")
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
            compileDict("huset1", "järnvågen", countdown=False),
            compileDict("huset2", "kungssten", countdown=False)
            # compileDict("kungssten", "lindholmen", countdown=False)
        ])

        return json.dumps({
            "stops": {
                "Nya Varvets Torg": deps[0],
                "Nya Varvsallén": deps[1]
                # "Kungssten": deps[2]
            },
            "ts": getTrafficSituation(place),
            # "comment": busPosition.getPosition(rp),
            "time": timeNow
        })

    elif place == "jt":
        deps = getDepartures([
            compileDict("jt", "chalmers"),
            compileDict("jt", "hjalmar"),
            compileDict("jt", "kberget"),
            compileDict("jt", "lgh", excludeLines=["6"])
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
            compileDict("domkyrkan", "bjurslättstorget"),
            compileDict("domkyrkan", "kapellplatsen")
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
            compileDict("bjurslättstorget", "hjalmar", first=True, dest="Hjalmar Brantingsplatsen", excludeLines=["31"]),
            compileDict("bjurslättstorget", "lindholmen")
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
            compileDict("hjalmar", "bjurslättstorget"),
            compileDict("hjalmar", "chalmers", excludeLines=["6"]),
            compileDict("hjalmar", "svingeln", first=True, dest="Svingeln")
        ])

        return json.dumps({
            "stops": {
                "Mot Bjurslätts torg": deps[0],
                "Mot Chalmers": deps[1],
                "Mot Svingeln": deps[2],
            },
            "ts": getTrafficSituation(place),
            "time": timeNow
        })

    elif place == "chalmers":
        deps = getDepartures([
            compileDict("chalmers", "domkyrkan", excludeLines=["6"]),
            compileDict("chalmers", "brunnsparken", first=True, dest="Brunnsparken", excludeLines=["6"]),
            compileDict("chalmers", "lgh", first=True, dest="Ullevi Norra"),
            compileDict("chalmers", "lindholmen")
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
            compileDict("lindholmen", "bjurslättstorget"),
            compileDict("lindholmen", "svingeln", first=True, dest="Svingeln"),
            compileDict("lpiren", "stenpiren"),
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

    # elif place == "kungssten":
    #     deps = getDepartures([
    #         compileDict("kungssten", "kberget"),
    #         compileDict("kungssten", "markland"),
    #         compileDict("kungssten", "lindholmen")
    #     ])

    #     return json.dumps({
    #         "stops": {
    #             "Mot Pappa": deps[0],
    #             "Mot Marklandsgatan": deps[1],
    #             "Mot Lindholmen": deps[2]
    #         },
    #         "ts": getTrafficSituation(place),
    #         "time": timeNow
    #     })
        
    elif place == "brunnsparken":
        deps = getDepartures([
            compileDict("brunnsparken", "chalmers", excludeLines=["6"]),
            compileDict("brunnsparken", "bjurslättstorget"),
            compileDict("brunnsparken", "hjalmar", first=True, dest="Hjalmar Brantingsplatsen")
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
        
    # elif place == "centrum":
    #     deps = getDepartures([
    #         compileDict("brunnsparken", "kapellplatsen"),
    #         compileDict("centralstn", "lgh", first=True, dest="Ullevi Norra"),
    #         compileDict("centralstn", "chalmers"),
    #         # compileDict("nordstan", "lindholmen", first=True, dest="Lindholmen"),
    #         compileDict("nordstan", "svingeln", first=True, dest="Svingeln")
    #     ])

    #     return json.dumps({
    #         "stops": {
    #             "Brunnsparken → Kapellplatsen": deps[0],
    #             "Centralen → Ullevi Norra": deps[1],
    #             "Centralen → Chalmers": deps[2],
    #             "Nordstan → Svingeln": deps[3]
    #             # "Nordstan → Lindholmen": deps[3]
    #         },
    #         "ts": getTrafficSituation("centrum"),
    #         "time": timeNow
    #     })

    # elif place == "vasaplatsen":
    #     deps = getDepartures([
    #         compileDict("vasaplatsen", "jt"),
    #         compileDict("jt", "kberget", offset=5),
    #         compileDict("vasaplatsen", "kapellplatsen", first=True, dest="Kapellplatsen"),
    #         compileDict("vasaplatsen", "lgh")
    #     ])

    #     return json.dumps({
    #         "stops": {
    #             "Mot Järntorget (restid 6/10 min)": deps[0],
    #             "Från Järntorget": deps[1],
    #             "Mot Kapellplatsen": deps[2],
    #             "Mot Ullevi Norra": deps[3]
    #         },
    #         "ts": getTrafficSituation("vasaplatsen"),
    #         "time": timeNow
    #     })

    # elif place == "kapellplatsen":
    #     deps = getDepartures([
    #         compileDict("kapellplatsen", "lindholmen"),
    #         compileDict("kapellplatsen", "brunnsparken", first=True, dest="Brunnsparken"),
    #         compileDict("ålandsgatan", "stenpiren"),
    #         compileDict("stenpiren", "lpiren", offset=8)
    #     ])

    #     return json.dumps({
    #         "stops": {
    #             "Mot Lindholmen": deps[0],
    #             "Mot Brunnsparken": deps[1],
    #             "Ålandsg. → Stenpiren (10 min)": deps[2],
    #             "Stenpiren → Lindholmen": deps[3]
    #         },
    #         "ts": getTrafficSituation("kapellplatsen"),
    #         "time": timeNow
    #     })

    # elif place == "ica":
    #     deps = getDepartures([
    #         compileDict("korsvägen", "varbergsgatan"),
    #         compileDict("varbergsgatan", "korsvägen"),
    #         compileDict("korsvägen", "ålandsgatan"),
    #         compileDict("korsvägen", "chalmers"),
    #         compileDict("valand", "kapellplatsen")
    #     ])

    #     return json.dumps({
    #         "stops": {
    #             "Korsvägen → ICA": deps[0],
    #             "ICA (7 min Korsvägen, 10 min Valand)": deps[1],
    #             "Korsvägen → Ålandsgatan": deps[2],
    #             "Korsvägen → Chalmers": deps[3],
    #             "Valand → Kapellplatsen": deps[4]
    #         },
    #         "ts": getTrafficSituation("ica"),
    #         "time": timeNow
    #     })

    # elif place == "frihamnen":
    #     deps = getDepartures([
    #         compileDict("frihamnen", "brunnsparken"),
    #         compileDict("frihamnsporten", "lindholmen", first=True, dest="Lindholmen")
    #     ])

    #     return json.dumps({
    #         "stops": {
    #             "Frihamnen": deps[0],
    #             "Frihamnsporten": deps[1]
    #         },
    #         "ts": getTrafficSituation("frihamnen"),
    #         "time": timeNow
    #     })

    # elif place == "stenpiren":
    #     deps = getDepartures([
    #         compileDict("stenpiren", "svingeln"),
    #         compileDict("stenpiren", "lpiren"),
    #         compileDict("stenpiren", "kapellplatsen")
    #     ])

    #     return json.dumps({
    #         "stops": {
    #             "Mot Svingeln": deps[0],
    #             "Mot Lindholmen": deps[1],
    #             "Mot Kapellplatsen": deps[2]
    #         },
    #         "ts": getTrafficSituation("stenpiren"),
    #         "time": timeNow
    #     })

    # elif place == "korsvagen":
    #     deps = getDepartures([
    #         compileDict("korsvägen", "lgh", first=True, dest="Ullevi Norra"),
    #         compileDict("korsvägen", "chalmers", first=True, dest="Chalmers"),
    #         compileDict("korsvägen", "ålandsgatan"),
    #         compileDict("korsvägen", "varbergsgatan")
    #     ])

    #     return json.dumps({
    #         "stops": {
    #             "Mot Ullevi Norra": deps[0],
    #             "Mot Ålandsgatan": deps[2],
    #             "Mot Chalmers": deps[1],
    #             "Mot Varbergsgatan": deps[3]
    #         },
    #         "ts": getTrafficSituation("korsvägen"),
    #         "time": timeNow
    #     })


    return json.dumps({
        "test":"test2",
        "time": timeNow
    })

# fr: From
# to: To
# countdown: If time left (countdown) or the timetable time with offset should be displayed
# first: Show combined row of all departures toward a stop (first 3)
# dest: Destination showed for the combined row
# offset: Time offset to not show unnecessary departures

# Compiles a dict with all info for getDeparture() so it can be sent asynchronously
def compileDict(fr, to, countdown=True, first=False, dest=" ", offset=0, excludeLines=[]):
    timeNow = datetime.now(tz.gettz("Europe/Stockholm")) + timedelta(minutes=offset)
    # timeNow = datetime(year=2023, month=6, day=28, hour=8, minute=0) + timedelta(minutes=offset)
    return {
        "request": {
            "gid": stopIDs[fr],
            "params": {
                "maxDeparturesPerLineAndDirection": 3,
                "directionGid": stopIDs[to],
                "startDateTime": timeNow.astimezone(timezone.utc).isoformat(),
                "limit": 100
            }
        },
        "countdown": countdown,
        "first": first,
        "dest": dest,
        "exclude": excludeLines
    }

# Takes a list of compiled dicts and returns a list of cleaned results
# Does what getDeparture() does but with many at the same time
def getDepartures(reqList):
    reqs = [req["request"] for req in reqList]
    responses = rp.asyncDepartureBoards(reqs)
    returnList = []
    for i, resp in enumerate(responses):
        returnList.append(clean(resp, reqList[i]["countdown"], reqList[i]["first"], reqList[i]["dest"], reqList[i]["exclude"]))
    return returnList

# obj: Object received from VT API
# countdown, first, dest: same as getDeparture()
def clean(obj, countdown, first, dest, exclude):
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
        if line in exclude: continue

        dest = cut(sj.get("direction"))
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

# Filter unwanted stuff from destination strings
def cut(s):
    s = s.split(" via ")[0]
    s = s.split(", Fri resa")[0]
    s = s.split(", Påstigning fram")[0]
    return s

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
        "lgh": ["lgh", "svingeln", "chalmers", "hjalmar"],
        "chalmers": ["chalmers", "lgh", "domkyrkan"],
        "huset": ["huset2", "jt"],
        "lindholmen": ["lindholmen", "lpiren", "svingeln", "stenpiren", "bjurslättstorget"],
        # "markland": ["markland", "kungssten", "mariaplan", "chalmers"],
        # "kungssten": ["kungssten", "lindholmen", "jt", "markland"],
        "jt": ["jt", "kungssten", "huset2", "chalmers", "lgh", "hjalmar"],
        "centrum": ["brunnsparken", "centralstn", "nordstan"],
        "domkyrkan": ["brunnsparken", "domkyrkan", "chalmers", "hjalmar", "bjurslättstorget"],
        "brunnsparken": ["brunnsparken", "domkyrkan", "chalmers", "hjalmar", "bjurslättstorget"],
        "bjurslatt": ["brunnsparken", "domkyrkan", "chalmers", "hjalmar", "bjurslättstorget"],
        "hjalmar": ["brunnsparken", "domkyrkan", "chalmers", "hjalmar", "bjurslättstorget"],
        # "vasaplatsen": ["vasaplatsen", "chalmers", "jt"],
        # "kapellplatsen": ["kapellplatsen", "vasaplatsen", "lindholmen"],
        # "ica": ["kapellplatsen", "chalmers", "valand", "korsvägen", "varbergsgatan"],
        # "regnbågsgatan": ["regnbågsgatan", "brunnsparken", "kapellplatsen"],
        # "frihamnen": ["frihamnen", "frihamnsporten"],
        # "stenpiren": ["stenpiren", "lpiren", "kapellplatsen"],
        # "korsvägen": ["korsvägen", "chalmers", "ålandsgatan", "varbergsgatan"]
    }

    traffic = [ts.stoparea(stopIDs[stop]) for stop in placeStops[place]]
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
