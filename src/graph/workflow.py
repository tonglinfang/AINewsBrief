"""LangGraph workflow definition with conditional short-circuit edges."""

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


# ---------------------------------------------------------------------------
# Routing functions for conditional edges
# ---------------------------------------------------------------------------

def _route_after_filter(state: BriefState) -> str:
    """Skip LLM analysis entirely when the filter stage produced no articles.

    Jumping straight to 'format' avoids unnecessary LLM API calls and lets the
    formatter emit an empty-report message for the operator.
    """
    return "analyze" if state.get("filtered_articles") else "format"


def _route_after_analyze(state: BriefState) -> str:
    """Skip deep analysis when no article passed the importance/relevance threshold.

    This prevents the deep-analyzer from being invoked when there is nothing to
    process, which would otherwise incur a redundant LLM setup cost.
    """
    return "deep_analyze" if state.get("analyzed_articles") else "format"


# ---------------------------------------------------------------------------
# Workflow factory
# ---------------------------------------------------------------------------

def create_brief_workflow() -> StateGraph:
    """Build and compile the AI News Brief LangGraph workflow.

    Pipeline (linear by default, with two conditional short-circuits):

        fetch → filter ──(empty)──────────────────────────┐
                       └──(articles)──► analyze           │
                                           │               │
                                   (empty)─┤   ┌──────────┘
                                           └──► deep_analyze
                                                    │
                                                  format
                                                    │
                                                  send
                                                    │
                                                  END

    Returns:
        Compiled StateGraph ready for ainvoke().
    """
    workflow = StateGraph(BriefState)

    # Register nodes
    workflow.add_node("fetch", fetch_news_node)
    workflow.add_node("filter", filter_node)
    workflow.add_node("analyze", analyze_node)
    workflow.add_node("deep_analyze", deep_analyze_node)
    workflow.add_node("format", format_node)
    workflow.add_node("send", send_node)

    # Entry point
    workflow.set_entry_point("fetch")

    # fetch → filter is always unconditional
    workflow.add_edge("fetch", "filter")

    # After filter: go to analyze only if articles exist, else jump to format.
    workflow.add_conditional_edges(
        "filter",
        _route_after_filter,
        {"analyze": "analyze", "format": "format"},
    )

    # After analyze: go to deep_analyze only if articles passed the threshold.
    workflow.add_conditional_edges(
        "analyze",
        _route_after_analyze,
        {"deep_analyze": "deep_analyze", "format": "format"},
    )

    # Remaining edges are unconditional
    workflow.add_edge("deep_analyze", "format")
    workflow.add_edge("format", "send")
    workflow.add_edge("send", END)

    return workflow.compile()
