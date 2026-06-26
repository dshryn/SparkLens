import json
from typing import NoReturn

from google import genai
from google.genai import errors, types

from ai.exceptions import (
    AIProviderError,
    AITransientError,
    AIPermanentError,
    EmptyResponseError,
    ResponseParsingError,
)

from ai.models import (
    AIConfig,
    AIExplanation,
    AIInsight,
    AIPrompt,
)

from ai.providers.base import AIProvider


class GeminiProvider(AIProvider):
    """
    Google Gemini implementation of the AIProvider interface.
    """

    TRANSIENT_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    PERMANENT_STATUS_CODES = {
        400,
        401,
        403,
        404,
    }

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
                            },
                            "insights": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "category": {
                                            "type": "STRING"
                                        },
                                        "title": {
                                            "type": "STRING"
                                        },
                                        "description": {
                                            "type": "STRING"
                                        }
                                    },
                                    "required": [
                                        "category",
                                        "title",
                                        "description",
                                    ]
                                }
                            }
                        },
                        "required": [
                            "summary",
                            "explanation",
                            "recommendations",
                            "insights",
                        ]
                    }
                )
            )

        except errors.APIError as exc:
            # Temporary debugging:
            # print(type(exc))
            # print(exc)
            # print(getattr(exc, "code", None))

            self._handle_api_error(exc)

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
                insights=[
                    AIInsight(
                        category=insight["category"],
                        title=insight["title"],
                        description=insight["description"],
                    )
                    for insight in data["insights"]
                ],
                model=self._config.model,
            )

        except KeyError as exc:
            raise ResponseParsingError(
                f"Missing field '{exc.args[0]}' in Gemini response."
            ) from exc

    def _handle_api_error(
        self,
        exc: errors.APIError,
    ) -> NoReturn:
        """
        Converts Gemini SDK errors into SparkLens-specific exceptions.
        """

        status_code = getattr(exc, "code", None)

        if status_code is None:
            status_code = getattr(exc, "status_code", None)

        message = (
            f"Gemini API request failed for model "
            f"'{self._config.model}'. "
            f"Status={status_code}. "
            f"Details={exc}"
        )

        if status_code in self.TRANSIENT_STATUS_CODES:
            raise AITransientError(message) from exc

        if status_code in self.PERMANENT_STATUS_CODES:
            raise AIPermanentError(message) from exc

        raise AIProviderError(message) from exc