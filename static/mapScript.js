mapboxgl.accessToken = 'pk.eyJ1IjoiZWRkZTAwMDAiLCJhIjoiY2tqYmUyMDQ4MmgyNzJwbnZuY252bDQ0cSJ9.eyyPrOK1DmQwn9Dy4BOSGA';

function addStop(map, stopInfo) {
    const popup = new mapboxgl.Popup()
        .setText(stopInfo.stopPoint.name + ", läge " + stopInfo.stopPoint.platform);

    const marker = new mapboxgl.Marker({"scale": 0.3})
        .setLngLat([stopInfo.stopPoint.longitude, stopInfo.stopPoint.latitude])
        .setPopup(popup)
        .addTo(map);

    marker.getElement().id = "stop";
    return marker;
}

function addLine(map, color, points, i) {
    map.on("load", () => {
        map.addSource("route" + i, {
            "type": "geojson",
            "data": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": points.map(d => [d.longitude, d.latitude])
                }
            }
        });
        map.addLayer({
            'id': 'routeOutline' + i,
            'type': 'line',
            'source': 'route' + i,
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': color.foregroundColor,
                'line-width': 1.5,
                'line-gap-width': 5
            }
        })
        map.addLayer({
            'id': 'route' + i,
            'type': 'line',
            'source': 'route' + i,
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': color.backgroundColor,
                'line-width': 5
            }
        });
    });
}

function getBounds(arr) {
    const geometry = arr.map(({serviceJourneyCoordinates}) => serviceJourneyCoordinates).flat();
    const w = geometry.reduce((prev, curr) => {
        return prev < curr.longitude*1 ? prev : curr.longitude*1;
    }, Infinity);
    const n = geometry.reduce((prev, curr) => {
        return prev > curr.latitude*1 ? prev : curr.latitude*1;
    }, -Infinity);
    const e = geometry.reduce((prev, curr) => {
        return prev > curr.longitude*1 ? prev : curr.longitude*1;
    }, -Infinity);
    const s = geometry.reduce((prev, curr) => {
        return prev < curr.latitude*1 ? prev : curr.latitude*1;
    }, Infinity);
    return [w,s,e,n];
}

let map;
const args = new URLSearchParams(window.location.search);

fetch("/mapdata?ref=" + args.get("ref") + "&gid=" + args.get("gid") + "&ad=" + args.get("ad"))
    .then(response => response.json())
    .then(arr => {
        const titleDiv = document.getElementById("title");
        for (let sj of arr) {
            const title = document.createElement("h2");
            title.innerText = sj.line.name + " " + sj.direction;
            title.style = "color:" +  sj.line.foregroundColor + 
                "; background-color:" + sj.line.backgroundColor +
                "; border: 1px solid " + sj.line.borderColor + ";";
                titleDiv.appendChild(title);
        }
        firstStop = arr[0].serviceJourneyCoordinates[0];
        map = new mapboxgl.Map({
            container: 'map', // container ID
            style: 'mapbox://styles/mapbox/streets-v11', // style URL
            center: [firstStop.longitude, firstStop.latitude], // starting position [lng, lat]
            zoom: 12 // starting zoom
        });

        console.log(arr);
        for (let [i, obj] of arr.entries()) {
            addLine(map, obj.line, obj.serviceJourneyCoordinates, i);
    
            for (s of obj.callsOnServiceJourney) {
                addStop(map, s);
            }
        }
        map.fitBounds(getBounds(arr), {padding: 20});
    });
