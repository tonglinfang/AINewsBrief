"""Article deduplication utilities."""

from typing import List
from difflib import SequenceMatcher
from src.models.article import Article


def deduplicate_articles(
    articles: List[Article], title_similarity_threshold: float = 0.8
) -> List[Article]:
    """Remove duplicate articles based on URL and title similarity.

    Args:
        articles: List of articles to deduplicate
        title_similarity_threshold: Minimum similarity to consider titles as duplicates

    Returns:
        Deduplicated list of articles
    """
    if not articles:
        return []

    seen_urls = set()
    seen_titles = []
    unique_articles = []

    for article in articles:
        # Check URL exact match
        url_str = str(article.url)
        if url_str in seen_urls:
            continue

        # Check title similarity
        is_duplicate = False
        for existing_title in seen_titles:
            similarity = _calculate_similarity(article.title, existing_title)
            if similarity >= title_similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_urls.add(url_str)
            seen_titles.append(article.title)
            unique_articles.append(article)

    return unique_articles


def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two strings.

    Args:
        text1: First string
        text2: Second string

    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
