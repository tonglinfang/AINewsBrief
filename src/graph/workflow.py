"""Plain-Python pipeline replacing the previous LangGraph StateGraph."""

from src.graph.state import BriefState
from src.graph.nodes import (
    fetch_news_node,
    filter_node,
    analyze_node,
    deep_analyze_node,
    format_node,
    send_node,
)


async def run_pipeline(state: BriefState) -> BriefState:
    """Run the AI News Brief pipeline.

    Pipeline (with two conditional short-circuits):

        fetch → filter ──(empty)──────────────────────────┐
                       └──(articles)──► analyze           │
                                           │               │
                                   (empty)─┤   ┌──────────┘
                                           └──► deep_analyze
                                                    │
                                                  format
                                                    │
                                                  send
    """
    state = await fetch_news_node(state)
    state = await filter_node(state)
    if state.get("filtered_articles"):
        state = await analyze_node(state)
        if state.get("analyzed_articles"):
            state = await deep_analyze_node(state)
    state = await format_node(state)
    state = await send_node(state)
    return state
