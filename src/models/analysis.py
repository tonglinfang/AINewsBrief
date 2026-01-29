"""Analysis result data model."""

from typing import Literal
from pydantic import BaseModel, Field
from src.models.article import Article


# Category types for AI news
CategoryType = Literal[
    "Breaking News",  # 重大新聞發布
    "Research",  # 學術研究和論文
    "Tools/Products",  # 新工具、產品、服務
    "Business",  # 商業動態、融資、併購
    "Tutorial",  # 教程、技術文章
]


class AnalysisResult(BaseModel):
    """LLM analysis result for an article."""

    article: Article = Field(..., description="Original article")
    title_cn: str = Field(..., description="Translated Chinese title", max_length=200)
    summary: str = Field(..., description="AI-generated summary (max 100 chars)", max_length=150)
    category: CategoryType = Field(..., description="Article category")
    importance_score: int = Field(
        ..., ge=0, le=10, description="Importance score from 0-10"
    )
    ai_relevance_score: int = Field(
        default=10, ge=0, le=10, description="AI relevance score from 0-10"
    )
    insight: str = Field(
        ..., description="Key insight: why important and impact (max 50 chars)", max_length=100
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "article": {
                    "title": "GPT-5 Released",
                    "url": "https://example.com",
                    "source": "TechCrunch",
                    "published_at": "2026-01-24T10:00:00Z",
                    "content": "...",
                    "tags": ["LLM"],
                },
                "summary": "OpenAI releases GPT-5 with 10x performance improvement over GPT-4",
                "category": "Breaking News",
                "importance_score": 9,
                "insight": "Major leap in LLM capabilities will impact entire AI ecosystem",
            }
        }
