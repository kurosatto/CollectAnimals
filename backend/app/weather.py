"""The weather outside right now, for the habitat scene (rain, snow, fog, wind).

From the US National Weather Service (api.weather.gov: free, no key, public
domain). Each state's weather is a big city's, unless the player's phone shares
roughly where they are (rounded to a tenth of a degree, about 10 km, before
it's used or cached). Answers are cached, and anything that goes wrong just means
no weather in the scene.
"""

from __future__ import annotations

import json
import re
import threading
import time
import urllib.request

API = "https://api.weather.gov"
USER_AGENT = "CaptureAnimals (github.com/kurosatto/CollectAnimals)"
TTL = 15 * 60
FAIL_TTL = 5 * 60

# A big city in each state: [lat, lon].
CITIES = {
    "AL": (33.52, -86.81), "AK": (61.22, -149.90), "AZ": (33.45, -112.07), "AR": (34.75, -92.29),
    "CA": (34.05, -118.24), "CO": (39.74, -104.99), "CT": (41.76, -72.68), "DE": (39.74, -75.55),
    "FL": (28.54, -81.38), "GA": (33.75, -84.39), "HI": (21.31, -157.86), "ID": (43.62, -116.20),
    "IL": (41.88, -87.63), "IN": (39.77, -86.16), "IA": (41.59, -93.62), "KS": (37.69, -97.34),
    "KY": (38.25, -85.76), "LA": (29.95, -90.07), "ME": (43.66, -70.26), "MD": (39.29, -76.61),
    "MA": (42.36, -71.06), "MI": (42.33, -83.05), "MN": (44.98, -93.27), "MS": (32.30, -90.18),
    "MO": (39.10, -94.58), "MT": (45.78, -108.50), "NE": (41.26, -95.93), "NV": (36.17, -115.14),
    "NH": (42.99, -71.46), "NJ": (40.74, -74.17), "NM": (35.08, -106.65), "NY": (40.71, -74.01),
    "NC": (35.23, -80.84), "ND": (46.88, -96.79), "OH": (39.96, -83.00), "OK": (35.47, -97.52),
    "OR": (45.52, -122.68), "PA": (39.95, -75.17), "RI": (41.82, -71.41), "SC": (34.00, -81.03),
    "SD": (43.54, -96.73), "TN": (36.16, -86.78), "TX": (29.76, -95.37), "UT": (40.76, -111.89),
    "VT": (44.48, -73.21), "VA": (37.54, -77.44), "WA": (47.61, -122.33), "WV": (38.35, -81.63),
    "WI": (43.04, -87.91), "WY": (41.14, -104.82),
}

_lock = threading.Lock()
_points: dict[tuple[float, float], dict | None] = {}
_now: dict[tuple[float, float], tuple[float, dict | None]] = {}


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json"})
    with urllib.request.urlopen(req, timeout=6) as r:
        return json.load(r)


def spot(state: str, lat: float | None, lon: float | None, bounds: dict | None) -> tuple[float, float] | None:
    """Where to look: the player's rounded position if it's in the state, else the state's city."""
    if lat is not None and lon is not None and bounds and \
            bounds["south"] <= lat <= bounds["north"] and bounds["west"] <= lon <= bounds["east"]:
        return round(lat, 1), round(lon, 1)
    return CITIES.get(state.upper())


def sky_of(text: str) -> str:
    """clear, partly, cloudy, fog, rain, storm or snow, from words like "Light Rain and Fog"."""
    t = text.lower()
    if re.search(r"thunder|t-storm|tstorm", t):
        return "storm"
    if re.search(r"snow|sleet|flurr|blizzard|ice pellets|freezing|wintry", t):
        return "snow"
    if re.search(r"rain|shower|drizzle", t):
        return "rain"
    if re.search(r"fog|mist|haze|smoke", t):
        return "fog"
    if re.search(r"partly|few clouds|scattered", t):
        return "partly"
    if re.search(r"cloud|overcast", t):
        return "cloudy"
    return "clear"


def wind_of(kmh: float | None, text: str = "") -> str:
    if (kmh or 0) >= 30 or re.search(r"windy|blustery", text.lower()):
        return "windy"
    if (kmh or 0) >= 18 or "breezy" in text.lower():
        return "breezy"
    return "calm"


def _mph_to_kmh(s: str) -> float | None:
    """"10 mph" or "5 to 15 mph" -> km/h of the top speed."""
    nums = [float(n) for n in re.findall(r"\d+", s or "")]
    return max(nums) * 1.609 if nums else None


def _point(where: tuple[float, float]) -> dict | None:
    if where not in _points:
        p = _get_json(f"{API}/points/{where[0]},{where[1]}")["properties"]
        stations = _get_json(p["observationStations"])["features"]
        _points[where] = {
            "city": (p.get("relativeLocation") or {}).get("properties", {}).get("city"),
            "hourly": p.get("forecastHourly"),
            "station": stations[0]["properties"]["stationIdentifier"] if stations else None,
        }
        if len(_points) > 2000:
            _points.pop(next(iter(_points)))
    return _points[where]


def _observe(p: dict) -> dict | None:
    """The station's latest report, if it's recent and says what the sky is doing."""
    if not p["station"]:
        return None
    o = _get_json(f"{API}/stations/{p['station']}/observations/latest")["properties"]
    text = o.get("textDescription") or ""
    if not text:
        return None
    wind = max((o.get("windSpeed") or {}).get("value") or 0, ((o.get("windGust") or {}).get("value") or 0) * .7)
    temp = (o.get("temperature") or {}).get("value")
    return {"text": text, "kmh": wind, "from": (o.get("windDirection") or {}).get("value"),
            "temp_f": round(temp * 9 / 5 + 32) if temp is not None else None}


def _forecast(p: dict) -> dict | None:
    """This hour's forecast, when the station has nothing to say."""
    if not p["hourly"]:
        return None
    hour = _get_json(p["hourly"])["properties"]["periods"][0]
    text = hour.get("shortForecast") or ""
    # "Slight Chance Rain Showers" means it probably isn't raining.
    if re.match(r"(slight )?chance", text.lower()) and \
            ((hour.get("probabilityOfPrecipitation") or {}).get("value") or 0) < 50:
        text = "Cloudy"
    dirs = "N NNE NE ENE E ESE SE SSE S SSW SW WSW W WNW NW NNW".split()
    d = hour.get("windDirection")
    return {"text": text, "kmh": _mph_to_kmh(hour.get("windSpeed")),
            "from": dirs.index(d) * 22.5 if d in dirs else None, "temp_f": hour.get("temperature")}


def current(where: tuple[float, float]) -> dict | None:
    """{sky, wind, wind_from, temp_f, text, place} for a spot, or None when unknown."""
    with _lock:
        hit = _now.get(where)
        if hit and time.time() < hit[0]:
            return hit[1]
    try:
        p = _point(where)
        w = _observe(p) or _forecast(p)
        out = w and {"sky": sky_of(w["text"]), "wind": wind_of(w["kmh"], w["text"]),
                     "wind_from": w["from"], "temp_f": w["temp_f"], "text": w["text"], "place": p["city"]}
    except Exception:  # noqa: BLE001 - no weather is fine
        out = None
    with _lock:
        _now[where] = (time.time() + (TTL if out else FAIL_TTL), out)
        if len(_now) > 2000:
            _now.pop(next(iter(_now)))
    return out
