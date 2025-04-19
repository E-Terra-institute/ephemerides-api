import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import pytz
from flask_cors import CORS
from utils.ephemeris_calc import (
    get_planet_positions,
    get_aspects
)

# Создание Flask-приложения с папками шаблонов и статики
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Маршрут для расчёта эфемерид
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
    # Сидерическое время для начала дня
    from utils.ephemeris_calc import get_sidereal_time
    sidereal_time = get_sidereal_time(year, month, day)

    return jsonify({
        "date": f"{year:04}-{month:02}-{day:02}",
        "sidereal_time": sidereal_time,
        "positions": positions,
        "aspects": aspects
    })

# Маршрут для конвертера сидерического времени
@app.route("/time-converter")
def time_converter():
    timezones = pytz.all_timezones
    default_lon = 30.5234  # долгота Киева
    return render_template("time_converter.html", timezones=timezones, default_lon=default_lon)

# API для конвертации локального времени в сидерическое по формуле Tзв = Tм - N + L/15 + GST - P
@app.route("/api/convert-to-sidereal")
def convert_to_sidereal():
    date_str = request.args.get("date")
    time_str = request.args.get("time")
    tz_name  = request.args.get("tz")
    lon_str  = request.args.get("lon")
    if not all([date_str, time_str, tz_name, lon_str]):
        return jsonify({"error": "Missing parameters"}), 400
    try:
        longitude = float(lon_str)
        # Парсим местное время
        local_tz = pytz.timezone(tz_name)
        naive_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        local_dt = local_tz.localize(naive_dt)
        # UTC-дата и время
        utc_dt = local_dt.astimezone(pytz.utc)

        # Tм — местное время события в часах
        Tm = naive_dt.hour + naive_dt.minute/60 + naive_dt.second/3600
        # N — номер часового пояса (смещение UTC) в часах
        offset = local_dt.utcoffset().total_seconds()/3600
        N = offset
        # L/15 — долгота в часах
        Lh = longitude / 15.0
        # GST — звездное время в полночь UTC (используем get_sidereal_time)
        from utils.ephemeris_calc import get_sidereal_time
        GST_str = get_sidereal_time(utc_dt.year, utc_dt.month, utc_dt.day)
        # переводим GST_str "HH:MM:SS" в часы
        h, m, s = map(int, GST_str.split(':'))
        GST = h + m/60 + s/3600
        # P — дополнительные поправки (считаем 0)
        P = 0

        # Tзв = Tм - N + Lh + GST - P
        Tzv_hours = (Tm - N + Lh + GST - P) % 24
        # Форматируем в HH:MM:SS
        h2 = int(Tzv_hours)
        m2 = int((Tzv_hours - h2) * 60)
        s2 = int(((Tzv_hours - h2) * 60 - m2) * 60)
        lst_str = f"{h2:02}:{m2:02}:{s2:02}"

        return jsonify({"sidereal_time": lst_str})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Список часовых поясов
@app.route("/api/timezones")
def get_timezones():
    return jsonify(pytz.all_timezones)

# Запуск
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
