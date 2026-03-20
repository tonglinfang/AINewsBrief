"""Deep analyzer for high-value articles with controlled concurrency and failover."""

import asyncio
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
    PracticalGuidance,
)
from src.analyzers.llm_analyzer import _build_llm_chain, is_rate_limit_error
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("deep_analyzer")


class DeepAnalyzer:
    """Deep analyzer for high-value articles.

    Improvements over the original:
    - Reuses the shared LLM chain (primary + optional fallback) from llm_analyzer,
      so no duplicate provider connections are opened.
    - Runs concurrent analyses bounded by settings.deep_analyze_concurrency
      (default 3) via asyncio.Semaphore, cutting wall-clock time by ~3x while
      still avoiding rate-limit bursts.
    """

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

    def __init__(self) -> None:
        # Reuse the same LLM chain as LLMAnalyzer to avoid duplicate connections.
        self._llms = _build_llm_chain()

        # Semaphore caps concurrent LLM calls to avoid rate-limit bursts.
        # Value is configurable via DEEP_ANALYZE_CONCURRENCY (default 3).
        self._semaphore = asyncio.Semaphore(settings.deep_analyze_concurrency)

        logger.info(
            "deep_analyzer_initialized",
            concurrency=settings.deep_analyze_concurrency,
            has_fallback=len(self._llms) > 1,
        )

    # ------------------------------------------------------------------
    # Internal retry + failover helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_rate_limit(exc: Exception) -> bool:
        return is_rate_limit_error(exc)

    @retry(
        retry=retry_if_exception(_is_rate_limit),
        stop=stop_after_attempt(4),
        wait=wait_exponential_jitter(initial=1, max=10),
        reraise=True,
    )
    async def _call_llm(self, llm, messages: list) -> object:
        """Single LLM call with rate-limit retry."""
        return await llm.ainvoke(messages)

    async def _invoke_with_failover(self, messages: list) -> object:
        """Attempt each LLM in the chain, falling through on non-rate-limit errors."""
        last_exc: Optional[Exception] = None
        for idx, llm in enumerate(self._llms):
            try:
                return await self._call_llm(llm, messages)
            except Exception as exc:
                last_exc = exc
                if idx < len(self._llms) - 1:
                    logger.warning(
                        "deep_llm_provider_failed_switching_to_fallback",
                        error=str(exc),
                    )
                else:
                    logger.error("deep_all_llm_providers_failed", error=str(exc))
        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Selection logic
    # ------------------------------------------------------------------

    def should_deep_analyze(self, analysis: AnalysisResult) -> bool:
        """Return True when an article warrants deep analysis.

        Criteria:
          - importance_score >= deep_analysis_threshold (default 8), or
          - Breaking News / Research categories with score >= 7.
        """
        threshold = settings.deep_analysis_threshold
        if analysis.importance_score >= threshold:
            return True
        if analysis.category in ("Breaking News", "Research") and analysis.importance_score >= 7:
            return True
        return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_batch(self, analyzed_articles: List[AnalysisResult]) -> List[DeepAnalysis]:
        """Perform deep analysis on qualifying articles concurrently.

        Uses asyncio.Semaphore to cap parallelism at settings.deep_analyze_concurrency
        (default 3), reducing wall-clock time vs. the previous sequential approach
        while staying within rate-limit budgets.

        Args:
            analyzed_articles: Results from the shallow analysis stage.

        Returns:
            Deep analysis results for articles that met the importance threshold.
        """
        candidates = [a for a in analyzed_articles if self.should_deep_analyze(a)]

        if not candidates:
            logger.info("no_articles_for_deep_analysis")
            return []

        logger.info(
            "deep_analyze_batch_start",
            total=len(analyzed_articles),
            selected=len(candidates),
            concurrency=settings.deep_analyze_concurrency,
        )

        async def _bounded(analysis: AnalysisResult) -> Optional[DeepAnalysis]:
            """Wrap analyze() with the semaphore so at most N tasks run at once."""
            async with self._semaphore:
                try:
                    result = await self.analyze(analysis)
                    logger.info("deep_analysis_done", title=analysis.title_cn[:50])
                    return result
                except Exception as exc:
                    logger.warning(
                        "deep_analysis_failed",
                        title=analysis.title_cn[:50],
                        error=str(exc),
                    )
                    return None

        raw_results = await asyncio.gather(*[_bounded(a) for a in candidates])
        results = [r for r in raw_results if r is not None]

        logger.info(
            "deep_analyze_batch_done",
            successful=len(results),
            failed=len(candidates) - len(results),
        )
        return results

    async def analyze(self, analysis: AnalysisResult) -> DeepAnalysis:
        """Deep-analyze a single article.

        Sends up to 5000 characters of content (vs. 2000 for shallow analysis)
        to capture more technical detail.

        Args:
            analysis: Shallow analysis result containing the original article.

        Returns:
            DeepAnalysis with multi-dimensional insights.
        """
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
            content=content_preview,
        )

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        response = await self._invoke_with_failover(messages)
        deep_data = self._parse_response(response.content)

        return DeepAnalysis(
            article_url=analysis.article.url,
            technical_context=TechnicalContext(**deep_data["technical_context"]),
            key_insights=deep_data["key_insights"],
            impact=ImpactAnalysis(**deep_data["impact"]),
            guidance=(
                PracticalGuidance(**deep_data["guidance"])
                if deep_data.get("guidance")
                else None
            ),
            controversies=deep_data.get("controversies", []),
            open_questions=deep_data.get("open_questions", []),
            related_resources=deep_data.get("related_resources", []),
        )

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, response_text: str) -> dict:
        """Extract and validate the deep-analysis JSON from the LLM response."""
        try:
            json_str = self._extract_json(response_text)
            data = json.loads(json_str)
            return self._validate_data(data)
        except Exception as exc:
            logger.error(
                "deep_analysis_parse_error",
                error=str(exc),
                response_preview=response_text[:500],
            )
            raise

    @staticmethod
    def _extract_json(text: str) -> str:
        """Pull the first JSON object from a (possibly markdown-wrapped) string."""
        for pattern in (
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'(\{[\s\S]*\})',
        ):
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return text

    @staticmethod
    def _validate_data(data: dict) -> dict:
        """Ensure required top-level and nested fields are present."""
        required_top = ("technical_context", "key_insights", "impact")
        for field in required_top:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        if "background" not in data["technical_context"]:
            raise ValueError("Missing technical_context.background")

        impact = data["impact"]
        if "immediate_impact" not in impact or "long_term_impact" not in impact:
            raise ValueError("Missing impact.immediate_impact or impact.long_term_impact")

        # Default impact_level when the LLM omits it.
        impact.setdefault("impact_level", 3)

        return data
