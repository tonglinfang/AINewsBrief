"""API-based fetchers for Reddit and HackerNews with improved content extraction."""

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import aiohttp
from bs4 import BeautifulSoup

from src.models.article import Article
from src.config import settings
from src.utils.logger import get_logger
from src.utils.retry import async_retry

logger = get_logger("api_fetcher")


class RedditFetcher:
    """Fetches AI-related posts from Reddit."""

    SUBREDDITS = [
        "MachineLearning",
        "artificial",
        "ArtificialInteligence",
        "LocalLLaMA",
        "ChatGPT",
        "ClaudeAI",
        "singularity",
    ]

    def __init__(self):
        """Initialize Reddit fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours)
        self.max_per_subreddit = 10
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def fetch_all(self) -> List[Article]:
        """Fetch posts from all subreddits.

        Returns:
            List of Article objects
        """
        logger.info("fetching_reddit", subreddits=len(self.SUBREDDITS))

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [self.fetch_subreddit(session, subreddit) for subreddit in self.SUBREDDITS]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for subreddit, result in zip(self.SUBREDDITS, results):
            if isinstance(result, list):
                articles.extend(result)
                if result:
                    logger.info("reddit_fetched", subreddit=subreddit, count=len(result))
            elif isinstance(result, Exception):
                logger.warning("reddit_fetch_error", subreddit=subreddit, error=str(result))

        logger.info("reddit_total", count=len(articles))
        return articles

    @async_retry(max_attempts=3, min_wait=2.0, max_wait=15.0)
    async def fetch_subreddit(self, session: aiohttp.ClientSession, subreddit: str) -> List[Article]:
        """Fetch hot posts from a subreddit using Reddit JSON API.

        Args:
            session: aiohttp session
            subreddit: Subreddit name

        Returns:
            List of Article objects
        """
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        params = {"limit": self.max_per_subreddit * 2}  # Over-fetch for filtering
        headers = {"User-Agent": settings.reddit_user_agent}

        async with session.get(url, params=params, headers=headers) as response:
            if response.status != 200:
                logger.warning(
                    "reddit_http_error",
                    subreddit=subreddit,
                    status=response.status,
                )
                return []

            data = await response.json()

        articles = []
        cutoff_time = datetime.now(timezone.utc) - self.max_age

        for post in data.get("data", {}).get("children", []):
            if len(articles) >= self.max_per_subreddit:
                break

            post_data = post.get("data", {})

            # Skip stickied posts
            if post_data.get("stickied"):
                continue

            # Parse timestamp
            created_utc = post_data.get("created_utc", 0)
            published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)

            if published_at < cutoff_time:
                continue

            # Extract content
            title = post_data.get("title", "").strip()
            selftext = post_data.get("selftext", "")
            external_url = post_data.get("url", "")

            # Skip if no meaningful content
            if not title:
                continue

            # Build content from available sources
            content_parts = []
            if selftext and len(selftext) > 50:
                content_parts.append(selftext[:1500])

            # Add score and engagement metrics
            score = post_data.get("score", 0)
            num_comments = post_data.get("num_comments", 0)
            if score > 100 or num_comments > 50:
                content_parts.append(f"Score: {score}, Comments: {num_comments}")

            content = "\n\n".join(content_parts) if content_parts else title

            article = Article(
                title=title,
                url=f"https://reddit.com{post_data.get('permalink', '')}",
                source=f"Reddit r/{subreddit}",
                published_at=published_at,
                content=content,
                tags=["Reddit", "AI", subreddit],
            )
            articles.append(article)

        return articles


class HackerNewsFetcher:
    """Fetches AI-related stories from HackerNews with full content extraction."""

    API_BASE = "https://hacker-news.firebaseio.com/v0"

    # Expanded AI keywords for better filtering
    AI_KEYWORDS = [
        "ai", "llm", "gpt", "claude", "anthropic", "openai",
        "machine learning", "neural", "transformer", "gemini",
        "chatgpt", "copilot", "midjourney", "stable diffusion",
        "langchain", "langgraph", "rag", "embedding", "vector",
        "fine-tuning", "llama", "mistral", "deepseek", "qwen",
        "hugging face", "pytorch", "tensorflow", "artificial intelligence",
    ]

    def __init__(self):
        """Initialize HackerNews fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours)
        self.max_stories = 25
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def fetch_all(self) -> List[Article]:
        """Fetch top AI-related stories from HackerNews.

        Returns:
            List of Article objects
        """
        logger.info("fetching_hackernews")

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Get top stories
                async with session.get(f"{self.API_BASE}/topstories.json") as response:
                    if response.status != 200:
                        logger.warning("hn_topstories_error", status=response.status)
                        return []
                    story_ids = await response.json()

                # Fetch first N stories in parallel
                tasks = [
                    self._fetch_story_with_content(session, story_id)
                    for story_id in story_ids[: self.max_stories * 4]  # Over-fetch for filtering
                ]
                stories = await asyncio.gather(*tasks, return_exceptions=True)

            articles = []
            cutoff_time = datetime.now(timezone.utc) - self.max_age

            for story in stories:
                if isinstance(story, Exception) or not story:
                    continue

                # Check if AI-related
                title_lower = story.get("title", "").lower()
                content_lower = story.get("extracted_content", "").lower()
                combined_text = f"{title_lower} {content_lower}"

                if not any(keyword in combined_text for keyword in self.AI_KEYWORDS):
                    continue

                # Check age
                published_at = datetime.fromtimestamp(
                    story.get("time", 0), tz=timezone.utc
                )
                if published_at < cutoff_time:
                    continue

                # Build article with extracted content
                # Always use HN discussion URL as the primary link
                url = f"https://news.ycombinator.com/item?id={story.get('id')}"
                content = story.get("extracted_content") or story.get("text") or story.get("title", "")

                # Add HN discussion metrics
                score = story.get("score", 0)
                descendants = story.get("descendants", 0)
                if score > 0 or descendants > 0:
                    content += f"\n\n[HN Score: {score}, Comments: {descendants}]"

                article = Article(
                    title=story.get("title", "").strip(),
                    url=url,
                    source="HackerNews",
                    published_at=published_at,
                    content=content[:3000],
                    tags=["HackerNews", "AI"],
                )
                articles.append(article)

                if len(articles) >= self.max_stories:
                    break

            logger.info("hackernews_total", count=len(articles))
            return articles

        except Exception as e:
            logger.error("hackernews_error", error=str(e))
            return []

    async def _fetch_story_with_content(
        self, session: aiohttp.ClientSession, story_id: int
    ) -> Optional[dict]:
        """Fetch a story and extract content from the linked URL.

        Args:
            session: aiohttp session
            story_id: HackerNews story ID

        Returns:
            Story data dict with extracted content
        """
        try:
            # Fetch story metadata
            async with session.get(
                f"{self.API_BASE}/item/{story_id}.json"
            ) as response:
                if response.status != 200:
                    return None
                story = await response.json()

            if not story or story.get("type") != "story":
                return None

            # Try to extract content from the linked URL
            url = story.get("url")
            if url:
                extracted = await self._extract_url_content(session, url)
                story["extracted_content"] = extracted

            return story

        except Exception as e:
            logger.debug("hn_story_error", story_id=story_id, error=str(e))
            return None

    async def _extract_url_content(
        self, session: aiohttp.ClientSession, url: str
    ) -> str:
        """Extract main content from a URL.

        Args:
            session: aiohttp session
            url: URL to extract content from

        Returns:
            Extracted text content
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; AINewsBrief/1.0)"
            }

            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
                allow_redirects=True,
            ) as response:
                if response.status != 200:
                    return ""

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    return ""

                html = await response.text()

            # Parse HTML and extract main content
            soup = BeautifulSoup(html, "html.parser")

            # Remove script, style, nav elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            # Try to find article content
            article = soup.find("article")
            if article:
                text = article.get_text(separator=" ", strip=True)
            else:
                # Fallback to main or body
                main = soup.find("main") or soup.find("body")
                if main:
                    # Get paragraphs
                    paragraphs = main.find_all("p")
                    text = " ".join(p.get_text(strip=True) for p in paragraphs[:10])
                else:
                    text = ""

            # Clean up whitespace
            text = re.sub(r"\s+", " ", text).strip()

            return text[:2000]

        except Exception as e:
            logger.debug("content_extraction_error", url=url[:100], error=str(e))
            return ""
