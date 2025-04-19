import swisseph as swe

swe.set_ephe_path('./ephe')

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

ASPECTS = {
    'Conjunction': 0,
    'Opposition': 180,
    'Trine': 120,
    'Square': 90
}

ORB = 6

def get_planet_positions(year, month, day):
    jd = swe.julday(year, month, day)
    pos = {}
    for name, code in PLANETS.items():
        data, _ = swe.calc_ut(jd, code)
        pos[name] = round(data[0], 2)
    return pos

def get_sidereal_time(year, month, day):
    jd = swe.julday(year, month, day)
    return round(swe.sidereal_time(jd), 4)

def get_aspects(positions):
    result = []
    names = list(positions)
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a, b = positions[names[i]], positions[names[j]]
            diff = abs((a - b) % 360)
            angle = diff if diff <= 180 else 360 - diff
            for asp, deg in ASPECTS.items():
                if abs(angle - deg) <= ORB:
                    result.append({
                        "between": [names[i], names[j]],
                        "aspect": asp,
                        "angle": round(angle, 2)
                    })
    return result
