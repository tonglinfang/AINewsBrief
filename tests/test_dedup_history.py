"""Tests for persisted deduplication history."""

from datetime import datetime, timedelta, timezone
import json

from src.models.article import Article
from src.utils.dedup_history import (
    filter_previously_seen,
    load_dedup_history,
    record_seen_articles,
)


def test_history_filters_seen_urls(tmp_path):
    """Filter articles already present in history by URL."""
    history_path = tmp_path / "history.json"
    history_path.write_text(
        json.dumps(
            {
                "version": 1,
                "articles": [
                    {
                        "url": "https://example.com/seen",
                        "title": "Seen title",
                        "seen_at": datetime.now(timezone.utc).isoformat(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    seen_urls, seen_titles = load_dedup_history(str(history_path), max_age_days=30)
    articles = [
        Article(
            title="Seen title",
            url="https://example.com/seen",
            source="Source",
            published_at=datetime.now(timezone.utc),
            content="Content",
            tags=[],
        ),
        Article(
            title="New title",
            url="https://example.com/new",
            source="Source",
            published_at=datetime.now(timezone.utc),
            content="Content",
            tags=[],
        ),
    ]

    filtered = filter_previously_seen(articles, seen_urls, seen_titles, 0.8)
    assert len(filtered) == 1
    assert filtered[0].url == "https://example.com/new"


def test_record_seen_articles_prunes_old_entries(tmp_path):
    """Persist new entries and prune old ones."""
    history_path = tmp_path / "history.json"
    old_time = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    history_path.write_text(
        json.dumps(
            {
                "version": 1,
                "articles": [
                    {
                        "url": "https://example.com/old",
                        "title": "Old title",
                        "seen_at": old_time,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    new_article = Article(
        title="Fresh title",
        url="https://example.com/fresh",
        source="Source",
        published_at=datetime.now(timezone.utc),
        content="Content",
        tags=[],
    )
    record_seen_articles([new_article], str(history_path), max_age_days=30)

    seen_urls, seen_titles = load_dedup_history(str(history_path), max_age_days=30)
    assert "https://example.com/old" not in seen_urls
    assert "https://example.com/fresh" in seen_urls
    assert "Fresh title" in seen_titles
