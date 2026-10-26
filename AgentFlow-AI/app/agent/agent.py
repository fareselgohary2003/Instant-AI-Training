
import json

from app.agent.llm import get_llm_response
from app.tools.email_tool import send_email
from app.tools.weather_tool import get_weather
from app.tools.text_analysis_tool import analyze_text


SYSTEM_PROMPT = """
You are an AI Task Execution Agent.

Identify the user's intent and extract parameters from their actual request.

Available intents:
- email: send an email. Required: recipient, subject, body.
- weather: get current weather. Required: city.
- text_analysis: analyze text. Required: text.
- none: general questions or unsupported requests.

Return ONLY a valid JSON object:
{
  "intent": "email | weather | text_analysis | none",
  "parameters": {},
  "message": "Brief explanation"
}

Rules:
- Never invent missing information.
- For email, extract recipient, subject, and body.
- For weather, extract the city.
- For text analysis, extract the exact text to analyze.
- If information is missing, leave the parameter out and explain what is needed.
"""


def understand_request(user_input: str) -> dict:
    """Classify a request and extract its parameters using the LLM."""

    if not isinstance(user_input, str) or not user_input.strip():
        raise ValueError("User input cannot be empty.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input.strip()},
    ]

    response = get_llm_response(messages)

    try:
        result = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The AI returned an invalid JSON response."
        ) from exc

    allowed_intents = {"email", "weather", "text_analysis", "none"}

    if not isinstance(result, dict):
        raise ValueError("The AI response must be a JSON object.")

    if result.get("intent") not in allowed_intents:
        raise ValueError("The AI returned an unsupported intent.")

    if not isinstance(result.get("parameters"), dict):
        raise ValueError("The AI parameters must be a JSON object.")

    return result


def execute_request(user_input: str) -> dict:
    """Understand a request, execute the matching tool, and return its result."""

    intent_data = understand_request(user_input)
    intent = intent_data["intent"]
    parameters = intent_data["parameters"]

    if intent == "email":
        required = ("recipient", "subject", "body")
        missing = [key for key in required if not parameters.get(key)]

        if missing:
            return {
                "success": False,
                "intent": intent,
                "message": (
                    "Missing required email information: "
                    + ", ".join(missing)
                ),
            }

        result = send_email(
            recipient=parameters["recipient"],
            subject=parameters["subject"],
            body=parameters["body"],
        )

    elif intent == "weather":
        city = parameters.get("city")

        if not isinstance(city, str) or not city.strip():
            return {
                "success": False,
                "intent": intent,
                "message": "Please provide a city name.",
            }

        result = get_weather(city)

    elif intent == "text_analysis":
        text = parameters.get("text")

        if not isinstance(text, str) or not text.strip():
            return {
                "success": False,
                "intent": intent,
                "message": "Please provide the text you want to analyze.",
            }

        result = analyze_text(text)

    else:
        return {
            "success": True,
            "intent": "none",
            "message": intent_data.get(
                "message",
                "I can help with email, weather, and text analysis.",
            ),
        }

    return {
        "success": True,
        "intent": intent,
        "message": "Request completed successfully.",
        "result": result,
    }
