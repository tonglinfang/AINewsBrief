"""Markdown formatter for daily reports."""

from datetime import datetime
from typing import Dict, List
from collections import defaultdict
from jinja2 import Template
from src.models.analysis import AnalysisResult, CategoryType
from src.models.report import DailyReport
from src.config import settings


class MarkdownFormatter:
    """Formats analysis results into markdown reports."""

    # Category emojis
    CATEGORY_EMOJIS = {
        "Breaking News": "🔥",
        "Research": "🔬",
        "Tools/Products": "🛠️",
        "Business": "💼",
        "Tutorial": "📚",
    }

    CATEGORY_NAMES_CN = {
        "Breaking News": "重大新聞",
        "Research": "學術研究",
        "Tools/Products": "工具與產品",
        "Business": "商業動態",
        "Tutorial": "技術教程",
    }

    TEMPLATE = """📰 AI快訊 {{ date }}
━━━━━━━━━━━━━━━━━━━━━
📊 今日共 {{ total_articles }} 則新聞
{% for category, articles in articles_by_category.items() %}
{% if articles %}
━━━━━━━━━━━━━━━━━━━━━
{{ category_emoji[category] }} {{ category_names[category] }}（{{ articles|length }}）
{% for analysis in articles %}

▸ {{ analysis.title_cn }}
  {{ analysis.summary }}
  💡 {{ analysis.insight }}
  📰 {{ analysis.article.source }} {{ importance_stars(analysis.importance_score) }}
  🔗 {{ analysis.article.url }}
{% endfor %}
{% endif %}
{% endfor %}

━━━━━━━━━━━━━━━━━━━━━
來源：AINewsBrief
Powered by {{ llm_provider|capitalize }} {{ llm_model }}
"""

    def __init__(self):
        """Initialize markdown formatter."""
        self.template = Template(self.TEMPLATE)

    @staticmethod
    def _importance_stars(score: int) -> str:
        """Convert importance score to star rating.

        Args:
            score: Importance score (0-10)

        Returns:
            Star rating string (e.g., "⭐⭐⭐" for score 6-7)
        """
        if score >= 9:
            return "⭐⭐⭐⭐⭐"
        elif score >= 7:
            return "⭐⭐⭐⭐"
        elif score >= 5:
            return "⭐⭐⭐"
        elif score >= 3:
            return "⭐⭐"
        else:
            return "⭐"

    def format(self, date: datetime, analyzed_articles: List[AnalysisResult]) -> DailyReport:
        """Format analyzed articles into a daily report.

        Args:
            date: Report date
            analyzed_articles: List of analyzed articles

        Returns:
            DailyReport object
        """
        # Group articles by category and sort by importance
        articles_by_category = self._group_by_category(analyzed_articles)

        # Calculate statistics
        total_articles = len(analyzed_articles)
        average_importance = (
            sum(a.importance_score for a in analyzed_articles) / total_articles
            if total_articles > 0
            else 0
        )

        # Generate markdown
        markdown_content = self.template.render(
            date=date.strftime("%Y-%m-%d %H:%M:%S"),
            total_articles=total_articles,
            average_importance=f"{average_importance:.1f}",
            articles_by_category=articles_by_category,
            category_emoji=self.CATEGORY_EMOJIS,
            category_names=self.CATEGORY_NAMES_CN,
            format_time=self._format_relative_time,
            importance_stars=self._importance_stars,
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
        )

        return DailyReport(
            date=date,
            articles_by_category=articles_by_category,
            markdown_content=markdown_content,
            total_articles=total_articles,
            average_importance=average_importance,
        )

    def _group_by_category(
        self, articles: List[AnalysisResult]
    ) -> Dict[CategoryType, List[AnalysisResult]]:
        """Group articles by category and sort by importance.

        Args:
            articles: List of analyzed articles

        Returns:
            Dict mapping category to sorted list of articles
        """
        grouped: Dict[CategoryType, List[AnalysisResult]] = defaultdict(list)

        for article in articles:
            grouped[article.category].append(article)

        # Sort each category by importance score (descending)
        for category in grouped:
            grouped[category].sort(key=lambda x: x.importance_score, reverse=True)

        # Return in desired order
        ordered_categories = ["Breaking News", "Research", "Tools/Products", "Business", "Tutorial"]
        return {cat: grouped[cat] for cat in ordered_categories if cat in grouped}

    def _format_relative_time(self, dt: datetime) -> str:
        """Format datetime as relative time string.

        Args:
            dt: Datetime to format

        Returns:
            Relative time string (e.g., "2小時前")
        """
        now = datetime.now()
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)

        delta = now - dt

        if delta.days > 0:
            return f"{delta.days}天前"

        hours = delta.seconds // 3600
        if hours > 0:
            return f"{hours}小時前"

        minutes = delta.seconds // 60
        if minutes > 0:
            return f"{minutes}分鐘前"

        return "剛剛"
