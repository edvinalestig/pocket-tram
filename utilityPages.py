from typing import Literal
from flask import send_file
import json
from datetime import datetime, timedelta
from dateutil.tz import tz
import math
from models.PR4.DeparturesAndArrivals import CallDetails, GetArrivalsResponse, GetDeparturesResponse, ArrivalsAPIModel, DepartureAPIModel, ServiceJourneyDetails
from models.PR4.Locations import Location
from vasttrafik import Reseplaneraren
from jinja2 import Environment, FileSystemLoader

from vasttrafik2 import PR4

def getDepDelay(dep: ArrivalsAPIModel | DepartureAPIModel, ank=False) -> str:
    if dep.isCancelled:
        return dep.plannedTime.strftime("%H:%M X")

    # Check if real time info is available
    if not dep.estimatedTime:
        return dep.plannedTime.strftime(f"%H:%M")

    delta: timedelta = dep.estimatedTime - dep.plannedTime

    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    delay = delta.days * 1440 + math.ceil(delta.seconds/60)

    if delay >= 0:
        return dep.plannedTime.strftime(f"%H:%M+{delay}")
    else:
        return dep.plannedTime.strftime("%H:%M") + str(delay)

def getStopDelay(stop: CallDetails, ank=False) -> str:
    plannedTime: datetime = stop.plannedArrivalTime if ank else stop.plannedDepartureTime # type: ignore
    
    if (ank and stop.isArrivalCancelled) or (not ank and stop.isDepartureCancelled):
        return plannedTime.strftime("%H:%M X")

    # Check if real time info is available
    if not stop.estimatedArrivalTime if ank else not stop.estimatedDepartureTime:
        return (stop.plannedArrivalTime if ank else stop.plannedDepartureTime).strftime("%H:%M") # type: ignore

    realTime: datetime = stop.estimatedArrivalTime if ank else stop.estimatedDepartureTime # type: ignore
    delta: timedelta = realTime - plannedTime

    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    delay: int = delta.days * 1440 + math.ceil(delta.seconds/60)

    if delay >= 0:
        return plannedTime.strftime(f"%H:%M+{delay}")
    else:
        return plannedTime.strftime("%H:%M") + str(delay)

###############################

class UtilityPages:
    def __init__(self, pr4: PR4, resep: Reseplaneraren) -> None:
        self.pr4: PR4 = pr4
        self.resep = resep

    def mainPage(self):
        return send_file("static/util.html")

    def searchStop(self, args):
        stopID: str
        stopName: str
        if args.get("stop"):
            stop: list[Location] = self.pr4.locations_by_text(args.get("stop")).results
            if not stop:
                return "<a href='/utilities'>Inga träffar</a>"
            stopName = stop[0].name
            stopID = stop[0].gid or ""
        else:
            stopID = args.get("stopId")
            stopName = args.get("stopName")
        
        dateTime = datetime.now(tz.gettz("Europe/Stockholm"))
        if args.get("time"):
            hh,mm = map(int,args.get("time").split(":"))
            dateTime = dateTime.replace(hour=hh, minute=mm)
        if args.get("date"):
            yy,mm,dd = map(int,args.get("date").split("-"))
            dateTime = dateTime.replace(year=yy, month=mm, day=dd)
        if args.get("datetime"):
            dateTime = datetime.fromisoformat("".join(args["datetime"].replace(" ", "+").split(".0000000")))

        offset: int = args.get("offset", 0)

        departures: GetDeparturesResponse = self.pr4.departureBoard(stopID, dateTime, offset)

        if not departures.results:
            return "<a href='/utilities'>Inga avgångar</a>"


        types = {
            "bus": "🚌",
            "tram": "🚋",
            "train": "🚂",
            "ferry": "⛴",
            "taxi": "🚕",
            "unknown": "?",
            "none": "-",
            "vasttagen": "Västtåg",
            "regionaltrain": "Regionaltåg"
        }

        departures.results.sort(key=lambda x: x.plannedTime)

        html = '<!DOCTYPE html>\n<html lang="sv">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Avgångar</title>\n</head>\n<body style="font-family: sans-serif">'
        html += "<a href='/utilities'>Till sökruta</a>"
        html += f"<h2>{stopName}, {dateTime.strftime('%Y-%m-%d, %H:%M')}</h2>"
        html += "\n<table>"
        html += "\n<tr><th>Linje</th><th>Destination</th><th>TT-tid</th><th>RT-tid</th><th>Låggolv</th><th>Läge</th><th>Typ</th><th>Subtyp</th><th>Inställd</th><th>Mer info</th></tr>"
        depRows = [(
            f'\n<tr style="border: 5px solid red;">'
            f"<td style='background-color: {dep.serviceJourney.line.backgroundColor}; \
                         color: {dep.serviceJourney.line.foregroundColor}; \
                         text-align: center; \
                         border: 1px solid {dep.serviceJourney.line.borderColor};'> \
                         {dep.serviceJourney.line.shortName}</td>"
            f"<td><a href='/simpleDepInfo?ref={dep.detailsReference}&gid={stopID}&ad=d'>{dep.serviceJourney.direction}</a></td>"
            f"<td style='text-align: center;'>{dep.plannedTime.strftime('%H:%M')}</td>"
            f"<td style='text-align: center;'>{dep.estimatedTime.strftime('%H:%M') if dep.estimatedTime is not None else '-'}</td>"
            f"<td style='text-align: center;'>{'♿' if dep.serviceJourney.line.isWheelchairAccessible else '❌'}</td>"
            f"<td style='text-align: center;'>{dep.stopPoint.platform}</td>"
            f"<td style='text-align: center;'>{types.get(dep.serviceJourney.line.transportMode.value, '?')}</td>"
            f"<td style='text-align: center;'>{types.get(dep.serviceJourney.line.transportSubMode.value, '?')}</td>"
            f"<td style='text-align: center;'>{'🔴' if dep.isCancelled else '🟢'}</td>"
            f"<td style='text-align: center;'><a href='/depInfo?ref={dep.detailsReference}&gid={stopID}&ad=d'>Mer info</a></td>"
            f"</tr>"
            ) for dep in departures.results]
        
        html += "".join(depRows)
        html += "\n</table>"

        if departures.links.previous:
            prev: str = departures.links.previous
            params: dict[str, str] = {k:v for k,v in map(lambda x: x.split("="), prev.split("?")[1].split("&"))}
            dtime: str = params["startDateTime"]
            offset2: str = params.get("offset", "0")
            html += f"<br><a href='/findDepartures?stop={stopName}&datetime={dtime}&offset={offset2}&moreInfo=on'>Föregående sida</a>"

        if departures.links.next:
            nxt: str = departures.links.next
            params: dict[str, str] = {k:v for k,v in map(lambda x: x.split("="), nxt.split("?")[1].split("&"))}
            dtime: str = params["startDateTime"]
            offset2: str = params.get("offset", "0")
            html += f"<br><a href='/findDepartures?stop={stopName}&datetime={dtime}&offset={offset2}&moreInfo=on'>Nästa sida</a>"

        html += "\n</body>\n</html>"

        return html
    
    def stopDepartures(self, args: dict) -> str:
        isArrival: bool = args.get("arrivals") == "on"

        stopID: str
        stopName: str
        if args.get("stop"):
            stop: list[Location] = self.pr4.locations_by_text(args["stop"]).results
            if not stop:
                return "<a href='/utilities'>Inga träffar</a>"
            stopName = stop[0].name
            stopID = stop[0].gid or ""
        else:
            stopID = args["stopId"]
            stopName = args["stopName"]

        dateTime = datetime.now(tz.gettz("Europe/Stockholm"))
        if args.get("time"):
            hh,mm = map(int,args["time"].split(":"))
            dateTime = dateTime.replace(hour=hh, minute=mm)
        if args.get("date"):
            yy,mm,dd = map(int,args["date"].split("-"))
            dateTime = dateTime.replace(year=yy, month=mm, day=dd)
        if args.get("datetime"):
            dateTime = datetime.fromisoformat("".join(args["datetime"].replace(" ", "+").split(".0000000")))

        offset = args.get("offset", 0)

        departures: GetArrivalsResponse | GetDeparturesResponse = self.pr4.arrivalBoard(stopID, dateTime, offset) if isArrival else self.pr4.departureBoard(stopID, dateTime, offset)
        results = [
            {
                "lineBgColor": dep.serviceJourney.line.backgroundColor,
                "lineFgColor": dep.serviceJourney.line.foregroundColor,
                "lineBorderColor": dep.serviceJourney.line.borderColor,
                "lineName": dep.serviceJourney.line.shortName,
                "lineDestination": dep.serviceJourney.origin if isArrival else dep.serviceJourney.directionDetails.shortDirection + (f" via {dep.serviceJourney.directionDetails.via}" if dep.serviceJourney.directionDetails.via else ""), # type: ignore
                "lineTime": getDepDelay(dep),
                "linePlatform": dep.stopPoint.platform or "",
                "detailsReference": dep.detailsReference
            } for dep in departures.results
        ]

        prevHref: str = ""
        nextHref: str = ""

        if prev := departures.links.previous:
            params = map(lambda x: x.split("="), prev.split("?")[1].split("&"))
            params = {k:v for k,v in params}
            dtime, offset = params["startDateTime"], params.get("offset", 0)
            prevHref = f"/findDepartures?stop={stopName}&datetime={dtime}&offset={offset}{'&arrivals=on' if isArrival else ''}" 
        if nxt := departures.links.next:
            params = map(lambda x: x.split("="), nxt.split("?")[1].split("&"))
            params = {k:v for k,v in params}
            dtime, offset = params["startDateTime"], params.get("offset", 0)
            nextHref = f"/findDepartures?stop={stopName}&datetime={dtime}&offset={offset}{'&arrivals=on' if isArrival else ''}"

        # Generate html using jinja2
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("util_stop.html.j2")

        return template.render(
            departures = results,
            stopName = stopName,
            stopID = stopID,
            dateTime = dateTime.strftime('%Y-%m-%d, %H:%M'),
            nextHref = nextHref,
            prevHref = prevHref,
            isArrival = isArrival
        )

    def simpleStopArrivals(self, args: dict):
        return json.dumps(args)

    def getStyle(self, dep: ServiceJourneyDetails) -> str:
        col = dep.line
        fg = col.foregroundColor
        bg = col.backgroundColor
        border = col.borderColor
        return f'color: {fg}; background-color: {bg}; border: 1px solid {border};'
    
    def depInfo(self, args):
        ref = args.get("ref")
        if not ref:
            return "<a href='/utilities'>Ingen referens</a>"
        gid = args.get("gid")
        ad = args.get("ad")
        dep = self.resep.request(ref, gid, ank=ad=="a").get("serviceJourneys")
        if not dep:
            return "<a href='/utilities'>Ingen info<a>"

        return "<a href='/utilities'>Temporärt trasigt</a><br>"

        # with open("dep.json", "w") as f:
        #     f.write(json.dumps(dep))

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
            f'<td rowspan="2" style="{self.getStyle(sj)}">{sj["line"]["name"]}</td>' # won't work until updated
            f'<td rowspan="2" style="{self.getStyle(sj)}">{sj["direction"]}</td>'
            f'<td>{stop["stopPoint"]["name"]}</td>'
            f'<td>Ank. {datetime.fromisoformat("".join(stop["plannedArrivalTime"].split(".0000000"))).strftime("%H:%M") if stop.get("plannedArrivalTime") else "-"}</td>'
            f'<td>Avg. {datetime.fromisoformat("".join(stop["plannedDepartureTime"].split(".0000000"))).strftime("%H:%M") if stop.get("plannedDepartureTime") else "-"}</td>'
            f'<td>Läge {stop["stopPoint"].get("platform")}</td>'
            f'<td>Hpl:läge-ID: {stop["stopPoint"]["gid"]}</td>'
            f'</tr>'
            f'<tr>'
            f'<td>{stop["stopPoint"]["stopArea"]["tariffZone1"]["name"]}{" & " + stop["stopPoint"]["stopArea"]["tariffZone2"]["name"] if stop["stopPoint"]["stopArea"].get("tariffZone2") else ""}</td>'
            f'<td>RT ank. {datetime.fromisoformat("".join(stop["estimatedArrivalTime"].split(".0000000"))).strftime("%H:%M") if stop.get("estimatedArrivalTime") else "-"}</td>'
            f'<td>RT avg. {datetime.fromisoformat("".join(stop["estimatedDepartureTime"].split(".0000000"))).strftime("%H:%M") if stop.get("estimatedDepartureTime") else "-"}</td>'
            f'<td>Inställd: {stop.get("isCancelled")}</td>'
            f'<td>Hpl-ID: {stop["stopPoint"]["stopArea"]["gid"]}</td>'
            f'</tr>'
        ) for sj in dep for stop in sj.get("callsOnServiceJourney")]
        
        html += "\n".join(stops)
        html += "\n</table>"


        html += f'\n<a href="/map?ref={ref}&gid={gid}&ad={ad}">Karta</a>'
        html += "\n</body>\n</html>"
        
        return html

    def simpleDepInfo(self, args):
        ref: str | None = args.get("ref")
        if not ref:
            return "<a href='/utilities'>Ingen referens</a>"
        gid: str = args.get("gid")
        ad: Literal['a', 'd'] = args.get("ad")
        departures: list[ServiceJourneyDetails] = self.pr4.request(ref, gid, ank=ad=="a").serviceJourneys
        if not departures:
            return "<a href='/utilities'>Ingen info<a>"

        html = (
            '<!DOCTYPE html>\n<html lang="sv">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '<title>Avgångar</title>\n'
            '<style>td, tr {margin: 0px; padding-left: 5px; padding-right: 5px;}'
            'tr:nth-of-type(even) {border-bottom: 1px solid black;}'
            'table {border-collapse: collapse; border: 1px solid black;}</style>'
            '</head>\n<body style="font-family: sans-serif">\n<table>\n')
        
        for sj in departures:
            html += ('<tr>\n'
                    f'<td colspan="3" style="{self.getStyle(sj)}">{sj.line.name}</td>'
                     '</tr>\n'
                     '<tr>\n'
                    f'<td colspan="3" style="{self.getStyle(sj)}">{sj.direction}</td>'
                     '</tr>\n')
            stops = [(
                f'<tr>'
                f'<td rowspan="2"><a href="/findDepartures'
                    f'?stopId={stop.stopPoint.stopArea.gid}'
                    f'&stopName={stop.stopPoint.name}'
                    f'&datetime={stop.plannedArrivalTime or stop.plannedDepartureTime}"'
                    f'>{stop.stopPoint.name}</a></td>'
                f'<td>{getStopDelay(stop, ank=True) if stop.plannedArrivalTime else "-"}</td>'
                f'<td rowspan="2" >Läge {stop.stopPoint.platform}</td>'
                f'</tr>'
                f'<tr>'
                f'<td>{getStopDelay(stop) if stop.plannedDepartureTime else "-"}</td>'
                f'</tr>'
            ) for stop in sj.callsOnServiceJourney]
            
            html += "\n".join(stops)
        html += "\n</table>"

        html += f'\n<a href="/map?ref={ref}&gid={gid}&ad={ad}">Karta</a>'
        html += "\n</body>\n</html>"

        ## ----------------------
        lines = []
        for sj in departures:

            stops = [{
                "stopID": stop.stopPoint.stopArea.gid,
                "stopName": stop.stopPoint.name,
                "arrivalTime": getStopDelay(stop, ank=True) if stop.plannedArrivalTime else "-",
                "departureTime": getStopDelay(stop) if stop.plannedDepartureTime else "-",
                "linkDateTime": stop.plannedArrivalTime or stop.plannedDepartureTime,
                "platform": stop.stopPoint.platform
            } for stop in sj.callsOnServiceJourney]

            lines.append({
                "lineStyle": self.getStyle(sj),
                "lineName": sj.line.name,
                "lineDirection": sj.direction,
                "stops": stops
            })

        mapRef: str = f"/map?ref={ref}&gid={gid}&ad={ad}"
        
        # Generate html using jinja2
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("util_line.html.j2")

        return template.render(
            deps = lines,
            mapRef = mapRef
        )


    def routemap(self, args):
        ref = args.get("ref")
        if not ref:
            return "<a href='/utilities'>Ingen referens</a>"
        gid = args.get("gid")
        ad  = args.get("ad")
        geo = self.resep.request(ref, gid, ank=ad=="a", geo=True).get("serviceJourneys")
        positions = self.position(args)
        return {"geo": geo, "positions": positions}
    
    def position(self, args):
        # Covers the whole of VGR
        lowerLeftLat = 57.270
        lowerLeftLon = 11.146
        upperRightLat = 59.378
        upperRightLon = 14.496
        ref = args.get("ref")
        line = args.getlist("line")
        if not ref and not line: return []
        if ref:
            return self.resep.positions(lowerLeftLat, lowerLeftLon, upperRightLat, upperRightLon, [ref])
        else:
            return self.resep.positions(lowerLeftLat, lowerLeftLon, upperRightLat, upperRightLon, lineDesignations=line)


if __name__ == "__main__":
    pass
