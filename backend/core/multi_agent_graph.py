"""
Multi-Agent Graph for Stack Sage

This module orchestrates the multi-agent system using LangGraph,
connecting specialist agents with conditional edges based on task plans.

Optimizations:
- Lazy agent imports for faster startup
- Shared LLM client instances
- Configurable logging levels
"""

import time
import os
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from backend.core.agent_state import AgentState, initialize_state, add_tool_used

# Lazy imports for agents - only load when needed
_agents_loaded = False
_agent_modules = {}

def _load_agents():
    """Lazy load agent modules to improve startup time."""
    global _agents_loaded, _agent_modules
    if not _agents_loaded:
        from backend.core.agents.planner import planner_agent
        from backend.core.agents.card_agent import card_agent
        from backend.core.agents.rules_agent import rules_agent
        from backend.core.agents.interaction_agent import interaction_agent
        from backend.core.agents.judge_agent import judge_agent
        from backend.core.agents.meta_agent import meta_agent
        
        _agent_modules = {
            'planner': planner_agent,
            'card': card_agent,
            'rules': rules_agent,
            'interaction': interaction_agent,
            'judge': judge_agent,
            'meta': meta_agent
        }
        _agents_loaded = True
    return _agent_modules

# Configurable logging
VERBOSE_LOGGING = os.getenv('STACK_SAGE_VERBOSE', 'false').lower() == 'true'


# Agent timing decorator
def timed_agent(agent_name: str):
    """Decorator to track agent execution time with configurable logging."""
    def decorator(agent_func):
        def wrapper(state: AgentState) -> AgentState:
            start_time = time.time()
            
            if VERBOSE_LOGGING:
                print(f"\n{'='*60}")
                print(f"[{agent_name}] Starting...")
                print(f"{'='*60}")
            
            result = agent_func(state)
            
            elapsed = time.time() - start_time
            if "diagnostics" not in result:
                result["diagnostics"] = {}
            if "agent_timings" not in result["diagnostics"]:
                result["diagnostics"]["agent_timings"] = {}
            result["diagnostics"]["agent_timings"][agent_name] = elapsed
            
            if VERBOSE_LOGGING:
                print(f"[{agent_name}] Completed in {elapsed:.2f}s")
            
            return result
        return wrapper
    return decorator


# Wrap agents with timing - using lazy loading
@timed_agent("Planner")
def planner_node(state: AgentState) -> AgentState:
    agents = _load_agents()
    return agents['planner'](state)


@timed_agent("CardAgent")
def card_node(state: AgentState) -> AgentState:
    agents = _load_agents()
    return agents['card'](state)


@timed_agent("RulesAgent")
def rules_node(state: AgentState) -> AgentState:
    agents = _load_agents()
    return agents['rules'](state)


@timed_agent("InteractionAgent")
def interaction_node(state: AgentState) -> AgentState:
    agents = _load_agents()
    return agents['interaction'](state)


@timed_agent("JudgeAgent")
def judge_node(state: AgentState) -> AgentState:
    agents = _load_agents()
    return agents['judge'](state)


@timed_agent("MetaAgent")
def meta_node(state: AgentState) -> AgentState:
    agents = _load_agents()
    return agents['meta'](state)


@timed_agent("Finalizer")
def finalizer_node(state: AgentState) -> AgentState:
    """
    Finalize the answer with citations and tools used.
    
    Args:
        state: Current agent state
        
    Returns:
        State with formatted final_answer
    """
    final_answer = state.get("final_answer", "")
    
    if not final_answer:
        # If no final answer yet, use draft
        final_answer = state.get("draft_answer", "I couldn't generate an answer.")
    
    # Add tools used section
    tools_used = state.get("tools_used", [])
    if tools_used:
        final_answer += f"\n\n{'─'*60}\n🔧 **Tools Used**: {', '.join(tools_used)}"
    
    # Add timing information (optional, for debugging)
    timings = state.get("diagnostics", {}).get("agent_timings", {})
    if timings:
        total_time = sum(timings.values())
        final_answer += f"\n⏱️ **Total Time**: {total_time:.2f}s"
    
    state["final_answer"] = final_answer
    state = add_tool_used(state, "finalizer")
    
    print(f"[Finalizer] Answer ready ({len(final_answer)} chars)")
    
    return state


# Routing functions

def route_after_planner(state: AgentState) -> str:
    """
    Route to the first specialist agent based on task plan.
    
    Args:
        state: Current state with task_plan
        
    Returns:
        Next node name
    """
    task_plan = state.get("task_plan", [])
    
    if not task_plan:
        return "finalize"
    
    first_task = task_plan[0]
    
    if first_task == "cards":
        return "cards"
    elif first_task == "rules":
        return "rules"
    elif first_task == "deck":
        return "deck"
    elif first_task == "meta":
        return "meta"
    elif first_task == "interaction":
        return "interaction"
    elif first_task == "judge":
        return "judge"
    else:
        return "finalize"


def route_after_cards(state: AgentState) -> str:
    """Route after card agent based on remaining task plan."""
    task_plan = state.get("task_plan", [])
    
    # Find next task after cards
    try:
        cards_idx = task_plan.index("cards")
        if cards_idx + 1 < len(task_plan):
            next_task = task_plan[cards_idx + 1]
            if next_task == "rules":
                return "rules"
            elif next_task == "interaction":
                return "interaction"
    except (ValueError, IndexError):
        pass
    
    # Default: go to interaction if it's in the plan
    if "interaction" in task_plan:
        return "interaction"
    
    return "finalize"


def route_after_rules(state: AgentState) -> str:
    """Route after rules agent based on remaining task plan."""
    task_plan = state.get("task_plan", [])
    
    # Check if we need cards
    if "cards" in task_plan:
        cards_in_context = state.get("context", {}).get("cards", [])
        if not cards_in_context:
            return "cards"
    
    # Go to interaction if in plan
    if "interaction" in task_plan:
        return "interaction"
    
    return "finalize"


def route_after_interaction(state: AgentState) -> str:
    """Route after interaction agent."""
    task_plan = state.get("task_plan", [])
    
    # Check if we have missing context
    missing_context = state.get("diagnostics", {}).get("missing_context", [])
    if missing_context:
        # Try to fetch missing context (simplified - just go to finalize for now)
        print(f"[Router] Missing context detected: {missing_context}")
        return "finalize"
    
    # Go to judge if in plan
    if "judge" in task_plan:
        return "judge"
    
    return "finalize"


def route_after_judge(state: AgentState) -> str:
    """Route after judge agent."""
    # Always finalize after judge
    return "finalize"


def route_after_meta(state: AgentState) -> str:
    """Route after meta agent."""
    # Meta agent generates its own answer, go directly to finalize
    return "finalize"


# Build the graph

def create_multi_agent_graph():
    """
    Create and compile the multi-agent graph.
    
    Returns:
        Compiled LangGraph
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("cards", card_node)
    workflow.add_node("rules", rules_node)
    workflow.add_node("interaction", interaction_node)
    workflow.add_node("judge", judge_node)
    workflow.add_node("meta", meta_node)
    workflow.add_node("finalize", finalizer_node)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "cards": "cards",
            "rules": "rules",
            "deck": "finalize",  # Deck agent not yet implemented
            "meta": "meta",
            "interaction": "interaction",
            "judge": "judge",
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "cards",
        route_after_cards,
        {
            "rules": "rules",
            "interaction": "interaction",
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "rules",
        route_after_rules,
        {
            "cards": "cards",
            "interaction": "interaction",
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "interaction",
        route_after_interaction,
        {
            "judge": "judge",
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "judge",
        route_after_judge,
        {
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "meta",
        route_after_meta,
        {
            "finalize": "finalize"
        }
    )
    
    # Finalize always ends
    workflow.add_edge("finalize", END)
    
    # Compile the graph
    graph = workflow.compile()
    
    print("[MultiAgentGraph] Graph compiled successfully")
    
    return graph


# Create the global graph instance
multi_agent_graph = create_multi_agent_graph()


def invoke_graph(question: str) -> Dict[str, Any]:
    """
    Invoke the multi-agent graph with a question.
    
    Args:
        question: User's question
        
    Returns:
        Result dictionary with final_answer and metadata
    """
    if VERBOSE_LOGGING:
        print(f"\n{'='*60}")
        print(f"[MultiAgentGraph] Processing question: {question}")
        print(f"{'='*60}\n")
    
    # Initialize state
    initial_state = initialize_state(question)
    
    # Invoke graph with recursion limit
    try:
        result = multi_agent_graph.invoke(
            initial_state,
            config={"recursion_limit": 15}
        )
        
        return {
            "response": result.get("final_answer", "No answer generated"),
            "tools_used": result.get("tools_used", []),
            "citations": result.get("citations", []),
            "diagnostics": result.get("diagnostics", {})
        }
        
    except Exception as e:
        print(f"[MultiAgentGraph] Error: {e}")
        return {
            "response": f"Error processing question: {str(e)}",
            "tools_used": [],
            "citations": [],
            "diagnostics": {}
        }


if __name__ == "__main__":
    # Test the graph
    test_questions = [
        "What is the effect of Rest in Peace?",
        "How does Dockside Extortionist work with Spark Double?",
        "If I Lightning Bolt my opponent's Birds of Paradise while they have Blood Artist, what happens?"
    ]
    
    for question in test_questions:
        print(f"\n\n{'#'*60}")
        print(f"TEST: {question}")
        print(f"{'#'*60}\n")
        
        result = invoke_graph(question)
        
        print(f"\n{'='*60}")
        print("FINAL ANSWER:")
        print(f"{'='*60}")
        print(result["response"])
        print(f"\n{'='*60}\n")

