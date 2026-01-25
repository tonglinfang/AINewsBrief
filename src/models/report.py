"""Daily report data model."""

from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field
from src.models.analysis import AnalysisResult, CategoryType


class DailyReport(BaseModel):
    """Daily AI news brief report."""

    date: datetime = Field(..., description="Report generation date")
    articles_by_category: Dict[CategoryType, List[AnalysisResult]] = Field(
        ..., description="Articles grouped by category"
    )
    markdown_content: str = Field(..., description="Formatted markdown report")
    total_articles: int = Field(..., description="Total number of articles")
    average_importance: float = Field(..., description="Average importance score")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "date": "2026-01-24T08:00:00+08:00",
                "articles_by_category": {
                    "Breaking News": [],
                    "Research": [],
                },
                "markdown_content": "# 🤖 AI 資訊日報...",
                "total_articles": 45,
                "average_importance": 7.2,
            }
        }
