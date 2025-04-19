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
      - planet_houses: номер дома для каждой планеты,
        вычисляя позиции при том же JD с учётом времени.
    """
    # 1) Переводим hsys в байты
    if isinstance(hsys, str):
        hsys = hsys.encode('ascii')

    # 2) JD с учётом UT
    ut = hour + minute/60.0 + second/3600.0
    jd = swe.julday(year, month, day, ut)

    # 3) Получаем cusps и ascmc
    cusps, ascmc = swe.houses(jd, lat, lon, hsys)
    asc = round(ascmc[0], 2)
    mc  = round(ascmc[1], 2)

    # 4) Приводим cusp к списку 12 границ
    cusp_list = list(cusps)
    if len(cusp_list) > 12:
        cusp_list = cusp_list[1:]
    n = len(cusp_list)  # должно быть 12

    # 5) Вычисляем положение каждой «планеты» (включая Lilith, Selena) в этот же момент JD
    planet_houses = {}
    for name, code in PLANETS.items():
        data, _ = swe.calc_ut(jd, code)  # геоцентрич. долгота на UT
        lon_p = data[0] % 360

        # 6) Определение дома через cusps
        house_no = None
        for i, start_raw in enumerate(cusp_list):
            start = start_raw % 360
            end   = cusp_list[(i+1) % n] % 360
            if start < end:
                if start <= lon_p < end:
                    house_no = i + 1
                    break
            else:
                # диапазон, пересекающий 0°
                if lon_p >= start or lon_p < end:
                    house_no = i + 1
                    break

        planet_houses[name] = house_no

    return {
        'asc': asc,
        'mc': mc,
        'planet_houses': planet_houses
    }
