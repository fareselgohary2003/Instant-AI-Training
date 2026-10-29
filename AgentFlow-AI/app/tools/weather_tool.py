
import httpx


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(city: str) -> dict:
    """Retrieve current weather for a city using Open-Meteo."""

    if not isinstance(city, str) or not city.strip():
        raise ValueError("City name must not be empty.")

    try:
        with httpx.Client(timeout=15.0) as client:
            geo_response = client.get(
                GEOCODING_URL,
                params={
                    "name": city.strip(),
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
            )
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            locations = geo_data.get("results", [])

            if not locations:
                raise ValueError(
                    f"Could not find a city named '{city}'."
                )

            location = locations[0]

            weather_response = client.get(
                WEATHER_URL,
                params={
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "current": (
                        "temperature_2m,"
                        "relative_humidity_2m,"
                        "apparent_temperature,"
                        "weather_code,"
                        "wind_speed_10m"
                    ),
                    "timezone": "auto",
                },
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()

    except httpx.TimeoutException as exc:
        raise RuntimeError("The weather service timed out.") from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            "The weather service returned an error."
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(
            "Could not connect to the weather service."
        ) from exc

    current = weather_data.get("current")

    if not current:
        raise RuntimeError("Current weather data is unavailable.")

    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        80: "Rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }

    code = current.get("weather_code")

    return {
        "city": location["name"],
        "country": location.get("country", "Unknown"),
        "temperature_c": current.get("temperature_2m"),
        "feels_like_c": current.get("apparent_temperature"),
        "conditions": weather_codes.get(code, "Unknown conditions"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "observed_at": current.get("time"),
    }
