import swisseph as swe

# Путь к папке с .se1‑файлами
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
    'Lilith':     swe.MEAN_APOG,
    'Selena':     swe.OSCU_APOG
}

# Аспекты и орбис
ASPECTS = {
    'Conjunction': 0,
    'Opposition': 180,
    'Trine': 120,
    'Square': 90
}
ORB = 6

def get_planet_positions(year: int, month: int, day: int) -> dict:
    jd = swe.julday(year, month, day)
    positions = {}
    for name, code in PLANETS.items():
        data, _ = swe.calc_ut(jd, code)
        positions[name] = round(data[0], 2)
    return positions

def get_sidereal_time(year: int, month: int, day: int) -> float:
    jd = swe.julday(year, month, day)
    st_deg = swe.sidtime(jd)       # градусы
    return round(st_deg / 15.0, 4)  # перевод в часы

def get_aspects(positions: dict) -> list:
    aspects = []
    names = list(positions.keys())
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            p1, p2 = names[i], names[j]
            diff = abs((positions[p1] - positions[p2]) % 360)
            angle = diff if diff <= 180 else 360 - diff
            for asp, deg in ASPECTS.items():
                if abs(angle - deg) <= ORB:
                    aspects.append({
                        "between": [p1, p2],
                        "aspect": asp,
                        "angle": round(angle, 2)
                    })
    return aspects

def get_houses_and_planet_houses(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    lat: float,
    lon: float,
    hsys: str = 'P'
) -> dict:
    """
    Возвращает:
      - asc, mc: сидерический асцендент и среднее небо
      - planet_houses: номер дома для каждой планеты
    """
    # Если передали str, конвертируем в байты
    if isinstance(hsys, str):
        hsys = hsys.encode('ascii')

    # Юлианская дата с учётом времени UT
    ut = hour + minute/60.0 + second/3600.0
    jd = swe.julday(year, month, day, ut)

    # cusps[1..12] — границы домов, ascmc[0]=Asc, ascmc[1]=MC
    cusps, ascmc = swe.houses(jd, lat, lon, hsys)
    asc = round(ascmc[0], 2)
    mc  = round(ascmc[1], 2)

    # Определяем дом для каждой планеты
    planet_positions = get_planet_positions(year, month, day)
    planet_houses = {}
    for name, lon_p in planet_positions.items():
        L = lon_p % 360
        house = None
        for i in range(1, 13):
            start = cusps[i] % 360
            # для домов 1–11 берем следующий элемент,
            # для 12‑го дома — возвращаемся к первому cusp
            if i < 12:
                end = cusps[i+1] % 360
            else:
                end = cusps[1] % 360

            if start < end:
                if start <= L < end:
                    house = i
                    break
            else:
                # дом пересекает 0° эклиптики
                if L >= start or L < end:
                    house = i
                    break

        planet_houses[name] = house

    return {
        'asc': asc,
        'mc': mc,
        'planet_houses': planet_houses
    }
