"""Deep analyzer for high-value articles."""

import json
import re
from typing import List, Optional
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential_jitter
from langchain_core.messages import SystemMessage, HumanMessage

from src.models.analysis import AnalysisResult
from src.models.deep_analysis import (
    DeepAnalysis,
    TechnicalContext,
    ImpactAnalysis,
    PracticalGuidance
)
from src.analyzers.llm_analyzer import create_llm
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("deep_analyzer")


class DeepAnalyzer:
    """Deep analyzer for high-value articles with multi-dimensional analysis."""

    # Deep analysis system prompt
    SYSTEM_PROMPT = """你是一位資深 AI 技術專家和產業分析師，擅長深度技術解析和趨勢洞察。

你的任務是對重要的 AI 新聞進行深度分析，提供多維度的專業見解。

請提供以下維度的分析：

1. **技術背景** (technical_context):
   - background: 200-300字的技術背景解釋，讓非專業人士也能理解核心概念
   - key_technologies: 關鍵技術名詞列表（3-5個）
   - prerequisites: 理解這篇文章需要的前置知識（可選）

2. **關鍵洞察** (key_insights): 3-5個核心要點
   - 每個洞察用一句話說明（30-50字）
   - 聚焦於"為什麼重要"而非"是什麼"
   - 提供獨到的分析視角

3. **影響分析** (impact):
   - immediate_impact: 直接影響（100-200字）- 對開發者、企業、研究者的即時影響
   - long_term_impact: 長期影響（100-200字）- 對產業、技術發展的長遠影響
   - affected_sectors: 受影響的領域列表（如 NLP、計算機視覺、代碼生成等）
   - impact_level: 影響等級 1-5（1=局部影響，5=產業級影響）

4. **實踐指導** (guidance) - 為 8 分以上文章提供:
   - for_developers: 給開發者的具體建議
   - for_researchers: 給研究者的建議
   - for_business: 給企業決策者的建議
   - action_items: 3-5個具體可執行的行動建議

5. **爭議與討論** (controversies, open_questions):
   - controversies: 業界存在的爭議點或質疑（如果有）
   - open_questions: 尚待解決的技術問題或研究方向

6. **相關資源** (related_resources) - 可選:
   - 相關論文、代碼庫、博客文章等
   - 格式: [{"title": "...", "url": "...", "type": "paper/code/blog"}]

請以標準 JSON 格式返回結果，確保所有中文為繁體中文。"""

    ANALYSIS_PROMPT = """請對以下 AI 新聞進行深度分析：

**中文標題**: {title_cn}
**原始標題**: {title_en}
**來源**: {source}
**類別**: {category}
**重要性評分**: {importance_score}/10
**AI 相關性**: {ai_relevance_score}/10

**基礎摘要**:
{summary}

**基礎洞察**:
{insight}

**完整內容** (前 5000 字符):
{content}

請提供深度分析結果（JSON 格式）："""

    def __init__(self):
        """Initialize deep analyzer."""
        self.llm = create_llm()
        logger.info("deep_analyzer_initialized")

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        """Check if exception is a rate limit error."""
        message = str(exc).lower()
        return "429" in message or "too many requests" in message or "rate limit" in message

    @retry(
        retry=retry_if_exception(_is_rate_limit_error),
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=10),
        reraise=True,
    )
    async def _ainvoke_with_retry(self, messages: List[object]):
        """Invoke LLM with retry logic."""
        return await self.llm.ainvoke(messages)

    def should_deep_analyze(self, analysis: AnalysisResult) -> bool:
        """Determine if article needs deep analysis.

        Criteria:
        1. Importance score >= deep_analysis_threshold (default 8)
        2. Or Breaking News/Research with score >= 7

        Args:
            analysis: Analysis result

        Returns:
            True if deep analysis is needed
        """
        threshold = getattr(settings, 'deep_analysis_threshold', 8)

        if analysis.importance_score >= threshold:
            return True
        if analysis.category in ["Breaking News", "Research"] and analysis.importance_score >= 7:
            return True
        return False

    async def analyze_batch(
        self,
        analyzed_articles: List[AnalysisResult]
    ) -> List[DeepAnalysis]:
        """Perform deep analysis on multiple articles.

        Args:
            analyzed_articles: List of analyzed articles

        Returns:
            List of deep analysis results
        """
        # Filter articles that need deep analysis
        articles_to_analyze = [
            a for a in analyzed_articles
            if self.should_deep_analyze(a)
        ]

        if not articles_to_analyze:
            logger.info("no_articles_for_deep_analysis")
            return []

        logger.info(
            "starting_deep_analysis",
            total=len(analyzed_articles),
            selected=len(articles_to_analyze)
        )

        # Analyze one by one (deep analysis is slower, avoid concurrent overload)
        results = []
        for analysis in articles_to_analyze:
            try:
                deep_result = await self.analyze(analysis)
                results.append(deep_result)
                logger.info(
                    "deep_analysis_completed",
                    title=analysis.title_cn[:50]
                )
            except Exception as e:
                logger.warning(
                    "deep_analysis_failed",
                    title=analysis.title_cn[:50],
                    error=str(e)
                )

        logger.info(
            "deep_analysis_batch_completed",
            successful=len(results),
            failed=len(articles_to_analyze) - len(results)
        )

        return results

    async def analyze(self, analysis: AnalysisResult) -> DeepAnalysis:
        """Perform deep analysis on a single article.

        Args:
            analysis: Basic analysis result

        Returns:
            Deep analysis result
        """
        # Prepare prompt with more content (5000 chars vs 2000)
        content_preview = analysis.article.content[:5000]
        user_prompt = self.ANALYSIS_PROMPT.format(
            title_cn=analysis.title_cn,
            title_en=analysis.article.title,
            source=analysis.article.source,
            category=analysis.category,
            importance_score=analysis.importance_score,
            ai_relevance_score=analysis.ai_relevance_score,
            summary=analysis.summary,
            insight=analysis.insight,
            content=content_preview
        )

        # Call LLM
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        response = await self._ainvoke_with_retry(messages)

        # Parse response
        deep_data = self._parse_response(response.content)

        # Build result
        return DeepAnalysis(
            article_url=analysis.article.url,
            technical_context=TechnicalContext(**deep_data["technical_context"]),
            key_insights=deep_data["key_insights"],
            impact=ImpactAnalysis(**deep_data["impact"]),
            guidance=PracticalGuidance(**deep_data["guidance"]) if deep_data.get("guidance") else None,
            controversies=deep_data.get("controversies", []),
            open_questions=deep_data.get("open_questions", []),
            related_resources=deep_data.get("related_resources", [])
        )

    def _parse_response(self, response_text: str) -> dict:
        """Parse LLM response to extract deep analysis data.

        Args:
            response_text: LLM response text

        Returns:
            Dict with deep analysis fields
        """
        try:
            # Extract JSON from response
            patterns = [
                r'```json\s*([\s\S]*?)\s*```',
                r'```\s*([\s\S]*?)\s*```',
                r'(\{[\s\S]*\})'
            ]

            json_str = None
            for pattern in patterns:
                match = re.search(pattern, response_text)
                if match:
                    json_str = match.group(1)
                    break

            if not json_str:
                json_str = response_text

            data = json.loads(json_str)

            # Validate required fields
            required = ["technical_context", "key_insights", "impact"]
            for field in required:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate nested required fields
            if "background" not in data["technical_context"]:
                raise ValueError("Missing technical_context.background")
            if "immediate_impact" not in data["impact"] or "long_term_impact" not in data["impact"]:
                raise ValueError("Missing impact.immediate_impact or impact.long_term_impact")
            if "impact_level" not in data["impact"]:
                data["impact"]["impact_level"] = 3  # Default to 3

            return data

        except Exception as e:
            logger.error(
                "deep_analysis_response_parse_error",
                error=str(e),
                response_preview=response_text[:500]
            )
            raise
