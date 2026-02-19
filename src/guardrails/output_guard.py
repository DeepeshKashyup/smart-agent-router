"""Output safety and formatting guardrails."""

import re

from app.core.config import load_yaml_config
from app.core.logging import get_logger

logger = get_logger(__name__)


class OutputGuard:
    """Sanitizes and validates LLM output before returning to the user."""

    def __init__(self):
        config = load_yaml_config()
        guardrails = config.get("guardrails", {})
        self.max_output_length = guardrails.get("max_output_length", 4096)

    def sanitize(self, output: str) -> str:
        """Clean and validate LLM output.

        Args:
            output: Raw LLM output string.

        Returns:
            Sanitized output string.
        """
        if not output:
            return "I wasn't able to generate a response. Please try again."

        # Strip leading/trailing whitespace
        output = output.strip()

        # Remove any system-level instruction leakage
        output = self._remove_instruction_leakage(output)

        # Truncate if too long
        if len(output) > self.max_output_length:
            output = output[: self.max_output_length - 50]
            last_sentence = output.rfind(".")
            if last_sentence > len(output) * 0.8:
                output = output[: last_sentence + 1]
            output += "\n\n[Response truncated due to length.]"

        return output

    def _remove_instruction_leakage(self, text: str) -> str:
        """Remove patterns where the model leaks its system instructions."""
        patterns = [
            r"<\|system\|>.*?<\|/system\|>",
            r"\[INST\].*?\[/INST\]",
            r"<<SYS>>.*?<</SYS>>",
        ]
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.DOTALL)
        return text
