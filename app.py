import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import pytz
from flask_cors import CORS
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from utils.ephemeris_calc import get_planet_positions, get_aspects

# Инициализируем Flask
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Геокодер и определитель часового пояса
geolocator = Nominatim(user_agent="sidereal_app")
tzfinder   = TimezoneFinder()

def compute_sidereal(date_str, time_str, tz_name, longitude):
    """
    По формуле Tзв = Tм – N + L/15 + GST – P
    вычисляет локальное сидерическое время в HH:MM:SS
    """
    # Парсим местное время
    naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_tz = pytz.timezone(tz_name)
    local_dt = local_tz.localize(naive_dt)

    # UTC-дата/время
    utc_dt = local_dt.astimezone(pytz.utc)
    year, month, day = utc_dt.year, utc_dt.month, utc_dt.day
    hour, minute, second = utc_dt.hour, utc_dt.minute, utc_dt.second

    # Tм — местное время события (часа + минуты/60 + секунды/3600)
    Tm = naive_dt.hour + naive_dt.minute/60 + naive_dt.second/3600

    # N — смещение часового пояса в часах
    N = local_dt.utcoffset().total_seconds() / 3600

    # L/15 — долгота в часах
    Lh = longitude / 15.0

    # GST — сидерическое время в 0h UT (HH:MM:SS) → часы
    from utils.ephemeris_calc import get_sidereal_time
    GST_str = get_sidereal_time(year, month, day)
    h, m, s = map(int, GST_str.split(':'))
    GST = h + m/60 + s/3600

    # P — поправка нутации (пока 0)
    P = 0

    # Считаем Tзв и нормализуем в диапазон [0,24)
    Tzv = (Tm - N + Lh + GST - P) % 24
    hh = int(Tzv)
    mm = int((Tzv - hh) * 60)
    ss = int(((Tzv - hh) * 60 - mm) * 60)
    return f"{hh:02}:{mm:02}:{ss:02}"

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
    sidereal_time = compute_sidereal(f"{year:04}-{month:02}-{day:02}", "00:00", "UTC", 0)

    return jsonify({
        "date": f"{year:04}-{month:02}-{day:02}",
        "sidereal_time": sidereal_time,
        "positions": positions,
        "aspects": aspects
    })

@app.route("/time-converter")
def time_converter():
    # Рендерим форму, куда пользователь вводит город, дату и время
    return render_template("time_converter.html")

@app.route("/api/convert-to-utc")
def convert_to_utc():
    date_str = request.args.get("date")
    time_str = request.args.get("time")
    tz_name  = request.args.get("tz")
    if not all([date_str, time_str, tz_name]):
        return jsonify({"error": "Missing parameters"}), 400

    try:
        local_tz = pytz.timezone(tz_name)
        naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = local_tz.localize(naive_dt)
        utc_dt   = local_dt.astimezone(pytz.utc)
        return jsonify({"utc_time": utc_dt.strftime("%H:%M")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/timezones")
def get_timezones():
    return jsonify(pytz.all_timezones)

@app.route("/api/convert-to-sidereal")
def convert_to_sidereal():
    date_str = request.args.get("date")
    time_str = request.args.get("time")
    tz_name  = request.args.get("tz")
    lon_str  = request.args.get("lon")
    if not all([date_str, time_str, tz_name, lon_str]):
        return jsonify({"error": "Missing parameters"}), 400
    try:
        sid = compute_sidereal(date_str, time_str, tz_name, float(lon_str))
        return jsonify({"sidereal_time": sid})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/convert-by-city")
def convert_by_city():
    city     = request.args.get("city")
    date_str = request.args.get("date")
    time_str = request.args.get("time")
    if not all([city, date_str, time_str]):
        return jsonify({"error": "Missing parameters"}), 400

    # 1) Геокодируем город
    location = geolocator.geocode(city)
    if not location:
        return jsonify({"error": "City not found"}), 404
    lon, lat = location.longitude, location.latitude

    # 2) Определяем часовой пояс
    tz_name = tzfinder.timezone_at(lng=lon, lat=lat)
    if not tzfinder:
        return jsonify({"error": "Timezone not found"}), 404

    # 3) Считаем сидерическое время
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
