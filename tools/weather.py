"""
tools/weather.py
Get current weather for Birmingham AL (Em's home base) or any city.
No API key required — uses open-meteo.com free API.
Usage: python tools/weather.py
       from tools.weather import get_weather; print(get_weather())
"""
import urllib.request
import urllib.parse
import json

# Birmingham AL coordinates
DEFAULT_LAT = 33.5186
DEFAULT_LON = -86.8104
DEFAULT_CITY = "Birmingham, AL"

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 71: "Light snow", 73: "Snow",
    75: "Heavy snow", 77: "Snow grains", 80: "Light showers", 81: "Showers",
    82: "Heavy showers", 85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Heavy thunderstorm with hail"
}

def get_weather(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON, city: str = DEFAULT_CITY) -> str:
    """Return a one-line weather summary for the given coordinates."""
    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m,relative_humidity_2m",
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "timezone": "America/Chicago"
    })
    url = f"https://api.open-meteo.com/v1/forecast?{params}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return f"ERROR fetching weather: {e}"

    c = data.get("current", {})
    code = c.get("weather_code", 0)
    desc = WEATHER_CODES.get(code, "Unknown")
    temp = c.get("temperature_2m", "?")
    feels = c.get("apparent_temperature", "?")
    wind = c.get("wind_speed_10m", "?")
    humidity = c.get("relative_humidity_2m", "?")

    return (f"{city}: {desc}, {temp}°F (feels like {feels}°F), "
            f"wind {wind} mph, humidity {humidity}%")

if __name__ == "__main__":
    print(get_weather())
