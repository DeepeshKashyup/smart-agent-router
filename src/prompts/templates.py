"""Prompt templates and management utilities."""

from app.core.config import load_prompts


def get_router_prompt(query: str) -> tuple[str, str]:
    """Build the router classification prompt.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    prompts = load_prompts()
    system = prompts["router"]["system"]

    few_shots = prompts["router"].get("few_shot_examples", [])
    examples = "\n".join(
        f"Query: {ex['query']}\nResponse: {ex['response']}" for ex in few_shots
    )

    user_prompt = f"Examples:\n{examples}\n\nNow classify this query:\n{query}"
    return system, user_prompt


def get_agent_prompt(query: str, context: str | None = None) -> tuple[str, str]:
    """Build the agent response prompt.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    prompts = load_prompts()
    system = prompts["agent"]["system"]
    output_format = prompts["agent"].get("output_format", "")

    if output_format:
        system += f"\n\n{output_format}"

    user_prompt = query
    if context:
        user_prompt = f"Context:\n{context}\n\nQuestion:\n{query}"

    return system, user_prompt
