class AIError(Exception):
    """
    Base exception for all AI-related errors in SparkLens.
    """

    pass


class AIProviderError(AIError):
    """
    Raised when communication with an AI provider fails.
    """

    pass


class AITransientError(AIProviderError):
    """
    Raised when a provider failure is temporary and retryable.
    Examples:
    - 429 Rate Limit
    - 500 Internal Server Error
    - 502 Bad Gateway
    - 503 Service Unavailable
    - 504 Gateway Timeout
    """

    pass


class AIPermanentError(AIProviderError):
    """
    Raised when a provider failure is permanent and should not be retried.
    Examples:
    - Invalid API key
    - Invalid model
    - Permission issues
    - Malformed request
    """

    pass


class EmptyResponseError(AIError):
    """
    Raised when the AI provider returns an empty response.
    """

    pass


class ResponseParsingError(AIError):
    """
    Raised when an AI response cannot be parsed into the expected format.
    """

    pass