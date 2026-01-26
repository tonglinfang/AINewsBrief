"""Fetcher for official AI company blogs."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from bs4 import BeautifulSoup
import aiohttp

from src.models.article import Article
from src.config import settings
from src.utils.logger import get_logger
from src.utils.retry import async_retry, RETRYABLE_EXCEPTIONS

logger = get_logger("blog_fetcher")


class BlogFetcher:
    """Fetches articles from official AI company blogs."""

    # Official AI company blogs with their RSS feeds or web pages
    BLOG_SOURCES = {
        "OpenAI Blog": {
            "type": "rss",
            "url": "https://openai.com/blog/rss.xml",
            "priority": 10,  # High priority for major announcements
        },
        "Anthropic Blog": {
            "type": "web",
            "url": "https://www.anthropic.com/news",
            "selector": "article",
            "priority": 10,
        },
        "Google AI Blog": {
            "type": "rss",
            "url": "https://blog.google/technology/ai/rss/",
            "priority": 9,
        },
        "DeepMind Blog": {
            "type": "rss",
            "url": "https://deepmind.google/blog/rss.xml",
            "priority": 9,
        },
        "Meta AI Blog": {
            "type": "rss",
            "url": "https://ai.meta.com/blog/rss/",
            "priority": 8,
        },
        "Hugging Face Blog": {
            "type": "rss",
            "url": "https://huggingface.co/blog/feed.xml",
            "priority": 7,
        },
        "Stability AI Blog": {
            "type": "web",
            "url": "https://stability.ai/news",
            "selector": "article",
            "priority": 7,
        },
    }

    def __init__(self):
        """Initialize blog fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours)
        self.max_per_source = settings.max_articles_per_source
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def fetch_all(self) -> List[Article]:
        """Fetch articles from all blog sources concurrently.

        Returns:
            List of Article objects sorted by priority
        """
        logger.info("fetching_blogs", sources=len(self.BLOG_SOURCES))

        tasks = []
        for name, config in self.BLOG_SOURCES.items():
            if config["type"] == "rss":
                tasks.append(self._fetch_rss(name, config))
            else:
                tasks.append(self._fetch_web(name, config))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for i, (name, result) in enumerate(zip(self.BLOG_SOURCES.keys(), results)):
            if isinstance(result, list):
                articles.extend(result)
                logger.info("blog_fetched", source=name, count=len(result))
            elif isinstance(result, Exception):
                logger.warning("blog_fetch_error", source=name, error=str(result))

        # Sort by priority (higher priority sources first)
        articles.sort(
            key=lambda a: self.BLOG_SOURCES.get(a.source, {}).get("priority", 0),
            reverse=True,
        )

        logger.info("blogs_total", count=len(articles))
        return articles

    @async_retry(max_attempts=3, min_wait=2.0, max_wait=15.0)
    async def _fetch_rss(self, source_name: str, config: dict) -> List[Article]:
        """Fetch articles from an RSS feed.

        Args:
            source_name: Name of the source
            config: Source configuration

        Returns:
            List of Article objects
        """
        import feedparser

        url = config["url"]

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.warning(
                        "rss_http_error", source=source_name, status=response.status
                    )
                    return []
                content = await response.text()

        # Parse feed
        feed = feedparser.parse(content)
        articles = []
        cutoff_time = datetime.now(timezone.utc) - self.max_age

        for entry in feed.entries[: self.max_per_source]:
            try:
                published_at = self._parse_feed_date(entry)
                if published_at < cutoff_time:
                    continue

                content = self._extract_feed_content(entry)
                if not content or len(content) < 50:
                    content = entry.get("title", "") + ". " + entry.get("summary", "")

                article = Article(
                    title=entry.get("title", "").strip(),
                    url=entry.get("link", ""),
                    source=source_name,
                    published_at=published_at,
                    content=content[:3000],
                    tags=["Official Blog", "AI"],
                )
                articles.append(article)

            except Exception as e:
                logger.debug("entry_parse_error", source=source_name, error=str(e))
                continue

        return articles

    @async_retry(max_attempts=2, min_wait=3.0, max_wait=10.0)
    async def _fetch_web(self, source_name: str, config: dict) -> List[Article]:
        """Fetch articles by scraping a web page.

        Args:
            source_name: Name of the source
            config: Source configuration

        Returns:
            List of Article objects
        """
        url = config["url"]
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; AINewsBrief/1.0; +https://github.com/AINewsBrief)"
        }

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.warning(
                        "web_http_error", source=source_name, status=response.status
                    )
                    return []
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        articles = []
        cutoff_time = datetime.now(timezone.utc) - self.max_age

        # Try to find article elements
        article_elements = soup.select(config.get("selector", "article"))[:self.max_per_source]

        for element in article_elements:
            try:
                # Extract title
                title_el = element.select_one("h1, h2, h3, .title, [class*='title']")
                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue

                # Extract link
                link_el = element.select_one("a[href]")
                if link_el:
                    article_url = link_el.get("href", "")
                    if article_url.startswith("/"):
                        from urllib.parse import urljoin
                        article_url = urljoin(url, article_url)
                else:
                    continue

                # Extract date
                date_el = element.select_one("time, .date, [class*='date']")
                if date_el:
                    date_str = date_el.get("datetime") or date_el.get_text(strip=True)
                    published_at = self._parse_web_date(date_str)
                else:
                    published_at = datetime.now(timezone.utc)

                if published_at < cutoff_time:
                    continue

                # Extract summary/content
                summary_el = element.select_one("p, .summary, .excerpt, [class*='summary']")
                content = summary_el.get_text(strip=True) if summary_el else title

                article = Article(
                    title=title,
                    url=article_url,
                    source=source_name,
                    published_at=published_at,
                    content=content[:2000],
                    tags=["Official Blog", "AI"],
                )
                articles.append(article)

            except Exception as e:
                logger.debug("element_parse_error", source=source_name, error=str(e))
                continue

        return articles

    def _parse_feed_date(self, entry: dict) -> datetime:
        """Parse date from feed entry."""
        import email.utils

        date_str = entry.get("published", entry.get("updated", ""))
        if date_str:
            try:
                parsed = email.utils.parsedate_to_datetime(date_str)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except Exception:
                pass

        # Try struct_time format
        for field in ["published_parsed", "updated_parsed"]:
            if hasattr(entry, field) and getattr(entry, field):
                import time
                try:
                    ts = time.mktime(getattr(entry, field))
                    return datetime.fromtimestamp(ts, tz=timezone.utc)
                except Exception:
                    pass

        return datetime.now(timezone.utc)

    def _parse_web_date(self, date_str: str) -> datetime:
        """Parse date from web page element."""
        from dateutil import parser as date_parser

        try:
            parsed = date_parser.parse(date_str)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    def _extract_feed_content(self, entry: dict) -> str:
        """Extract content from feed entry."""
        if hasattr(entry, "content") and entry.content:
            return entry.content[0].get("value", "")

        if hasattr(entry, "summary"):
            return entry.summary

        if hasattr(entry, "description"):
            return entry.description

        return ""
