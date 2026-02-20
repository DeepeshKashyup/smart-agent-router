"""LLM provider abstraction with cost tracking."""

from dataclasses import dataclass

import tiktoken
from langchain_google_vertexai import ChatVertexAI

from app.core.config import get_settings, load_yaml_config
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""

    content: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float


class LLMClient:
    """Unified LLM client with model routing and cost estimation."""

    def __init__(self):
        self.settings = get_settings()
        self.config = load_yaml_config()
        self._models: dict[str, ChatVertexAI] = {}
        self._tokenizer = tiktoken.get_encoding("cl100k_base")

    def _get_model(self, tier: str) -> ChatVertexAI:
        """Get or create a model instance for the given tier."""
        if tier not in self._models:
            model_config = self.config["models"][tier]
            self._models[tier] = ChatVertexAI(
                model_name=model_config["name"],
                temperature=model_config["temperature"],
                max_output_tokens=model_config["max_tokens"],
                top_p=model_config["top_p"],
                project=self.settings.google_cloud_project,
                location=self.settings.vertex_ai_location,
            )
        return self._models[tier]

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a text string."""
        return len(self._tokenizer.encode(text))

    def estimate_cost(self, tier: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for a model call."""
        model_config = self.config["models"][tier]
        input_cost = (input_tokens / 1000) * model_config.get("cost_per_1k_input", 0)
        output_cost = (output_tokens / 1000) * model_config.get("cost_per_1k_output", 0)
        return round(input_cost + output_cost, 6)

    async def invoke(self, tier: str, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Invoke an LLM at the specified tier and return a structured response.

        Args:
            tier: Model tier - 'large', 'small', or 'router'.
            prompt: The user prompt.
            system_prompt: Optional system-level instructions.

        Returns:
            LLMResponse with content, token counts, and cost estimate.
        """
        model = self._get_model(tier)

        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("human", prompt))

        input_tokens = self.estimate_tokens(system_prompt + prompt)

        logger.info("llm_invoke", tier=tier, model=self.config["models"][tier]["name"], input_tokens=input_tokens)

        response = await model.ainvoke(messages)
        content = response.content

        output_tokens = self.estimate_tokens(content)
        total_tokens = input_tokens + output_tokens
        cost = self.estimate_cost(tier, input_tokens, output_tokens)

        logger.info("llm_response", tier=tier, output_tokens=output_tokens, cost_usd=cost)

        return LLMResponse(
            content=content,
            model_name=self.config["models"][tier]["name"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=cost,
        )
