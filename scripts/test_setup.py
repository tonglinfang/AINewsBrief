#!/usr/bin/env python
"""Test script to validate environment setup."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_config():
    """Test configuration loading."""
    print("🔍 Testing configuration...")
    try:
        from src.config import settings

        print(f"  ✓ Config loaded")
        print(f"  ✓ LLM Model: {settings.llm_model}")
        print(f"  ✓ Max articles: {settings.max_total_articles}")

        # Check for API keys based on provider
        provider = (settings.llm_provider or "").lower()
        if provider == "anthropic":
            if not settings.anthropic_api_key:
                print("  ✗ ANTHROPIC_API_KEY not set")
                return False
        elif provider == "openai":
            if not settings.openai_api_key:
                print("  ✗ OPENAI_API_KEY not set")
                return False
        elif provider == "google":
            if not settings.google_api_key:
                print("  ✗ GOOGLE_API_KEY not set")
                return False
        else:
            print(f"  ✗ Unsupported LLM_PROVIDER: {settings.llm_provider}")
            return False

        if not settings.telegram_bot_token:
            print("  ✗ TELEGRAM_BOT_TOKEN not set")
            return False

        if not settings.telegram_chat_id:
            print("  ✗ TELEGRAM_CHAT_ID not set")
            return False

        print("  ✓ All required API keys present")
        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


async def test_fetchers():
    """Test data fetchers."""
    print("\n🔍 Testing fetchers...")
    try:
        from src.tools.rss_fetcher import RSSFetcher
        from src.tools.api_fetcher import HackerNewsFetcher

        # Test RSS
        print("  Testing RSS fetcher...")
        rss = RSSFetcher()
        articles = await rss.fetch_all()
        print(f"  ✓ RSS: Fetched {len(articles)} articles")

        # Test HackerNews
        print("  Testing HackerNews fetcher...")
        hn = HackerNewsFetcher()
        articles = await hn.fetch_all()
        print(f"  ✓ HackerNews: Fetched {len(articles)} articles")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


async def test_telegram():
    """Test Telegram connection."""
    print("\n🔍 Testing Telegram...")
    try:
        from telegram import Bot
        from src.config import settings

        bot = Bot(token=settings.telegram_bot_token)
        me = await bot.get_me()
        print(f"  ✓ Connected to bot: @{me.username}")

        # Try to send a test message
        test_message = "🧪 AI News Brief - Test message from setup script"
        await bot.send_message(chat_id=settings.telegram_chat_id, text=test_message)
        print(f"  ✓ Test message sent to chat {settings.telegram_chat_id}")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


async def test_llm():
    """Test LLM connection."""
    print("\n🔍 Testing LLM API...")
    try:
        from src.analyzers.llm_analyzer import LLMAnalyzer
        from src.models.article import Article
        from datetime import datetime

        # Create a test article
        test_article = Article(
            title="Test: GPT-5 Released",
            url="https://example.com/test",
            source="Test Source",
            published_at=datetime.now(),
            content="This is a test article about GPT-5 release with groundbreaking performance improvements in reasoning and coding capabilities.",
            tags=["test"],
        )

        analyzer = LLMAnalyzer()
        result = await analyzer.analyze(test_article)

        print(f"  ✓ Analysis completed")
        print(f"    Category: {result.category}")
        print(f"    Score: {result.importance_score}/10")
        print(f"    Summary: {result.summary[:50]}...")

        return True

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("AI News Brief - Environment Setup Test")
    print("=" * 60)

    results = []

    # Test config
    results.append(await test_config())

    # Test fetchers
    results.append(await test_fetchers())

    # Test Telegram
    results.append(await test_telegram())

    # Test LLM
    results.append(await test_llm())

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if all(results):
        print("✅ All tests passed! Your environment is ready.")
        print("\nNext steps:")
        print("  1. Run the full workflow: python -m src.agent")
        print("  2. Or wait for GitHub Actions to run automatically")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
