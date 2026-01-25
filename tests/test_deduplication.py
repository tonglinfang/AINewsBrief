"""Tests for deduplication utilities."""

from datetime import datetime
from src.models.article import Article
from src.utils.deduplication import deduplicate_articles


def test_deduplicate_by_url():
    """Test deduplication by exact URL match."""
    now = datetime.now()

    articles = [
        Article(
            title="Article 1",
            url="https://example.com/same",
            source="Source 1",
            published_at=now,
            content="Content 1",
            tags=[],
        ),
        Article(
            title="Article 2",
            url="https://example.com/same",  # Same URL
            source="Source 2",
            published_at=now,
            content="Content 2",
            tags=[],
        ),
        Article(
            title="Article 3",
            url="https://example.com/different",
            source="Source 3",
            published_at=now,
            content="Content 3",
            tags=[],
        ),
    ]

    deduplicated = deduplicate_articles(articles)

    assert len(deduplicated) == 2
    assert deduplicated[0].title == "Article 1"
    assert deduplicated[1].title == "Article 3"


def test_deduplicate_by_title_similarity():
    """Test deduplication by title similarity."""
    now = datetime.now()

    articles = [
        Article(
            title="GPT-5 Released by OpenAI",
            url="https://example.com/1",
            source="Source 1",
            published_at=now,
            content="Content 1",
            tags=[],
        ),
        Article(
            title="GPT-5 Released by OpenAI Inc",  # Very similar title
            url="https://example.com/2",
            source="Source 2",
            published_at=now,
            content="Content 2",
            tags=[],
        ),
        Article(
            title="New AI Model Announced",  # Different title
            url="https://example.com/3",
            source="Source 3",
            published_at=now,
            content="Content 3",
            tags=[],
        ),
    ]

    deduplicated = deduplicate_articles(articles, title_similarity_threshold=0.8)

    # Should remove the second article (similar title)
    assert len(deduplicated) == 2
    assert deduplicated[0].title == "GPT-5 Released by OpenAI"
    assert deduplicated[1].title == "New AI Model Announced"


def test_empty_list():
    """Test deduplication with empty list."""
    deduplicated = deduplicate_articles([])
    assert deduplicated == []
