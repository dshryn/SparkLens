import logging
import time


from ai.exceptions import AITransientError
from ai.models import (
    AIExplanation,
    AIPrompt,
)
from ai.providers.base import AIProvider


logger = logging.getLogger(__name__)


class RetryingProvider(AIProvider):
    """
    Decorator that adds retry support to any AIProvider.

    Retries only transient failures using exponential backoff.
    """

    def __init__(
        self,
        provider: AIProvider,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
    ):
        super().__init__(provider._config)

        self._provider = provider
        self._max_attempts = max_attempts
        self._initial_delay = initial_delay
        self._backoff_multiplier = backoff_multiplier

    def generate(
        self,
        prompt: AIPrompt,
    ) -> AIExplanation:
        """
        Generates an AI explanation with retry support.
        """

        delay = self._initial_delay

        for attempt in range(1, self._max_attempts + 1):
            try:
                return self._provider.generate(prompt)

            except AITransientError:
                if attempt == self._max_attempts:
                    raise

                logger.warning(
                    "Transient AI error on attempt %d/%d. Retrying in %.1fs.",
                    attempt,
                    self._max_attempts,
                    delay,
                )

                time.sleep(delay)
                delay *= self._backoff_multiplier

        raise RuntimeError(
            "Retry loop exited unexpectedly."
        )