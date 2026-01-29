"""Tests for data models."""

import pytest
from datetime import datetime
from src.models.article import Article
from src.models.analysis import AnalysisResult


def test_article_creation():
    """Test creating an Article instance."""
    article = Article(
        title="Test Article",
        url="https://example.com/test",
        source="Test Source",
        published_at=datetime.now(),
        content="Test content that is long enough to pass validation",
        tags=["test", "ai"],
    )

    assert article.title == "Test Article"
    assert str(article.url) == "https://example.com/test"
    assert article.source == "Test Source"
    assert "test" in article.tags


def test_article_equality():
    """Test article equality based on URL."""
    now = datetime.now()

    article1 = Article(
        title="Article 1",
        url="https://example.com/same",
        source="Source 1",
        published_at=now,
        content="Content 1",
        tags=[],
    )

    article2 = Article(
        title="Article 2",
        url="https://example.com/same",
        source="Source 2",
        published_at=now,
        content="Content 2",
        tags=[],
    )

    assert article1 == article2
    assert hash(article1) == hash(article2)


def test_analysis_result_validation():
    """Test AnalysisResult validation."""
    article = Article(
        title="Test",
        url="https://example.com",
        source="Test",
        published_at=datetime.now(),
        content="Test content",
        tags=[],
    )

    analysis = AnalysisResult(
        article=article,
        title_cn="測試標題",
        summary="Test summary",
        category="Breaking News",
        importance_score=8,
        insight="Test insight",
    )

    assert analysis.importance_score >= 0
    assert analysis.importance_score <= 10
    assert analysis.category in [
        "Breaking News",
        "Research",
        "Tools/Products",
        "Business",
        "Tutorial",
    ]


def test_analysis_result_invalid_score():
    """Test that invalid importance scores are handled."""
    article = Article(
        title="Test",
        url="https://example.com",
        source="Test",
        published_at=datetime.now(),
        content="Test content",
        tags=[],
    )

    with pytest.raises(ValueError):
        AnalysisResult(
            article=article,
            title_cn="測試標題",
            summary="Test",
            category="Breaking News",
            importance_score=15,  # Invalid: > 10
            insight="Test",
        )


def test_analysis_result_ai_relevance_score():
    """Test AnalysisResult with ai_relevance_score."""
    article = Article(
        title="Test",
        url="https://example.com",
        source="Test",
        published_at=datetime.now(),
        content="Test content",
        tags=[],
    )

    # Test with explicit ai_relevance_score
    analysis = AnalysisResult(
        article=article,
        title_cn="測試標題",
        summary="Test summary",
        category="Research",
        importance_score=8,
        ai_relevance_score=9,
        insight="Test insight",
    )

    assert analysis.ai_relevance_score == 9
    assert analysis.ai_relevance_score >= 0
    assert analysis.ai_relevance_score <= 10


def test_analysis_result_ai_relevance_default():
    """Test AnalysisResult ai_relevance_score default value."""
    article = Article(
        title="Test",
        url="https://example.com",
        source="Test",
        published_at=datetime.now(),
        content="Test content",
        tags=[],
    )

    # Test without ai_relevance_score (should default to 10)
    analysis = AnalysisResult(
        article=article,
        title_cn="測試標題",
        summary="Test summary",
        category="Breaking News",
        importance_score=8,
        insight="Test insight",
    )

    assert analysis.ai_relevance_score == 10


def test_analysis_result_invalid_ai_relevance():
    """Test that invalid ai_relevance_score is handled."""
    article = Article(
        title="Test",
        url="https://example.com",
        source="Test",
        published_at=datetime.now(),
        content="Test content",
        tags=[],
    )

    with pytest.raises(ValueError):
        AnalysisResult(
            article=article,
            title_cn="測試標題",
            summary="Test",
            category="Breaking News",
            importance_score=8,
            ai_relevance_score=15,  # Invalid: > 10
            insight="Test",
        )
