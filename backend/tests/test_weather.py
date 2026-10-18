import pytest

from app import weather
from test_api import client, fake  # noqa: F401  (fixtures)


@pytest.fixture
def nws(monkeypatch):
    """A pretend api.weather.gov: records the URLs asked for."""
    calls = []
    reply = {
        "/points/": {"properties": {"observationStations": "https://api.weather.gov/gridpoints/X/1,1/stations",
                                    "forecastHourly": "https://api.weather.gov/gridpoints/X/1,1/forecast/hourly",
                                    "relativeLocation": {"properties": {"city": "Los Angeles"}}}},
        "/stations": {"features": [{"properties": {"stationIdentifier": "KCQT"}}]},
        "/observations/latest": {"properties": {"textDescription": "Light Rain and Fog/Mist",
                                                "windSpeed": {"value": 33.5}, "windDirection": {"value": 270},
                                                "temperature": {"value": 15}}},
    }

    def get(url):
        calls.append(url)
        for k, v in sorted(reply.items(), key=lambda kv: -len(kv[0])):
            if k in url:
                return v
        raise OSError("offline")
    weather._points.clear(); weather._now.clear()
    monkeypatch.setattr(weather, "_get_json", get)
    yield calls, reply
    weather._points.clear(); weather._now.clear()


def test_words_become_weather():
    assert weather.sky_of("Thunderstorms and Rain") == "storm"
    assert weather.sky_of("Light Snow") == "snow"
    assert weather.sky_of("Rain Showers") == "rain"
    assert weather.sky_of("Fog/Mist") == "fog"
    assert weather.sky_of("Partly Cloudy") == "partly"
    assert weather.sky_of("Mostly Cloudy") == "cloudy"
    assert weather.sky_of("Sunny") == "clear"
    assert weather.wind_of(35) == "windy" and weather.wind_of(20) == "breezy" and weather.wind_of(5) == "calm"
    assert weather.wind_of(None, "Breezy") == "breezy"


def test_the_states_weather_now(client, nws):
    calls, _ = nws
    r = client.get("/weather/CA")
    assert r.status_code == 200
    assert r.json() == {"sky": "rain", "wind": "windy", "wind_from": 270, "temp_f": 59,
                        "text": "Light Rain and Fog/Mist", "place": "Los Angeles"}
    assert "/points/34.05,-118.24" in calls[0]
    # Cached: asking again doesn't go back to the weather service.
    n = len(calls)
    client.get("/weather/CA")
    assert len(calls) == n


def test_near_the_player_but_rounded(client, nws):
    calls, _ = nws
    w = client.get("/weather/CA", params={"lat": 37.7749, "lon": -122.4194}).json()
    assert "/points/37.8,-122.4" in calls[0]
    assert w["near"] is True
    assert "near" not in client.get("/weather/CA").json()
    # Somewhere outside the state: the state's city instead.
    weather._now.clear()
    client.get("/weather/CA", params={"lat": 40.7, "lon": -74.0})
    assert any("/points/34.05,-118.24" in c for c in calls)


def test_the_forecast_when_the_station_is_quiet(client, nws):
    _, reply = nws
    reply["/observations/latest"] = {"properties": {"textDescription": ""}}
    reply["/forecast/hourly"] = {"properties": {"periods": [{
        "shortForecast": "Slight Chance Rain Showers", "probabilityOfPrecipitation": {"value": 20},
        "windSpeed": "5 to 10 mph", "windDirection": "SW", "temperature": 61}]}}
    w = client.get("/weather/CA").json()
    assert (w["sky"], w["wind"], w["wind_from"], w["temp_f"]) == ("cloudy", "calm", 225, 61)


def test_no_weather_when_offline(client, monkeypatch):
    weather._now.clear(); weather._points.clear()
    monkeypatch.setattr(weather, "_get_json", lambda url: (_ for _ in ()).throw(OSError("offline")))
    r = client.get("/weather/NC")
    assert r.status_code == 200 and r.json() is None
    assert client.get("/weather/ZZ").status_code == 404


def test_too_many_spots_fall_back_to_the_city(client, nws):
    calls, _ = nws
    for i in range(25):
        client.get("/weather/CA", params={"lat": 32.5 + i * .35, "lon": -117})
    assert any("/points/34.05,-118.24" in c for c in calls)
