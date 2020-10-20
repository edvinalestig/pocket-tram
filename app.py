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
        return json.dumps({
            "Ullevi Norra": getDeparture("lgh", "chalmers", countdown=False, first=True, dest="Chalmers"),
            "Svingeln": getDeparture("svingeln", "lindholmen", first=True, dest="Lindholmen")
        })

    elif place == "huset":
        return json.dumps({
            "Rengatan": getDeparture("huset1", "kungssten", countdown=False), 
            "Nya Varvsallén": getDeparture("huset2", "kungssten", countdown=False),
            "Kungssten": getDeparture("kungsstenvl", "lindholmen", countdown=False)
        })
    
    elif place == "markland":
        return json.dumps({
            "Till Kungssten": getDeparture("markland", "kungssten"),
            "Till Mariaplan (restid 6 min)": getDeparture("markland", "mariaplan"),
            "Från Mariaplan": getDeparture("mariaplan", "kungssten", offset=5)
        })

    elif place == "jt":
        return json.dumps({
            "Mot Chalmers": getDeparture("jt", "chalmers"),
            "Mot Vasaplatsen": getDeparture("jt", "vasaplatsen"),
            "Mot Huset": getDeparture("jt", "kberget"),
            "Mot Lägenheten": getDeparture("jt", "lgh")
        })

    elif place == "chalmers":
        return json.dumps({
            "Mot Ullevi Norra": getDeparture("chalmers", "lgh", first=True, dest="Ullevi Norra"),
            "Mot Järntorget (restid 10 min)": getDeparture("chalmers", "jt"),
            "Från Järntorget": getDeparture("jt", "kberget", offset=9),
            "Mot Marklandsgatan (restid 10 min)": getDeparture("chalmers", "markland", first=True, dest="Marklandsgatan"),
            "Från Marklandsgatan": getDeparture("markland", "kungssten", offset=9)
        })

    elif place == "lindholmen":
        return json.dumps({
            "Mot Svingeln": getDeparture("lindholmen", "svingeln", first=True, dest="Svingeln"),
            "Mot Kungssten": getDeparture("lindholmen", "kungssten"),
            "Båt": getDeparture("lpiren", "stenpiren")
        })

    elif place == "kungssten":
        return json.dumps({
            "Mot Huset": getDeparture("kungssten", "kberget"),
            "Mot Marklandsgatan": getDeparture("kungssten", "markland"),
            "Mot Lindholmen": getDeparture("kungsstenvl", "lindholmen")
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
    time_now = datetime.now(tz.gettz("Europe/Stockholm")) + timedelta(minutes=offset)
    date = time_now.strftime("%Y%m%d")
    time = time_now.strftime("%H:%M")
    return clean(rp.departureBoard(
        id=stopIDs[fr], date=date, timeSpan=60,
        time=time, maxDeparturesPerLine=3, 
        direction=stopIDs[to], needJourneyDetail=0), countdown, first, dest)

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
            time = dep.get("time")+getDelay(dep)
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
        sort = sort_departures([firstDeps])[0]
        sort["time"] = sort["time"][:3]
        outArr.append(sort)

    return sort_departures(outArr)

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
    d_time = departure.get("rtTime")
    if d_time == None:
        realtime = False
        d_time = departure.get("time")
    else:
        realtime = True

    # Convert it all to minutes
    hour, minutes = d_time.split(":")
    minutes = int(minutes)
    minutes += int(hour) * 60

    # Now:
    time_now = datetime.now(tz.gettz("Europe/Stockholm"))
    minutes_now = int(time_now.strftime("%M")) + int(time_now.strftime("%H")) * 60

    # Time left:
    countdown = minutes - minutes_now

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

def sort_departures(arr):
    # Get the departures in the correct order in case the one behind is actually in front
    for i, dep in enumerate(arr):
        try:
            arr[i]["time"].sort()
        except TypeError:
            # One departure was a string and it doesn't like mixing strings and numbers
            pass
    # Sort firstly by line number and secondly by destination
    sorted_by_destination = sorted(arr, key=lambda dep: dep["dest"])
    sorted_by_line = sorted(sorted_by_destination, key=lambda dep: tryConvert(dep["line"]))
    return sorted_by_line

def tryConvert(value):
    try:
        return int(value)
    except ValueError:
        if value == "🚋":
            return 0
        else:
            new = [str(ord(i)) for i in value]
            return int("".join(new))