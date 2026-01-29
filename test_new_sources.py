#!/usr/bin/env python3
"""Quick test script for X and YouTube fetchers."""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.tools.x_fetcher import XFetcher
from src.tools.youtube_fetcher import YouTubeFetcher
from src.utils.logger import get_logger

logger = get_logger("test_sources")


async def test_x_fetcher():
    """Test X (Twitter) fetcher."""
    print("\n" + "=" * 60)
    print("🐦 Testing X (Twitter) Fetcher")
    print("=" * 60)

    fetcher = XFetcher()
    print(f"📋 Tracking {len(fetcher.ACCOUNTS)} accounts:")
    for username, info in list(fetcher.ACCOUNTS.items())[:5]:
        print(f"  - @{username} ({info['name']}) - Priority: {info['priority']}")
    print(f"  ... and {len(fetcher.ACCOUNTS) - 5} more\n")

    print("🔍 Fetching posts (this may take 30-60 seconds)...")
    articles = await fetcher.fetch_all()

    print(f"✅ Fetched {len(articles)} AI-related posts\n")

    if articles:
        print("📝 Sample posts:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article.source}")
            print(f"   Title: {article.title[:80]}...")
            print(f"   URL: {article.url}")
            print(f"   Priority: {article.priority}")
            print(f"   Published: {article.published_at}")
    else:
        print("⚠️  No posts fetched. This could mean:")
        print("   - All Nitter instances are temporarily unavailable")
        print("   - No recent AI-related posts in the time window")
        print("   - Network connectivity issues")

    return len(articles)


async def test_youtube_fetcher():
    """Test YouTube fetcher."""
    print("\n" + "=" * 60)
    print("🎥 Testing YouTube Fetcher")
    print("=" * 60)

    # Load environment variables
    load_dotenv()
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        print("⚠️  YOUTUBE_API_KEY not set in .env file")
        print("   YouTube fetcher will be skipped")
        print("\n   To enable YouTube:")
        print("   1. Get API key: https://console.cloud.google.com/")
        print("   2. Add to .env: YOUTUBE_API_KEY=your_key_here")
        return 0

    fetcher = YouTubeFetcher(api_key=api_key)
    print(f"📋 Tracking {len(fetcher.CHANNELS)} channels:")
    for channel_id, info in list(fetcher.CHANNELS.items())[:5]:
        print(
            f"  - {info['name']} - Priority: {info['priority']} ({info['description']})"
        )
    print(f"  ... and {len(fetcher.CHANNELS) - 5} more\n")

    print("🔍 Fetching videos (this may take 30-60 seconds)...")
    articles = await fetcher.fetch_all()

    print(f"✅ Fetched {len(articles)} AI-related videos\n")

    if articles:
        print("📝 Sample videos:")
        for i, article in enumerate(articles[:3], 1):
            print(f"\n{i}. {article.source}")
            print(f"   Title: {article.title[:80]}...")
            print(f"   URL: {article.url}")
            print(f"   Priority: {article.priority}")
            print(f"   Published: {article.published_at}")
    else:
        print("⚠️  No videos fetched. This could mean:")
        print("   - Invalid API key")
        print("   - API quota exceeded")
        print("   - No recent AI-related videos in the time window")
        print("   - API not enabled in Google Cloud Console")

    return len(articles)


async def main():
    """Run all tests."""
    print("\n🧪 Testing New Data Sources")
    print("=" * 60)

    try:
        # Test X
        x_count = await test_x_fetcher()

        # Test YouTube
        youtube_count = await test_youtube_fetcher()

        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        print(f"✅ X (Twitter): {x_count} posts")
        print(f"✅ YouTube: {youtube_count} videos")
        print(f"🎯 Total: {x_count + youtube_count} articles")

        if x_count > 0 or youtube_count > 0:
            print("\n✨ Tests completed successfully!")
            print("   You can now enable these sources in your .env:")
            print("   ENABLE_X=true")
            print("   ENABLE_YOUTUBE=true")
        else:
            print("\n⚠️  No articles fetched from either source")
            print("   Check the warnings above for troubleshooting steps")

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
