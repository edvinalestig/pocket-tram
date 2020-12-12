from flask import send_file
import json
import codecs
from datetime import datetime
import dateutil.tz as tz

class UtilityPages:
    def __init__(self, resep):
        self.resep = resep

    def mainPage(self):
        return send_file("static/util.html")

    def searchStop(self, args):
        stop = self.resep.location_name(input=args.get("stop")).get("LocationList").get("StopLocation")
        if type(stop == list):
            stop = stop[0]
        stopName = stop.get("name")
        stopID = stop.get("id")

        depTime = args.get("time") if args.get("time") else datetime.now(tz.gettz("Europe/Stockholm")).strftime("%H:%M")
        depDate = args.get("date") if args.get("date") else datetime.now(tz.gettz("Europe/Stockholm")).strftime("%Y%m%d")

        departures = self.resep.departureBoard(id=stopID, date=depDate, time=depTime).get("DepartureBoard").get("Departure")

        with open("deps.json", "w") as f:
            f.write(json.dumps(departures))

        if not departures:
            return "<a href='/utilities'>Inga avgångar</a>"

        if type(departures) == dict:
            departures = [departures]

        html = '<!DOCTYPE html>\n<html lang="sv">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Avgångar</title>\n</head>\n<body>'
        html += f"<h1>{stopName}, {depTime}, {depDate}</h1>"
        html += "\n<table>"
        html += "\n<tr><th>Linje</th><th>Destination</th><th>TT-tid</th><th>RT-tid</th><th>Låggolv</th><th>Läge</th><th>Typ</th><th>Mer info</th></tr>"
        depRows = [(
            f"\n<tr>"
            f"<td style='background-color: {dep.get('fgColor')}; color: {dep.get('bgColor')}; text-align: center;'>{dep.get('sname')}</td>"
            f"<td>{dep.get('direction')}</td>"
            f"<td style='text-align: center;'>{dep.get('time')}</td>"
            f"<td style='text-align: center;'>{dep.get('rtTime')}</td>"
            f"<td style='text-align: center;'>{'♿' if dep.get('accessibility') == 'wheelChair' else '❌'}</td>"
            f"<td style='text-align: center;'>{dep.get('track')}</td>"
            f"<td style='text-align: center;'>{dep.get('type')}</td>"
            f"<td style='text-align: center;'><a href='/depInfo?ref={dep.get('JourneyDetailRef').get('ref').split('?ref=')[1]}'>Mer info</a></td>"
            f"</tr>"
            ) for dep in departures]
        
        html += "".join(depRows)
        html += "\n</table>\n</body>\n</html>"
        
        return html
    
    def depInfo(self, args):
        ref = "https://api.vasttrafik.se/bin/rest.exe/v2/journeyDetail?ref=" + args.get("ref")
        dep = self.resep.request(ref).get("JourneyDetail")
        if not dep:
            return "<a href='/utilities'>Ingen info<a>"

        with open("dep.json", "w") as f:
            f.write(json.dumps(dep))


        
        
        return json.dumps(dep)

if __name__ == "__main__":
    pass