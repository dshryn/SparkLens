import pytest

from ai.exceptions import (
    AIPermanentError,
    AITransientError,
)
from ai.models import (
    AIConfig,
    AIExplanation,
    AIPrompt,
)
from ai.providers.base import AIProvider
from ai.providers.retrying_provider import RetryingProvider


class FakeProvider(AIProvider):
    """
    Fails twice with a transient error, then succeeds.
    """

    def __init__(self):
        super().__init__(
            AIConfig(
                api_key="test",
            )
        )
        self.calls = 0

    def generate(
        self,
        prompt: AIPrompt,
    ) -> AIExplanation:
        self.calls += 1

        if self.calls < 3:
            raise AITransientError(
                "Temporary failure."
            )

        return AIExplanation(
            summary="Success",
            explanation="Recovered after retries.",
            recommendations=[],
            insights=[],
            model="fake",
        )


class AlwaysFailProvider(AIProvider):
    """
    Always raises a transient error.
    """

    def __init__(self):
        super().__init__(
            AIConfig(
                api_key="test",
            )
        )

    def generate(
        self,
        prompt: AIPrompt,
    ) -> AIExplanation:
        raise AITransientError(
            "Temporary failure."
        )


class PermanentFailProvider(AIProvider):
    """
    Always raises a permanent error.
    """

    def __init__(self):
        super().__init__(
            AIConfig(
                api_key="test",
            )
        )
        self.calls = 0

    def generate(
        self,
        prompt: AIPrompt,
    ) -> AIExplanation:
        self.calls += 1
        raise AIPermanentError(
            "Invalid API key."
        )


def test_retry_then_success():
    provider = RetryingProvider(
        FakeProvider(),
        max_attempts=3,
        initial_delay=0,
    )

    result = provider.generate(
        AIPrompt(
            system_prompt="",
            user_prompt="",
        )
    )

    assert result.summary == "Success"


def test_retry_limit():
    provider = RetryingProvider(
        AlwaysFailProvider(),
        max_attempts=3,
        initial_delay=0,
    )

    with pytest.raises(AITransientError):
        provider.generate(
            AIPrompt(
                system_prompt="",
                user_prompt="",
            )
        )


def test_no_retry_on_permanent_error():
    provider = PermanentFailProvider()

    retrying = RetryingProvider(
        provider,
        max_attempts=5,
        initial_delay=0,
    )

    with pytest.raises(AIPermanentError):
        retrying.generate(
            AIPrompt(
                system_prompt="",
                user_prompt="",
            )
        )

    assert provider.calls == 1