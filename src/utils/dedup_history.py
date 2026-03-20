"""Persisted deduplication helpers for cross-run article filtering."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, List, Set, Tuple
from difflib import SequenceMatcher

from src.models.article import Article


def load_dedup_history(
    path: str, max_age_days: int
) -> Tuple[Set[str], List[str]]:
    """Load previously seen URLs and titles from the history file.

    Entries older than max_age_days are pruned in memory (not on disk; the
    next successful write will flush the pruned state).

    Args:
        path: Path to the history JSON file.
        max_age_days: Discard entries older than this many days.

    Returns:
        Tuple of (seen_urls set, seen_titles list).
    """
    records = _read_history(path)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    active = [r for r in records if _parse_seen_at(r.get("seen_at")) >= cutoff]
    return (
        {r["url"] for r in active if r.get("url")},
        [r["title"] for r in active if r.get("title")],
    )


def filter_previously_seen(
    articles: Iterable[Article],
    seen_urls: Set[str],
    seen_titles: List[str],
    title_similarity_threshold: float,
) -> List[Article]:
    """Remove articles already present in the deduplication history.

    Deduplication uses two signals:
      1. Exact URL match.
      2. Title similarity >= title_similarity_threshold (default 0.8).

    Args:
        articles: Candidate articles to filter.
        seen_urls: Set of previously seen URLs.
        seen_titles: List of previously seen titles.
        title_similarity_threshold: Minimum SequenceMatcher ratio to consider a duplicate.

    Returns:
        Articles not found in the history.
    """
    filtered: List[Article] = []
    for article in articles:
        url_str = str(article.url)
        if url_str in seen_urls:
            continue

        is_duplicate = any(
            _calculate_similarity(article.title, existing) >= title_similarity_threshold
            for existing in seen_titles
        )
        if not is_duplicate:
            filtered.append(article)

    return filtered


def record_seen_articles(
    articles: Iterable[Article], path: str, max_age_days: int
) -> None:
    """Persist newly sent articles so future runs can deduplicate against them.

    The write is atomic: data is first written to a sibling temp file, then
    renamed over the target path.  This prevents a mid-write crash from
    leaving a corrupt or truncated history file.

    Args:
        articles: Articles to record.
        path: Path to the history JSON file.
        max_age_days: Retention window; older entries are pruned before writing.
    """
    records = _read_history(path)

    # Drop expired entries before appending new ones.
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

    _write_history_atomic(path, records)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_history(path: str) -> List[dict]:
    """Read and parse the history JSON file; return an empty list on any error."""
    history_path = Path(path)
    if not history_path.exists():
        return []

    try:
        data = json.loads(history_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    # Support both the legacy list format and the current versioned dict format.
    if isinstance(data, dict):
        records = data.get("articles", [])
    elif isinstance(data, list):
        records = data
    else:
        return []

    return [r for r in records if isinstance(r, dict)]


def _write_history_atomic(path: str, records: List[dict]) -> None:
    """Write the history file atomically using a temp file + os.replace().

    os.replace() is an atomic POSIX rename when the source and destination are
    on the same filesystem, so a crash mid-write leaves the previous file intact.

    Args:
        path: Target path for the history JSON file.
        records: Pruned list of seen-article records to persist.
    """
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {"version": 1, "articles": records}
    serialised = json.dumps(payload, ensure_ascii=True, indent=2)

    # Write to a temp file in the same directory to guarantee same-filesystem rename.
    fd, tmp_path = tempfile.mkstemp(
        dir=history_path.parent,
        prefix=".dedup_tmp_",
        suffix=".json",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(serialised)
        # Atomic rename; replaces the target even if it already exists.
        os.replace(tmp_path, history_path)
    except Exception:
        # Clean up the orphaned temp file on any failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _parse_seen_at(value: str | None) -> datetime:
    """Parse an ISO-format timestamp string; return epoch on failure."""
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
    """Return SequenceMatcher similarity ratio in [0, 1] for two strings."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
