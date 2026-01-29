"""Tests for X and YouTube fetchers."""

import pytest
from datetime import datetime, timezone
from src.tools.x_fetcher import XFetcher
from src.tools.youtube_fetcher import YouTubeFetcher


@pytest.mark.asyncio
async def test_x_fetcher_initialization():
    """Test XFetcher initialization."""
    fetcher = XFetcher()
    assert fetcher is not None
    assert len(fetcher.ACCOUNTS) > 0
    assert "sama" in fetcher.ACCOUNTS
    assert "OpenAI" in fetcher.ACCOUNTS


@pytest.mark.asyncio
async def test_x_fetcher_ai_filter():
    """Test AI-related content filtering."""
    fetcher = XFetcher()

    # Should pass
    assert fetcher._is_ai_related("Just released GPT-5 with amazing capabilities")
    assert fetcher._is_ai_related("New LLM training techniques")
    assert fetcher._is_ai_related("Claude 3.5 is incredible for coding")

    # Should fail
    assert not fetcher._is_ai_related("Beautiful sunset today")
    assert not fetcher._is_ai_related("Going for a walk in the park")


@pytest.mark.asyncio
async def test_youtube_fetcher_initialization():
    """Test YouTubeFetcher initialization."""
    fetcher = YouTubeFetcher()
    assert fetcher is not None
    assert len(fetcher.CHANNELS) > 0
    # Check that Two Minute Papers is in the list
    assert "UCbfYPyITQ-7l4upoX8nvctg" in fetcher.CHANNELS


@pytest.mark.asyncio
async def test_youtube_fetcher_ai_filter():
    """Test AI-related content filtering."""
    fetcher = YouTubeFetcher()

    # Should pass
    assert fetcher._is_ai_related("How GPT-4 Works: A Deep Dive")
    assert fetcher._is_ai_related("New Diffusion Model Breakthrough")
    assert fetcher._is_ai_related("Machine Learning Tutorial for Beginners")

    # Should fail
    assert not fetcher._is_ai_related("Cooking Recipe: Best Pasta")
    assert not fetcher._is_ai_related("Travel Vlog: Paris 2024")


@pytest.mark.asyncio
async def test_youtube_fetcher_no_api_key():
    """Test YouTube fetcher behavior without API key."""
    fetcher = YouTubeFetcher(api_key="")
    articles = await fetcher.fetch_all()
    assert articles == []  # Should return empty list without API key


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires live network access and API keys")
async def test_x_fetcher_live():
    """Test X fetcher with live data (requires network)."""
    fetcher = XFetcher()
    articles = await fetcher.fetch_all()
    # Should get some articles (or empty if all Nitter instances are down)
    assert isinstance(articles, list)


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires YouTube API key and live network access")
async def test_youtube_fetcher_live():
    """Test YouTube fetcher with live data (requires API key and network)."""
    import os
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        pytest.skip("YOUTUBE_API_KEY not set")

    fetcher = YouTubeFetcher(api_key=api_key)
    articles = await fetcher.fetch_all()
    assert isinstance(articles, list)

    if articles:
        # Verify article structure
        article = articles[0]
        assert article.title.startswith("🎥 ")
        assert "youtube.com" in str(article.url)
        assert "YouTube" in article.source
