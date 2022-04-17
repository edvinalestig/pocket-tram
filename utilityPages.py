import base64
from flask import send_file
import json
from datetime import datetime
import dateutil.tz as tz
import math


def getDelay(dep, ank=False):
    if dep.get("cancelled"):
        return " X"

    # Check if real time info is available
    tttime = dep.get("depTime" if not ank else "arrTime")
    rttime = dep.get("rtDepTime" if not ank else "rtArrTime")
    if rttime == None:
        return ""
    ttdate = dep.get("depDate" if not ank else "arrDate")
    rtdate = dep.get("rtDepDate" if not ank else "rtArrDate")

    ttdt = convertToDatetime(tttime, ttdate)
    rtdt = convertToDatetime(rttime, rtdate)
    delta = rtdt - ttdt

    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    delay = delta.days * 1440 + math.floor(delta.seconds/60)

    if delay >= 0:
        return f"+{delay}"
    else:
        return str(delay)

def convertToDatetime(time, date):
    t = time.split(":")
    d = date.split("-")
    return datetime(hour=int(t[0]), minute=int(t[1]), year=int(d[0]), month=int(d[1]), day=int(d[2]))

###############################

class UtilityPages:
    def __init__(self, resep):
        self.resep = resep

    def mainPage(self):
        return send_file("static/util.html")

    def searchStop(self, args):
        if args.get("stop"):
            stop = self.resep.location_name(input=args.get("stop")).get("LocationList").get("StopLocation")
            if type(stop) == list:
                stop = stop[0]
            stopName = stop.get("name")
            stopID = stop.get("id")
        else:
            stopID = args.get("stopId")
            stopName = args.get("stopName")
            
        depTime = args.get("time") if args.get("time") else datetime.now(tz.gettz("Europe/Stockholm")).strftime("%H:%M")
        depDate = args.get("date") if args.get("date") else datetime.now(tz.gettz("Europe/Stockholm")).strftime("%Y%m%d")

        departures = self.resep.departureBoard(id=stopID, date=depDate, time=depTime).get("DepartureBoard").get("Departure")

        with open("deps.json", "w") as f:
            f.write(json.dumps(departures))

        if not departures:
            return "<a href='/utilities'>Inga avgångar</a>"

        if type(departures) == dict:
            departures = [departures]

        types = {
            "BUS": "🚌",
            "TRAM": "🚋",
            "VAS": "Västtåg",
            "LDT": "Fjärrtåg",
            "REG": "Regionaltåg",
            "BOAT": "⛴",
            "TAXI": "🚕"
        }

        html = '<!DOCTYPE html>\n<html lang="sv">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Avgångar</title>\n</head>\n<body style="font-family: sans-serif">'
        html += "<a href='/utilities'>Till sökruta</a>"
        html += f"<h1>{stopName}, {depTime}, {depDate}</h1>"
        html += "\n<table>"
        html += "\n<tr><th>Linje</th><th>Destination</th><th>TT-tid</th><th>RT-tid</th><th>Låggolv</th><th>Läge</th><th>Typ</th><th>Inställd</th><th>Bokas?</th><th>Mer info</th></tr>"
        depRows = [(
            f'\n<tr style="border: 5px solid red;">'
            f"<td style='background-color: {dep.get('bgColor')}; color: {dep.get('fgColor')}; text-align: center; border: 1px {dep.get('stroke')} {dep.get('bgColor')};'>{dep.get('sname')}</td>"
            f"<td><a href='/simpleDepInfo?ref={dep.get('JourneyDetailRef').get('ref').split('?ref=')[1]}'>{dep.get('direction')}</a></td>"
            f"<td style='text-align: center;'>{dep.get('time')}</td>"
            f"<td style='text-align: center;'>{dep.get('rtTime') if dep.get('rtTime') else '-'}</td>"
            f"<td style='text-align: center;'>{'♿' if dep.get('accessibility') == 'wheelChair' else '❌'}</td>"
            f"<td style='text-align: center;'>{dep.get('track')}</td>"
            f"<td style='text-align: center;'>{types.get(dep.get('type'))}</td>"
            f"<td style='text-align: center;'>{'🔴' if dep.get('cancelled') else '🟢'}</td>"
            f'<td style="text-align: center;">{"Ja" if dep.get("booking") else "Nej"}</td>'
            f"<td style='text-align: center;'><a href='/depInfo?ref={dep.get('JourneyDetailRef').get('ref').split('?ref=')[1]}'>Mer info</a></td>"
            f"</tr>"
            ) for dep in departures]
        
        html += "".join(depRows)
        html += "\n</table>"
        html += f"<br><a href='/findDepartures?stop={stopName}&time={departures[-1].get('time')}&date={departures[-1].get('date')}'>Fler avgångar</a>"
        html += "\n</body>\n</html>"

        return html

    def getStyle(self, dep, stop):
        col = dep.get("Color")
        if type(col) == dict:
            color = col.get("fgColor")
            bg = col.get("bgColor")
            stroke = col.get("stroke")
        else:
            idx = int(stop.get("routeIdx"))
            color = "red"
            bg = "hotpink"

        return f'color: {color}; background-color: {bg}; border: 1px {stroke} {color};'

    def getLine(self, dep, stop):
        line = dep.get("JourneyName")
        if type(line) == dict:
            return line.get("name")
        else:
            idx = int(stop.get("routeIdx"))
            for l in reversed(line):
                if int(l.get("routeIdxFrom")) <= idx and int(l.get("routeIdxTo")) >= idx:
                    return l.get("name")
            return "Linje"

    def getDestination(self, dep, stop):
        dest = dep.get("Direction")
        if type(dest) == dict:
            return dest.get("$")
        else:
            idx = int(stop.get("routeIdx"))
            for d in reversed(dest):
                if int(d.get("routeIdxFrom")) <= idx and int(d.get("routeIdxTo")) >= idx:
                    return d.get("$")
            return "Destination"
    
    def depInfo(self, args):
        refArg = args.get("ref")
        if not refArg:
            return "<a href='/utilities'>Ingen referens</a>"
        ref = "https://api.vasttrafik.se/bin/rest.exe/v2/journeyDetail?ref=" + refArg
        dep = self.resep.request(ref).get("JourneyDetail")
        if not dep:
            return "<a href='/utilities'>Ingen info<a>"

        with open("dep.json", "w") as f:
            f.write(json.dumps(dep))

        html = (
            '<!DOCTYPE html>\n<html lang="sv">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '<title>Avgångar</title>\n'
            '<style>td, tr {margin: 0px; padding-left: 5px; padding-right: 5px;}'
            'tr:nth-of-type(even) {border-bottom: 1px solid black;}'
            'table {border-collapse: collapse;}</style>'
            '</head>\n<body style="font-family: sans-serif">\n<table>\n')
        # header here
        stops = [(
            f'<tr>'
            f'<td rowspan="2" style="{self.getStyle(dep, stop)}">{self.getLine(dep, stop)}</td>'
            f'<td rowspan="2" style="{self.getStyle(dep, stop)}">{self.getDestination(dep, stop)}</td>'
            f'<td>{stop.get("name").split(", ")[0]}</td>'
            f'<td>Ank. {stop.get("arrTime") if stop.get("arrTime") else "-"}</td>'
            f'<td>Avg. {stop.get("depTime") if stop.get("depTime") else "-"}</td>'
            f'<td>Läge {stop.get("track")}</td>'
            f'<td>Hpl-ID: {stop.get("id")}</td>'
            f'</tr>'
            f'<tr>'
            f'<td>{stop.get("name").split(", ")[1]}</td>'
            f'<td>RT ank. {stop.get("rtArrTime") if stop.get("rtArrTime") else "-"}</td>'
            f'<td>RT avg. {stop.get("rtDepTime") if stop.get("rtDepTime") else "-"}</td>'
            f'<td>Lat: {stop.get("lat")}</td>'
            f'<td>Lon: {stop.get("lon")}</td>'
            f'</tr>'
        ) for stop in dep.get("Stop")]
        
        html += "\n".join(stops)
        html += "\n</table>"

        georef = dep.get("GeometryRef").get("ref").split("?ref=")[1]

        b64Dep = base64.b64encode(refArg.encode("ascii")).decode("ascii")
        b64Geo = base64.b64encode(georef.encode("ascii")).decode("ascii")

        # b64Geo = base64_encode(georef).decode("ascii")
        # b64Dep = base64_encode(refArg).decode("ascii")
        html += f'\n<a href="/map?depRef={b64Dep}&geoRef={b64Geo}">Map</a>'
        html += f'\n<a href="/getgeometry?ref={georef}">Geometry</a>'
        html += "\n</body>\n</html>"
        
        return html

    def simpleDepInfo(self, args):
        refArg: str | None = args.get("ref")
        if not refArg:
            return "<a href='/utilities'>Ingen referens</a>"
        ref = "https://api.vasttrafik.se/bin/rest.exe/v2/journeyDetail?ref=" + refArg
        dep = self.resep.request(ref).get("JourneyDetail")
        if not dep:
            return "<a href='/utilities'>Ingen info<a>"

        with open("dep.json", "w") as f:
            f.write(json.dumps(dep))

        html = (
            '<!DOCTYPE html>\n<html lang="sv">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '<title>Avgångar</title>\n'
            '<style>td, tr {margin: 0px; padding-left: 5px; padding-right: 5px;}'
            'tr:nth-of-type(even) {border-bottom: 1px solid black;}'
            'table {border-collapse: collapse; border: 1px solid black;}</style>'
            '</head>\n<body style="font-family: sans-serif">\n<table>\n')
        # header here
        stops = [(
            f'<tr>'
            f'<td rowspan="2"  style="{self.getStyle(dep, stop)}">{self.getLine(dep, stop)}</td>'
            f'<td rowspan="2"  style="{self.getStyle(dep, stop)}">{self.getDestination(dep, stop)}</td>'
            f'<td rowspan="2"><a href="/findDepartures'
                f'?stopId={stop.get("id")}'
                f'&stopName={stop.get("name")}'
                f'&date={stop.get("arrDate") if stop.get("arrDate") else stop.get("depDate")}'
                f'&time={stop.get("arrTime") if stop.get("arrTime") else stop.get("depTime")}"'
                f'>{stop.get("name")}</a></td>'
            f'<td>{stop.get("arrTime") + getDelay(stop, True) if stop.get("arrTime") else "-"}</td>'
            # f'<td>RT ank. {stop.get("rtArrTime") if stop.get("rtArrTime") else "-"}</td>'
            f'<td rowspan="2" >Läge {stop.get("track")}</td>'
            f'</tr>'
            f'<tr>'
            f'<td>{stop.get("depTime") + getDelay(stop) if stop.get("depTime") else "-"}</td>'
            # f'<td>RT avg. {stop.get("rtDepTime") if stop.get("rtDepTime") else "-"}</td>'
            f'</tr>'
        ) for stop in dep.get("Stop")]
        
        html += "\n".join(stops)
        html += "\n</table>"

        georef = dep.get("GeometryRef").get("ref").split("?ref=")[1]

        b64Dep = base64.b64encode(refArg.encode("ascii")).decode("ascii")
        b64Geo = base64.b64encode(georef.encode("ascii")).decode("ascii")

        html += f'\n<a href="/map?depRef={b64Dep}&geoRef={b64Geo}">Map</a>'
        html += "\n</body>\n</html>"
        
        return html


    def getGeometry(self, args):
        ref = args.get("ref")
        geo = self.resep.geometry(ref).get("Geometry").get("Points").get("Point")
        return json.dumps(geo)


    def routemap(self, args):
        geo: str  = args.get("geoRef")
        ref: str  = "https://api.vasttrafik.se/bin/rest.exe/v2/journeyDetail?ref=" + args.get("depRef")
        dep: dict = self.resep.request(ref).get("JourneyDetail")

        jName = dep.get("JourneyName")
        if type(jName) == list:
            jName = jName[0]
        jName = jName.get("name")

        jDest = dep.get("Direction")
        if type(jDest) == list:
            jDest = jDest[0]
        jDest = jDest.get("$")

        return {
            "geometry": json.loads(self.getGeometry({"ref":geo})),
            "stops": dep.get("Stop"),
            "color": dep.get("Color"),
            "name": f'{jName} {jDest}'
        }


if __name__ == "__main__":
    pass
