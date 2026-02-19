"""Input validation and filtering guardrails."""

from app.core.config import load_yaml_config
from app.core.logging import get_logger

logger = get_logger(__name__)


class InputGuardError(ValueError):
    """Raised when input fails guardrail validation."""


class InputGuard:
    """Validates and filters incoming queries before processing."""

    def __init__(self):
        config = load_yaml_config()
        guardrails = config.get("guardrails", {})
        self.max_input_length = guardrails.get("max_input_length", 10000)
        self.blocked_topics = guardrails.get("blocked_topics", [])

    def validate(self, query: str) -> str:
        """Validate the input query against guardrail rules.

        Args:
            query: The raw user query.

        Returns:
            The validated query string.

        Raises:
            InputGuardError: If the query violates any guardrail.
        """
        if not query or not query.strip():
            raise InputGuardError("Query cannot be empty.")

        if len(query) > self.max_input_length:
            raise InputGuardError(
                f"Query exceeds maximum length of {self.max_input_length} characters."
            )

        # Check for obvious prompt injection patterns
        injection_patterns = [
            "ignore previous instructions",
            "ignore all instructions",
            "disregard your instructions",
            "you are now",
            "new instructions:",
        ]
        query_lower = query.lower()
        for pattern in injection_patterns:
            if pattern in query_lower:
                logger.warning("prompt_injection_detected", pattern=pattern)
                raise InputGuardError("Query contains disallowed patterns.")

        return query.strip()
