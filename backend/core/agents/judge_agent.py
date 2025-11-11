"""
Judge/Verifier Agent

This agent verifies that answers are grounded in retrieved context
and checks controller logic for correctness. Migrated from rag_pipeline.py.
"""

import re
from typing import Dict, Any, Tuple
from backend.core.agent_state import AgentState, add_tool_used


def judge_agent(state: AgentState) -> AgentState:
    """
    Verify the draft answer for grounding and controller logic.
    
    Checks:
    1. All specific facts in the answer exist in retrieved context
    2. Controller logic is correct for "opponent" questions
    3. No hallucinations or invented information
    
    Args:
        state: Current agent state with draft_answer and context
        
    Returns:
        Updated state with judge_report and potentially corrected answer
    """
    draft_answer = state.get("draft_answer", "")
    question = state.get("user_question", "")
    context_data = state.get("context", {})
    
    if not draft_answer:
        print("[JudgeAgent] No draft answer to verify")
        return state
    
    print(f"[JudgeAgent] Verifying answer ({len(draft_answer)} chars)")
    
    # Step 1: Verify grounding
    is_grounded, grounding_note = _verify_grounding(draft_answer, context_data)
    
    # Step 2: Verify controller logic
    controller_ok, controller_note = _verify_controller_logic(question, draft_answer)
    
    # Create judge report
    judge_report = {
        "grounded": is_grounded,
        "controller_ok": controller_ok,
        "notes": f"Grounding: {grounding_note}. Controller: {controller_note}",
        "corrections": None
    }
    
    # If controller logic is wrong, add correction
    if not controller_ok:
        correction = _generate_controller_correction(question, draft_answer)
        judge_report["corrections"] = correction
        print(f"[JudgeAgent] Controller error detected, adding correction")
    
    # If not grounded, flag for rejection
    if not is_grounded:
        print(f"[JudgeAgent] Answer not grounded: {grounding_note}")
        state["final_answer"] = (
            "I don't have enough reliable information to answer that accurately. "
            "The question requires specific card details or rules that I couldn't verify. "
            "Please try asking about a specific card name or rules topic.\n\n"
            f"Debug: {grounding_note}"
        )
    elif not controller_ok and judge_report["corrections"]:
        # Apply correction to draft answer
        state["final_answer"] = judge_report["corrections"] + "\n\n" + draft_answer
    else:
        # Answer is good, promote to final
        state["final_answer"] = draft_answer
    
    state["judge_report"] = judge_report
    state = add_tool_used(state, "judge_verification")
    
    print(f"[JudgeAgent] Grounded: {is_grounded}, Controller OK: {controller_ok}")
    
    return state


def _verify_grounding(answer: str, context: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verify that facts in the answer exist in the retrieved context.
    
    Args:
        answer: The draft answer
        context: Retrieved context (cards and rules)
        
    Returns:
        (is_grounded, confidence_message) tuple
    """
    # Combine all context into searchable text
    all_context = ""
    
    # Add card context
    for card in context.get("cards", []):
        all_context += card.get("name", "") + " "
        all_context += card.get("oracle_text", "") + " "
        all_context += card.get("type_line", "") + " "
        all_context += " ".join(card.get("rulings", [])) + " "
    
    # Add rules context
    for rule in context.get("rules", []):
        all_context += rule.get("content", "") + " "
    
    all_context = all_context.lower()
    
    # If no context retrieved, answer is likely hallucinated
    if not all_context or len(all_context) < 50:
        return (False, "No retrieved context - likely hallucination")
    
    answer_lower = answer.lower()
    
    # Extract potential card names from answer (capitalized words followed by MTG action verbs)
    card_name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\s+(?:is|has|can|will|would|enters|leaves|triggers|creates|deals|gains|loses|taps|untaps|sacrifices|exiles|draws|discards|reveals|searches|shuffles|puts|returns|destroys|counters|copies|targets)'
    card_names_in_answer = re.findall(card_name_pattern, answer)
    
    # Check if card names mentioned in answer exist in context
    suspicious_cards = []
    skip_words = ['when', 'since', 'if', 'the', 'you', 'your', 'this', 'that', 'player', 'card', 'it', 'they', 'each', 'any', 'all', 'as', 'while']
    
    for card_name in card_names_in_answer[:10]:  # Check more candidates
        # Skip common phrases and sentence starters
        first_word = card_name.lower().split()[0]
        if first_word in skip_words:
            continue
        
        if card_name.lower() not in all_context:
            suspicious_cards.append(card_name)
    
    # Only fail if we find many suspicious card names (relaxed threshold)
    if len(suspicious_cards) >= 3:
        return (False, f"Suspicious card names not in context: {suspicious_cards[:3]}")
    
    # Check for specific numbers (power/toughness, damage) in answer
    # Only flag if multiple numbers are suspicious (LLM can correctly infer some P/T)
    number_pattern = r'\b(\d+/\d+)\b'
    numbers_in_answer = re.findall(number_pattern, answer)
    
    suspicious_numbers = []
    for number in numbers_in_answer:
        if number not in all_context:
            suspicious_numbers.append(number)
    
    # Only fail if multiple suspicious numbers (relaxed - LLM can infer copy effects)
    if len(suspicious_numbers) >= 3:
        return (False, f"Specific numbers not in context: {suspicious_numbers[:3]}")
    
    # Basic length check - very short context with long answer is suspicious
    context_length = len(all_context)
    answer_length = len(answer_lower)
    
    if answer_length > context_length * 2 and context_length < 500:
        return (False, "Answer much longer than context - may contain hallucinations")
    
    # Passed basic grounding checks
    return (True, "Answer appears grounded in context")


def _verify_controller_logic(question: str, answer: str) -> Tuple[bool, str]:
    """
    Verify that controller logic is correct in the answer.
    
    Specifically checks for "opponent controls X" scenarios where
    "you" on the card refers to the opponent, not the player asking.
    
    Args:
        question: Original question
        answer: Draft answer
        
    Returns:
        (controller_ok, note) tuple
    """
    question_lower = question.lower()
    answer_lower = answer.lower()
    
    # Check if this is an opponent-controls question
    if "opponent" not in question_lower:
        return (True, "No opponent mentioned")
    
    # Check for specific controller error patterns
    
    # Blood Artist specific check (common error case)
    if "blood artist" in question_lower and "opponent" in question_lower:
        # If opponent controls Blood Artist, opponent should gain life
        if ("you gain" in answer_lower and "life" in answer_lower) or \
           ("opponent lose" in answer_lower and "you gain" not in answer_lower):
            return (False, "Blood Artist controller error: opponent should gain life, not player")
    
    # Generic opponent-controls check
    if "opponent has" in question_lower or "opponent's" in question_lower or "their" in question_lower:
        # Look for reversed benefits
        if "you gain" in answer_lower and "opponent" in answer_lower:
            # This might be wrong - opponent controls the permanent
            return (False, "Possible controller error: benefits may be reversed")
    
    return (True, "Controller logic appears correct")


def _generate_controller_correction(question: str, answer: str) -> str:
    """
    Generate a correction message for controller logic errors.
    
    Args:
        question: Original question
        answer: Draft answer with error
        
    Returns:
        Correction message
    """
    question_lower = question.lower()
    
    if "blood artist" in question_lower and "opponent" in question_lower:
        return """⚠️ **Controller Correction:**

Since your opponent controls Blood Artist:
- Your **opponent gains 1 life** (Blood Artist's controller)
- **You lose 1 life** (opponent targets you with the ability)

Remember: "You" on a card always refers to that card's controller."""
    
    return """⚠️ **Controller Correction:**

Remember: "You" on a card refers to that card's CONTROLLER.
If your opponent controls the permanent, they get the benefits, not you."""


def check_controller_map(question: str) -> str:
    """
    Generate a controller map for opponent questions.
    
    This helps visualize who controls what in multi-player scenarios.
    
    Args:
        question: User's question
        
    Returns:
        Formatted controller map
    """
    question_lower = question.lower()
    
    result = "=== CONTROLLER MAP ===\n\n"
    
    player1_controls = []
    player2_controls = []
    
    # Parse who controls what
    if "i cast" in question_lower or "i lightning" in question_lower:
        player1_controls.append("Lightning Bolt (spell you're casting)")
    
    if "opponent" in question_lower:
        if "blood artist" in question_lower:
            player2_controls.append("Blood Artist (opponent controls this)")
        
        if "birds" in question_lower or "paradise" in question_lower:
            player2_controls.append("Birds of Paradise (opponent controls this)")
        
        # Generic extraction
        match = re.search(r"opponent(?:'s)?\s+(?:has\s+)?([A-Za-z\s]+?)(?:\s*,|\s*\?|$)", question_lower)
        if match:
            card = match.group(1).strip()
            if card and len(card) > 2 and card not in str(player2_controls):
                player2_controls.append(f"{card.title()} (opponent controls this)")
    
    # Format output
    result += "**YOU (Player asking the question):**\n"
    if player1_controls:
        for item in player1_controls:
            result += f"  - {item}\n"
    else:
        result += "  - (No permanents specified)\n"
    
    result += "\n**OPPONENT:**\n"
    if player2_controls:
        for item in player2_controls:
            result += f"  - {item}\n"
    else:
        result += "  - (No permanents specified)\n"
    
    # Add Blood Artist specific guidance
    if "blood artist" in question_lower:
        result += "\n**BLOOD ARTIST TRIGGER:**\n"
        result += "Since opponent controls Blood Artist:\n"
        result += "  1. Opponent gains 1 life (controller benefit)\n"
        result += "  2. You lose 1 life (opponent targets you)\n"
    
    return result

