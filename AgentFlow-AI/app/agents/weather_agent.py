from typing import Any
from app.tools.weather_tool import get_weather


def run_weather_agent(parameters: dict[str, Any]) -> dict[str, Any]:
    """Execute the weather agent with validated parameters."""
    city = parameters.get("city")
    if not isinstance(city, str) or not city.strip():
        raise ValueError("The weather agent requires a valid 'city' parameter.")

    return get_weather(city.strip())
