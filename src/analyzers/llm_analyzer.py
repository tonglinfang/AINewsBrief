"""LLM-based article analyzer with multi-provider support."""

import asyncio
import json
from typing import List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from src.models.article import Article
from src.models.analysis import AnalysisResult, CategoryType
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("llm_analyzer")


def create_llm() -> BaseChatModel:
    """Create LLM instance based on configured provider.

    Returns:
        Configured LLM instance

    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    provider = settings.llm_provider

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")

        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    elif provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    elif provider == "google":
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required for Google provider")

        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=settings.llm_temperature,
            max_output_tokens=settings.llm_max_tokens,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: anthropic, openai, google"
        )


class LLMAnalyzer:
    """Analyzes articles using configurable LLM."""

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
5. **關鍵洞察** (insight): 50字以內的繁體中文關鍵洞察，說明為什麼重要、有什麼影響

請以 JSON 格式返回結果（確保所有中文內容為繁體中文）：
{
  "title_cn": "文章中文標題...",
  "summary": "文章摘要...",
  "category": "Breaking News",
  "importance_score": 8,
  "insight": "關鍵洞察..."
}"""

    ANALYSIS_PROMPT_TEMPLATE = """請分析以下文章：

**標題**: {title}

**來源**: {source}

**內容**:
{content}

請提供分析結果（JSON 格式）："""

    def __init__(self):
        """Initialize LLM analyzer with configured provider."""
        self.llm = create_llm()
        logger.info(
            "llm_initialized",
            provider=settings.llm_provider,
            model=settings.llm_model,
        )

    async def analyze_batch(self, articles: List[Article]) -> List[AnalysisResult]:
        """Analyze multiple articles concurrently.

        Args:
            articles: List of articles to analyze

        Returns:
            List of AnalysisResult objects
        """
        # Process in batches of 5 to avoid rate limits
        batch_size = 5
        results = []

        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]
            batch_results = await asyncio.gather(
                *[self.analyze(article) for article in batch], return_exceptions=True
            )

            for result in batch_results:
                if isinstance(result, AnalysisResult):
                    results.append(result)
                elif isinstance(result, Exception):
                    logger.warning("article_analysis_error", error=str(result))

            # Small delay between batches
            if i + batch_size < len(articles):
                await asyncio.sleep(1)

        return results

    async def analyze(self, article: Article) -> AnalysisResult:
        """Analyze a single article.

        Args:
            article: Article to analyze

        Returns:
            AnalysisResult object
        """
        try:
            # Prepare prompt
            content_preview = article.content[:2000]  # Limit content length
            user_prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
                title=article.title, source=article.source, content=content_preview
            )

            # Call LLM
            messages = [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]

            response = await self.llm.ainvoke(messages)

            # Parse response
            analysis_data = self._parse_response(response.content)

            # Create AnalysisResult
            return AnalysisResult(
                article=article,
                title_cn=analysis_data["title_cn"][:200],  # Enforce max length
                summary=analysis_data["summary"][:150],  # Enforce max length
                category=analysis_data["category"],
                importance_score=min(10, max(0, analysis_data["importance_score"])),
                insight=analysis_data["insight"][:100],  # Enforce max length
            )

        except Exception as e:
            logger.warning(
                "article_analysis_failed",
                title=article.title[:50],
                error=str(e),
            )
            # Return default analysis on error
            return AnalysisResult(
                article=article,
                title_cn=article.title[:200],  # Fallback to original title
                summary=article.title[:150],
                category="Tools/Products",
                importance_score=5,
                insight="分析失敗，使用預設值",
            )

    def _parse_response(self, response_text: str) -> dict:
        """Parse LLM response to extract analysis data.

        Args:
            response_text: LLM response text

        Returns:
            Dict with analysis fields
        """
        try:
            # Try to extract JSON from response
            # Handle potential markdown code blocks
            text = response_text.strip()

            # Remove markdown code blocks if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            # Parse JSON
            data = json.loads(text)

            # Validate required fields
            required_fields = ["title_cn", "summary", "category", "importance_score", "insight"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            # Validate category
            valid_categories = ["Breaking News", "Research", "Tools/Products", "Business", "Tutorial"]
            if data["category"] not in valid_categories:
                data["category"] = "Tools/Products"

            return data

        except Exception as e:
            logger.error(
                "llm_response_parse_error",
                error=str(e),
                response_preview=response_text[:200],
            )
            raise
