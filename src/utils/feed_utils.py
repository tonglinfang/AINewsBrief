"""Shared utilities for feed parsing and content extraction."""

import email.utils
from datetime import datetime, timezone
from typing import Optional


def extract_feed_content(entry: dict) -> str:
    """Extract content from a feed entry.

    Tries multiple common feed content fields in order of preference.

    Args:
        entry: Feed entry dictionary (from feedparser)

    Returns:
        Extracted content string, empty if not found
    """
    if hasattr(entry, "content") and entry.content:
        return entry.content[0].get("value", "")

    if hasattr(entry, "summary"):
        return entry.summary

    if hasattr(entry, "description"):
        return entry.description

    return ""


def parse_feed_date(entry: dict, default: Optional[datetime] = None) -> Optional[datetime]:
    """Parse publication date from a feed entry.

    Tries standard date fields and returns None if parsing fails.

    Args:
        entry: Feed entry dictionary
        default: Default datetime if parsing fails (defaults to None)

    Returns:
        Parsed datetime with UTC timezone, or None if parsing fails
    """
    # Try standard date string fields
    date_str = entry.get("published", entry.get("updated", ""))
    if date_str:
        try:
            parsed = email.utils.parsedate_to_datetime(date_str)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            pass

    # Try struct_time format from feedparser
    import time
    for field in ["published_parsed", "updated_parsed"]:
        struct_time = getattr(entry, field, None)
        if struct_time:
            try:
                ts = time.mktime(struct_time)
                return datetime.fromtimestamp(ts, tz=timezone.utc)
            except Exception:
                pass

    return default
