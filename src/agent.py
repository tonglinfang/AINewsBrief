"""Main agent entry point for running the AI News Brief workflow."""

import asyncio
from datetime import datetime
from src.graph.state import BriefState
from src.graph.workflow import create_brief_workflow
from src.config import settings


async def run_daily_brief() -> BriefState:
    """Run the daily AI news brief workflow.

    Returns:
        Final workflow state
    """
    print("🚀 Starting AI News Brief workflow...")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    # Create workflow
    workflow = create_brief_workflow()

    # Initialize state
    initial_state: BriefState = {
        "date": datetime.now(),
        "max_articles": settings.max_total_articles,
        "raw_articles": [],
        "filtered_articles": [],
        "analyzed_articles": [],
        "report": None,
        "report_path": None,
        "telegram_message_id": None,
        "errors": [],
    }

    # Run workflow
    try:
        final_state = await workflow.ainvoke(initial_state)

        print("-" * 60)
        print("✅ Workflow completed successfully!")
        print(f"📊 Total articles processed: {len(final_state['analyzed_articles'])}")

        if final_state.get("report_path"):
            print(f"💾 Report saved: {final_state['report_path']}")

        if final_state.get("telegram_message_id"):
            print(f"📱 Telegram message ID: {final_state['telegram_message_id']}")

        if final_state.get("errors"):
            print(f"⚠️ Errors: {len(final_state['errors'])}")
            for error in final_state["errors"]:
                print(f"   - {error}")

        return final_state

    except Exception as e:
        print("-" * 60)
        print(f"❌ Workflow failed: {e}")
        raise


def main():
    """CLI entry point."""
    asyncio.run(run_daily_brief())


if __name__ == "__main__":
    main()
