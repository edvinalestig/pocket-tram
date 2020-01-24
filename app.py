from flask import Flask, request, send_file
from vasttrafik import Auth, Reseplaneraren, TrafficSituations
import json
from time import strftime

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
    "kberget": 9021014004230000
}

@app.route("/")
def index():
    return send_file("static/index.html")

@app.route("/request")
def req():
    place = request.args.get("place")

    if place == "lgh":
        return json.dumps({
            "Ullevi Norra": getDeparture("lgh", "chalmers")
        })

    elif place == "huset":
        return json.dumps({
            "Rengatan": getDeparture("huset1", "kungssten"), 
            "Nya Varvsallén": getDeparture("huset2", "kungssten")
        })
    
    elif place == "markland":
        return json.dumps({
            "Till Kungssten": getDeparture("markland", "kungssten"),
            "Till Mariaplan": getDeparture("markland", "mariaplan"),
            "Från Mariaplan": getDeparture("mariaplan", "kungssten")
        })

    elif place == "jt":
        return json.dumps({
            "Mot Chalmers": getDeparture("jt", "chalmers"),
            "Mot Vasaplatsen": getDeparture("jt", "vasaplatsen"),
            "Mot Huset": getDeparture("jt", "kberget")
        })

    elif place == "chalmers":
        return json.dumps({
            "Mot Ullevi N": getDeparture("chalmers", "lgh"),
            "Mot Järntorget": getDeparture("chalmers", "jt"),
            "Från Järntorget": getDeparture("jt", "huset1"),
            "Mot Marklandsgatan": getDeparture("chalmers", "markland"),
            "Från Marklandsgatan": getDeparture("markland", "kungssten")
        })

    return json.dumps({
        "test":"test2"
    })

def getDeparture(fr, to):
    return clean(rp.departureBoard(
        id=stopIDs[fr], date=strftime("%Y-%m-%d"), timeSpan=60,
        time=strftime("%H:%M"), maxDeparturesPerLine=3, 
        direction=stopIDs[to], needJourneyDetail=0))

def clean(obj):
    deps = obj.get("DepartureBoard").get("Departure")
    if deps == None:
        return []
    
    if type(deps) != list:
        deps = [deps]

    outArr = []
    for dep in deps:
        line = dep.get("sname")
        dest = cut(dep.get("direction"))
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
    hour, minutes = rttime.split(":")
    rtminutes = int(minutes)
    rtminutes += int(hour) * 60

    hour, minutes = tttime.split(":")
    ttminutes = int(minutes)
    ttminutes += int(hour) * 60

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

def sort_departures(arr):
    # Sort firstly by line number and secondly by destination
    sorted_by_destination = sorted(arr, key=lambda dep: dep["dest"])
    sorted_by_line = sorted(sorted_by_destination, key=lambda dep: int(dep['line']))
    return sorted_by_line