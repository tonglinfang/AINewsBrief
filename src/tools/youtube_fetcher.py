"""YouTube fetcher for AI-related video content."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import List
import aiohttp
from src.models.article import Article
from src.config import settings
from src.utils.logger import get_logger
from src.utils.retry import async_retry

logger = get_logger("youtube_fetcher")


class YouTubeFetcher:
    """Fetches videos from AI-focused YouTube channels."""

    # Priority AI YouTube channels
    CHANNELS = {
        # Technical Deep Dives
        "UCbfYPyITQ-7l4upoX8nvctg": {
            "name": "Two Minute Papers",
            "priority": 9,
            "description": "AI research paper reviews",
        },
        "UCZHmQk67mSJgfCCTn7xBfew": {
            "name": "Yannic Kilcher",
            "priority": 8,
            "description": "ML research paper explanations",
        },
        "UCYO_jab_esuFRV4b17AJtAw": {
            "name": "3Blue1Brown",
            "priority": 8,
            "description": "Math/AI visual explanations",
        },
        # AI News & Analysis
        "UCkLfEba0iefnKTsKTtr1YVA": {
            "name": "AI Explained",
            "priority": 8,
            "description": "AI news and paper analysis",
        },
        "UCXZCJLdBC09xxGZ6gcdrc6A": {
            "name": "The AI Epiphany",
            "priority": 7,
            "description": "AI tutorials and news",
        },
        "UCfzlCWGWYyIQ0aLC5w48gBQ": {
            "name": "Sentdex",
            "priority": 7,
            "description": "Python AI tutorials",
        },
        # AI Companies
        "UCXZCJLdBC09xxGZ6gcdrc6A": {
            "name": "Google DeepMind",
            "priority": 9,
            "description": "Official DeepMind channel",
        },
        "UCd9EEd6BrMGMmGKMeO1K8qQ": {
            "name": "OpenAI",
            "priority": 10,
            "description": "Official OpenAI channel",
        },
        # AI Tools & Applications
        "UCi89gMqvjfiEP_Qhm3zMTxw": {
            "name": "Matt Wolfe",
            "priority": 7,
            "description": "AI tools and news",
        },
        "UCbRP3c757lWg9M-U7TyEkXA": {
            "name": "AI Advantage",
            "priority": 6,
            "description": "AI productivity tools",
        },
        # Academic/Educational
        "UCBa5G_ESCn8Yd4vw5U-gIcg": {
            "name": "Lex Fridman",
            "priority": 8,
            "description": "AI researcher interviews",
        },
        "UCtYLUTtgS3k1Fg4y5tAhLbw": {
            "name": "Stanford Online",
            "priority": 8,
            "description": "Stanford AI lectures",
        },
    }

    def __init__(self, api_key: str = None):
        """Initialize YouTube fetcher.

        Args:
            api_key: YouTube Data API v3 key (optional, from settings)
        """
        self.api_key = api_key or getattr(settings, "youtube_api_key", "")
        self.max_age = timedelta(hours=settings.article_age_hours * 2)  # 48h window
        self.max_per_channel = 3  # Limit videos per channel
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def fetch_all(self) -> List[Article]:
        """Fetch videos from all YouTube channels concurrently.

        Returns:
            List of Article objects
        """
        if not self.api_key:
            logger.warning("youtube_api_key_missing", message="Skipping YouTube fetch")
            return []

        logger.info("fetching_youtube_videos", channels=len(self.CHANNELS))
        tasks = [
            self.fetch_channel(channel_id, info)
            for channel_id, info in self.CHANNELS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        articles = []
        for channel_id, result in zip(self.CHANNELS.keys(), results):
            if isinstance(result, list):
                articles.extend(result)
                channel_name = self.CHANNELS[channel_id]["name"]
                logger.info("youtube_fetched", channel=channel_name, count=len(result))
            elif isinstance(result, Exception):
                logger.warning(
                    "youtube_fetch_error", channel=channel_id, error=str(result)
                )

        logger.info("youtube_total", count=len(articles))
        return articles

    @async_retry(max_attempts=3, min_wait=1.0, max_wait=10.0)
    async def fetch_channel(
        self, channel_id: str, channel_info: dict
    ) -> List[Article]:
        """Fetch recent videos from a YouTube channel.

        Args:
            channel_id: YouTube channel ID
            channel_info: Channel metadata (name, priority)

        Returns:
            List of Article objects
        """
        try:
            # Step 1: Get channel's upload playlist ID
            uploads_playlist_id = await self._get_uploads_playlist(channel_id)
            if not uploads_playlist_id:
                return []

            # Step 2: Get recent videos from playlist
            videos = await self._get_playlist_videos(uploads_playlist_id)

            # Step 3: Get video details
            if not videos:
                return []

            video_ids = [v["videoId"] for v in videos[: self.max_per_channel]]
            video_details = await self._get_video_details(video_ids)

            # Step 4: Convert to Article objects
            articles = []
            cutoff_time = datetime.now(timezone.utc) - self.max_age

            for video in video_details:
                try:
                    published_at = datetime.fromisoformat(
                        video["snippet"]["publishedAt"].replace("Z", "+00:00")
                    )

                    if published_at < cutoff_time:
                        continue

                    # Filter: must be AI-related in title or description
                    title = video["snippet"]["title"]
                    description = video["snippet"]["description"]
                    if not self._is_ai_related(title + " " + description):
                        continue

                    article = Article(
                        title=f"🎥 {title}",
                        url=f"https://www.youtube.com/watch?v={video['id']}",
                        source=f"YouTube - {channel_info['name']}",
                        published_at=published_at,
                        content=description[:500],  # Truncate long descriptions
                        tags=["YouTube", "Video", "AI"],
                        priority=channel_info.get("priority", 5),
                    )
                    articles.append(article)

                except Exception as e:
                    logger.debug(
                        "youtube_video_error",
                        channel=channel_info["name"],
                        error=str(e),
                    )
                    continue

            return articles

        except Exception as e:
            logger.warning(
                "youtube_channel_error",
                channel=channel_info["name"],
                error=str(e),
            )
            return []

    async def _get_uploads_playlist(self, channel_id: str) -> str:
        """Get the uploads playlist ID for a channel.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Uploads playlist ID (starts with UU)
        """
        url = f"{self.base_url}/channels"
        params = {
            "part": "contentDetails",
            "id": channel_id,
            "key": self.api_key,
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.warning(
                            "youtube_api_error",
                            endpoint="channels",
                            status=response.status,
                        )
                        return ""

                    data = await response.json()
                    if "items" not in data or not data["items"]:
                        return ""

                    return data["items"][0]["contentDetails"]["relatedPlaylists"][
                        "uploads"
                    ]

        except Exception as e:
            logger.debug("youtube_playlist_error", channel=channel_id, error=str(e))
            return ""

    async def _get_playlist_videos(self, playlist_id: str) -> List[dict]:
        """Get videos from a playlist.

        Args:
            playlist_id: YouTube playlist ID

        Returns:
            List of video items
        """
        url = f"{self.base_url}/playlistItems"
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": self.max_per_channel * 2,  # Get more to filter
            "key": self.api_key,
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.warning(
                            "youtube_api_error",
                            endpoint="playlistItems",
                            status=response.status,
                        )
                        return []

                    data = await response.json()
                    if "items" not in data:
                        return []

                    return [
                        {"videoId": item["snippet"]["resourceId"]["videoId"]}
                        for item in data["items"]
                    ]

        except Exception as e:
            logger.debug("youtube_videos_error", playlist=playlist_id, error=str(e))
            return []

    async def _get_video_details(self, video_ids: List[str]) -> List[dict]:
        """Get detailed information for videos.

        Args:
            video_ids: List of video IDs

        Returns:
            List of video detail objects
        """
        url = f"{self.base_url}/videos"
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(video_ids),
            "key": self.api_key,
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.warning(
                            "youtube_api_error",
                            endpoint="videos",
                            status=response.status,
                        )
                        return []

                    data = await response.json()
                    return data.get("items", [])

        except Exception as e:
            logger.debug("youtube_details_error", error=str(e))
            return []

    def _is_ai_related(self, text: str) -> bool:
        """Check if video content is AI-related.

        Args:
            text: Video title + description

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
            "artificial intelligence",
            "gemini",
            "mistral",
            "llama",
            "computer vision",
            "nlp",
            "natural language",
            "reinforcement learning",
            "agi",
        ]

        return any(keyword in text_lower for keyword in ai_keywords)
