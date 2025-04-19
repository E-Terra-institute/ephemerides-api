import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import pytz
from flask_cors import CORS
from utils.ephemeris_calc import (
    get_planet_positions,
    get_aspects,
    get_sidereal_time
)

# Создание Flask-приложения с папками шаблонов и статики
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Существующий маршрут для расчёта эфемерид
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

# Маршрут для отображения страницы конвертера времени
@app.route("/time-converter")
def time_converter():
    # Передаём в шаблон полный список IANA-часовых поясов
    timezones = pytz.all_timezones
    return render_template("time_converter.html", timezones=timezones)

# API-эндпоинт для конвертации локального времени в UTC
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

# API-эндпоинт для конвертации локального времени в сидерическое время
@app.route("/api/convert-to-sidereal")
def convert_to_sidereal():
    date_str = request.args.get("date")
    time_str = request.args.get("time")
    tz_name  = request.args.get("tz")
    if not all([date_str, time_str, tz_name]):
        return jsonify({"error": "Missing parameters"}), 400
    try:
        # Локальное время -> UTC
        local_tz = pytz.timezone(tz_name)
        local_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        localized = local_tz.localize(local_dt)
        utc_dt = localized.astimezone(pytz.utc)
        # Вычисляем сидерическое время через библиотеку
        sidereal = get_sidereal_time(
            utc_dt.year, utc_dt.month, utc_dt.day,
            utc_dt.hour, utc_dt.minute
        )
        return jsonify({"sidereal_time": sidereal})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API-эндпоинт для получения списка часовых поясов
@app.route("/api/timezones")
def get_timezones():
    return jsonify(pytz.all_timezones)

# Запуск сервера
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
