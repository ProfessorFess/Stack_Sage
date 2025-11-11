"""
Agent State Schema for Multi-Agent Stack Sage

This module defines the shared state structure used across all agents
in the multi-agent graph architecture.
"""

from typing import TypedDict, List, Dict, Optional, Any
from dataclasses import dataclass, field


class Context(TypedDict, total=False):
    """Context gathered by specialist agents."""
    cards: List[Dict[str, Any]]  # Card information from CardAgent
    rules: List[Dict[str, Any]]  # Rules from RulesAgent
    deck_info: Optional[Dict[str, Any]]  # Deck validation from DeckAgent
    metagame: Optional[Dict[str, Any]]  # Meta information from MetaAgent


class Diagnostics(TypedDict, total=False):
    """Diagnostic information for tracking agent performance."""
    coverage_score: float
    missing_context: List[str]
    retries: Dict[str, int]
    latency_budget_ms: int
    agent_timings: Dict[str, float]


class JudgeReport(TypedDict, total=False):
    """Report from Judge agent verification."""
    grounded: bool
    controller_ok: bool
    notes: str
    corrections: Optional[str]


class AgentState(TypedDict, total=False):
    """
    Shared state across all agents in the multi-agent graph.
    
    This state is passed between agents and updated as they process
    the user's question.
    """
    # Input
    messages: List[Any]  # LangChain messages
    user_question: str
    
    # Planning
    task_plan: List[str]  # Steps decided by Planner
    
    # Context from specialist agents
    context: Context
    
    # Diagnostics and tracking
    diagnostics: Diagnostics
    citations: List[Dict[str, str]]
    tools_used: List[str]
    
    # Answer generation
    draft_answer: str
    final_answer: str
    
    # Verification
    judge_report: Optional[JudgeReport]


# Helper functions for state updates

def add_card_context(state: AgentState, cards: List[Dict[str, Any]]) -> AgentState:
    """Add card information to state context."""
    if "context" not in state:
        state["context"] = Context()
    if "cards" not in state["context"]:
        state["context"]["cards"] = []
    state["context"]["cards"].extend(cards)
    return state


def add_rules_context(state: AgentState, rules: List[Dict[str, Any]]) -> AgentState:
    """Add rules information to state context."""
    if "context" not in state:
        state["context"] = Context()
    if "rules" not in state["context"]:
        state["context"]["rules"] = []
    state["context"]["rules"].extend(rules)
    return state


def add_tool_used(state: AgentState, tool_name: str) -> AgentState:
    """Track which tools have been used."""
    if "tools_used" not in state:
        state["tools_used"] = []
    if tool_name not in state["tools_used"]:
        state["tools_used"].append(tool_name)
    return state


def add_citation(state: AgentState, citation_type: str, citation_id: str, source_url: str = "") -> AgentState:
    """Add a citation to the state."""
    if "citations" not in state:
        state["citations"] = []
    state["citations"].append({
        "type": citation_type,
        "id": citation_id,
        "source_url": source_url
    })
    return state


def add_missing_context(state: AgentState, missing_item: str) -> AgentState:
    """Add an item to the missing context list."""
    if "diagnostics" not in state:
        state["diagnostics"] = Diagnostics()
    if "missing_context" not in state["diagnostics"]:
        state["diagnostics"]["missing_context"] = []
    if missing_item not in state["diagnostics"]["missing_context"]:
        state["diagnostics"]["missing_context"].append(missing_item)
    return state


def update_coverage_score(state: AgentState, score: float) -> AgentState:
    """Update the coverage score in diagnostics."""
    if "diagnostics" not in state:
        state["diagnostics"] = Diagnostics()
    state["diagnostics"]["coverage_score"] = score
    return state


def initialize_state(user_question: str) -> AgentState:
    """Initialize a new agent state with default values."""
    return AgentState(
        user_question=user_question,
        messages=[],
        task_plan=[],
        context=Context(cards=[], rules=[], deck_info=None, metagame=None),
        diagnostics=Diagnostics(
            coverage_score=0.0,
            missing_context=[],
            retries={},
            latency_budget_ms=10000,
            agent_timings={}
        ),
        citations=[],
        tools_used=[],
        draft_answer="",
        final_answer="",
        judge_report=None
    )

