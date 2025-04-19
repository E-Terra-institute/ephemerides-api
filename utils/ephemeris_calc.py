# utils/ephemeris_calc.py

import swisseph as swe

# Указываем папку с файлами эфемерид (загруженными в ephe/)
swe.set_ephe_path('./ephe')

# Список планет и фиктивных точек
PLANETS = {
    'Sun':        swe.SUN,
    'Moon':       swe.MOON,
    'Mercury':    swe.MERCURY,
    'Venus':      swe.VENUS,
    'Mars':       swe.MARS,
    'Saturn':     swe.SATURN,
    'Uranus':     swe.URANUS,
    'Pluto':      swe.PLUTO,
    'True Node':  swe.TRUE_NODE,
    'Lilith':     swe.MEAN_APOG,   # Средний лилит
    'Selena':     swe.OSCU_APOG    # Осциллирующий апогей ("белая луна")
}

# Определяем аспекты и их идеальные градусы
ASPECTS = {
    'Conjunction': 0,
    'Opposition': 180,
    'Trine': 120,
    'Square': 90
}

ORB = 6  # Допуск в градусах для определения аспекта

def get_planet_positions(year: int, month: int, day: int) -> dict:
    """
    Рассчитывает геоцентрические долготы всех точек на заданную дату.
    Возвращает словарь {название: долгота (°)}.
    """
    jd = swe.julday(year, month, day)
    positions = {}
    for name, code in PLANETS.items():
        data, _ = swe.calc_ut(jd, code)
        lon = data[0]  # первая позиция — долготa в градусах
        positions[name] = round(lon, 2)
    return positions

def get_sidereal_time(year: int, month: int, day: int) -> float:
    """
    Возвращает сидерическое время (UT) в часах.
    pyswisseph.swe.sidtime даёт сидерическое время в градусах (0–360°).
    Делим на 15, чтобы получить часы (360° → 24 ч).
    """
    jd = swe.julday(year, month, day)
    st_deg = swe.sidtime(jd)      # сидерическое время в градусах
    st_hours = st_deg / 15.0      # переводим градусы в часы
    return round(st_hours, 4)

def get_aspects(positions: dict) -> list:
    """
    Ищет все важные аспекты между планетами в словаре positions.
    Возвращает список словарей:
      {
        "between": [name1, name2],
        "aspect": "Square",
        "angle": 89.50
      }
    """
    aspects = []
    names = list(positions.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p1, p2 = names[i], names[j]
            a1, a2 = positions[p1], positions[p2]
            diff = abs((a1 - a2) % 360)
            angle = diff if diff <= 180 else 360 - diff
            for asp_name, asp_deg in ASPECTS.items():
                if abs(angle - asp_deg) <= ORB:
                    aspects.append({
                        "between": [p1, p2],
                        "aspect": asp_name,
                        "angle": round(angle, 2)
                    })
    return aspects
