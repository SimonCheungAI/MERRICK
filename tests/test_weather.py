import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

import weather  # noqa: E402


class WeatherRoutingTests(unittest.IsolatedAsyncioTestCase):
    def test_location_extraction_handles_natural_questions(self) -> None:
        cases = {
            "What's the weather like in Glasgow today?": "Glasgow",
            "Hi Merrick, will it rain in New York tomorrow?": "New York",
            "Edinburgh weather today": "Edinburgh",
            "Give me the forecast for São Paulo tonight": "São Paulo",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(weather.extract_weather_location(text), expected)

    async def test_structured_weather_returns_only_bounded_fields(self) -> None:
        geocoding = AsyncMock()
        geocoding.raise_for_status = lambda: None
        geocoding.json = lambda: {
            "results": [{
                "name": "Glasgow",
                "country": "United Kingdom",
                "admin1": "Scotland",
                "latitude": 55.86,
                "longitude": -4.25,
            }]
        }
        forecast = AsyncMock()
        forecast.raise_for_status = lambda: None
        forecast.json = lambda: {
            "timezone": "Europe/London",
            "current": {
                "time": "2026-07-13T02:00",
                "temperature_2m": 13.8,
                "apparent_temperature": 12.5,
                "precipitation": 0.0,
                "rain": 0.0,
                "weather_code": 1,
                "wind_speed_10m": 10.4,
                "relative_humidity_2m": 83,
            },
            "daily": {
                "time": ["2026-07-13", "2026-07-14"],
                "temperature_2m_max": [21.3, 21.4],
                "temperature_2m_min": [13.0, 12.1],
                "precipitation_probability_max": [0, 0],
            },
        }
        client = AsyncMock()
        client.get = AsyncMock(side_effect=[geocoding, forecast])
        context_manager = AsyncMock()
        context_manager.__aenter__.return_value = client
        context_manager.__aexit__.return_value = None

        with patch.object(weather.httpx, "AsyncClient", return_value=context_manager):
            result = await weather.fetch_weather_context(
                "What's the weather like in Glasgow today?"
            )

        self.assertEqual(result["kind"], "structured_weather")
        self.assertEqual(result["source"], "Open-Meteo")
        self.assertEqual(result["location"]["name"], "Glasgow")
        self.assertEqual(result["current"]["temperature_c"], 13.8)
        self.assertEqual(result["current"]["condition"], "mainly clear")
        self.assertEqual(result["daily"]["max_c"], [21.3, 21.4])


if __name__ == "__main__":
    unittest.main()
