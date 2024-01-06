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
        });
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

function updatePosition() {
    const checkbox = document.getElementById("showall");
    let url;
    if (checkbox.checked) {
        url = "/position?";
        for (const line of lineDesignation) {
            url += "line=" + line + "&";
        }
    } else {
        url = "/position?ref=" + args.get("ref");
    }
    fetch(url).then(response => response.json()).then(posarr => {
        const refs = posarr.map(({detailsReference}) => detailsReference);
        for (const [ref, marker] of Object.entries(posMarkers)) {
            if (!refs.includes(ref)) {
                // Remove any markers of vehicles not in the new data
                marker.remove();
                delete posMarkers[ref];
            }
        }

        if (posarr.length > 0) {
            for (const pos of posarr) {
                if (Object.keys(posMarkers).includes(pos.detailsReference)) {
                    const coords = [pos.longitude, pos.latitude];
                    posMarkers[pos.detailsReference].setLngLat(coords)
                } else {
                    createPositionMarker(pos);
                }
            }
            positionTimer = setTimeout(updatePosition, 1000);
        }
    });
}

function showLine() {
    clearTimeout(positionTimer);
    updatePosition();
}

function createPositionMarker(position) {
    const pos = [position.longitude, position.latitude];
    const emptyDiv = document.createElement("div");
    const popup = new mapboxgl.Popup()
        .setText(position.line.name + " " + position.direction);
    const marker = new mapboxgl.Marker({"scale": 0.3, "anchor": "center", "element": emptyDiv})
        .setLngLat(pos)
        .setPopup(popup)
        .addTo(map);

    marker.getElement().classList.add("position");
    if (["bus", "taxi"].includes(position.line.transportMode)) {
        marker.getElement().classList.add("bus");
    } else if (position.line.transportMode == "ferry") {
        marker.getElement().classList.add("boat");
    } else {
        marker.getElement().classList.add("tram");
    }
    posMarkers[position.detailsReference] = marker;
}

let map;
const args = new URLSearchParams(window.location.search);
let marker;
let posMarkers = {};
let positionTimer;
let lineDesignation = [];

fetch("/mapdata?ref=" + args.get("ref") + "&gid=" + args.get("gid") + "&ad=" + args.get("ad"))
.then(response => response.json())
.then(arr => {
    const titleDiv = document.getElementById("title");
    for (let sj of arr.geo) {
        const title = document.createElement("h2");
        title.innerText = sj.line.name + " " + sj.direction;
        lineDesignation.push(sj.line.name);
        title.style = "color:" +  sj.line.foregroundColor + 
        "; background-color:" + sj.line.backgroundColor +
        "; border: 1px solid " + sj.line.borderColor + ";";
        titleDiv.appendChild(title);
    }
    firstStop = arr.geo[0].serviceJourneyCoordinates[0];
    map = new mapboxgl.Map({
        container: 'map', // container ID
        style: 'mapbox://styles/mapbox/streets-v11', // style URL
        center: [firstStop.longitude, firstStop.latitude], // starting position [lng, lat]
        zoom: 12 // starting zoom
    });

    for (let [i, obj] of arr.geo.entries()) {
        addLine(map, obj.line, obj.serviceJourneyCoordinates, i);

        for (s of obj.callsOnServiceJourney) {
            addStop(map, s);
        }
    }
    map.fitBounds(getBounds(arr.geo), {padding: 20});
    
    console.log(arr.positions);
    if (arr.positions.length > 0) {
        createPositionMarker(arr.positions[0]);
        positionTimer = setTimeout(updatePosition, 1000);
    }
    });
