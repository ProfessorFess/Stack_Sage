"""
Planner/Router Agent

This agent uses LLM-based intelligent analysis to:
1. Extract card names from questions
2. Classify question intent
3. Route to appropriate specialist agents

No more fragile regex patterns!
"""

import time
import json
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from backend.core.agent_state import AgentState, add_tool_used
from backend.core.llm_client import get_shared_llm
from backend.core.config import config


def planner_agent(state: AgentState) -> AgentState:
    """
    The Planner agent uses LLM-based intelligent analysis to determine:
    1. What card names are mentioned in the question
    2. What type of question this is (card interaction, rules, meta, deck validation)
    3. Which specialist agents should be invoked
    
    Routes to:
    - Cards mentioned → CardAgent
    - Rules/mechanics → RulesAgent
    - Deck validation → DeckAgent
    - Meta/popularity → MetaAgent
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with task_plan and extracted card names
    """
    start_time = time.time()
    question = state.get("user_question", "")
    
    # Track that planner was used
    state = add_tool_used(state, "planner")
    
    # Use LLM to intelligently analyze the question
    analysis = _analyze_question_with_llm(question)
    
    # Extract results
    card_names = analysis.get("card_names", [])
    intent = analysis.get("intent", "rules")
    
    # Store extracted card names in state for CardAgent to use
    if card_names:
        state["extracted_cards"] = card_names
    
    # Build task plan based on LLM analysis
    task_plan = []
    
    if intent == "meta":
        task_plan.append("meta")
        if card_names:
            task_plan.append("cards")
    
    elif intent == "deck_validation":
        task_plan.append("deck")
        if card_names:
            task_plan.append("cards")
    
    else:  # card_interaction or rules
        # If cards are mentioned, always fetch them first
        if card_names:
            task_plan.append("cards")
        
        # Add rules search
        task_plan.append("rules")
        
        # Add interaction and judge for standard queries
        task_plan.append("interaction")
        task_plan.append("judge")
    
    # Always finalize
    task_plan.append("finalize")
    
    state["task_plan"] = task_plan
    
    elapsed = time.time() - start_time
    print(f"[Planner] Intent: {intent}, Cards: {card_names}")
    print(f"[Planner] Task plan: {' → '.join(task_plan)} ({elapsed:.2f}s)")
    
    return state


def _analyze_question_with_llm(question: str) -> Dict[str, Any]:
    """
    Use LLM to intelligently analyze the question and extract:
    - Card names mentioned
    - Intent/query type
    
    Args:
        question: User's question
        
    Returns:
        Dictionary with 'card_names' (list) and 'intent' (string)
    """
    llm = get_shared_llm(temperature=config.AGENT_TEMPERATURES["planner"])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at analyzing Magic: The Gathering questions.

Your task is to extract:
1. Card names mentioned in the question
2. The type of question being asked

Respond ONLY with valid JSON in this exact format:
{{
  "card_names": ["Card Name 1", "Card Name 2"],
  "intent": "card_interaction"
}}

Intent types:
- "card_interaction": Questions about how cards work together or interact (e.g., "Does X stop Y?", "How does X work with Y?", "What is X?")
- "rules": Questions about game rules or mechanics (e.g., "How does the stack work?", "What are state-based actions?")
- "meta": Questions about popular decks, tournament results, what's good in a format
- "deck_validation": Questions about checking if a deck is legal or validating a decklist

Card name extraction:
- Extract ONLY actual Magic card names, not game terms
- "Rest in Peace" is a card name
- "Unearth" is a card name  
- "Lightning Bolt" is a card name
- "Goblin Bombardment" is a card name
- "the stack" is NOT a card name
- "graveyard" is NOT a card name
- "battlefield" is NOT a card name

Examples:
Q: "Does Rest in Peace stop Unearth?"
A: {{"card_names": ["Rest in Peace", "Unearth"], "intent": "card_interaction"}}

Q: "How does the stack work?"
A: {{"card_names": [], "intent": "rules"}}

Q: "What are the best decks in Standard?"
A: {{"card_names": [], "intent": "meta"}}

Q: "Is my deck legal in Modern?"
A: {{"card_names": [], "intent": "deck_validation"}}

Q: "What is Lightning Bolt?"
A: {{"card_names": ["Lightning Bolt"], "intent": "card_interaction"}}

Q: "If my opponent has Goblin Bombardment, who can sacrifice creatures?"
A: {{"card_names": ["Goblin Bombardment"], "intent": "card_interaction"}}

Q: "give me the decklist for a mono red standard aggro deck"
A: {{"card_names": [], "intent": "meta"}}"""),
        ("human", "{question}")
    ])
    
    response = None
    try:
        messages = prompt.format_messages(question=question)
        response = llm.invoke(messages)
        
        # Parse JSON response
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if "```" in content:
            # Extract content between code blocks
            parts = content.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part and (part.startswith("{") or part.startswith("[")):
                    content = part
                    break
        
        # Try to parse JSON
        result = json.loads(content)
        
        # Validate structure
        if "card_names" not in result or "intent" not in result:
            raise ValueError("Invalid response structure")
        
        # Ensure card_names is a list
        if not isinstance(result["card_names"], list):
            result["card_names"] = []
        
        return result
        
    except Exception as e:
        print(f"[Planner] LLM analysis error: {str(e)[:100]}")
        if response:
            print(f"[Planner] Response was: {response.content[:200]}")
        # Safe fallback
        return {
            "card_names": [],
            "intent": "rules"
        }


def should_run_parallel(state: AgentState) -> bool:
    """
    Determine if card and rules agents should run in parallel.
    
    Parallel execution is beneficial when:
    - Both cards and rules are in the task plan
    - Multiple cards are mentioned (interaction questions)
    """
    task_plan = state.get("task_plan", [])
    
    if "cards" in task_plan and "rules" in task_plan:
        card_names = state.get("extracted_cards", [])
        return len(card_names) >= 2  # Multiple cards = likely interaction
    
    return False
