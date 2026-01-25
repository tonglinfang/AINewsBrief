"""RSS feed fetcher for AI news sources."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
import feedparser
from src.models.article import Article
from src.config import settings


class RSSFetcher:
    """Fetches articles from RSS feeds."""

    RSS_FEEDS = {
        "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
        "The Verge AI": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "AI News": "https://artificialintelligence-news.com/feed/",
    }

    def __init__(self):
        """Initialize RSS fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours)
        self.max_per_source = settings.max_articles_per_source

    async def fetch_all(self) -> List[Article]:
        """Fetch articles from all RSS sources concurrently.

        Returns:
            List of Article objects
        """
        tasks = [self.fetch_feed(name, url) for name, url in self.RSS_FEEDS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                print(f"Error fetching RSS feed: {result}")

        return articles

    async def fetch_feed(self, source_name: str, feed_url: str) -> List[Article]:
        """Fetch articles from a single RSS feed.

        Args:
            source_name: Name of the source
            feed_url: RSS feed URL

        Returns:
            List of Article objects
        """
        try:
            # Run feedparser in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, feed_url)

            articles = []
            cutoff_time = datetime.now(timezone.utc) - self.max_age

            for entry in feed.entries[: self.max_per_source]:
                try:
                    # Parse published date
                    published_at = self._parse_date(entry)
                    if published_at < cutoff_time:
                        continue

                    # Extract content
                    content = self._extract_content(entry)
                    if not content or len(content) < 100:
                        continue

                    article = Article(
                        title=entry.get("title", "").strip(),
                        url=entry.get("link", ""),
                        source=source_name,
                        published_at=published_at,
                        content=content,
                        tags=self._extract_tags(entry),
                    )
                    articles.append(article)

                except Exception as e:
                    print(f"Error parsing entry from {source_name}: {e}")
                    continue

            return articles

        except Exception as e:
            print(f"Error fetching feed {source_name}: {e}")
            return []

    def _parse_date(self, entry: dict) -> datetime:
        """Parse publication date from feed entry."""
        import email.utils

        date_str = entry.get("published", entry.get("updated", ""))
        if date_str:
            parsed = email.utils.parsedate_to_datetime(date_str)
            if parsed:
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)

        return datetime.now(timezone.utc)

    def _extract_content(self, entry: dict) -> str:
        """Extract content from feed entry."""
        # Try different content fields
        if hasattr(entry, "content") and entry.content:
            return entry.content[0].get("value", "")

        if hasattr(entry, "summary"):
            return entry.summary

        if hasattr(entry, "description"):
            return entry.description

        return ""

    def _extract_tags(self, entry: dict) -> List[str]:
        """Extract tags from feed entry."""
        tags = []

        if hasattr(entry, "tags"):
            tags.extend([tag.get("term", "") for tag in entry.tags])

        # Add default AI tag
        tags.append("AI")

        return [tag for tag in tags if tag]
