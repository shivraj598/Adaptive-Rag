"""
Tools for graph routing.
"""

from typing import Literal

from src.models.state import State


def routing_tool(state: State) -> Literal["__end__", "web_search"]:
    if state["route"] == "search":
        return "web_search"
    return "__end__"
