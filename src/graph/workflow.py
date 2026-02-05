"""LangGraph workflow definition."""

from langgraph.graph import StateGraph, END
from src.graph.state import BriefState
from src.graph.nodes import (
    fetch_news_node,
    filter_node,
    analyze_node,
    deep_analyze_node,
    format_node,
    send_node,
)


def create_brief_workflow() -> StateGraph:
    """Create the AI News Brief workflow.

    Returns:
        Compiled StateGraph workflow
    """
    # Create workflow
    workflow = StateGraph(BriefState)

    # Add nodes
    workflow.add_node("fetch", fetch_news_node)
    workflow.add_node("filter", filter_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("deep_analyze", deep_analyze_node)
    workflow.add_node("format", format_node)
    workflow.add_node("send", send_node)

    # Define edges (linear flow)
    workflow.set_entry_point("fetch")
    workflow.add_edge("fetch", "filter")
    workflow.add_edge("filter", "analyze")
    workflow.add_edge("analyze", "deep_analyze")
    workflow.add_edge("deep_analyze", "format")
    workflow.add_edge("format", "send")
    workflow.add_edge("send", END)

    # Compile workflow
    return workflow.compile()
