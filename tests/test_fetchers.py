"""Tests for news fetchers."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.article import Article


class TestRSSFetcher:
    """Tests for RSS fetcher."""

    @pytest.mark.asyncio
    async def test_fetch_all_returns_articles(self):
        """Test that fetch_all returns articles from RSS feeds."""
        from src.tools.rss_fetcher import RSSFetcher

        fetcher = RSSFetcher()

        # Mock the fetch_feed method
        mock_article = Article(
            title="Test Article",
            url="https://example.com/article",
            source="Test Source",
            published_at=datetime.now(timezone.utc),
            content="Test content " * 20,
            tags=["AI"],
        )

        with patch.object(
            fetcher, "fetch_feed", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = [mock_article]

            articles = await fetcher.fetch_all()

            assert len(articles) > 0
            assert mock_fetch.called


class TestHackerNewsFetcher:
    """Tests for HackerNews fetcher."""

    def test_ai_keywords_filtering(self):
        """Test that AI keywords are properly defined in shared module."""
        from src.utils.ai_filter import AI_KEYWORDS

        # Check essential keywords are present
        assert "ai" in AI_KEYWORDS
        assert "llm" in AI_KEYWORDS
        assert "gpt" in AI_KEYWORDS
        assert "claude" in AI_KEYWORDS
        assert "anthropic" in AI_KEYWORDS
        assert "openai" in AI_KEYWORDS

    def test_keyword_matching(self):
        """Test keyword matching logic."""
        from src.utils.ai_filter import is_ai_related

        # Test titles that should match
        ai_titles = [
            "OpenAI releases GPT-5",
            "New LLM benchmark results",
            "Claude 3 vs GPT-4 comparison",
            "Machine learning advances",
        ]

        for title in ai_titles:
            assert is_ai_related(title), f"Expected '{title}' to match AI keywords"

        # Test title that should not match
        non_ai_title = "Apple announces new iPhone"
        assert not is_ai_related(non_ai_title)


class TestRedditFetcher:
    """Tests for Reddit fetcher."""

    def test_subreddits_defined(self):
        """Test that relevant subreddits are defined."""
        from src.tools.api_fetcher import RedditFetcher

        fetcher = RedditFetcher()

        assert "MachineLearning" in fetcher.SUBREDDITS
        assert "LocalLLaMA" in fetcher.SUBREDDITS
        assert len(fetcher.SUBREDDITS) >= 4


class TestBlogFetcher:
    """Tests for official blog fetcher."""

    def test_blog_sources_defined(self):
        """Test that major AI company blogs are defined."""
        from src.tools.blog_fetcher import BlogFetcher

        fetcher = BlogFetcher()

        # Check essential blogs are present
        source_names = list(fetcher.BLOG_SOURCES.keys())

        assert any("OpenAI" in name for name in source_names)
        assert any("Anthropic" in name for name in source_names)
        assert any("Google" in name for name in source_names)
        assert any("DeepMind" in name for name in source_names)

    def test_blog_priorities(self):
        """Test that blog priorities are set correctly."""
        from src.tools.blog_fetcher import BlogFetcher

        fetcher = BlogFetcher()

        # Major company blogs should have high priority
        openai_priority = fetcher.BLOG_SOURCES["OpenAI Blog"]["priority"]
        anthropic_priority = fetcher.BLOG_SOURCES["Anthropic Blog"]["priority"]

        assert openai_priority >= 9
        assert anthropic_priority >= 9


class TestGitHubFetcher:
    """Tests for GitHub releases fetcher."""

    def test_repositories_defined(self):
        """Test that important AI repos are tracked."""
        from src.tools.github_fetcher import GitHubFetcher

        fetcher = GitHubFetcher()

        repo_names = [
            f"{r['owner']}/{r['repo']}" for r in fetcher.REPOSITORIES
        ]

        # Check essential repos
        assert "langchain-ai/langchain" in repo_names
        assert "huggingface/transformers" in repo_names

    def test_repository_categories(self):
        """Test that repos have categories."""
        from src.tools.github_fetcher import GitHubFetcher

        fetcher = GitHubFetcher()

        for repo in fetcher.REPOSITORIES:
            assert "category" in repo
            assert repo["category"] in [
                "Framework",
                "ML Library",
                "Inference",
                "Agents",
                "SDK",
                "Training",
                "Vector DB",
            ]


class TestArxivFetcher:
    """Tests for ArXiv fetcher."""

    def test_categories_defined(self):
        """Test that AI-related ArXiv categories are defined."""
        from src.tools.arxiv_fetcher import ArxivFetcher

        fetcher = ArxivFetcher()

        assert "cs.AI" in fetcher.CATEGORIES
        assert "cs.LG" in fetcher.CATEGORIES
        assert "cs.CL" in fetcher.CATEGORIES
