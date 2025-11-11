"""
Interaction/Reasoning Agent

This agent takes card and rules context and generates a draft answer,
detecting any missing context needed for a complete response.
"""

from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from backend.core.agent_state import AgentState, add_missing_context, add_tool_used
from backend.core.agents.card_agent import format_card_context_for_llm
from backend.core.agents.rules_agent import format_rules_context_for_llm
from backend.core.llm_client import get_shared_llm
from backend.core.config import config


def interaction_agent(state: AgentState) -> AgentState:
    """
    Generate a draft answer based on gathered context.
    
    Analyzes card and rules context to provide a step-by-step explanation
    of how cards interact. Detects if additional context is needed.
    
    Args:
        state: Current agent state with card and rules context
        
    Returns:
        Updated state with draft_answer or missing_context items
    """
    question = state.get("user_question", "")
    context_data = state.get("context", {})
    
    print(f"[InteractionAgent] Generating answer for: {question}")
    
    # Format context for LLM
    card_context = format_card_context_for_llm(context_data.get("cards", []))
    rules_context = format_rules_context_for_llm(context_data.get("rules", []))
    
    # Check if we have enough context
    if not card_context and not rules_context:
        print("[InteractionAgent] No context available, requesting more")
        state = add_missing_context(state, "Need card or rules context to answer question")
        return state
    
    # Build combined context
    combined_context = ""
    if card_context:
        combined_context += card_context + "\n\n"
    if rules_context:
        combined_context += rules_context + "\n\n"
    
    # Use shared LLM instance for better performance
    llm = get_shared_llm(temperature=config.AGENT_TEMPERATURES["interaction"])
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Stack Sage, an expert Magic: The Gathering rules assistant.

Your task is to provide a clear, accurate answer based ONLY on the context provided below.

**Critical Rules:**
1. Use ONLY information from the context - never guess or use outside knowledge
2. If the context is insufficient, say "I need more information about [specific thing]"
3. For card interactions, explain step-by-step what happens
4. Pay attention to controller relationships - "you" on a card means that card's controller
5. Be concise but complete - aim for 2-4 sentences for simple questions

**Response Format:**
- State the answer directly first
- Then explain the reasoning if needed
- Cite specific rules or card text when relevant
- For complex interactions, use step-by-step format

**Context Provided:**
{context}

**Question:** {question}

Provide your answer:"""),
    ])
    
    # Generate answer
    try:
        messages = prompt.format_messages(context=combined_context, question=question)
        response = llm.invoke(messages)
        draft_answer = response.content
        
        # Check if the answer indicates missing context
        if _indicates_missing_context(draft_answer):
            print("[InteractionAgent] Answer indicates missing context")
            missing_item = _extract_missing_context(draft_answer, question)
            state = add_missing_context(state, missing_item)
        else:
            state["draft_answer"] = draft_answer
            print(f"[InteractionAgent] Generated draft answer ({len(draft_answer)} chars)")
        
        state = add_tool_used(state, "interaction_reasoner")
        
    except Exception as e:
        print(f"[InteractionAgent] Error generating answer: {e}")
        state = add_missing_context(state, f"Error during answer generation: {str(e)}")
    
    return state


def _indicates_missing_context(answer: str) -> bool:
    """
    Check if the answer indicates missing context.
    
    Args:
        answer: Generated answer text
        
    Returns:
        True if answer indicates missing information
    """
    missing_indicators = [
        "i need more information",
        "i don't have enough",
        "insufficient information",
        "cannot determine",
        "need to know",
        "requires additional",
        "missing information"
    ]
    
    answer_lower = answer.lower()
    return any(indicator in answer_lower for indicator in missing_indicators)


def _extract_missing_context(answer: str, question: str) -> str:
    """
    Extract what specific context is missing from the answer.
    
    Args:
        answer: Generated answer text
        question: Original question
        
    Returns:
        Description of missing context
    """
    # Try to extract specific missing information from the answer
    answer_lower = answer.lower()
    
    if "card" in answer_lower and "specific" in answer_lower:
        return "Need specific card details"
    elif "rule" in answer_lower:
        return "Need specific rules about the interaction"
    elif "format" in answer_lower or "legal" in answer_lower:
        return "Need format legality information"
    else:
        return "Need additional context to answer completely"


def generate_step_by_step_interaction(
    state: AgentState,
    card_names: list
) -> AgentState:
    """
    Generate a detailed step-by-step interaction analysis.
    
    Used for complex multi-card interactions that require careful sequencing.
    
    Args:
        state: Current agent state
        card_names: List of cards involved in the interaction
        
    Returns:
        Updated state with detailed interaction analysis
    """
    print(f"[InteractionAgent] Generating step-by-step analysis for: {card_names}")
    
    context_data = state.get("context", {})
    card_context = format_card_context_for_llm(context_data.get("cards", []))
    rules_context = format_rules_context_for_llm(context_data.get("rules", []))
    
    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=0.1,
        openai_api_key=config.OPENAI_API_KEY
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are analyzing a complex Magic: The Gathering card interaction.

Provide a step-by-step breakdown of what happens:

1. Initial game state
2. What triggers/abilities go on the stack (in order)
3. How they resolve (last in, first out)
4. Final game state

Be precise about timing, priority, and controller relationships.

**Context:**
{context}

**Cards Involved:** {cards}

Provide step-by-step analysis:"""),
    ])
    
    try:
        combined_context = card_context + "\n\n" + rules_context
        messages = prompt.format_messages(
            context=combined_context,
            cards=", ".join(card_names)
        )
        response = llm.invoke(messages)
        
        state["draft_answer"] = response.content
        state = add_tool_used(state, "step_by_step_analysis")
        
        print("[InteractionAgent] Generated step-by-step analysis")
        
    except Exception as e:
        print(f"[InteractionAgent] Error in step-by-step analysis: {e}")
    
    return state

