from flask import Flask
from vasttrafik import Auth, Reseplaneraren, TrafficSituations

app = Flask(__name__)

with open("credentials.txt", "r") as f:
    creds = f.readlines()

auth = Auth(creds[0].strip(), creds[1].strip(), "app")
rp = Reseplaneraren(auth)
ts = TrafficSituations(auth)

@app.route("/")
def index():
    with open("static/index.html", "r") as f:
        page = f.read()
    return page