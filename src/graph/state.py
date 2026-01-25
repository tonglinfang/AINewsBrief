"""State definition for the brief workflow."""

from datetime import datetime
from typing import List, Optional, TypedDict
from src.models.article import Article
from src.models.analysis import AnalysisResult
from src.models.report import DailyReport


class BriefState(TypedDict):
    """State for the AI News Brief workflow.

    This state is passed through all nodes in the LangGraph workflow.
    """

    # Input parameters
    date: datetime  # Report date
    max_articles: int  # Maximum articles to include

    # Article processing stages
    raw_articles: List[Article]  # All fetched articles
    filtered_articles: List[Article]  # After filtering and deduplication
    analyzed_articles: List[AnalysisResult]  # After LLM analysis

    # Output
    report: Optional[DailyReport]  # Final formatted report
    report_path: Optional[str]  # Path to saved report file
    telegram_message_id: Optional[str]  # Telegram message ID

    # Error tracking
    errors: List[str]  # List of error messages
