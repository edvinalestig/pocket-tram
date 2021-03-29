import dateutil.tz as tz
from datetime import datetime
from geopy.distance import distance
import json
import math
from requests.exceptions import HTTPError

import vasttrafik


rengatan  = 9021014005470000
kungssten = 9021014004100000
nyavarv   = 9021014005100000

maxX = "11908150"
maxY = "57683321"
minX = "11864719"
minY = "57649626"

def getPosition(rp):
    # Hard coded for line 91

    timeNow = datetime.now(tz.gettz("Europe/Stockholm"))
    date = timeNow.strftime("%Y%m%d")
    time = timeNow.strftime("%H:%M")

    departure = rp.departureBoard(
        id=rengatan, date=date, timeSpan=35,
        time=time, maxDeparturesPerLine=1, 
        direction=kungssten, needJourneyDetail=1)

    d = departure.get("DepartureBoard")

    try:
        dd = d.get("Departure")
        if type(dd) == list:
            dd = dd[0]

        journeyID = dd.get("journeyid")
        ref = dd.get("JourneyDetailRef").get("ref")
    except AttributeError:
        return "Error 1"
    

    linemap = rp.livemap(maxx=maxX, maxy=maxY, minx=minX, miny=minY, onlyRealtime="yes")

    try:
        vehicles = linemap.get("livemap").get("vehicles")
    except AttributeError:
        return "Error 2"

    for vehicle in vehicles:
        if vehicle.get("gid") == journeyID:
            # Correct vehicle
            lon = int(vehicle.get("x"))/1000000
            lat = int(vehicle.get("y"))/1000000
            position = (lat, lon)
            break
    else:
        return "Okänd position"


    try:
        journey = rp.request(ref)
    except HTTPError:
        return "Error 3"

    try:
        jd = journey.get("JourneyDetail")
        journey = jd.get("Stop")
        gr = jd.get("GeometryRef")
        georef  = gr.get("ref")
    except AttributeError:
        return "Error 4"

    try:
        geo = rp.request(georef)
    except HTTPError:
        return "Error 5"

    try:
        polyline = geo.get("Geometry").get("Points").get("Point")
        polylines = splitOnEqual(polyline)
    except (AttributeError, TypeError):
        return "Error 6"


    poly  = 0
    point = 0
    shortestDistance = math.inf
    
    for i, pol in enumerate(polylines):
        for j, poi in enumerate(pol):
            pos = (poi.get("lat"), poi.get("lon"))
            d = distance(position, pos).km
            if d < shortestDistance:
                poly  = i
                point = j
                shortestDistance = d

    distanceToNext = 0
    i = point
    while i < len(polylines[poly])-1:
        prev = (polylines[poly][i].get("lat"), polylines[poly][i].get("lon"))
        next = (polylines[poly][i+1].get("lat"), polylines[poly][i+1].get("lon"))
        distanceToNext += distance(prev, next).km
        i += 1
    distanceToNext = math.floor(distanceToNext * 1000)

    startPos = (polylines[poly][0].get("lat"), polylines[poly][0].get("lon"))
    endPos = (polylines[poly][-1].get("lat"), polylines[poly][-1].get("lon"))
    startStop = ""
    endStop   = ""

    for stop in journey:
        if stop.get("lat") == startPos[0] and stop.get("lon") == startPos[1]:
            startStop = stop.get("name").split(",")[0]
        elif stop.get("lat") == endPos[0] and stop.get("lon") == endPos[1]:
            endStop   = stop.get("name").split(",")[0]

    if distance(endPos, position) < 0.05: # 50 m
        return "Bussen är vid " + endStop
    else:
        return "Bussen är mellan " + startStop + " och " + endStop + f". (ca. {distanceToNext} m kvar)"   

    # # (Sum of distances, distance to next stop, prev stop, next stop)
    # stops = (math.inf, math.inf, "Stop 1", "Stop 2")
    # i = 1
    # while i < len(journey):
    #     stop1 = journey[i-1]
    #     stop2 = journey[i]
    #     pos1  = (stop1.get("lat"), stop1.get("lon"))
    #     pos2  = (stop2.get("lat"), stop2.get("lon"))
    #     dis1  = distance(position, pos1).km
    #     dis2  = distance(position, pos2).km
    #     total = dis1 + dis2

    #     if stops[0] > total:
    #         stops = (total, dis2,
    #             stop1.get("name").split(",")[0],
    #             stop2.get("name").split(",")[0])
    #     i += 1

    # if stops[1] < 0.05: # 50 m
    #     return "Bussen är vid " + stops[3]
    # else:
    #     return "Bussen är mellan " + stops[2] + " och " + stops[3] + f". (ca. {math.floor(stops[1]*1000)} m kvar)"


# Splits a list when two consecutive elements are equal.
# Does not remove any elements.
def splitOnEqual(arr):
    if type(arr) != list:
        raise TypeError("Expected list")
    lists = []
    tempList = []
    i = 0
    while i < len(arr)-1:
        tempList.append(arr[i])
        if arr[i] == arr[i+1]:
            lists.append(tempList)
            tempList = []
        i += 1

    tempList.append(arr[i])
    lists.append(tempList)
    return lists