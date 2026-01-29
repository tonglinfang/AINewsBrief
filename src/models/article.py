"""Article data model."""

from datetime import datetime
from typing import List
from pydantic import BaseModel, HttpUrl, Field


class Article(BaseModel):
    """Represents a news article or blog post."""

    title: str = Field(..., description="Article title")
    url: HttpUrl = Field(..., description="Article URL")
    source: str = Field(..., description="Source name (e.g., 'TechCrunch AI', 'Reddit')")
    published_at: datetime = Field(..., description="Publication timestamp")
    content: str = Field(..., description="Article content or summary")
    tags: List[str] = Field(default_factory=list, description="Article tags/keywords")
    priority: int = Field(default=5, ge=0, le=10, description="Source priority (0-10)")

    def __hash__(self):
        """Make Article hashable for deduplication."""
        return hash(str(self.url))

    def __eq__(self, other):
        """Compare articles by URL."""
        if not isinstance(other, Article):
            return False
        return str(self.url) == str(other.url)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "title": "GPT-5 Released with Breakthrough Performance",
                "url": "https://techcrunch.com/2026/01/24/gpt5-release",
                "source": "TechCrunch AI",
                "published_at": "2026-01-24T10:00:00Z",
                "content": "OpenAI announces GPT-5 with significant improvements...",
                "tags": ["LLM", "OpenAI", "GPT-5"],
            }
        }
