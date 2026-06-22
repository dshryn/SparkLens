import os

import pytest
from dotenv import load_dotenv

from ai.exceptions import AIProviderError
from ai.models import AIConfig, AIPrompt
from ai.providers.gemini_provider import GeminiProvider

load_dotenv()

pytestmark = pytest.mark.external


def test_gemini_provider():
    api_key = os.getenv("GEMINI_API_KEY")

    assert (
        api_key is not None
    ), "GEMINI_API_KEY environment variable is not set."

    provider = GeminiProvider(
        AIConfig(
            api_key=api_key,
        )
    )

    prompt = AIPrompt(
        system_prompt="You are a helpful assistant.",
        user_prompt="""
Return JSON describing Apache Spark.

Summary:
One sentence.

Explanation:
Two sentences.

Recommendations:
Exactly two recommendations.
""",
    )

    try:
        explanation = provider.generate(prompt)

    except AIProviderError as exc:
        pytest.skip(
            f"Skipping external Gemini test: {exc}"
        )

    assert explanation.summary
    assert explanation.explanation
    assert len(explanation.recommendations) == 2