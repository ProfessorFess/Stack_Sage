"""
Deck Agent

This agent handles deck validation queries by parsing deck lists
and validating them according to format rules.
"""

from typing import Dict, Any
from backend.core.agent_state import AgentState, add_tool_used
from backend.core.deck_models import Deck, parse_decklist
from backend.core.deck_validator import validate_deck


def deck_agent(state: AgentState) -> AgentState:
    """
    Parse and validate a deck from the user's question.
    
    Looks for deck list in the question and validates it.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with deck validation results
    """
    question = state.get("user_question", "")
    
    print(f"[DeckAgent] Processing deck validation request")
    
    # Try to extract deck list and format from question
    deck_text, format_name = _extract_deck_info(question)
    
    if not deck_text:
        print("[DeckAgent] No deck list found in question")
        state["final_answer"] = "I couldn't find a deck list in your question. Please provide a deck list in the format:\n\n4 Lightning Bolt\n3 Counterspell\n...\n\nAnd specify the format (e.g., 'Standard', 'Modern', 'Commander')."
        return state
    
    # Parse deck list
    try:
        mainboard, sideboard = parse_decklist(deck_text)
        
        deck = Deck(
            name="User Deck",
            format=format_name or "unknown",
            mainboard=mainboard,
            sideboard=sideboard
        )
        
        print(f"[DeckAgent] Parsed deck: {deck.total_mainboard_cards()} mainboard, {deck.total_sideboard_cards()} sideboard")
        
        # Validate deck
        validation_result = validate_deck(deck)
        
        # Format result for user
        answer = _format_validation_result(validation_result, deck)
        
        # Add to state
        if "context" not in state:
            state["context"] = {}
        state["context"]["deck_info"] = {
            "deck": deck.to_dict(),
            "validation": validation_result.to_dict()
        }
        
        state["final_answer"] = answer
        state = add_tool_used(state, "deck_validation")
        
        print(f"[DeckAgent] Validation complete: {'Legal' if validation_result.is_legal else 'Illegal'}")
        
    except Exception as e:
        print(f"[DeckAgent] Error parsing/validating deck: {e}")
        state["final_answer"] = f"Error validating deck: {str(e)}\n\nPlease check your deck list format."
    
    return state


def _extract_deck_info(question: str) -> tuple[str, str]:
    """
    Extract deck list and format from question.
    
    Args:
        question: User's question
        
    Returns:
        Tuple of (deck_text, format_name)
    """
    # Look for format keywords
    format_keywords = {
        "standard": "standard",
        "modern": "modern",
        "commander": "commander",
        "edh": "commander",
        "pioneer": "pioneer",
        "legacy": "legacy",
        "vintage": "vintage",
        "pauper": "pauper",
        "brawl": "brawl"
    }
    
    question_lower = question.lower()
    format_name = ""
    
    for keyword, format_val in format_keywords.items():
        if keyword in question_lower:
            format_name = format_val
            break
    
    # Try to extract deck list (look for lines with card quantities)
    # Simplified: assume the entire question after format mention is the deck list
    # In a real implementation, you'd want better parsing
    
    # For now, if question contains numbers followed by card names, treat as deck list
    import re
    if re.search(r'\d+\s+[A-Z]', question):
        # This looks like a deck list
        deck_text = question
    else:
        deck_text = ""
    
    return deck_text, format_name


def _format_validation_result(result: Dict[str, Any], deck: Deck) -> str:
    """
    Format validation result for user display.
    
    Args:
        result: Validation result
        deck: The deck that was validated
        
    Returns:
        Formatted string
    """
    output = "=== DECK VALIDATION RESULT ===\n\n"
    
    output += f"**Format:** {result.format.capitalize()}\n"
    output += f"**Total Cards:** {result.total_cards}\n"
    output += f"**Status:** {'✅ LEGAL' if result.is_legal else '❌ ILLEGAL'}\n\n"
    
    # Show errors
    if result.errors:
        output += f"**Errors ({len(result.errors)}):**\n"
        for error in result.errors:
            card_info = f" ({error.card_name})" if error.card_name else ""
            output += f"  ❌ {error.message}{card_info}\n"
        output += "\n"
    
    # Show warnings
    if result.warnings:
        output += f"**Warnings ({len(result.warnings)}):**\n"
        for warning in result.warnings:
            card_info = f" ({warning.card_name})" if warning.card_name else ""
            output += f"  ⚠️ {warning.message}{card_info}\n"
        output += "\n"
    
    # If legal, add confirmation
    if result.is_legal:
        output += "✅ Your deck is legal in {result.format.capitalize()}!\n"
    else:
        output += "Please fix the errors above to make your deck legal.\n"
    
    return output

