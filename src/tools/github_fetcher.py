"""Fetcher for GitHub releases from major AI repositories."""

import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import aiohttp

from src.models.article import Article
from src.config import settings
from src.utils.logger import get_logger
from src.utils.retry import async_retry

logger = get_logger("github_fetcher")


class GitHubFetcher:
    """Fetches releases and announcements from major AI repositories."""

    # Major AI repositories to track
    REPOSITORIES = [
        # LLM Frameworks
        {"owner": "langchain-ai", "repo": "langchain", "category": "Framework"},
        {"owner": "langchain-ai", "repo": "langgraph", "category": "Framework"},
        {"owner": "run-llama", "repo": "llama_index", "category": "Framework"},
        {"owner": "guidance-ai", "repo": "guidance", "category": "Framework"},
        # Models & Inference
        {"owner": "huggingface", "repo": "transformers", "category": "ML Library"},
        {"owner": "huggingface", "repo": "diffusers", "category": "ML Library"},
        {"owner": "vllm-project", "repo": "vllm", "category": "Inference"},
        {"owner": "ggerganov", "repo": "llama.cpp", "category": "Inference"},
        {"owner": "ollama", "repo": "ollama", "category": "Inference"},
        # Agent Frameworks
        {"owner": "microsoft", "repo": "autogen", "category": "Agents"},
        {"owner": "Significant-Gravitas", "repo": "AutoGPT", "category": "Agents"},
        {"owner": "crewAIInc", "repo": "crewAI", "category": "Agents"},
        # AI Tools
        {"owner": "openai", "repo": "openai-python", "category": "SDK"},
        {"owner": "anthropics", "repo": "anthropic-sdk-python", "category": "SDK"},
        {"owner": "google", "repo": "generative-ai-python", "category": "SDK"},
        # Training & Fine-tuning
        {"owner": "pytorch", "repo": "pytorch", "category": "ML Library"},
        {"owner": "unslothai", "repo": "unsloth", "category": "Training"},
        {"owner": "axolotl-ai-cloud", "repo": "axolotl", "category": "Training"},
        # Vector DBs
        {"owner": "chroma-core", "repo": "chroma", "category": "Vector DB"},
        {"owner": "qdrant", "repo": "qdrant", "category": "Vector DB"},
    ]

    API_BASE = "https://api.github.com"

    def __init__(self):
        """Initialize GitHub fetcher."""
        self.max_age = timedelta(hours=settings.article_age_hours * 2)  # Releases are less frequent
        self.timeout = aiohttp.ClientTimeout(total=30)
        # GitHub API token is optional but recommended for higher rate limits
        self.github_token = getattr(settings, "github_token", None)

    async def fetch_all(self) -> List[Article]:
        """Fetch releases from all tracked repositories.

        Returns:
            List of Article objects
        """
        logger.info("fetching_github_releases", repos=len(self.REPOSITORIES))

        # Batch requests to avoid rate limiting
        batch_size = 10
        all_articles = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for i in range(0, len(self.REPOSITORIES), batch_size):
                batch = self.REPOSITORIES[i : i + batch_size]
                tasks = [self._fetch_repo_releases(session, repo) for repo in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for repo, result in zip(batch, results):
                    repo_name = f"{repo['owner']}/{repo['repo']}"
                    if isinstance(result, list):
                        all_articles.extend(result)
                        if result:
                            logger.info("github_fetched", repo=repo_name, count=len(result))
                    elif isinstance(result, Exception):
                        logger.warning("github_fetch_error", repo=repo_name, error=str(result))

                # Rate limit protection
                if i + batch_size < len(self.REPOSITORIES):
                    await asyncio.sleep(1)

        logger.info("github_total", count=len(all_articles))
        return all_articles

    @async_retry(max_attempts=2, min_wait=2.0, max_wait=10.0)
    async def _fetch_repo_releases(self, session: aiohttp.ClientSession, repo_config: dict) -> List[Article]:
        """Fetch releases for a single repository.

        Args:
            session: aiohttp session
            repo_config: Repository configuration dict

        Returns:
            List of Article objects
        """
        owner = repo_config["owner"]
        repo = repo_config["repo"]
        category = repo_config.get("category", "AI Tool")

        url = f"{self.API_BASE}/repos/{owner}/{repo}/releases"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AINewsBrief/1.0",
        }

        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        async with session.get(url, headers=headers, params={"per_page": 5}) as response:
            if response.status == 404:
                return []
            if response.status == 403:
                # Rate limited
                logger.warning("github_rate_limited", repo=f"{owner}/{repo}")
                return []
            if response.status != 200:
                return []

            releases = await response.json()

        articles = []
        cutoff_time = datetime.now(timezone.utc) - self.max_age

        for release in releases:
            try:
                # Parse release date
                published_str = release.get("published_at", release.get("created_at", ""))
                if published_str:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                else:
                    continue

                if published_at < cutoff_time:
                    continue

                # Skip drafts and prereleases (optional)
                if release.get("draft"):
                    continue

                # Build article
                tag_name = release.get("tag_name", "")
                name = release.get("name", "") or tag_name
                body = release.get("body", "") or ""

                # Create meaningful title
                title = f"{repo} {name}" if name else f"{repo} {tag_name}"
                if release.get("prerelease"):
                    title += " (Pre-release)"

                # Truncate body but keep important info
                content = self._format_release_body(body, release)

                article = Article(
                    title=title,
                    url=release.get("html_url", ""),
                    source=f"GitHub {category}",
                    published_at=published_at,
                    content=content[:3000],
                    tags=["GitHub", "Release", category, repo],
                )
                articles.append(article)

            except Exception as e:
                logger.debug(
                    "release_parse_error",
                    repo=f"{owner}/{repo}",
                    error=str(e),
                )
                continue

        return articles

    def _format_release_body(self, body: str, release: dict) -> str:
        """Format release body for article content.

        Args:
            body: Release body markdown
            release: Full release data

        Returns:
            Formatted content string
        """
        parts = []
        tag = release.get("tag_name", "")

        if tag:
            parts.append(f"Version: {tag}")
            # Check if it's a major release (version >= 1.0.0)
            if self._is_major_release(tag):
                parts.append("Major release")

        if body:
            # Remove HTML comments and limit length
            cleaned = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)[:2500]
            parts.append(cleaned)

        return "\n\n".join(parts)

    def _is_major_release(self, tag: str) -> bool:
        """Check if a tag represents a major release (version >= 1.0.0).

        Args:
            tag: Version tag string (e.g., "v1.0.0", "2.3.1")

        Returns:
            True if major version is >= 1
        """
        if "." not in tag:
            return False
        try:
            major = int(tag.lstrip("v").split(".")[0])
            return major >= 1
        except (ValueError, IndexError):
            return False
