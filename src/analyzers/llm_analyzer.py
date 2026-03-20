"""LLM-based article analyzer with multi-provider support, shared LLM cache, and failover."""

import asyncio
import json
import re
from typing import List, Optional, Dict, Tuple
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential_jitter
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from src.models.article import Article
from src.models.analysis import AnalysisResult, CategoryType
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("llm_analyzer")

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_PROVIDER_CONFIGS: Dict[str, dict] = {
    "anthropic": {
        "api_key_attr": "anthropic_api_key",
        "api_key_name": "ANTHROPIC_API_KEY",
        "module": "langchain_anthropic",
        "class_name": "ChatAnthropic",
        "api_key_param": "api_key",
        "max_tokens_param": "max_tokens",
    },
    "openai": {
        "api_key_attr": "openai_api_key",
        "api_key_name": "OPENAI_API_KEY",
        "module": "langchain_openai",
        "class_name": "ChatOpenAI",
        "api_key_param": "api_key",
        "max_tokens_param": "max_tokens",
    },
    "google": {
        "api_key_attr": "google_api_key",
        "api_key_name": "GOOGLE_API_KEY",
        "module": "langchain_google_genai",
        "class_name": "ChatGoogleGenerativeAI",
        "api_key_param": "google_api_key",
        "max_tokens_param": "max_output_tokens",
    },
    "zhipu": {
        "api_key_attr": "zhipu_api_key",
        "api_key_name": "ZHIPU_API_KEY",
        "module": "langchain_community.chat_models",
        "class_name": "ChatZhipuAI",
        "api_key_param": "api_key",
        "max_tokens_param": "max_tokens",
    },
}

# Module-level LLM cache keyed by (provider, model) to avoid duplicate connections.
_llm_cache: Dict[Tuple[str, str], BaseChatModel] = {}


def create_llm(provider: Optional[str] = None, model: Optional[str] = None) -> BaseChatModel:
    """Return a (cached) LLM instance for the given provider and model.

    Instances are shared across the process lifetime so that LLMAnalyzer and
    DeepAnalyzer reuse the same connection pool instead of opening two separate
    ones for the same endpoint.

    Args:
        provider: Provider name; defaults to settings.llm_provider.
        model: Model name; defaults to settings.llm_model.

    Returns:
        Configured BaseChatModel instance.

    Raises:
        ValueError: If the provider is unsupported or its API key is missing.
    """
    provider = provider or settings.llm_provider
    model = model or settings.llm_model
    cache_key = (provider, model)

    if cache_key in _llm_cache:
        return _llm_cache[cache_key]

    config = _PROVIDER_CONFIGS.get(provider)
    if not config:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported: {', '.join(_PROVIDER_CONFIGS)}"
        )

    api_key = getattr(settings, config["api_key_attr"])
    if not api_key:
        raise ValueError(
            f"{config['api_key_name']} is required for {provider.capitalize()} provider"
        )

    import importlib
    module = importlib.import_module(config["module"])
    llm_class = getattr(module, config["class_name"])

    kwargs = {
        "model": model,
        config["api_key_param"]: api_key,
        "temperature": settings.llm_temperature,
        config["max_tokens_param"]: settings.llm_max_tokens,
    }

    instance = llm_class(**kwargs)
    _llm_cache[cache_key] = instance
    logger.info("llm_created", provider=provider, model=model)
    return instance


def _build_llm_chain() -> List[BaseChatModel]:
    """Build the ordered list of LLM instances: [primary, fallback?].

    Returns:
        List with at least the primary LLM; includes fallback when configured.
    """
    chain: List[BaseChatModel] = [create_llm()]

    if settings.llm_fallback_provider:
        fallback_model = settings.llm_fallback_model or settings.llm_model
        try:
            fallback_llm = create_llm(
                provider=settings.llm_fallback_provider,
                model=fallback_model,
            )
            chain.append(fallback_llm)
            logger.info(
                "llm_fallback_configured",
                fallback_provider=settings.llm_fallback_provider,
                fallback_model=fallback_model,
            )
        except ValueError as exc:
            # Missing API key for fallback is non-fatal; log and continue without it.
            logger.warning("llm_fallback_skipped", reason=str(exc))

    return chain


# ---------------------------------------------------------------------------
# Rate-limit detection helper (shared between analyzers)
# ---------------------------------------------------------------------------

def is_rate_limit_error(exc: Exception) -> bool:
    """Return True when the exception indicates an API rate limit."""
    message = str(exc).lower()
    return "429" in message or "too many requests" in message or "rate limit" in message


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class LLMAnalyzer:
    """Analyzes articles using a configurable LLM with optional failover."""

    SYSTEM_PROMPT = """你是一位 AI 技術專家，負責分析 AI 新聞文章和研究論文。

你的任務是為每篇文章提供：
1. **中文標題** (title_cn): 將文章標題翻譯為繁體中文，保持專業術語準確
2. **摘要** (summary): 100字以內的繁體中文精煉摘要，突出核心內容
3. **分類** (category): 選擇最合適的類別：
   - "Breaking News": 重大新聞發布、產品發布
   - "Research": 學術研究、論文
   - "Tools/Products": 新工具、產品、開源項目
   - "Business": 商業動態、融資、併購
   - "Tutorial": 教程、技術文章、實踐指南
4. **重要性評分** (importance_score): 0-10分，評估文章的重要性和影響力
   - 9-10: 行業突破性進展
   - 7-8: 重要新聞或研究
   - 5-6: 有價值的更新
   - 0-4: 一般性內容
5. **AI 相關性評分** (ai_relevance_score): 0-10分，評估文章與 AI 技術本身的相關程度
   - 9-10: AI 核心技術（新模型架構、訓練方法、AI 系統、LLM、神經網路等）
   - 7-8: AI 工具/平台/框架（PyTorch、TensorFlow、AI 開發工具等）
   - 5-6: AI 產業動態（AI 公司新聞、融資、政策等）
   - 3-4: AI 應用案例（將 AI 用於其他領域，如醫療、體育、農業等，但重點不在 AI 技術本身）
   - 0-2: 與 AI 幾乎無關（只是標題提到 AI，或只是使用 ML 做數據分析的其他領域研究）
6. **關鍵洞察** (insight): 50字以內的繁體中文關鍵洞察，說明為什麼重要、有什麼影響

請以 JSON 格式返回結果（確保所有中文內容為繁體中文）：
{
  "title_cn": "文章中文標題...",
  "summary": "文章摘要...",
  "category": "Breaking News",
  "importance_score": 8,
  "ai_relevance_score": 9,
  "insight": "關鍵洞察..."
}"""

    ANALYSIS_PROMPT_TEMPLATE = """請分析以下文章：

**標題**: {title}

**來源**: {source}

**內容**:
{content}

請提供分析結果（JSON 格式）："""

    def __init__(self) -> None:
        # Ordered list of LLMs: primary first, optional fallback second.
        self._llms = _build_llm_chain()
        logger.info(
            "llm_analyzer_initialized",
            provider=settings.llm_provider,
            model=settings.llm_model,
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
    async def _call_llm(self, llm: BaseChatModel, messages: list) -> object:
        """Single LLM call with rate-limit retry (up to 4 attempts)."""
        return await llm.ainvoke(messages)

    async def _invoke_with_failover(self, messages: list) -> object:
        """Try each LLM in the chain; fall through to the next on non-rate-limit failure.

        Rate-limit errors are retried on the *same* provider (via _call_llm).
        Any other error immediately tries the next provider in the chain.
        If all providers fail, the last exception is re-raised.
        """
        last_exc: Optional[Exception] = None
        for idx, llm in enumerate(self._llms):
            try:
                return await self._call_llm(llm, messages)
            except Exception as exc:
                last_exc = exc
                if idx < len(self._llms) - 1:
                    logger.warning(
                        "llm_provider_failed_switching_to_fallback",
                        failed_provider=settings.llm_provider if idx == 0
                            else settings.llm_fallback_provider,
                        error=str(exc),
                    )
                else:
                    logger.error("all_llm_providers_failed", error=str(exc))
        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_batch(self, articles: List[Article]) -> List[AnalysisResult]:
        """Analyze multiple articles in batches of 5 to respect rate limits.

        Args:
            articles: Articles to analyze.

        Returns:
            Successfully analyzed results (failed articles are silently dropped).
        """
        batch_size = 5
        results: List[AnalysisResult] = []

        for i in range(0, len(articles), batch_size):
            batch = articles[i: i + batch_size]
            batch_results = await asyncio.gather(
                *[self.analyze(article) for article in batch],
                return_exceptions=True,
            )

            for result in batch_results:
                if isinstance(result, AnalysisResult):
                    results.append(result)
                elif isinstance(result, Exception):
                    logger.warning("article_analysis_error", error=str(result))

            # Brief pause between batches to avoid bursting rate limits.
            if i + batch_size < len(articles):
                await asyncio.sleep(1)

        return results

    async def analyze(self, article: Article) -> AnalysisResult:
        """Analyze a single article and return a structured result.

        On failure returns a zero-scored placeholder that the filter node will
        discard, preserving pipeline continuity.

        Args:
            article: Article to analyze.

        Returns:
            AnalysisResult with LLM-generated fields.
        """
        try:
            content_preview = article.content[: settings.llm_content_preview_length]
            user_prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
                title=article.title,
                source=article.source,
                content=content_preview,
            )

            messages = [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            response = await self._invoke_with_failover(messages)
            analysis_data = self._parse_response(response.content)

            return AnalysisResult(
                article=article,
                title_cn=analysis_data["title_cn"][:200],
                summary=analysis_data["summary"][:150],
                category=analysis_data["category"],
                importance_score=min(10, max(0, analysis_data["importance_score"])),
                ai_relevance_score=min(10, max(0, analysis_data.get("ai_relevance_score", 10))),
                insight=analysis_data["insight"][:100],
            )

        except Exception as exc:
            logger.warning(
                "article_analysis_failed",
                title=article.title[:50],
                error=str(exc),
            )
            # Score 0 ensures this result is discarded by the importance/relevance filter.
            return AnalysisResult(
                article=article,
                title_cn=article.title[:200],
                summary="Analysis failed; see original article",
                category="Tools/Products",
                importance_score=0,
                ai_relevance_score=0,
                insight="Automatic analysis failed",
            )

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, response_text: str) -> dict:
        """Extract and validate JSON from the LLM response."""
        json_str = self._extract_json(response_text)
        data = json.loads(json_str)
        return self._validate_data(data, response_text)

    @staticmethod
    def _extract_json(text: str) -> str:
        """Pull the first JSON object out of a (possibly markdown-wrapped) response."""
        text = text.strip()
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
    def _validate_data(data: dict, response_text: str) -> dict:
        """Ensure required fields are present and normalize optional ones."""
        required = ["title_cn", "summary", "category", "importance_score", "insight"]
        for field in required:
            if field not in data:
                logger.error(
                    "llm_response_missing_field",
                    field=field,
                    response_preview=response_text[:200],
                )
                raise ValueError(f"Missing required field: {field}")

        # Backward-compatibility: older prompts may omit ai_relevance_score.
        data.setdefault("ai_relevance_score", 5)

        valid_categories = ["Breaking News", "Research", "Tools/Products", "Business", "Tutorial"]
        if data["category"] not in valid_categories:
            data["category"] = "Tools/Products"

        return data
