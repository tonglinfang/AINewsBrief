"""Node implementations for the brief workflow."""

import asyncio
from typing import List
from datetime import datetime, timedelta, timezone

from src.graph.state import BriefState
from src.models.article import Article
from src.models.analysis import AnalysisResult
from src.tools.rss_fetcher import RSSFetcher
from src.tools.api_fetcher import RedditFetcher, HackerNewsFetcher
from src.tools.arxiv_fetcher import ArxivFetcher
from src.tools.blog_fetcher import BlogFetcher
from src.tools.github_fetcher import GitHubFetcher
from src.tools.x_fetcher import XFetcher
from src.tools.youtube_fetcher import YouTubeFetcher
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
from src.utils.logger import get_logger
from src.config import settings

logger = get_logger("workflow")


async def fetch_news_node(state: BriefState) -> BriefState:
    """Fetch news from all sources concurrently.

    Args:
        state: Current workflow state

    Returns:
        Updated state with raw_articles populated
    """
    logger.info("fetch_node_start")

    # Define available sources with their settings flags and fetcher factories
    source_configs = [
        ("RSS Feeds", settings.enable_rss, RSSFetcher),
        ("Reddit", settings.enable_reddit, RedditFetcher),
        ("HackerNews", settings.enable_hackernews, HackerNewsFetcher),
        ("ArXiv", settings.enable_arxiv, ArxivFetcher),
        ("Official Blogs", settings.enable_blogs, BlogFetcher),
        ("GitHub Releases", settings.enable_github, GitHubFetcher),
        ("X (Twitter)", settings.enable_x, XFetcher),
        ("YouTube", settings.enable_youtube, YouTubeFetcher),
    ]

    # Initialize enabled fetchers
    fetchers = []
    for source_name, is_enabled, fetcher_class in source_configs:
        if is_enabled:
            fetchers.append((source_name, fetcher_class().fetch_all()))
        else:
            logger.info("source_disabled", source=source_name)

    # Fetch concurrently
    if fetchers:
        tasks = [fetcher[1] for fetcher in fetchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    else:
        results = []

    # Collect articles
    raw_articles: List[Article] = []
    errors: List[str] = list(state.get("errors", []))
    source_stats = {}

    for (source_name, _), result in zip(fetchers, results):
        if isinstance(result, list):
            raw_articles.extend(result)
            source_stats[source_name] = len(result)
            logger.info("source_fetched", source=source_name, count=len(result))
        elif isinstance(result, Exception):
            error_msg = f"Error fetching from {source_name}: {result}"
            logger.error("source_error", source=source_name, error=str(result))
            errors.append(error_msg)
            source_stats[source_name] = 0

    logger.info(
        "fetch_node_complete",
        total_articles=len(raw_articles),
        source_stats=source_stats,
    )

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
    logger.info("filter_node_start", raw_count=len(state["raw_articles"]))

    raw_articles = state["raw_articles"]
    max_articles = state["max_articles"]

    def _coerce_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    # Filter by age (already done in fetchers, but double-check)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=settings.article_age_hours)
    time_filtered = [a for a in raw_articles if _coerce_utc(a.published_at) >= cutoff_time]
    logger.debug("time_filtered", count=len(time_filtered))

    # Filter by content length
    content_filtered = [a for a in time_filtered if len(a.content) >= settings.min_content_length]
    logger.debug("content_filtered", count=len(content_filtered))

    # Deduplicate against history
    seen_urls, seen_titles = load_dedup_history(
        settings.dedup_history_path, settings.dedup_history_days
    )
    history_filtered = filter_previously_seen(
        content_filtered,
        seen_urls,
        seen_titles,
        title_similarity_threshold=0.8,
    )
    logger.debug("history_filtered", count=len(history_filtered))

    # Deduplicate within current batch
    deduplicated = deduplicate_articles(history_filtered)
    logger.debug("deduplicated", count=len(deduplicated))

    # Sort by source priority (official blogs first, then HN/Reddit by engagement)
    def priority_sort(article: Article) -> tuple:
        source_priority = {
            "OpenAI Blog": 100,
            "Anthropic Blog": 100,
            "Google AI Blog": 95,
            "DeepMind Blog": 95,
            "GitHub": 80,
            "HackerNews": 70,
            "ArXiv": 60,
        }
        for source_key, priority in source_priority.items():
            if source_key in article.source:
                return (-priority, article.published_at)
        return (-50, article.published_at)

    sorted_articles = sorted(deduplicated, key=priority_sort)

    # Limit to max articles
    filtered_articles = sorted_articles[:max_articles]

    logger.info(
        "filter_node_complete",
        input=len(raw_articles),
        output=len(filtered_articles),
    )

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
    filtered_articles = state["filtered_articles"]

    logger.info(
        "analyze_node_start",
        article_count=len(filtered_articles),
        provider=settings.llm_provider,
        model=settings.llm_model,
    )

    if not filtered_articles:
        logger.warning("no_articles_to_analyze")
        return {
            **state,
            "analyzed_articles": [],
        }

    # Analyze with LLM
    analyzer = LLMAnalyzer()
    analyzed_articles = await analyzer.analyze_batch(filtered_articles)

    logger.info("llm_analysis_complete", analyzed=len(analyzed_articles))

    # Filter by minimum importance score
    filtered_by_importance = [
        a for a in analyzed_articles if a.importance_score >= settings.min_importance_score
    ]
    logger.debug("filtered_by_importance", count=len(filtered_by_importance))

    # Filter by minimum AI relevance score (remove non-AI content)
    filtered_by_score = [
        a for a in filtered_by_importance if a.ai_relevance_score >= settings.min_ai_relevance_score
    ]

    logger.info(
        "analyze_node_complete",
        analyzed=len(analyzed_articles),
        passed_importance_filter=len(filtered_by_importance),
        passed_relevance_filter=len(filtered_by_score),
        min_importance=settings.min_importance_score,
        min_ai_relevance=settings.min_ai_relevance_score,
    )

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
    analyzed_articles = state["analyzed_articles"]
    date = state["date"]

    logger.info("format_node_start", article_count=len(analyzed_articles))

    if not analyzed_articles:
        logger.warning("no_articles_to_format")

    formatter = MarkdownFormatter()
    report = formatter.format(date, analyzed_articles)

    logger.info(
        "format_node_complete",
        content_length=len(report.markdown_content),
    )

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
    logger.info("send_node_start")

    report = state["report"]
    analyzed_articles = state.get("analyzed_articles", [])
    errors: List[str] = list(state.get("errors", []))

    if not report:
        error_msg = "No report to send"
        logger.error("send_error", reason=error_msg)
        errors.append(error_msg)
        return {
            **state,
            "errors": errors,
        }

    if not analyzed_articles:
        logger.warning("no_articles_skipping_telegram")
        return {
            **state,
            "telegram_message_id": None,
            "errors": errors,
        }

    # Save report to file
    report_path = None
    try:
        report_path = save_report(report)
        logger.info("report_saved", path=str(report_path))
    except Exception as e:
        error_msg = f"Error saving report: {e}"
        logger.error("report_save_error", error=str(e))
        errors.append(error_msg)

    # Send to Telegram
    telegram_message_id = None
    sender = TelegramSender()
    try:
        telegram_message_id = await sender.send_report(report)
        if telegram_message_id:
            logger.info("telegram_sent", message_id=telegram_message_id)
        else:
            error_msg = "Failed to send to Telegram"
            logger.error("telegram_send_failed")
            errors.append(error_msg)
    except Exception as e:
        error_msg = f"Error sending to Telegram: {e}"
        logger.error("telegram_error", error=str(e))
        errors.append(error_msg)

        # Send error notification
        try:
            await sender.send_error(error_msg)
        except Exception:
            pass

    # Record seen articles for deduplication
    if telegram_message_id and analyzed_articles:
        try:
            record_seen_articles(
                [a.article for a in analyzed_articles],
                settings.dedup_history_path,
                settings.dedup_history_days,
            )
            logger.info("dedup_history_updated", count=len(analyzed_articles))
        except Exception as e:
            error_msg = f"Error updating dedup history: {e}"
            logger.error("dedup_history_error", error=str(e))
            errors.append(error_msg)

    logger.info(
        "send_node_complete",
        telegram_sent=telegram_message_id is not None,
        report_saved=report_path is not None,
    )

    return {
        **state,
        "telegram_message_id": telegram_message_id,
        "report_path": str(report_path) if report_path else None,
        "errors": errors,
    }
