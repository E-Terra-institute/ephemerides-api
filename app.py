import os
from flask import Flask, request, jsonify, render_template   # 1) добавлен render_template
from datetime import datetime                               # 2) добавлен импорт datetime
import pytz                                                 # 3) добавлен pytz

from flask_cors import CORS
from utils.ephemeris_calc import (
    get_planet_positions,
    get_aspects,
    get_sidereal_time
)

app = Flask(__name__)   # можно оставить как есть — по умолчанию ищет templates/ и static/
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

# 4) новый маршрут для страницы конвертера времени
@app.route("/time-converter")
def time_converter():
    return render_template("time_converter.html")

# 5) новый API‑эндпоинт для конвертации локального времени в UTC
@app.route("/api/convert-to-utc")
def convert_to_utc():
    date_str = request.args.get("date")
    time_str = request.args.get("time")
    tz_name  = request.args.get("tz")
    if not all([date_str, time_str, tz_name]):
        return jsonify({"error": "Missing parameters"}), 400

    try:
        local_tz = pytz.timezone(tz_name)
        local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        localized = local_tz.localize(local_dt)
        utc_dt = localized.astimezone(pytz.utc)
        return jsonify({"utc_time": utc_dt.strftime("%H:%M")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
