"""API-based fetchers for Reddit and HackerNews."""

import asyncio
from datetime import datetime, timedelta
from typing import List
import aiohttp
from src.models.article import Article
from src.config import settings


class RedditFetcher:
    """Fetches AI-related posts from Reddit."""

    SUBREDDITS = ["MachineLearning", "artificial", "ArtificialInteligence", "LocalLLaMA"]

    def __init__(self):
        """Initialize Reddit fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours)
        self.max_per_subreddit = 10

    async def fetch_all(self) -> List[Article]:
        """Fetch posts from all subreddits.

        Returns:
            List of Article objects
        """
        if not settings.reddit_client_id or not settings.reddit_client_secret:
            print("Reddit credentials not configured, skipping Reddit fetcher")
            return []

        tasks = [self.fetch_subreddit(subreddit) for subreddit in self.SUBREDDITS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                print(f"Error fetching Reddit: {result}")

        return articles

    async def fetch_subreddit(self, subreddit: str) -> List[Article]:
        """Fetch hot posts from a subreddit using Reddit JSON API.

        Args:
            subreddit: Subreddit name

        Returns:
            List of Article objects
        """
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json"
            params = {"limit": self.max_per_subreddit}
            headers = {"User-Agent": settings.reddit_user_agent}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        print(f"Reddit API error for r/{subreddit}: {response.status}")
                        return []

                    data = await response.json()

            articles = []
            cutoff_time = datetime.now() - self.max_age

            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})

                # Parse timestamp
                created_utc = post_data.get("created_utc", 0)
                published_at = datetime.fromtimestamp(created_utc)

                if published_at < cutoff_time:
                    continue

                # Extract content
                title = post_data.get("title", "").strip()
                selftext = post_data.get("selftext", "")
                url_str = post_data.get("url", "")

                # Skip if no meaningful content
                if not title or len(selftext) < 50:
                    continue

                article = Article(
                    title=title,
                    url=f"https://reddit.com{post_data.get('permalink', '')}",
                    source=f"Reddit r/{subreddit}",
                    published_at=published_at,
                    content=selftext[:1000] if selftext else title,
                    tags=["Reddit", "AI"],
                )
                articles.append(article)

            return articles

        except Exception as e:
            print(f"Error fetching r/{subreddit}: {e}")
            return []


class HackerNewsFetcher:
    """Fetches AI-related stories from HackerNews."""

    API_BASE = "https://hacker-news.firebaseio.com/v0"

    def __init__(self):
        """Initialize HackerNews fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours)
        self.max_stories = 20

    async def fetch_all(self) -> List[Article]:
        """Fetch top AI-related stories from HackerNews.

        Returns:
            List of Article objects
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Get top stories
                async with session.get(f"{self.API_BASE}/topstories.json") as response:
                    story_ids = await response.json()

                # Fetch first N stories
                tasks = [
                    self.fetch_story(session, story_id)
                    for story_id in story_ids[: self.max_stories * 3]  # Over-fetch for filtering
                ]
                stories = await asyncio.gather(*tasks, return_exceptions=True)

            articles = []
            cutoff_time = datetime.now() - self.max_age
            ai_keywords = ["ai", "llm", "gpt", "claude", "machine learning", "neural", "openai"]

            for story in stories:
                if isinstance(story, Exception) or not story:
                    continue

                # Check if AI-related
                title_lower = story.get("title", "").lower()
                if not any(keyword in title_lower for keyword in ai_keywords):
                    continue

                # Check age
                published_at = datetime.fromtimestamp(story.get("time", 0))
                if published_at < cutoff_time:
                    continue

                url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id')}")

                article = Article(
                    title=story.get("title", "").strip(),
                    url=url,
                    source="HackerNews",
                    published_at=published_at,
                    content=story.get("text", story.get("title", ""))[:1000],
                    tags=["HackerNews", "AI"],
                )
                articles.append(article)

                if len(articles) >= self.max_stories:
                    break

            return articles

        except Exception as e:
            print(f"Error fetching HackerNews: {e}")
            return []

    async def fetch_story(self, session: aiohttp.ClientSession, story_id: int) -> dict:
        """Fetch a single story by ID.

        Args:
            session: aiohttp session
            story_id: HackerNews story ID

        Returns:
            Story data dict
        """
        try:
            async with session.get(f"{self.API_BASE}/item/{story_id}.json") as response:
                return await response.json()
        except Exception as e:
            print(f"Error fetching story {story_id}: {e}")
            return {}
