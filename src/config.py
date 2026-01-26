"""Configuration management using Pydantic Settings."""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


LLMProvider = Literal["anthropic", "openai", "google", "zhipu"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Provider Configuration
    llm_provider: LLMProvider = Field(
        default="anthropic", description="LLM provider (anthropic/openai/google)"
    )

    # API Keys (provider-specific)
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    google_api_key: str = Field(default="", description="Google API key")
    zhipu_api_key: str = Field(default="", description="Zhipu AI (GLM) API key")

    # Telegram Configuration
    telegram_bot_token: str = Field(..., description="Telegram bot token")
    telegram_chat_id: str = Field(..., description="Telegram chat ID")

    # Reddit API (optional)
    reddit_client_id: str = Field(default="", description="Reddit client ID")
    reddit_client_secret: str = Field(default="", description="Reddit client secret")
    reddit_user_agent: str = Field(
        default="AINewsBrief/1.0.0", description="Reddit user agent"
    )

    # GitHub API (optional, for higher rate limits)
    github_token: str = Field(default="", description="GitHub personal access token")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")
    log_format: str = Field(default="console", description="Log format (console, json)")

    # Article filtering
    max_total_articles: int = Field(
        default=50, ge=1, le=200, description="Maximum total articles to process"
    )
    min_importance_score: int = Field(
        default=5, ge=0, le=10, description="Minimum importance score to include"
    )

    # Timezone
    timezone: str = Field(default="Asia/Shanghai", description="Timezone for reports")

    # LLM Settings
    llm_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="LLM model name (provider-specific)",
    )
    llm_temperature: float = Field(
        default=0.3, ge=0.0, le=1.0, description="LLM temperature"
    )
    llm_max_tokens: int = Field(default=4096, ge=256, description="LLM max tokens")

    # Fetcher settings
    max_articles_per_source: int = Field(
        default=20, description="Max articles per source"
    )
    article_age_hours: int = Field(
        default=24, description="Only fetch articles from last N hours"
    )
    enable_rss: bool = Field(default=True, description="Enable RSS feed fetching")
    enable_reddit: bool = Field(default=True, description="Enable Reddit fetching")
    enable_hackernews: bool = Field(default=True, description="Enable HackerNews fetching")
    enable_arxiv: bool = Field(default=True, description="Enable ArXiv fetching")
    enable_blogs: bool = Field(default=True, description="Enable official blog fetching")
    enable_github: bool = Field(default=True, description="Enable GitHub releases fetching")

    # Deduplication history
    dedup_history_path: str = Field(
        default="reports/seen_articles.json",
        description="Path to persisted deduplication history file",
    )
    dedup_history_days: int = Field(
        default=30, ge=1, le=365, description="History retention window in days"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
