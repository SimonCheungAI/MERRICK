"""Bounded, structured weather lookup for conversational answers."""

from __future__ import annotations

import re

import httpx


WEATHER_QUERY_RE = re.compile(
    r"\b(?:weather|forecast|temperature|rain|snow|wind|humidity|uv\s+index)\b",
    re.IGNORECASE,
)
UNICODE_LETTER = r"[^\W\d_]"
LOCATION_CAPTURE = rf"({UNICODE_LETTER}(?:{UNICODE_LETTER}|[ .'-]){{1,79}}?)"
WEATHER_LOCATION_PATTERNS = (
    re.compile(
        r"\b(?:in|for|at|near|around)\s+"
        + LOCATION_CAPTURE +
        r"(?=\s+(?:today|tomorrow|tonight|now|right\s+now|"
        r"this\s+(?:morning|afternoon|evening|week))\b|[?!,;.]|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:weather|forecast)\s+(?:in|for)\s+"
        + LOCATION_CAPTURE +
        r"(?=\s+(?:today|tomorrow|tonight|now)\b|[?!,;.]|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:hi|hello|hey|ok|okay|alright|jarvis|[\s,])*"
        + LOCATION_CAPTURE + r"\s+(?:weather|forecast)\b",
        re.IGNORECASE,
    ),
)


def extract_weather_location(text: str) -> str | None:
    if not WEATHER_QUERY_RE.search(text):
        return None
    for pattern in WEATHER_LOCATION_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        location = re.sub(r"\s+", " ", match.group(1)).strip(" ,.!?;'")
        if 1 < len(location) <= 80:
            return location
    return None


def _weather_description(code: object) -> str:
    if not isinstance(code, (int, float)):
        return "unknown conditions"
    value = int(code)
    if value == 0:
        return "clear"
    if value in {1, 2}:
        return "mainly clear"
    if value == 3:
        return "overcast"
    if value in {45, 48}:
        return "foggy"
    if value in {51, 53, 55, 56, 57}:
        return "drizzle"
    if value in {61, 63, 65, 66, 67, 80, 81, 82}:
        return "rain"
    if value in {71, 73, 75, 77, 85, 86}:
        return "snow"
    if value in {95, 96, 99}:
        return "thunderstorms"
    return "mixed conditions"


async def fetch_weather_context(text: str) -> dict | None:
    """Fetch current/daily public weather data without opening a browser."""
    location = extract_weather_location(text)
    if not location:
        return None
    timeout = httpx.Timeout(connect=4.0, read=8.0, write=4.0, pool=4.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            geocoding = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": location, "count": 1, "language": "en", "format": "json"},
            )
            geocoding.raise_for_status()
            results = geocoding.json().get("results") or []
            if not results or not isinstance(results[0], dict):
                return None
            place = results[0]
            latitude = place.get("latitude")
            longitude = place.get("longitude")
            if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
                return None
            forecast = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": (
                        "temperature_2m,apparent_temperature,precipitation,rain,"
                        "weather_code,wind_speed_10m,relative_humidity_2m"
                    ),
                    "daily": (
                        "temperature_2m_max,temperature_2m_min,"
                        "precipitation_probability_max"
                    ),
                    "timezone": "auto",
                    "forecast_days": 2,
                },
            )
            forecast.raise_for_status()
            payload = forecast.json()
    except (httpx.HTTPError, ValueError, TypeError):
        return None

    current = payload.get("current") if isinstance(payload, dict) else None
    daily = payload.get("daily") if isinstance(payload, dict) else None
    if not isinstance(current, dict) or not isinstance(daily, dict):
        return None
    return {
        "kind": "structured_weather",
        "source": "Open-Meteo",
        "location": {
            "name": place.get("name", location),
            "admin1": place.get("admin1"),
            "country": place.get("country"),
            "timezone": payload.get("timezone"),
        },
        "current": {
            "time": current.get("time"),
            "condition": _weather_description(current.get("weather_code")),
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "precipitation_mm": current.get("precipitation"),
            "rain_mm": current.get("rain"),
            "humidity_percent": current.get("relative_humidity_2m"),
            "wind_kmh": current.get("wind_speed_10m"),
        },
        "daily": {
            "date": daily.get("time"),
            "max_c": daily.get("temperature_2m_max"),
            "min_c": daily.get("temperature_2m_min"),
            "max_precipitation_probability_percent": daily.get(
                "precipitation_probability_max"
            ),
        },
    }
