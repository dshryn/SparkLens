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