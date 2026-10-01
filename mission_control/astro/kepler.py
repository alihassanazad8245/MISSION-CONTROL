"""Planet positions from JPL's approximate Keplerian elements.

Uses the E.M. Standish "Keplerian Elements for Approximate Positions of the
Major Planets" table (valid 1800-2050, positions good to about an arc-minute
for the inner planets). Pure math - no downloads, works offline instantly.
"""

from __future__ import annotations

import math

from .timeutil import centuries

# name: (a, a_rate, e, e_rate, I, I_rate, L, L_rate, varpi, varpi_rate, node, node_rate)
# angles in degrees, rates per Julian century, a in AU
ELEMENTS: dict[str, tuple[float, ...]] = {
    "Mercury": (0.38709927, 0.00000037, 0.20563593, 0.00001906, 7.00497902, -0.00594749,
                252.25032350, 149472.67411175, 77.45779628, 0.16047689, 48.33076593, -0.12534081),
    "Venus": (0.72333566, 0.00000390, 0.00677672, -0.00004107, 3.39467605, -0.00078890,
              181.97909950, 58517.81538729, 131.60246718, 0.00268329, 76.67984255, -0.27769418),
    "Earth": (1.00000261, 0.00000562, 0.01671123, -0.00004392, -0.00001531, -0.01294668,
              100.46457166, 35999.37244981, 102.93768193, 0.32327364, 0.0, 0.0),
    "Mars": (1.52371034, 0.00001847, 0.09339410, 0.00007882, 1.84969142, -0.00813131,
             -4.55343205, 19140.30268499, -23.94362959, 0.44441088, 49.55953891, -0.29257343),
    "Jupiter": (5.20288700, -0.00011607, 0.04838624, -0.00013253, 1.30439695, -0.00183714,
                34.39644051, 3034.74612775, 14.72847983, 0.21252668, 100.47390909, 0.20469106),
    "Saturn": (9.53667594, -0.00125060, 0.05386179, -0.00050991, 2.48599187, 0.00193609,
               49.95424423, 1222.49362201, 92.59887831, -0.41897216, 113.66242448, -0.28867794),
    "Uranus": (19.18916464, -0.00196176, 0.04725744, -0.00004397, 0.77263783, -0.00242939,
               313.23810451, 428.48202785, 170.95427630, 0.40805281, 74.01692503, 0.04240589),
    "Neptune": (30.06992276, 0.00026291, 0.00859048, 0.00005105, 1.77004347, 0.00035372,
                -55.12002969, 218.45945325, 44.96476227, -0.32241464, 131.78422574, -0.00508664),
}

PLANETS = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]

#: General precession in ecliptic longitude, degrees per Julian century.
PRECESSION_DEG_PER_CENTURY = 1.3969713


def _solve_kepler(mean_anomaly: float, e: float) -> float:
    """Solve Kepler's equation E - e sin E = M (radians) by Newton iteration."""
    ecc = mean_anomaly + e * math.sin(mean_anomaly)
    for _ in range(12):
        delta = (ecc - e * math.sin(ecc) - mean_anomaly) / (1.0 - e * math.cos(ecc))
        ecc -= delta
        if abs(delta) < 1e-12:
            break
    return ecc


def heliocentric(name: str, jd: float) -> tuple[float, float, float]:
    """Heliocentric ecliptic (J2000) rectangular coordinates, in AU."""
    a0, a1, e0, e1, i0, i1, l0, l1, w0, w1, n0, n1 = ELEMENTS[name]
    t = centuries(jd)
    a, e = a0 + a1 * t, e0 + e1 * t
    inc = math.radians(i0 + i1 * t)
    mean_long, peri_long, node = l0 + l1 * t, w0 + w1 * t, n0 + n1 * t

    arg_peri = math.radians(peri_long - node)
    node_r = math.radians(node)
    m = math.radians((mean_long - peri_long + 180.0) % 360.0 - 180.0)
    ecc_anom = _solve_kepler(m, e)

    xp = a * (math.cos(ecc_anom) - e)
    yp = a * math.sqrt(1.0 - e * e) * math.sin(ecc_anom)

    cw, sw = math.cos(arg_peri), math.sin(arg_peri)
    cn, sn = math.cos(node_r), math.sin(node_r)
    ci, si = math.cos(inc), math.sin(inc)

    x = (cw * cn - sw * sn * ci) * xp + (-sw * cn - cw * sn * ci) * yp
    y = (cw * sn + sw * cn * ci) * xp + (-sw * sn + cw * cn * ci) * yp
    z = (sw * si) * xp + (cw * si) * yp
    return x, y, z


def heliocentric_longitude(name: str, jd: float) -> float:
    x, y, _ = heliocentric(name, jd)
    return math.degrees(math.atan2(y, x)) % 360.0


def orbital_period_years(name: str) -> float:
    return ELEMENTS[name][0] ** 1.5


def orbit_points(name: str, jd: float, count: int = 180) -> list[tuple[float, float]]:
    """Sample a full orbit (top-down x, y in AU) using the current elements."""
    a0, a1, e0, e1, i0, i1, l0, l1, w0, w1, n0, n1 = ELEMENTS[name]
    t = centuries(jd)
    a, e = a0 + a1 * t, e0 + e1 * t
    inc = math.radians(i0 + i1 * t)
    peri_long, node = w0 + w1 * t, n0 + n1 * t
    arg_peri, node_r = math.radians(peri_long - node), math.radians(node)
    cw, sw, cn, sn = math.cos(arg_peri), math.sin(arg_peri), math.cos(node_r), math.sin(node_r)
    ci = math.cos(inc)
    points = []
    for k in range(count):
        ecc_anom = 2.0 * math.pi * k / count
        xp = a * (math.cos(ecc_anom) - e)
        yp = a * math.sqrt(1.0 - e * e) * math.sin(ecc_anom)
        points.append((
            (cw * cn - sw * sn * ci) * xp + (-sw * cn - cw * sn * ci) * yp,
            (cw * sn + sw * cn * ci) * xp + (-sw * sn + cw * cn * ci) * yp,
        ))
    return points
