"""
Card Knowledge Agent

This agent handles all card-related queries by wrapping Scryfall tools
and providing structured card context.
"""

from typing import Dict, Any, List
from backend.core.agent_state import AgentState, add_card_context, add_tool_used, add_citation
from backend.core.scryfall import ScryfallAPI, extract_card_names


# Initialize shared Scryfall API instance
_scryfall = ScryfallAPI()


def card_agent(state: AgentState) -> AgentState:
    """
    Fetch card information based on the user's question.
    
    Extracts card names from the question and fetches their details
    from Scryfall, including oracle text, type, mana cost, and rulings.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with card context
    """
    question = state.get("user_question", "")
    
    # Extract card names from question
    card_names = extract_card_names(question)
    
    if not card_names:
        print("[CardAgent] No card names detected in question")
        return state
    
    print(f"[CardAgent] Extracting cards: {card_names}")
    
    # Fetch cards from Scryfall
    cards = _scryfall.fetch_cards(card_names)
    
    if not cards:
        print("[CardAgent] No cards found")
        return state
    
    # Convert cards to structured format
    card_data = []
    for card in cards:
        card_dict = {
            "name": card.name,
            "oracle_text": card.oracle_text,
            "type_line": card.type_line,
            "mana_cost": card.mana_cost,
            "colors": card.colors,
            "keywords": card.keywords,
            "rulings": card.rulings[:2] if card.rulings else [],  # Limit to 2 most relevant rulings
            "controller_note": "you" in card.oracle_text.lower()
        }
        card_data.append(card_dict)
        
        # Add citation
        state = add_citation(state, "card", card.name, f"https://scryfall.com/search?q={card.name}")
    
    # Add to state context
    state = add_card_context(state, card_data)
    state = add_tool_used(state, "lookup_card")
    
    print(f"[CardAgent] Added {len(card_data)} cards to context")
    
    return state


def compare_cards(state: AgentState, card_names: List[str]) -> AgentState:
    """
    Compare multiple cards for interaction analysis.
    
    Args:
        state: Current agent state
        card_names: List of card names to compare
        
    Returns:
        Updated state with card comparison context
    """
    print(f"[CardAgent] Comparing cards: {card_names}")
    
    # Fetch all cards
    cards = _scryfall.fetch_cards(card_names)
    
    if not cards:
        return state
    
    # Add all cards to context
    card_data = []
    for card in cards:
        card_dict = {
            "name": card.name,
            "oracle_text": card.oracle_text,
            "type_line": card.type_line,
            "mana_cost": card.mana_cost,
            "colors": card.colors,
            "keywords": card.keywords,
            "rulings": card.rulings[:2] if card.rulings else [],
            "controller_note": "you" in card.oracle_text.lower()
        }
        card_data.append(card_dict)
        state = add_citation(state, "card", card.name, f"https://scryfall.com/search?q={card.name}")
    
    state = add_card_context(state, card_data)
    state = add_tool_used(state, "compare_multiple_cards")
    
    print(f"[CardAgent] Compared {len(card_data)} cards")
    
    return state


def check_legality(state: AgentState, card_name: str, format_name: str) -> AgentState:
    """
    Check if a card is legal in a specific format.
    
    Args:
        state: Current agent state
        card_name: Name of the card
        format_name: Format to check (e.g., "standard", "modern", "commander")
        
    Returns:
        Updated state with legality information
    """
    print(f"[CardAgent] Checking legality: {card_name} in {format_name}")
    
    try:
        import requests
        url = f"{_scryfall.BASE_URL}/cards/named"
        params = {'fuzzy': card_name}
        response = _scryfall.session.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        legalities = data.get('legalities', {})
        format_legal = legalities.get(format_name.lower(), 'unknown')
        
        # Add to context as a special card entry
        legality_info = {
            "name": data.get('name', card_name),
            "legality_check": True,
            "format": format_name,
            "status": format_legal,
            "all_legalities": legalities
        }
        
        state = add_card_context(state, [legality_info])
        state = add_tool_used(state, "check_format_legality")
        
        print(f"[CardAgent] {card_name} is {format_legal} in {format_name}")
        
    except Exception as e:
        print(f"[CardAgent] Error checking legality: {e}")
    
    return state


def format_card_context_for_llm(cards: List[Dict[str, Any]]) -> str:
    """
    Format card context for LLM consumption.
    
    Args:
        cards: List of card dictionaries
        
    Returns:
        Formatted string with card information
    """
    if not cards:
        return ""
    
    context = "=== CARD INFORMATION ===\n\n"
    
    for card in cards:
        # Handle legality checks differently
        if card.get("legality_check"):
            context += f"**{card['name']}** - Legality in {card['format'].upper()}: {card['status'].upper()}\n\n"
            continue
        
        context += f"**{card['name']}**\n"
        context += f"Type: {card.get('type_line', 'Unknown')}\n"
        
        if card.get('mana_cost'):
            context += f"Mana Cost: {card['mana_cost']}\n"
        
        context += f"Oracle Text: {card.get('oracle_text', 'No text available')}\n"
        
        if card.get('controller_note'):
            context += "⚠️ Note: 'You' in this card's text refers to this card's CONTROLLER\n"
        
        if card.get('rulings'):
            context += "\nKey Rulings:\n"
            for i, ruling in enumerate(card['rulings'], 1):
                context += f"  {i}. {ruling}\n"
        
        context += "\n" + "="*60 + "\n\n"
    
    return context

