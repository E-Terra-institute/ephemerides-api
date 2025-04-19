import swisseph as swe

# Путь к папке с .se1‑файлами
swe.set_ephe_path('./ephe')

# Список планет и фиктивных точек (без Selena)
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
    'Ліліт':     swe.MEAN_APOG
}

def get_planet_positions(year: int, month: int, day: int) -> dict:
    """
    Геоцентрические долготы планет + Ліліт и Selena (Ліліт + 180°).
    """
    jd = swe.julday(year, month, day)
    positions = {}

    # 1) базовые планеты + Lilith
    for name, code in PLANETS.items():
        data, _ = swe.calc_ut(jd, code)
        positions[name] = round(data[0] % 360, 2)

    # 2) Selena как оппозиция к Lilith
    if 'Ліліт' in positions:
        positions['Selena'] = round((positions['Lilith'] + 180) % 360, 2)

    return positions

# Аспекты и орбис
ASPECTS = {
    'Conjunction': 0,
    'Opposition': 180,
    'Trine': 120,
    'Square': 90
}
ORB = 6

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
