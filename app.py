import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import pytz
from flask_cors import CORS
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from utils.ephemeris_calc import (
    get_planet_positions,
    get_aspects,
    get_sidereal_time
)
from calendar import monthrange

# Инициализация Flask
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Инициализация геокодера и определителя часового пояса
geolocator = Nominatim(user_agent="sidereal_app")
tzfinder = TimezoneFinder()

# Функция вычисления местного сидерического времени
def compute_sidereal(date_str, time_str, tz_name, longitude):
    naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(tz_name)
    local_dt = local_tz.localize(naive_dt)
    utc_dt = local_dt.astimezone(pytz.utc)

    year, month, day = utc_dt.year, utc_dt.month, utc_dt.day
    Tm = naive_dt.hour + naive_dt.minute / 60 + naive_dt.second / 3600
    N = local_dt.utcoffset().total_seconds() / 3600
    Lh = longitude / 15.0
    GST = get_sidereal_time(year, month, day)
    P = 0

    Tzv = (Tm - N + Lh + GST - P) % 24

    h = int(Tzv)
    m = int((Tzv - h) * 60)
    s = int(((Tzv - h) * 60 - m) * 60)
    return f"{h:02}:{m:02}:{s:02}"

# Главная страница (проверка API)
@app.route("/")
def home():
    return "E-Terra Ephemerides API працює!"

# Страница конвертера времени
@app.route("/time-converter")
def time_converter():
    return render_template("time_converter.html")

# Расчёт эфемерид на ОДИН день
@app.route("/ephemerides", methods=["GET"])
def ephemerides():
    try:
        year = int(request.args["year"])
        month = int(request.args["month"])
        day = int(request.args["day"])
    except Exception:
        return jsonify({"error": "Укажи year, month и day числом"}), 400

    positions = get_planet_positions(year, month, day)
    aspects = get_aspects(positions)
    sidereal_time = get_sidereal_time(year, month, day)

    return jsonify({
        "date": f"{year:04}-{month:02}-{day:02}",
        "sidereal_time": sidereal_time,
        "positions": positions,
        "aspects": aspects
    })

# Расчёт эфемерид на ВЕСЬ месяц
@app.route("/ephemeris", methods=["GET"])
def ephemeris_month():
    try:
        year = int(request.args["year"])
        month = int(request.args["month"])
    except Exception:
        return jsonify({"error": "Укажи year и month числом"}), 400

    days_in_month = monthrange(year, month)[1]
    results = []

    for day in range(1, days_in_month + 1):
        positions = get_planet_positions(year, month, day)
        aspects = get_aspects(positions)
        sidereal_time = get_sidereal_time(year, month, day)

        results.append({
            "date": f"{year:04}-{month:02}-{day:02}",
            "sidereal_time": sidereal_time,
            "positions": positions,
            "aspects": aspects
        })

    return jsonify(results)

# Конвертация локального времени в UTC
@app.route("/api/convert-to-utc")
def convert_to_utc():
    date_str = request.args.get("date")
    time_str = request.args.get("time")
    tz_name = request.args.get("tz")
    if not all([date_str, time_str, tz_name]):
        return jsonify({"error": "Missing parameters"}), 400
    try:
        local_tz = pytz.timezone(tz_name)
        naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = local_tz.localize(naive_dt)
        utc_dt = local_dt.astimezone(pytz.utc)
        return jsonify({"utc_time": utc_dt.strftime("%H:%M")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Список часовых поясов
@app.route("/api/timezones")
def get_timezones():
    return jsonify(pytz.all_timezones)

# Конвертация в сидерическое время по координатам
@app.route("/api/convert-to-sidereal")
def convert_to_sidereal():
    date_str = request.args.get("date")
    time_str = request.args.get("time")
    tz_name = request.args.get("tz")
    lon_str = request.args.get("lon")
    if not all([date_str, time_str, tz_name, lon_str]):
        return jsonify({"error": "Missing parameters"}), 400
    try:
        sid = compute_sidereal(date_str, time_str, tz_name, float(lon_str))
        return jsonify({"sidereal_time": sid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Конвертация в сидерическое время по городу
@app.route("/api/convert-by-city")
def convert_by_city():
    city = request.args.get("city")
    date_str = request.args.get("date")
    time_str = request.args.get("time")
    if not all([city, date_str, time_str]):
        return jsonify({"error": "Missing parameters"}), 400
    location = geolocator.geocode(city)
    if not location:
        return jsonify({"error": "City not found"}), 404
    lon, lat = location.longitude, location.latitude
    tz_name = tzfinder.timezone_at(lng=lon, lat=lat)
    if not tz_name:
        return jsonify({"error": "Timezone not found"}), 404
    try:
        sid = compute_sidereal(date_str, time_str, tz_name, lon)
        return jsonify({
            "city": city,
            "timezone": tz_name,
            "longitude": lon,
            "sidereal_time": sid
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Запуск
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
