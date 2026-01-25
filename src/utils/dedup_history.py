"""Persisted deduplication helpers for cross-run filtering."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Set, Tuple
from difflib import SequenceMatcher

from src.models.article import Article


def load_dedup_history(
    path: str, max_age_days: int
) -> Tuple[Set[str], List[str]]:
    """Load previously seen URLs and titles from history file.

    Args:
        path: Path to history JSON file
        max_age_days: Only keep entries within this many days

    Returns:
        Tuple of (seen_urls, seen_titles)
    """
    records = _read_history(path)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    pruned = [r for r in records if _parse_seen_at(r.get("seen_at")) >= cutoff]
    return {r["url"] for r in pruned if r.get("url")}, [r["title"] for r in pruned if r.get("title")]


def filter_previously_seen(
    articles: Iterable[Article],
    seen_urls: Set[str],
    seen_titles: List[str],
    title_similarity_threshold: float,
) -> List[Article]:
    """Filter out articles already seen in history."""
    filtered: List[Article] = []
    for article in articles:
        url_str = str(article.url)
        if url_str in seen_urls:
            continue

        is_duplicate = False
        for existing_title in seen_titles:
            similarity = _calculate_similarity(article.title, existing_title)
            if similarity >= title_similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            filtered.append(article)
    return filtered


def record_seen_articles(
    articles: Iterable[Article], path: str, max_age_days: int
) -> None:
    """Persist sent articles for future deduplication."""
    records = _read_history(path)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    records = [r for r in records if _parse_seen_at(r.get("seen_at")) >= cutoff]

    existing_urls = {r.get("url") for r in records if r.get("url")}
    now_iso = datetime.now(timezone.utc).isoformat()

    for article in articles:
        url_str = str(article.url)
        if url_str in existing_urls:
            continue
        records.append({"url": url_str, "title": article.title, "seen_at": now_iso})
        existing_urls.add(url_str)

    _write_history(path, records)


def _read_history(path: str) -> List[dict]:
    history_path = Path(path)
    if not history_path.exists():
        return []

    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if isinstance(data, dict):
        records = data.get("articles", [])
    elif isinstance(data, list):
        records = data
    else:
        return []

    return [r for r in records if isinstance(r, dict)]


def _write_history(path: str, records: List[dict]) -> None:
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "articles": records}
    history_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _parse_seen_at(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _calculate_similarity(text1: str, text2: str) -> float:
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
