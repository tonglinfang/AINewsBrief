"""X (Twitter) fetcher for AI thought leaders and organizations."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
import aiohttp
from src.models.article import Article
from src.config import settings
from src.utils.logger import get_logger
from src.utils.retry import async_retry

logger = get_logger("x_fetcher")


class XFetcher:
    """Fetches posts from X (Twitter) accounts."""

    # Priority AI thought leaders and organizations
    ACCOUNTS = {
        # AI Company Leaders
        "sama": {"name": "Sam Altman (OpenAI CEO)", "priority": 10},
        "gdb": {"name": "Greg Brockman (OpenAI)", "priority": 9},
        "danielgross": {"name": "Daniel Gross (AI Pioneer Labs)", "priority": 9},
        "karpathy": {"name": "Andrej Karpathy", "priority": 10},
        "ylecun": {"name": "Yann LeCun (Meta AI)", "priority": 9},
        "demishassabis": {"name": "Demis Hassabis (Google DeepMind)", "priority": 10},
        "JeffDean": {"name": "Jeff Dean (Google AI)", "priority": 9},
        "DrJimFan": {"name": "Jim Fan (NVIDIA)", "priority": 8},
        # AI Companies
        "OpenAI": {"name": "OpenAI", "priority": 10},
        "AnthropicAI": {"name": "Anthropic", "priority": 10},
        "GoogleAI": {"name": "Google AI", "priority": 9},
        "GoogleDeepMind": {"name": "Google DeepMind", "priority": 9},
        "MetaAI": {"name": "Meta AI", "priority": 8},
        "MistralAI": {"name": "Mistral AI", "priority": 8},
        "StabilityAI": {"name": "Stability AI", "priority": 7},
        "HuggingFace": {"name": "Hugging Face", "priority": 8},
        # AI Researchers & Influencers
        "emollick": {"name": "Ethan Mollick", "priority": 8},
        "poolio": {"name": "Patrick Ouchida", "priority": 7},
        "AndrewYNg": {"name": "Andrew Ng", "priority": 9},
        "goodfellow_ian": {"name": "Ian Goodfellow", "priority": 8},
        "fchollet": {"name": "François Chollet", "priority": 8},
        "rasbt": {"name": "Sebastian Raschka", "priority": 7},
    }

    # Nitter instances (Twitter frontend alternatives that don't require API)
    NITTER_INSTANCES = [
        "https://nitter.net",
        "https://nitter.poast.org",
        "https://nitter.privacydev.net",
        "https://nitter.cz",
    ]

    def __init__(self):
        """Initialize X fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours)
        self.max_per_account = 5  # Limit posts per account
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.current_nitter_idx = 0

    async def fetch_all(self) -> List[Article]:
        """Fetch posts from all X accounts concurrently.

        Returns:
            List of Article objects
        """
        logger.info("fetching_x_posts", accounts=len(self.ACCOUNTS))
        tasks = [
            self.fetch_account(username, info)
            for username, info in self.ACCOUNTS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for username, result in zip(self.ACCOUNTS.keys(), results):
            if isinstance(result, list):
                articles.extend(result)
                logger.info("x_fetched", account=username, count=len(result))
            elif isinstance(result, Exception):
                logger.warning("x_fetch_error", account=username, error=str(result))

        logger.info("x_total", count=len(articles))
        return articles

    @async_retry(max_attempts=3, min_wait=1.0, max_wait=10.0)
    async def fetch_account(
        self, username: str, account_info: dict
    ) -> List[Article]:
        """Fetch posts from a single X account using Nitter.

        Args:
            username: X username (without @)
            account_info: Account metadata (name, priority)

        Returns:
            List of Article objects
        """
        # Try multiple Nitter instances if one fails
        for instance in self.NITTER_INSTANCES:
            try:
                articles = await self._fetch_from_nitter(
                    instance, username, account_info
                )
                if articles:
                    return articles
            except Exception as e:
                logger.debug(
                    "nitter_instance_failed",
                    instance=instance,
                    username=username,
                    error=str(e),
                )
                continue

        logger.warning("all_nitter_instances_failed", username=username)
        return []

    async def _fetch_from_nitter(
        self, nitter_instance: str, username: str, account_info: dict
    ) -> List[Article]:
        """Fetch posts from a Nitter instance.

        Args:
            nitter_instance: Nitter instance URL
            username: X username
            account_info: Account metadata

        Returns:
            List of Article objects
        """
        url = f"{nitter_instance}/{username}/rss"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.debug(
                            "nitter_http_error",
                            instance=nitter_instance,
                            username=username,
                            status=response.status,
                        )
                        return []

                    content = await response.text()

            # Parse RSS feed from Nitter
            import feedparser

            feed = feedparser.parse(content)
            articles = []
            cutoff_time = datetime.now(timezone.utc) - self.max_age

            for entry in feed.entries[: self.max_per_account]:
                try:
                    # Parse published date - skip if no valid date
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = datetime(
                            *entry.published_parsed[:6], tzinfo=timezone.utc
                        )
                    else:
                        # No date - skip to avoid old content
                        logger.debug(
                            "x_entry_no_date",
                            username=username,
                        )
                        continue

                    if published_at < cutoff_time:
                        continue

                    # Extract post content
                    post_content = entry.get("description", "")
                    if not post_content or len(post_content) < 20:
                        continue

                    # Remove HTML tags
                    from bs4 import BeautifulSoup

                    post_text = BeautifulSoup(post_content, "html.parser").get_text()

                    # Filter: must mention AI-related keywords
                    if not self._is_ai_related(post_text):
                        continue

                    article = Article(
                        title=f"@{username}: {post_text[:100]}...",
                        url=entry.get("link", ""),
                        source=f"X - {account_info['name']}",
                        published_at=published_at,
                        content=post_text,
                        tags=["X", "Twitter", "AI"],
                        priority=account_info.get("priority", 5),
                    )
                    articles.append(article)

                except Exception as e:
                    logger.debug(
                        "x_entry_error",
                        username=username,
                        error=str(e),
                    )
                    continue

            return articles

        except Exception as e:
            logger.debug(
                "nitter_fetch_error",
                instance=nitter_instance,
                username=username,
                error=str(e),
            )
            raise

    def _is_ai_related(self, text: str) -> bool:
        """Check if post content is AI-related.

        Args:
            text: Post text content

        Returns:
            True if AI-related
        """
        text_lower = text.lower()
        ai_keywords = [
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
            "model",
            "training",
            "inference",
            "agi",
            "artificial intelligence",
            "gemini",
            "bard",
            "mistral",
            "llama",
        ]

        return any(keyword in text_lower for keyword in ai_keywords)
