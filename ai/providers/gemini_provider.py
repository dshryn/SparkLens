import json

from google import genai
from google.genai import errors, types

from ai.exceptions import AIProviderError, EmptyResponseError, ResponseParsingError
from ai.models import AIConfig, AIExplanation, AIPrompt
from ai.providers.base import AIProvider


class GeminiProvider(AIProvider):
    """
    Google Gemini implementation of the AIProvider interface.
    """

    def __init__(self, config: AIConfig):
        super().__init__(config)

        self._client = genai.Client(
            api_key=self._config.api_key,
        )

    def generate(self, prompt: AIPrompt) -> AIExplanation:
        """
        Generates a structured AI explanation using Gemini.
        """

        try:
            response = self._client.models.generate_content(
                model=self._config.model,
                contents=prompt.user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=prompt.system_prompt,
                    temperature=self._config.temperature,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "summary": {
                                "type": "STRING"
                            },
                            "explanation": {
                                "type": "STRING"
                            },
                            "recommendations": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "STRING"
                                }
                            }
                        },
                        "required": [
                            "summary",
                            "explanation",
                            "recommendations"
                        ]
                    }
                )
            )

        except errors.APIError as exc:
            raise AIProviderError(
                f"Gemini API request failed for model '{self._config.model}'."
            ) from exc

        text = response.text

        if text is None or not text.strip():
            raise EmptyResponseError(
                "Gemini returned an empty response."
            )

        try:
            data = json.loads(text)

        except json.JSONDecodeError as exc:
            raise ResponseParsingError(
                "Failed to parse Gemini JSON response."
            ) from exc

        try:
            return AIExplanation(
                summary=data["summary"],
                explanation=data["explanation"],
                recommendations=data["recommendations"],
                model=self._config.model,
            )

        except KeyError as exc:
            raise ResponseParsingError(
                f"Missing field '{exc.args[0]}' in Gemini response."
            ) from exc