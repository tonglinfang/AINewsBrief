"""Shared AI content filtering utilities."""

# Common AI-related keywords for content filtering
AI_KEYWORDS = frozenset([
    "ai",
    "gpt",
    "llm",
    "claude",
    "chatgpt",
    "openai",
    "anthropic",
    "machine learning",
    "deep learning",
    "neural network",
    "transformer",
    "diffusion",
    "stable diffusion",
    "midjourney",
    "generative",
    "artificial intelligence",
    "gemini",
    "mistral",
    "llama",
    "computer vision",
    "nlp",
    "natural language",
    "reinforcement learning",
    "agi",
    "bard",
    "model",
    "training",
    "inference",
])


def is_ai_related(text: str) -> bool:
    """Check if text content is AI-related.

    Args:
        text: Text content to check

    Returns:
        True if text contains AI-related keywords
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in AI_KEYWORDS)
