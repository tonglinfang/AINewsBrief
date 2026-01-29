"""RSS feed fetcher for AI news sources."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
import aiohttp
import feedparser
from src.models.article import Article
from src.config import settings
from src.utils.logger import get_logger
from src.utils.retry import async_retry
from src.utils.feed_utils import extract_feed_content, parse_feed_date

logger = get_logger("rss_fetcher")


class RSSFetcher:
    """Fetches articles from RSS feeds."""

    RSS_FEEDS = {
        "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
        "The Verge AI": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "AI News": "https://artificialintelligence-news.com/feed/",
        # Additional high-quality sources
        "Ars Technica AI": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
        "The Information AI": "https://www.theinformation.com/feed",
    }

    def __init__(self):
        """Initialize RSS fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours)
        self.max_per_source = settings.max_articles_per_source
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def fetch_all(self) -> List[Article]:
        """Fetch articles from all RSS sources concurrently.

        Returns:
            List of Article objects
        """
        logger.info("fetching_rss_feeds", sources=len(self.RSS_FEEDS))
        tasks = [self.fetch_feed(name, url) for name, url in self.RSS_FEEDS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for name, result in zip(self.RSS_FEEDS.keys(), results):
            if isinstance(result, list):
                articles.extend(result)
                logger.info("rss_fetched", source=name, count=len(result))
            elif isinstance(result, Exception):
                logger.warning("rss_fetch_error", source=name, error=str(result))

        logger.info("rss_total", count=len(articles))
        return articles

    @async_retry(max_attempts=3, min_wait=1.0, max_wait=10.0)
    async def fetch_feed(self, source_name: str, feed_url: str) -> List[Article]:
        """Fetch articles from a single RSS feed.

        Args:
            source_name: Name of the source
            feed_url: RSS feed URL

        Returns:
            List of Article objects
        """
        try:
            # Fetch with aiohttp for better timeout control
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(feed_url) as response:
                    if response.status != 200:
                        logger.warning(
                            "rss_http_error",
                            source=source_name,
                            status=response.status,
                        )
                        return []
                    content = await response.text()

            # Parse feed
            feed = feedparser.parse(content)

            articles = []
            cutoff_time = datetime.now(timezone.utc) - self.max_age

            for entry in feed.entries[: self.max_per_source]:
                try:
                    # Parse published date - skip if date cannot be parsed
                    published_at = parse_feed_date(entry)
                    if published_at is None:
                        logger.debug(
                            "rss_entry_no_date",
                            source=source_name,
                            title=entry.get("title", "")[:50],
                        )
                        continue
                    if published_at < cutoff_time:
                        continue

                    # Extract content
                    entry_content = extract_feed_content(entry)
                    if not entry_content or len(entry_content) < 100:
                        continue

                    article = Article(
                        title=entry.get("title", "").strip(),
                        url=entry.get("link", ""),
                        source=source_name,
                        published_at=published_at,
                        content=entry_content,
                        tags=self._extract_tags(entry),
                    )
                    articles.append(article)

                except Exception as e:
                    logger.debug(
                        "rss_entry_error",
                        source=source_name,
                        error=str(e),
                    )
                    continue

            return articles

        except Exception as e:
            logger.warning("rss_feed_error", source=source_name, error=str(e))
            return []

    def _extract_tags(self, entry: dict) -> List[str]:
        """Extract tags from feed entry."""
        tags = []

        if hasattr(entry, "tags"):
            tags.extend([tag.get("term", "") for tag in entry.tags])

        # Add default AI tag
        tags.append("AI")

        return [tag for tag in tags if tag]
