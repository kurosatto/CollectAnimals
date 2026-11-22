"""The weather outside right now, for the habitat scene (rain, snow, fog, wind).

From the US National Weather Service (api.weather.gov: free, no key, public
domain) for US states, and from MET Norway (api.met.no: free, CC BY 4.0, credit
"Weather data from MET Norway") for European countries, whose codes have three
letters. Each state's weather is a big city's (a country's is its capital's), unless the player's phone shares
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
MET = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
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

# A European country's capital: (lat, lon, name), from Natural Earth's populated places.
CAPITALS = {
    "ALB": (41.33, 19.82, "Tirana"), "AUT": (48.20, 16.36, "Vienna"), "BLR": (53.90, 27.56, "Minsk"),
    "BEL": (50.84, 4.33, "Brussels"), "BIH": (43.85, 18.38, "Sarajevo"), "BGR": (42.69, 23.31, "Sofia"),
    "HRV": (45.80, 16.00, "Zagreb"), "CYP": (35.17, 33.37, "Nicosia"), "CZE": (50.09, 14.46, "Prague"),
    "DNK": (55.68, 12.56, "Copenhagen"), "EST": (59.43, 24.73, "Tallinn"), "FIN": (60.18, 24.93, "Helsinki"),
    "FRA": (48.87, 2.33, "Paris"), "DEU": (52.52, 13.40, "Berlin"), "GRC": (37.99, 23.73, "Athens"),
    "HUN": (47.50, 19.08, "Budapest"), "ISL": (64.15, -21.95, "Reykjavík"), "IRL": (53.34, -6.25, "Dublin"),
    "ITA": (41.90, 12.48, "Rome"), "XKX": (42.67, 21.17, "Pristina"), "LVA": (56.95, 24.10, "Riga"),
    "LTU": (54.68, 25.32, "Vilnius"), "LUX": (49.61, 6.13, "Luxembourg"), "MLT": (35.90, 14.51, "Valletta"),
    "MDA": (47.01, 28.86, "Chișinău"), "MNE": (42.47, 19.27, "Podgorica"), "NLD": (52.35, 4.91, "Amsterdam"),
    "MKD": (42.00, 21.43, "Skopje"), "NOR": (59.92, 10.75, "Oslo"), "POL": (52.25, 21.00, "Warsaw"),
    "PRT": (38.72, -9.15, "Lisbon"), "ROU": (44.44, 26.10, "Bucharest"), "RUS": (55.75, 37.61, "Moscow"),
    "SRB": (44.82, 20.47, "Belgrade"), "SVK": (48.15, 17.12, "Bratislava"), "SVN": (46.06, 14.51, "Ljubljana"),
    "ESP": (40.40, -3.69, "Madrid"), "SWE": (59.35, 18.10, "Stockholm"), "CHE": (46.92, 7.47, "Bern"),
    "TUR": (39.93, 32.86, "Ankara"), "UKR": (50.44, 30.51, "Kyiv"), "GBR": (51.50, -0.12, "London"),
}

_lock = threading.Lock()
_points: dict[tuple[float, float], dict | None] = {}
_now: dict[tuple[float, float], tuple[float, dict | None]] = {}


def _get_json(url: str, accept: str = "application/geo+json") -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=6) as r:
        return json.load(r)


def home(state: str) -> tuple[float, float] | None:
    """The state's big city, or the country's capital."""
    st = state.upper()
    return CITIES.get(st) or (CAPITALS[st][:2] if st in CAPITALS else None)


def spot(state: str, lat: float | None, lon: float | None, bounds: dict | None) -> tuple[float, float] | None:
    """Where to look: the player's rounded position if it's in the state, else the state's city."""
    if lat is not None and lon is not None and bounds and \
            bounds["south"] <= lat <= bounds["north"] and bounds["west"] <= lon <= bounds["east"]:
        return round(lat, 1), round(lon, 1)
    return home(state)


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


# MET Norway's symbol codes ("lightrainshowers_day") in words ("Light Rain Showers").
_MET_WORDS = {"clearsky": "Clear", "fair": "Mostly Clear", "partlycloudy": "Partly Cloudy",
              "cloudy": "Cloudy", "fog": "Fog", "light": "Light", "heavy": "Heavy", "rain": "Rain",
              "sleet": "Sleet", "snow": "Snow", "showers": "Showers", "and": "and", "thunder": "Thunder"}


def met_words(symbol: str) -> str:
    base = (symbol or "").split("_")[0]
    found = re.findall(r"clearsky|fair|partlycloudy|cloudy|fog|light|heavy|rain|sleet|snow|showers|and|thunder", base)
    return " ".join(_MET_WORDS[w] for w in found)


def _met(where: tuple[float, float]) -> dict | None:
    """MET Norway's forecast for this hour (europe: no station reports to read)."""
    d = _get_json(f"{MET}?lat={where[0]:.2f}&lon={where[1]:.2f}", "application/json")
    now = d["properties"]["timeseries"][0]["data"]
    text = met_words(((now.get("next_1_hours") or {}).get("summary") or {}).get("symbol_code", ""))
    if not text:
        return None
    det = now["instant"]["details"]
    ms, temp = det.get("wind_speed"), det.get("air_temperature")
    return {"text": text, "kmh": ms * 3.6 if ms is not None else None, "from": det.get("wind_from_direction"),
            "temp_f": round(temp * 9 / 5 + 32) if temp is not None else None,
            "temp_c": round(temp) if temp is not None else None}


def current(where: tuple[float, float], state: str = "") -> dict | None:
    """{sky, wind, wind_from, temp_f, text, place} for a spot, or None when unknown.

    A European country's (three-letter code) also has temp_c and comes from MET Norway."""
    st = state.upper()
    with _lock:
        hit = _now.get(where)
        if hit and time.time() < hit[0]:
            return hit[1]
    try:
        if st in CAPITALS:
            w = _met(where)
            p = {"city": CAPITALS[st][2] if where == home(st) else None}
        else:
            p = _point(where)
            w = _observe(p) or _forecast(p)
        out = w and {"sky": sky_of(w["text"]), "wind": wind_of(w["kmh"], w["text"]),
                     "wind_from": w["from"], "temp_f": w["temp_f"], "text": w["text"], "place": p["city"]}
        if out and "temp_c" in w:
            out["temp_c"] = w["temp_c"]
    except Exception:  # noqa: BLE001 - no weather is fine
        out = None
    with _lock:
        _now[where] = (time.time() + (TTL if out else FAIL_TTL), out)
        if len(_now) > 2000:
            _now.pop(next(iter(_now)))
    return out
