"""Main agent entry point for running the AI News Brief workflow."""

import asyncio
import sys
from datetime import datetime
from src.graph.state import BriefState
from src.graph.workflow import create_brief_workflow
from src.config import settings
from src.utils.logger import init_logger, get_logger


def setup_logging():
    """Initialize logging based on configuration."""
    json_format = settings.log_format.lower() == "json"
    return init_logger(
        level=settings.log_level,
        json_format=json_format,
    )


async def run_daily_brief() -> BriefState:
    """Run the daily AI news brief workflow.

    Returns:
        Final workflow state
    """
    # Initialize logging
    setup_logging()
    logger = get_logger("agent")

    logger.info(
        "workflow_start",
        timestamp=datetime.now().isoformat(),
        max_articles=settings.max_total_articles,
        llm_provider=settings.llm_provider,
    )

    # Create workflow
    workflow = create_brief_workflow()

    # Initialize state
    initial_state: BriefState = {
        "date": datetime.now(),
        "max_articles": settings.max_total_articles,
        "raw_articles": [],
        "filtered_articles": [],
        "analyzed_articles": [],
        "deep_analyses": [],
        "report": None,
        "report_path": None,
        "telegram_message_id": None,
        "errors": [],
    }

    # Run workflow
    try:
        final_state = await workflow.ainvoke(initial_state)

        logger.info(
            "workflow_complete",
            articles_processed=len(final_state["analyzed_articles"]),
            report_path=final_state.get("report_path"),
            telegram_sent=final_state.get("telegram_message_id") is not None,
            error_count=len(final_state.get("errors", [])),
        )

        if final_state.get("errors"):
            for error in final_state["errors"]:
                logger.warning("workflow_error", error=error)

        return final_state

    except Exception as e:
        logger.error("workflow_failed", error=str(e), exc_info=True)
        raise


def main():
    """CLI entry point."""
    try:
        asyncio.run(run_daily_brief())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
