import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.ephemeris_calc import (
    get_planet_positions,
    get_aspects,
    get_sidereal_time
)

app = Flask(__name__)
CORS(app)

@app.route("/ephemerides", methods=["GET"])
def ephemerides():
    try:
        year  = int(request.args["year"])
        month = int(request.args["month"])
        day   = int(request.args["day"])
    except Exception:
        return jsonify({"error": "Укажи year, month и day числом"}), 400

    positions     = get_planet_positions(year, month, day)
    aspects       = get_aspects(positions)
    sidereal_time = get_sidereal_time(year, month, day)

    return jsonify({
        "date": f"{year:04}-{month:02}-{day:02}",
        "sidereal_time": sidereal_time,
        "positions": positions,
        "aspects": aspects
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
