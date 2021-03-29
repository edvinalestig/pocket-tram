let place;
let departures;
const choicebox = document.getElementById("setup");
const depbox = document.getElementById("departures");
const title = document.getElementById("title");
const places = {
    "chalmers": "Chalmers",
    "lgh": "Lägenheten",
    "markland": "Marklandsgatan",
    "jt": "Järntorget",
    "huset": "Huset",
    "lindholmen": "Lindholmen",
    "kungssten": "Kungssten",
    "centrum": "Centrum",
    "vasaplatsen": "Vasaplatsen"
}

function reset() {
    killChildren(depbox);
    choicebox.classList.remove("hide");
    title.innerHTML = "Välj plats";
}

function choose(p) {
    place = p;
    title.innerHTML = places[place];
    choicebox.classList.add("hide");
    getDepartures();
}

function killChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function addDeparture(obj) {
    console.log(obj);
    createComment(obj.comment);
    for (let box of Object.keys(obj.stops)) {
        createBox(box, obj.stops[box]);
    }
    for (let disr of obj.ts) {
        createDisrBox(disr);
    }
}

function createBox(title, contents) {
    let box = document.createElement("div");
    depbox.appendChild(box);
    let h3 = document.createElement("h3");
    h3.innerHTML = title;
    h3.classList.add("grouptitle");
    box.appendChild(h3);

    for (let d of contents) {
        times = d.time;
        let row = createRow(
            d.line, d.dest, times[0], (times.length > 1) ? times[1]:"", 
            (times.length > 2) ? times[2]:"", "background-color: " + 
            d.fgColor + "; color: " + d.bgColor + ";");
        box.appendChild(row);
    }

}

function createRow(line, dir, d1, d2, d3, style) {
    let row = document.createElement("tr");
    let td1 = document.createElement("td");
    let td2 = document.createElement("td");
    let td3 = document.createElement("td");
    let td4 = document.createElement("td");
    let td5 = document.createElement("td");
    td1.innerHTML = line;
    td2.innerHTML = dir;
    td3.innerHTML = d1;
    td4.innerHTML = d2;
    td5.innerHTML = d3;
    td1.classList.add("line");
    td2.classList.add("direction");
    td3.classList.add("time");
    td4.classList.add("time");
    td5.classList.add("time");
    td1.style = style;
    row.appendChild(td1);
    row.appendChild(td2);
    row.appendChild(td3);
    row.appendChild(td4);
    row.appendChild(td5);
    return row;
}

function createDisrBox(disruption) {
    let box = document.createElement("div");
    depbox.appendChild(box);
    let title = document.createElement("h3");
    let description = document.createElement("p");
    title.textContent = disruption.title;
    description.textContent = disruption.description;
    title.classList.add("disrTitle");
    description.classList.add("disrDescription");
    box.appendChild(title);
    box.appendChild(description);
}

function createComment(comment) {
    if (comment) {
        let box = document.createElement("div");
        depbox.appendChild(box);
        let c = document.createElement("p");
        c.textContent = comment;
        c.classList.add("comment");
        box.appendChild(c);
    }
}

function getDepartures() {
    let xhr = new XMLHttpRequest();
    xhr.open("GET", "/request?place="+place);
    xhr.onload = () => {
        departures = xhr.response
        addDeparture(xhr.response);
    }
    xhr.responseType = "json";
    xhr.send();
}