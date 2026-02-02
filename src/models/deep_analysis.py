"""Deep analysis data models for high-value articles."""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TechnicalContext(BaseModel):
    """Technical background context."""

    background: str = Field(
        ...,
        max_length=500,
        description="Technical background explanation (200-300 chars)"
    )
    key_technologies: List[str] = Field(
        default_factory=list,
        description="List of key technologies"
    )
    prerequisites: Optional[str] = Field(
        None,
        max_length=300,
        description="Prerequisites for understanding"
    )


class ImpactAnalysis(BaseModel):
    """Impact scope analysis."""

    immediate_impact: str = Field(
        ...,
        max_length=300,
        description="Immediate impact (100-200 chars)"
    )
    long_term_impact: str = Field(
        ...,
        max_length=300,
        description="Long-term impact (100-200 chars)"
    )
    affected_sectors: List[str] = Field(
        default_factory=list,
        description="Affected sectors/domains"
    )
    impact_level: int = Field(
        ...,
        ge=1,
        le=5,
        description="Impact level from 1-5"
    )


class PracticalGuidance(BaseModel):
    """Practical guidance for different audiences."""

    for_developers: Optional[str] = Field(
        None,
        max_length=300,
        description="Advice for developers"
    )
    for_researchers: Optional[str] = Field(
        None,
        max_length=300,
        description="Advice for researchers"
    )
    for_business: Optional[str] = Field(
        None,
        max_length=300,
        description="Advice for business/enterprises"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="Specific action items"
    )


class DeepAnalysis(BaseModel):
    """Deep analysis result for high-value articles."""

    # Link to original analysis
    article_url: str = Field(..., description="Article URL as ID")

    # Technical depth
    technical_context: TechnicalContext = Field(..., description="Technical background")
    key_insights: List[str] = Field(..., description="3-5 key insights")

    # Impact analysis
    impact: ImpactAnalysis = Field(..., description="Impact scope analysis")

    # Practical guidance
    guidance: Optional[PracticalGuidance] = Field(
        None,
        description="Practical guidance (optional)"
    )

    # Controversies and discussions
    controversies: List[str] = Field(
        default_factory=list,
        description="Controversial points"
    )
    open_questions: List[str] = Field(
        default_factory=list,
        description="Open questions to be resolved"
    )

    # Related resources
    related_resources: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Related resources [{'title': '...', 'url': '...', 'type': 'paper|code|blog'}]"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "article_url": "https://example.com/article",
                "technical_context": {
                    "background": "Transformer架構自2017年提出以來已成為NLP領域的主流...",
                    "key_technologies": ["Multi-head Attention", "Positional Encoding"],
                    "prerequisites": "需要了解神經網絡基礎和注意力機制"
                },
                "key_insights": [
                    "首次實現零樣本推理能力",
                    "訓練成本降低40%",
                    "推理速度提升3倍"
                ],
                "impact": {
                    "immediate_impact": "將直接影響所有使用LLM的應用開發...",
                    "long_term_impact": "可能重新定義AI應用開發範式...",
                    "affected_sectors": ["NLP", "代碼生成", "智能助手"],
                    "impact_level": 5
                },
                "guidance": {
                    "for_developers": "開始評估遷移現有應用到新模型...",
                    "action_items": ["評估API兼容性", "測試性能提升", "更新文檔"]
                }
            }
        }
