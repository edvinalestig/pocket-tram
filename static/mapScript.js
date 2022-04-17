mapboxgl.accessToken = 'pk.eyJ1IjoiZWRkZTAwMDAiLCJhIjoiY2tqYmUyMDQ4MmgyNzJwbnZuY252bDQ0cSJ9.eyyPrOK1DmQwn9Dy4BOSGA';

function addStop(map, stopInfo) {
    const popup = new mapboxgl.Popup()
        .setText(stopInfo.name + ", läge " + stopInfo.track);

    const marker = new mapboxgl.Marker()
        .setLngLat([stopInfo.lon, stopInfo.lat])
        .setPopup(popup)
        .addTo(map);

    marker.getElement().id = "stop";
    return marker;
}

function addLine(map, color, points) {
    map.on("load", () => {
        map.addSource("route", {
            "type": "geojson",
            "data": {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": points.map(d => [d.lon, d.lat])
                }
            }
        });
        map.addLayer({
            'id': 'route',
            'type': 'line',
            'source': 'route',
            'layout': {
                'line-join': 'round',
                'line-cap': 'round'
            },
            'paint': {
                'line-color': color,
                'line-width': 8
            }
        });
    })
}

let map;
const args = new URLSearchParams(window.location.search);
const depRef = atob(args.get("depRef"));
const geoRef = atob(args.get("geoRef"));

fetch("/mapdata?geoRef=" + geoRef + "&depRef=" + depRef)
    .then(response => response.json())
    .then(obj => {
        document.getElementById("title").innerText = obj.name;

        firstStop = obj.stops[0];

        map = new mapboxgl.Map({
            container: 'map', // container ID
            style: 'mapbox://styles/mapbox/streets-v11', // style URL
            center: [firstStop.lon, firstStop.lat], // starting position [lng, lat]
            zoom: 12 // starting zoom
        });

        console.log(obj);

        addLine(map, obj.color.bgColor, obj.geometry);

        for (s of obj.stops) {
            addStop(map, s);
        }
    });




// const l = document.createElement("a");
// l.href = "/depInfo?ref=" + depRef;
// l.innerText = "TEST";
// document.body.appendChild(l);