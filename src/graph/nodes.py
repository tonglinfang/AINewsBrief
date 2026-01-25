"""Node implementations for the brief workflow."""

import asyncio
from typing import List
from src.graph.state import BriefState
from src.models.article import Article
from src.models.analysis import AnalysisResult
from src.tools.rss_fetcher import RSSFetcher
from src.tools.api_fetcher import RedditFetcher, HackerNewsFetcher
from src.tools.arxiv_fetcher import ArxivFetcher
from src.tools.telegram_sender import TelegramSender
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.formatters.markdown_formatter import MarkdownFormatter
from src.utils.deduplication import deduplicate_articles
from src.utils.dedup_history import (
    filter_previously_seen,
    load_dedup_history,
    record_seen_articles,
)
from src.utils.report_saver import save_report
from src.config import settings
from datetime import datetime, timedelta, timezone


async def fetch_news_node(state: BriefState) -> BriefState:
    """Fetch news from all sources concurrently.

    Args:
        state: Current workflow state

    Returns:
        Updated state with raw_articles populated
    """
    print("📡 Fetching news from all sources...")

    # Initialize fetchers
    fetchers = [
        RSSFetcher().fetch_all(),
        RedditFetcher().fetch_all(),
        HackerNewsFetcher().fetch_all(),
        ArxivFetcher().fetch_all(),
    ]

    # Fetch concurrently
    results = await asyncio.gather(*fetchers, return_exceptions=True)

    # Collect articles
    raw_articles: List[Article] = []
    errors: List[str] = list(state.get("errors", []))

    for i, result in enumerate(results):
        if isinstance(result, list):
            raw_articles.extend(result)
            print(f"  ✓ Source {i+1}: {len(result)} articles")
        elif isinstance(result, Exception):
            error_msg = f"Error fetching from source {i+1}: {result}"
            print(f"  ✗ {error_msg}")
            errors.append(error_msg)

    print(f"📊 Total fetched: {len(raw_articles)} articles")

    return {
        **state,
        "raw_articles": raw_articles,
        "errors": errors,
    }


async def filter_node(state: BriefState) -> BriefState:
    """Filter and deduplicate articles.

    Args:
        state: Current workflow state

    Returns:
        Updated state with filtered_articles populated
    """
    print("🔍 Filtering and deduplicating articles...")

    raw_articles = state["raw_articles"]
    max_articles = state["max_articles"]

    def _coerce_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    # Filter by age (already done in fetchers, but double-check)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=settings.article_age_hours)
    time_filtered = [a for a in raw_articles if _coerce_utc(a.published_at) >= cutoff_time]
    print(f"  ✓ After time filter: {len(time_filtered)} articles")

    # Filter by content length
    content_filtered = [a for a in time_filtered if len(a.content) >= 100]
    print(f"  ✓ After content filter: {len(content_filtered)} articles")

    # Deduplicate
    seen_urls, seen_titles = load_dedup_history(
        settings.dedup_history_path, settings.dedup_history_days
    )
    history_filtered = filter_previously_seen(
        content_filtered,
        seen_urls,
        seen_titles,
        title_similarity_threshold=0.8,
    )
    print(f"  ✓ After history filter: {len(history_filtered)} articles")

    deduplicated = deduplicate_articles(history_filtered)
    print(f"  ✓ After deduplication: {len(deduplicated)} articles")

    # Limit to max articles
    filtered_articles = deduplicated[:max_articles]
    print(f"  ✓ Final filtered: {len(filtered_articles)} articles")

    return {
        **state,
        "filtered_articles": filtered_articles,
    }


async def analyze_node(state: BriefState) -> BriefState:
    """Analyze articles using LLM.

    Args:
        state: Current workflow state

    Returns:
        Updated state with analyzed_articles populated
    """
    provider_label = {
        "anthropic": "Claude",
        "openai": "OpenAI",
        "google": "Google",
    }.get(settings.llm_provider, settings.llm_provider)
    print(f"🤖 Analyzing articles with {provider_label}...")

    filtered_articles = state["filtered_articles"]

    if not filtered_articles:
        print("  ⚠️ No articles to analyze")
        return {
            **state,
            "analyzed_articles": [],
        }

    # Analyze with LLM
    analyzer = LLMAnalyzer()
    analyzed_articles = await analyzer.analyze_batch(filtered_articles)

    print(f"  ✓ Analyzed {len(analyzed_articles)} articles")

    # Filter by minimum importance score
    filtered_by_score = [
        a for a in analyzed_articles if a.importance_score >= settings.min_importance_score
    ]
    print(f"  ✓ After importance filter: {len(filtered_by_score)} articles")

    return {
        **state,
        "analyzed_articles": filtered_by_score,
    }


async def format_node(state: BriefState) -> BriefState:
    """Format analysis results into markdown report.

    Args:
        state: Current workflow state

    Returns:
        Updated state with report populated
    """
    print("📝 Formatting report...")

    analyzed_articles = state["analyzed_articles"]
    date = state["date"]
    formatter = MarkdownFormatter()

    if not analyzed_articles:
        print("  ⚠️ No articles to format")
        report = formatter.format(date, [])
    else:
        report = formatter.format(date, analyzed_articles)
        print(f"  ✓ Report generated ({len(report.markdown_content)} characters)")

    return {
        **state,
        "report": report,
    }


async def send_node(state: BriefState) -> BriefState:
    """Send report to Telegram and save to file.

    Args:
        state: Current workflow state

    Returns:
        Updated state with telegram_message_id and report_path populated
    """
    print("📤 Sending report...")

    report = state["report"]
    errors: List[str] = list(state.get("errors", []))

    if not report:
        error_msg = "No report to send"
        print(f"  ✗ {error_msg}")
        errors.append(error_msg)
        return {
            **state,
            "errors": errors,
        }

    # Save report to file
    try:
        report_path = save_report(report)
        print(f"  ✓ Report saved to {report_path}")
    except Exception as e:
        error_msg = f"Error saving report: {e}"
        print(f"  ✗ {error_msg}")
        errors.append(error_msg)
        report_path = None

    # Send to Telegram
    telegram_message_id = None
    sender = TelegramSender()
    try:
        telegram_message_id = await sender.send_report(report)
        if telegram_message_id:
            print(f"  ✓ Sent to Telegram (message_id: {telegram_message_id})")
        else:
            error_msg = "Failed to send to Telegram"
            print(f"  ✗ {error_msg}")
            errors.append(error_msg)
    except Exception as e:
        error_msg = f"Error sending to Telegram: {e}"
        print(f"  ✗ {error_msg}")
        errors.append(error_msg)

        # Send error notification
        try:
            await sender.send_error(error_msg)
        except Exception:
            pass

    if telegram_message_id and state.get("analyzed_articles"):
        try:
            record_seen_articles(
                [a.article for a in state["analyzed_articles"]],
                settings.dedup_history_path,
                settings.dedup_history_days,
            )
            print("  ✓ Updated dedup history")
        except Exception as e:
            error_msg = f"Error updating dedup history: {e}"
            print(f"  ✗ {error_msg}")
            errors.append(error_msg)

    return {
        **state,
        "telegram_message_id": telegram_message_id,
        "report_path": str(report_path) if report_path else None,
        "errors": errors,
    }
