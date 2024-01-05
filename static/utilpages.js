let timeout = null;
const stopList = document.getElementById("stoplist");
const searchBox = document.getElementById("stop");
searchBox.addEventListener("input", updateTimeout);

// Send request 750 ms after no input change
function updateTimeout() {
    clearTimeout(timeout);
    timeout = setTimeout(searchStop, 750);
}

// Get stop info from Västtrafik
function searchStop() {
    const val = searchBox.value;
    if (val == "") {
        return;
    }
    fetch("/searchstop?stop=" + val)
    .then(response => response.json())
    .then(data => displayStops(data));
}

// Add stops to a datalist element
function displayStops(data) {
    while (stopList.firstChild) {
        stopList.removeChild(stopList.lastChild);
    }

    const stops = data.results;
    console.log(stops);

    if (stops.length == 0) {
        let op = document.createElement("option");
        op.value = "Inga resultat";
        stopList.appendChild(op);
        return;
    }
    for (stop of stops) {
        let op = document.createElement("option");
        op.value = stop.name;
        stopList.appendChild(op);
    }
}
