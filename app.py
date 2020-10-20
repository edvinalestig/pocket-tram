from flask import Flask, request, send_file
from vasttrafik import Auth, Reseplaneraren, TrafficSituations
import json
import dateutil.tz as tz
from datetime import datetime, timedelta

app = Flask(__name__)

with open("credentials.txt", "r") as f:
    creds = f.readlines()

auth = Auth(creds[0].strip(), creds[1].strip(), "app")
rp = Reseplaneraren(auth)
ts = TrafficSituations(auth)

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
    "kungsstenvl": 9021014004101000
}

@app.route("/")
def index():
    return send_file("static/index.html")

@app.route("/request")
def req():
    place = request.args.get("place")

    if place == "lgh":
        deps = getDepartures([
            compileDict("lgh", "chalmers", countdown=False, first=True, dest="Chalmers"),
            compileDict("svingeln", "lindholmen", first=True, dest="Lindholmen")
        ])

        return json.dumps({
            "Ullevi Norra": deps[0],
            "Svingeln": deps[1]
        })

    elif place == "huset":
        deps = getDepartures([
            compileDict("huset1", "kungssten", countdown=False),
            compileDict("huset2", "kungssten", countdown=False),
            compileDict("kungsstenvl", "lindholmen", countdown=False)
        ])

        return json.dumps({
            "Rengatan": deps[0], 
            "Nya Varvsallén": deps[1],
            "Kungssten": deps[2]
        })
    
    elif place == "markland":
        deps = getDepartures([
            compileDict("markland", "kungssten"),
            compileDict("markland", "mariaplan"),
            compileDict("mariaplan", "kungssten", offset=5)
        ])

        return json.dumps({
            "Till Kungssten": deps[0],
            "Till Mariaplan (restid 6 min)": deps[1],
            "Från Mariaplan": deps[2]
        })

    elif place == "jt":
        deps = getDepartures([
            compileDict("jt", "chalmers"),
            compileDict("jt", "vasaplatsen"),
            compileDict("jt", "kberget"),
            compileDict("jt", "lgh")
        ])

        return json.dumps({
            "Mot Chalmers": deps[0],
            "Mot Vasaplatsen": deps[1],
            "Mot Huset": deps[2],
            "Mot Lägenheten": deps[3]
        })

    elif place == "chalmers":
        deps = getDepartures([
            compileDict("chalmers", "lgh", first=True, dest="Ullevi Norra"),
            compileDict("chalmers", "jt"),
            compileDict("jt", "kberget", offset=9),
            compileDict("chalmers", "markland", first=True, dest="Marklandsgatan"),
            compileDict("markland", "kungssten", offset=9)
        ])

        return json.dumps({
            "Mot Ullevi Norra": deps[0],
            "Mot Järntorget (restid 10 min)": deps[1],
            "Från Järntorget": deps[2],
            "Mot Marklandsgatan (restid 10 min)": deps[3],
            "Från Marklandsgatan": deps[4]
        })

    elif place == "lindholmen":
        deps = getDepartures([
            compileDict("lindholmen", "svingeln", first=True, dest="Svingeln"),
            compileDict("lindholmen", "kungssten"),
            compileDict("lpiren", "stenpiren")
        ])

        return json.dumps({
            "Mot Svingeln": deps[0],
            "Mot Kungssten": deps[1],
            "Båt": deps[2]
        })

    elif place == "kungssten":
        deps = getDepartures([
            compileDict("kungssten", "kberget"),
            compileDict("kungssten", "markland"),
            compileDict("kungsstenvl", "lindholmen")
        ])

        return json.dumps({
            "Mot Huset": deps[0],
            "Mot Marklandsgatan": deps[1],
            "Mot Lindholmen": deps[2]
        })

    return json.dumps({
        "test":"test2"
    })

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
        return []
    
    if type(deps) != list:
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
        if countdown:
            time = ctdown
        else:
            time = dep.get("time") + getDelay(dep)
        i = 0
        while i < len(outArr):
            if outArr[i].get("line") == line and outArr[i].get("dest") == dest:
                outArr[i]["time"].append(time)
                break
            i += 1
        else:
            vitals = {
                "line": line,
                "dest": dest,
                "time": [time],
                "fgColor": dep.get("fgColor"),
                "bgColor": dep.get("bgColor")
            }
            outArr.append(vitals)
        
        if (type(ctdown) == int) or ("Ca" not in ctdown):
            firstDeps["time"].append(ctdown)

    if first:
        #Get only the first three
        sort = sortDepartures([firstDeps])[0]
        sort["time"] = sort["time"][:3]
        outArr.append(sort)

    return sortDepartures(outArr)

def cut(s):
    return s.split(" via ")[0]

def getDelay(dep):
    if dep.get("cancelled"):
        return " X"

    # Check if real time info is available
    tttime = dep.get("time")
    rttime = dep.get("rtTime")
    if rttime == None:
        return ""

    # Convert it all to minutes
    rtminutes = timeToMinutes(rttime)
    ttminutes = timeToMinutes(tttime)

    # Time difference:
    delay = rtminutes - ttminutes

    if delay < -1300:
        # Past midnight, 24 hours = 1440 min
        delay += 1440
    elif delay > 1300:
        delay -= 1440

    if delay >= 0:
        return f"+{delay}"
    else:
        return str(delay)

def calculateCountdown(departure):
    if departure.get("cancelled"):
        return "X"

    # Check if real time info is available
    dTime = departure.get("rtTime")
    if dTime == None:
        realtime = False
        dTime = departure.get("time")
    else:
        realtime = True

    # Convert it all to minutes
    hour, minutes = dTime.split(":")
    minutes = int(minutes)
    minutes += int(hour) * 60

    # Now:
    timeNow = datetime.now(tz.gettz("Europe/Stockholm"))
    minutesNow = int(timeNow.strftime("%M")) + int(timeNow.strftime("%H")) * 60

    # Time left:
    countdown = minutes - minutesNow

    if countdown < -1300:
        # Past midnight, 24 hours = 1440 min
        countdown += 1440
    elif countdown > 1300:
        countdown -= 1440

    if realtime:
        if countdown <= 0:
            return "Nu"
        else:
            return countdown
    else:
        return f'Ca {countdown}'

def timeToMinutes(t):
    hour, minutes = t.split(":")
    minutes = int(minutes)
    minutes += int(hour) * 60
    return minutes

def sortDepartures(arr):
    # Get the departures in the correct order in case the one behind is actually in front
    for i, dep in enumerate(arr):
        try:
            arr[i]["time"].sort()
        except TypeError:
            # One departure was a string and it doesn't like mixing strings and numbers
            pass
    # Sort firstly by line number and secondly by destination
    sortedByDestination = sorted(arr, key=lambda dep: dep["dest"])
    sortedByLine = sorted(sortedByDestination, key=lambda dep: tryConvert(dep["line"]))
    return sortedByLine

def tryConvert(value):
    try:
        return int(value)
    except ValueError:
        if value == "🚋":
            return 0
        else:
            new = [str(ord(i)) for i in value]
            return int("".join(new))