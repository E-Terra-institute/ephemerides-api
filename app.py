import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.ephemeris_calc import (
    get_planet_positions,
    get_aspects,
    get_sidereal_time,
    get_houses_and_planet_houses
)

app = Flask(__name__)
CORS(app)

@app.route("/ephemerides", methods=["GET"])
def ephemerides():
    try:
        year  = int(request.args["year"])
        month = int(request.args["month"])
        day   = int(request.args["day"])
        time_str = request.args.get("time", "00:00:00")
        hour, minute, second = map(int, time_str.split(":"))
        lat = float(request.args.get("lat", 0.0))
        lon = float(request.args.get("lon", 0.0))
    except Exception:
        return jsonify({
            "error": "Укажи year, month, day, time (HH:MM:SS), lat и lon"
        }), 400

    positions     = get_planet_positions(year, month, day)
    aspects       = get_aspects(positions)
    sidereal_time = get_sidereal_time(year, month, day)
    houses_info   = get_houses_and_planet_houses(
        year, month, day, hour, minute, second, lat, lon
    )

    return jsonify({
        "date": f"{year:04}-{month:02}-{day:02}",
        "sidereal_time": sidereal_time,
        "positions": positions,
        "aspects": aspects,
        "asc": houses_info['asc'],
        "mc": houses_info['mc'],
        "planet_houses": houses_info['planet_houses']
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
