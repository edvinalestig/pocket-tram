from flask import Flask, request, send_file
from vasttrafik import Auth, Reseplaneraren, TrafficSituations
import json
import dateutil.tz as tz
from datetime import datetime, timedelta
import math

from utilityPages import UtilityPages
import busPosition

app = Flask(__name__)

with open("credentials.txt", "r") as f:
    creds = f.readlines()

auth = Auth(creds[0].strip(), creds[1].strip(), "app")
rp = Reseplaneraren(auth)
ts = TrafficSituations(auth)
utilPages = UtilityPages(rp)

stopIDs = {
    "chalmers": 9021014001960000,
    "lgh": 9021014007171000,
    "markland": 9021014004760000,
    "huset1": 9021014005470000,
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
    "kungsstenvl": 9021014004101000,
    "brunnsparken": 9021014001760000,
    "centralstn": 9021014001950000,
    "kapellplatsen": 9021014003760000,
    "tolvskilling": 9022014006790000,
    "korsvägen": 9022014003980000,
    "varbergsgatan": 9022014007270000,
    "valand": 9022014007220000,
    "regnbågsgatan": 9022014005465000,
    "nordstan": 9022014004945000
}

@app.route("/")
def index():
    return send_file("static/index.html")

# "Hidden" page: displays response from VT when searching for a stop
# Usage: <url>/searchstop?stop=<name>
@app.route("/searchstop")
def seachStop():
    return json.dumps(rp.location_name(input=request.args.get("stop")))

@app.route("/utilities")
def utilities():
    return utilPages.mainPage()

@app.route("/findDepartures")
def findDepartures():
    if request.args.get("moreInfo") == "on":
        return utilPages.searchStop(request.args)
    else:
        return utilPages.simpleSearchStop(request.args)

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

@app.route("/request")
def req():
    place = request.args.get("place")

    if place == "lgh":
        deps = getDepartures([
            compileDict("lgh", "chalmers", countdown=False, first=True, dest="Chalmers"),
            compileDict("svingeln", "lindholmen", countdown=False, first=True, dest="Lindholmen"),
            compileDict("lgh", "centralstn")
        ])

        return json.dumps({
            "stops": {
                "Mot Chalmers": deps[0],
                "Mot Lindholmen": deps[1],
                "Mot Centralstationen": deps[2]
            },
            "ts": getTrafficSituation(place)
        })

    elif place == "huset":
        deps = getDepartures([
            compileDict("huset1", "kungssten", countdown=False),
            compileDict("huset2", "kungssten", countdown=False),
            compileDict("kungsstenvl", "lindholmen", countdown=False)
        ])

        return json.dumps({
            "stops": {
                "Rengatan": deps[0], 
                "Nya Varvsallén": deps[1],
                "Kungssten": deps[2]
            },
            "ts": getTrafficSituation(place),
            "comment": busPosition.getPosition(rp)
        })
    
    elif place == "markland":
        deps = getDepartures([
            compileDict("markland", "chalmers", first=True, dest="Chalmers"),
            compileDict("markland", "kungssten"),
            compileDict("markland", "mariaplan"),
            compileDict("mariaplan", "kungssten", offset=5),
            compileDict("markland", "tolvskilling")
        ])

        return json.dumps({
            "stops": {
                "Mot Chalmers": deps[0],
                "Mot Kungssten": deps[1],
                "Mot Mariaplan (restid 6 min)": deps[2],
                "Från Mariaplan": deps[3],
                "Mot Högsbohöjd": deps[4]
            },
            "ts": getTrafficSituation(place)
        })

    elif place == "jt":
        deps = getDepartures([
            compileDict("jt", "chalmers"),
            compileDict("jt", "vasaplatsen"),
            compileDict("jt", "kberget"),
            compileDict("jt", "lgh")
        ])

        return json.dumps({
            "stops": {
                "Mot Chalmers": deps[0],
                "Mot Vasaplatsen": deps[1],
                "Mot Pappa": deps[2],
                "Mot Mamma": deps[3]
            },
            "ts": getTrafficSituation(place)
        })

    elif place == "chalmers":
        deps = getDepartures([
            compileDict("chalmers", "lgh", first=True, dest="Ullevi Norra"),
            compileDict("chalmers", "jt"),
            compileDict("jt", "kberget", offset=9),
            compileDict("chalmers", "markland", first=True, dest="Marklandsgatan"),
            compileDict("markland", "kungssten", offset=9),
            compileDict("chalmers", "vasaplatsen", first=True, dest="Vasaplatsen"),
            compileDict("vasaplatsen", "jt", offset=4),
            compileDict("chalmers", "lindholmen")
        ])

        return json.dumps({
            "stops": {
                "Mot Lindholmen": deps[7],
                "Mot Ullevi Norra": deps[0],
                "Mot Järntorget (restid 10 min)": deps[1],
                "Från Järntorget": deps[2],
                "Mot Marklandsgatan (restid 10 min)": deps[3],
                "Från Marklandsgatan": deps[4],
                "Mot Vasaplatsen (restid 5 min)": deps[5],
                "Från Vasaplatsen": deps[6]
            },
            "ts": getTrafficSituation(place)
        })

    elif place == "lindholmen":
        deps = getDepartures([
            compileDict("lindholmen", "svingeln", first=True, dest="Svingeln"),
            compileDict("lindholmen", "kungssten"),
            compileDict("lpiren", "stenpiren"),
            compileDict("lindholmen", "kapellplatsen")
        ])

        return json.dumps({
            "stops": {
                "Mot Kapellplatsen": deps[3],
                "Mot Svingeln": deps[0],
                "Mot Kungssten": deps[1],
                "Båt": deps[2]
            },
            "ts": getTrafficSituation(place)
        })

    elif place == "kungssten":
        deps = getDepartures([
            compileDict("kungssten", "kberget"),
            compileDict("kungssten", "markland"),
            compileDict("kungsstenvl", "lindholmen")
        ])

        return json.dumps({
            "stops": {
                "Mot Pappa": deps[0],
                "Mot Marklandsgatan": deps[1],
                "Mot Lindholmen": deps[2]
            },
            "ts": getTrafficSituation(place)
        })
        
    elif place == "centrum":
        deps = getDepartures([
            compileDict("brunnsparken", "kapellplatsen"),
            # compileDict("brunnsparken", "lgh"),
            # compileDict("centralstn", "svingeln"),
            compileDict("centralstn", "chalmers"),
            compileDict("nordstan", "lindholmen", first=True, dest="Lindholmen")
        ])

        return json.dumps({
            "stops": {
                "Brunnsparken → Kapellplatsen": deps[0],
                # "Brunnsparken → Ullevi Norra": deps[1],
                # "Centralen → Svingeln": deps[2],
                "Centralen → Chalmers": deps[1],
                "Nordstan → Lindholmen": deps[2]
            },
            "ts": getTrafficSituation("centrum")
        })

    elif place == "vasaplatsen":
        deps = getDepartures([
            compileDict("vasaplatsen", "jt"),
            compileDict("jt", "kberget", offset=5),
            compileDict("vasaplatsen", "kapellplatsen", first=True, dest="Chalmers"),
            compileDict("vasaplatsen", "lgh")
        ])

        return json.dumps({
            "stops": {
                "Mot Järntorget (restid 6 min)": deps[0],
                "Från Järntorget": deps[1],
                "Mot Chalmers": deps[2],
                "Mot Ullevi Norra": deps[3]
            },
            "ts": getTrafficSituation("vasaplatsen")
        })

    elif place == "kapellplatsen":
        deps = getDepartures([
            compileDict("kapellplatsen", "lindholmen"),
            compileDict("kapellplatsen", "brunnsparken", first=True, dest="Brunnsparken")
        ])

        return json.dumps({
            "stops": {
                "Mot Lindholmen": deps[0],
                "Mot Brunnsparken": deps[1]
            },
            "ts": getTrafficSituation("kapellplatsen")
        })

    elif place == "ica":
        deps = getDepartures([
            compileDict("kapellplatsen", "valand"),
            compileDict("valand", "varbergsgatan"),
            compileDict("chalmers", "korsvägen"),
            compileDict("korsvägen", "varbergsgatan"),
            compileDict("varbergsgatan", "korsvägen"),
            compileDict("korsvägen", "chalmers"),
            compileDict("valand", "kapellplatsen")
        ])

        return json.dumps({
            "stops": {
                "Kapellplatsen → Valand (4 min)": deps[0],
                "Valand → ICA": deps[1],
                "Chalmers → Korsvägen (4 min)": deps[2],
                "Korsvägen → ICA": deps[3],
                "ICA (7 min Korsvägen, 10 min Valand)": deps[4],
                "Korsvägen → Chalmers": deps[5],
                "Valand → Kapellplatsen": deps[6]
            },
            "ts": getTrafficSituation("ica")
        })

    elif place == "regnbågsgatan":
        deps = getDepartures([
            compileDict("regnbågsgatan", "kapellplatsen"),
            compileDict("regnbågsgatan", "nordstan", first=True, dest="Nordstan"),
            compileDict("lpiren", "stenpiren")
        ])

        return json.dumps({
            "stops": {
                "Mot Kapellplatsen": deps[0],
                "Mot Nordstan": deps[1],
                "Båt": deps[2]
            },
            "ts": getTrafficSituation("regnbågsgatan")
        })


    return json.dumps({
        "test":"test2"
    })

@app.route("/test")
def test():
    return busPosition.getPosition(rp)

# fr: From
# to: To
# countdown: If time left (countdown) or the timetable time with offset should be displayed
# first: Show combined row of all departures toward a stop (first 3)
# dest: Destination showed for the combined row
# offset: Time offset to not show unnecessary departures
def getDeparture(fr, to, countdown=True, first=False, dest=" ", offset=0):
    timeNow = datetime.now(tz.gettz("Europe/Stockholm")) + timedelta(minutes=offset)
    date = timeNow.strftime("%Y%m%d")
    time = timeNow.strftime("%H:%M")
    return clean(rp.departureBoard(
        id=stopIDs[fr], date=date, timeSpan=60,
        time=time, maxDeparturesPerLine=3, 
        direction=stopIDs[to], needJourneyDetail=0), countdown, first, dest)

# Compiles a dict with all info for getDeparture() so it can be sent asynchronously
def compileDict(fr, to, countdown=True, first=False, dest=" ", offset=0):
    timeNow = datetime.now(tz.gettz("Europe/Stockholm")) + timedelta(minutes=offset)
    # timeNow = datetime(year=2020, month=12, day=16, hour=7, minute=0) + timedelta(minutes=offset)
    return {
        "request": {
            "id": stopIDs[fr],
            "date": timeNow.strftime("%Y%m%d"),
            "timeSpan": 60,
            "time": timeNow.strftime("%H:%M"),
            "maxDeparturesPerLine": 3,
            "direction": stopIDs[to],
            "needJourneyDetail": 0
        },
        "countdown": countdown,
        "first": first,
        "dest": dest
    }

# Takes a list of compiled dicts and returns a list of cleaned results
# Does what getDeparture() does but with many at the same time
def getDepartures(reqList):
    reqs = [req["request"] for req in reqList]
    responses = rp.asyncDepartureBoards(reqs)
    returnList = []
    for i, resp in enumerate(responses):
        returnList.append(clean(resp, reqList[i]["countdown"], reqList[i]["first"], reqList[i]["dest"]))
    return returnList

# obj: Object received from VT API
# countdown, first, dest: same as getDeparture()
def clean(obj, countdown, first, dest):
    deps = obj.get("DepartureBoard").get("Departure")

    if deps == None:
        # No departures found
        return []
    
    if type(deps) != list:
        # Only one departure, put it in a list so
        # the rest of the code doesn't break
        deps = [deps]

    firstDeps = {
        "line": "🚋",
        "dest": dest,
        "time": [],
        "fgColor": "white",
        "bgColor": "blue"
    }

    outArr = []
    for dep in deps:
        line = dep.get("sname")
        dest = cut(dep.get("direction"))
        ctdown = calculateCountdown(dep)

        # If the time left or the time+delay should be shown
        if countdown:
            time = ctdown
        else:
            time = dep.get("time") + getDelay(dep)

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
                "fgColor": dep.get("bgColor"),
                "bgColor": dep.get("fgColor")
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
    if dep.get("cancelled"):
        return " X"

    # Check if real time info is available
    tttime = dep.get("time")
    rttime = dep.get("rtTime")
    if rttime == None:
        return ""
    ttdate = dep.get("date")
    rtdate = dep.get("rtDate")

    ttdt = convertToDatetime(tttime, ttdate)
    rtdt = convertToDatetime(rttime, rtdate)
    delta = rtdt - ttdt

    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    delay = delta.days * 1440 + math.floor(delta.seconds/60)

    if delay >= 0:
        return f"+{delay}"
    else:
        return str(delay)

def calculateCountdown(departure):
    if departure.get("cancelled"):
        return "X"

    # Check if real time info is available
    dTime = departure.get("rtTime")
    dDate = departure.get("rtDate")
    if dTime == None:
        realtime = False
        dTime = departure.get("time")
        dDate = departure.get("date")
    else:
        realtime = True

    depTime = convertToDatetime(dTime, dDate)
    timeNow = datetime.now(tz.gettz("Europe/Stockholm"))

    # Time left:
    countdown = depTime - timeNow.replace(tzinfo=None)
    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    countdown = countdown.days * 1440 + math.ceil(countdown.seconds/60)


    if realtime:
        if countdown <= 0:
            return "Nu"
        else:
            return countdown
    else:
        return f'Ca {countdown}'

def convertToDatetime(time, date):
    t = time.split(":")
    d = date.split("-")
    return datetime(hour=int(t[0]), minute=int(t[1]), year=int(d[0]), month=int(d[1]), day=int(d[2]))

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
        "lgh": ["Ullevi Norra", "Svingeln", "Chalmers"],
        "chalmers": ["Chalmers", "Ullevi Norra", "Järntorget", "Marklandsgatan"],
        "huset": ["Rengatan", "Nya Varvsallén", "Nya Varvsallen", "Järntorget"],
        "lindholmen": ["Lindholmen", "Lindholmspiren", "Svingeln", "Stenpiren"],
        "markland": ["Marklandsgatan", "Kungssten", "Mariaplan", "Chalmers"],
        "kungssten": ["Kungssten", "Kungssten Västerleden", "Lindholmen", "Järntorget", "Marklandsgatan"],
        "jt": ["Järntorget", "Kungssten", "Rengatan", "Nya Varvsallén", "Chalmers", "Ullevi Norra"],
        "centrum": ["Brunnsparken", "Centralstationen", "Nordstan"],
        "vasaplatsen": ["Vasaplatsen", "Chalmers", "Järntorget"],
        "kapellplatsen": ["Kapellplatsen", "Vasaplatsen", "Lindholmen"],
        "ica": ["Kapellplatsen", "Chalmers", "Valand", "Korsvägen", "Varbergsgatan"],
        "regnbågsgatan": ["Regnbågsgatan", "Brunnsparken", "Kapellplatsen"]
    }

    names = placeStops.get(place)

    arr = []
    traffic = ts.trafficsituations()
    for situation in traffic:
        for stop in situation.get("affectedStopPoints"):
            name = stop.get("name")
            # Get only disruptions concerning the nearby stops
            if name in names:
                arr.append(situation)
                break

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
