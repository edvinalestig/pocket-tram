from flask import send_file
import json
from datetime import datetime
from dateutil.tz import tz
import math
from vasttrafik import Reseplaneraren

def getDepDelay(dep, ank=False):
    date_time = datetime.fromisoformat("".join(dep.get("plannedTime").split(".0000000")))

    if dep.get("isCancelled"):
        return date_time.strftime("%H:%M X")

    # Check if real time info is available
    rttime = dep.get("estimatedTime")
    if rttime is None:
        return date_time.strftime(f"%H:%M")

    real_date_time = datetime.fromisoformat("".join(dep.get("estimatedTime").split(".0000000")))
    delta = real_date_time - date_time

    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    delay = delta.days * 1440 + math.ceil(delta.seconds/60)

    if delay >= 0:
        return date_time.strftime(f"%H:%M+{delay}")
    else:
        return date_time.strftime("%H:%M") + str(delay)

def getStopDelay(stop, ank=False):
    date_time = datetime.fromisoformat("".join(stop.get("plannedArrivalTime" if ank else "plannedDepartureTime").split(".0000000")))

    if stop.get("isArrivalCancelled" if ank else "isDepartureCancelled"):
        return date_time.strftime("%H:%M X")

    # Check if real time info is available
    rttime = stop.get("estimatedArrivalTime" if ank else "estimatedDepartureTime")
    if rttime is None:
        return date_time.strftime(f"%H:%M")

    real_date_time = datetime.fromisoformat("".join(stop.get("estimatedArrivalTime" if ank else "estimatedDepartureTime").split(".0000000")))
    delta = real_date_time - date_time

    # 1440 minutes in a day. If it's 1 min early then it says days=-1, minutes=1439.
    delay = delta.days * 1440 + math.ceil(delta.seconds/60)

    if delay >= 0:
        return date_time.strftime(f"%H:%M+{delay}")
    else:
        return date_time.strftime("%H:%M") + str(delay)

###############################

class UtilityPages:
    def __init__(self, resep: Reseplaneraren):
        self.resep = resep

    def mainPage(self):
        return send_file("static/util.html")

    def searchStop(self, args):
        if args.get("stop"):
            stop = self.resep.locations_by_text(args.get("stop")).get("results")
            stopName = stop[0].get("name")
            stopID = stop[0].get("gid")
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

        departures = self.resep.departureBoard(stopID, dateTime)

        with open("deps.json", "w") as f:
            f.write(json.dumps(departures))

        if not departures.get("results"):
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

        res = departures["results"]
        res.sort(key=lambda x: x["plannedTime"])

        html = '<!DOCTYPE html>\n<html lang="sv">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Avgångar</title>\n</head>\n<body style="font-family: sans-serif">'
        html += "<a href='/utilities'>Till sökruta</a>"
        html += f"<h2>{stopName}, {dateTime.strftime('%Y-%m-%d, %H:%M')}</h2>"
        html += "\n<table>"
        html += "\n<tr><th>Linje</th><th>Destination</th><th>TT-tid</th><th>RT-tid</th><th>Låggolv</th><th>Läge</th><th>Typ</th><th>Subtyp</th><th>Inställd</th><th>Mer info</th></tr>"
        depRows = [(
            f'\n<tr style="border: 5px solid red;">'
            f"<td style='background-color: {dep['serviceJourney']['line']['backgroundColor']}; \
                         color: {dep['serviceJourney']['line']['foregroundColor']}; \
                         text-align: center; \
                         border: 1px solid {dep['serviceJourney']['line']['borderColor']};'> \
                         {dep['serviceJourney']['line']['shortName']}</td>"
            f"<td><a href='/simpleDepInfo?ref={dep.get('detailsReference')}&gid={stopID}&ad=d'>{dep['serviceJourney']['direction']}</a></td>"
            f"<td style='text-align: center;'>{datetime.fromisoformat(''.join(dep['plannedTime'].split('.0000000'))).strftime('%H:%M')}</td>"
            f"<td style='text-align: center;'>{datetime.fromisoformat(''.join(dep['estimatedTime'].split('.0000000'))).strftime('%H:%M') if dep.get('estimatedTime') else '-'}</td>"
            f"<td style='text-align: center;'>{'♿' if dep['serviceJourney']['line']['isWheelchairAccessible'] else '❌'}</td>"
            f"<td style='text-align: center;'>{dep['stopPoint'].get('platform')}</td>"
            f"<td style='text-align: center;'>{types.get(dep['serviceJourney']['line']['transportMode'], 'mode')}</td>"
            f"<td style='text-align: center;'>{types.get(dep['serviceJourney']['line']['transportSubMode'], 'submode')}</td>"
            f"<td style='text-align: center;'>{'🔴' if dep.get('isCancelled') else '🟢'}</td>"
            f"<td style='text-align: center;'><a href='/depInfo?ref={dep.get('detailsReference')}&gid={stopID}&ad=d'>Mer info</a></td>"
            f"</tr>"
            ) for dep in res]
        
        html += "".join(depRows)
        html += "\n</table>"
        # html += f"<br><a href='/findDepartures?stop={stopName}&time={departures[-1].get('time')}&date={departures[-1].get('date')}&moreInfo=on'>Fler avgångar</a>"
        html += "\n</body>\n</html>"

        return html

    def simpleSearchStop(self, args: dict) -> str:
        if args.get("stop"):
            stop = self.resep.locations_by_text(args.get("stop")).get("results")
            stopName = stop[0].get("name")
            stopID = stop[0].get("gid")
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

        departures = self.resep.departureBoard(stopID, dateTime)

        with open("deps.json", "w") as f:
            f.write(json.dumps(departures))

        if not departures:
            return "<a href='/utilities'>Inga avgångar</a>"

        res = departures["results"]
        res.sort(key=lambda x: x["plannedTime"])
        html = '<!DOCTYPE html>\n<html lang="sv">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Avgångar</title>\n</head>\n<body style="font-family: sans-serif">'
        html += "<a href='/utilities'>Till sökruta</a>"
        html += f"<h2>{stopName} - {dateTime.strftime('%Y-%m-%d, %H:%M')}</h2>"
        html += f"<a href='/findArrivals?{'&'.join([f'{k}={v}' for k,v in args.items()])}'>Ankomster</a>"
        html += "\n<table>"
        html += "\n<tr><th>Linje</th><th>Destination</th><th>Tid</th><th>Läge</th></tr>"
        depRows = [(
            f'\n<tr style="border: 5px solid red;">'
            f"<td style='background-color: {dep['serviceJourney']['line']['backgroundColor']}; \
                         color: {dep['serviceJourney']['line']['foregroundColor']}; \
                         text-align: center; \
                         border: 1px solid {dep['serviceJourney']['line']['borderColor']};'> \
                         {dep['serviceJourney']['line']['shortName']}</td>"
            f"<td><a href='/simpleDepInfo?ref={dep.get('detailsReference')}&gid={stopID}&ad=d'>{dep['serviceJourney']['direction'].split(', Påstigning fram')[0]}</a></td>"
            f"<td style='text-align: center;'>{getDepDelay(dep)}</td>"
            f"<td style='text-align: center;'>{dep['stopPoint'].get('platform')}</td>"
            f"</tr>"
            ) for dep in res]
        
        html += "".join(depRows)
        html += "\n</table>"

        if departures["links"].get("previous"):
            pass
        if departures["links"].get("next"):
            pass
            # html += f"<br><a href='/findDepartures?stop={stopName}&time={departures[-1].get('plannedTime')}&date={departures[-1].get('date')}'>Fler avgångar</a>"
        html += "\n</body>\n</html>"

        return html

    def simpleStopArrivals(self, args: dict):
        return json.dumps(args)

    def getStyle(self, dep):
        col = dep.get("line")
        fg = col.get("foregroundColor")
        bg = col.get("backgroundColor")
        border = col.get("borderColor")
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
            f'<td rowspan="2" style="{self.getStyle(sj)}">{sj["line"]["name"]}</td>'
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
        ref = args.get("ref")
        if not ref:
            return "<a href='/utilities'>Ingen referens</a>"
        gid = args.get("gid")
        ad  = args.get("ad")
        dep = self.resep.request(ref, gid, ank=ad=="a").get("serviceJourneys")
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
        
        for sj in dep:
            html += ('<tr>\n'
                    f'<td colspan="3" style="{self.getStyle(sj)}">{sj["line"]["name"]}</td>'
                     '</tr>\n'
                     '<tr>\n'
                    f'<td colspan="3" style="{self.getStyle(sj)}">{sj["direction"]}</td>'
                     '</tr>\n')
            stops = [(
                f'<tr>'
                f'<td rowspan="2"><a href="/findDepartures'
                    f'?stopId={stop["stopPoint"]["stopArea"].get("gid")}'
                    f'&stopName={stop["stopPoint"].get("name")}'
                    f'&datetime={stop.get("plannedArrivalTime") if stop.get("plannedArrivalTime") else stop.get("plannedDepartureTime")}"'
                    f'>{stop["stopPoint"].get("name")}</a></td>'
                f'<td>{getStopDelay(stop, ank=True) if stop.get("plannedArrivalTime") else "-"}</td>'
                f'<td rowspan="2" >Läge {stop["stopPoint"].get("platform")}</td>'
                f'</tr>'
                f'<tr>'
                f'<td>{getStopDelay(stop) if stop.get("plannedDepartureTime") else "-"}</td>'
                f'</tr>'
            ) for stop in sj["callsOnServiceJourney"]]
            
            html += "\n".join(stops)
        html += "\n</table>"

        html += f'\n<a href="/map?ref={ref}&gid={gid}&ad={ad}">Karta</a>'
        html += "\n</body>\n</html>"
        
        return html

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
        line = args.get("line")
        if not ref and not line: return []
        if ref:
            return self.resep.positions(lowerLeftLat, lowerLeftLon, upperRightLat, upperRightLon, [ref])
        else:
            return self.resep.positions(lowerLeftLat, lowerLeftLon, upperRightLat, upperRightLon, lineDesignations=line)


if __name__ == "__main__":
    pass
