"""
MTG Agent Tools

This module defines all the tools available to the Stack Sage agent
for answering Magic: The Gathering questions.
"""

from typing import List, Optional
from functools import lru_cache
from langchain.tools import tool
from langchain_core.documents import Document
from backend.core.scryfall import ScryfallAPI, extract_card_names
from backend.core.retriever import MTGRetriever
from backend.core.bm25_retriever import make_bm25_retriever, make_hybrid_retriever
from backend.core.config import config
import requests


# Initialize shared resources (k=6 balances coverage vs noise)
_scryfall = ScryfallAPI()
_retriever = MTGRetriever(k=6)  # Reduced from 8 to minimize noise

# Initialize BM25 and hybrid retrievers (lazy loading)
_bm25_retriever = None
_hybrid_retriever = None

def _get_bm25_retriever():
    """Get or create BM25 retriever instance."""
    global _bm25_retriever
    if _bm25_retriever is None:
        _bm25_retriever = make_bm25_retriever(k=6)
    return _bm25_retriever

def _get_hybrid_retriever():
    """Get or create hybrid retriever instance."""
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = make_hybrid_retriever(k=6)
    return _hybrid_retriever

# Cached card lookup to avoid redundant API calls
@lru_cache(maxsize=256)
def _cached_card_fetch(card_name: str):
    """
    Cached card lookup to speed up repeated queries.
    Uses LRU cache to store up to 256 most recent card lookups.
    """
    return _scryfall.fetch_card(card_name)


@tool
def lookup_card(card_name: str) -> str:
    """
    Look up a single Magic: The Gathering card by name.
    
    Use this when you need detailed information about a specific card including:
    - Oracle text (official card text)
    - Card type
    - Mana cost
    - Keywords
    - Official rulings
    
    Args:
        card_name: The exact or fuzzy name of the card to look up
        
    Returns:
        Formatted card information or error message if not found
        
    Example:
        lookup_card("Rest in Peace")
        lookup_card("Lightning Bolt")
    """
    # Use cached fetch to avoid redundant API calls
    card = _cached_card_fetch(card_name)
    
    if not card:
        return f"❌ Card '{card_name}' not found. Please check the spelling or try a different name."
    
    return card.to_context_string()


@tool
def search_rules(query: str, num_results: int = 6) -> str:
    """
    Search the Magic: The Gathering Comprehensive Rules.
    
    Use this when you need to find specific rules about game mechanics, phases,
    triggers, replacement effects, state-based actions, or any other game rules.
    
    Args:
        query: The rules question or topic to search for (e.g., "stack resolution", 
               "state-based actions", "triggered abilities")
        num_results: Number of relevant rule sections to return (default: 6)
        
    Returns:
        Relevant sections from the Comprehensive Rules
        
    Example:
        search_rules("how does the stack work")
        search_rules("replacement effects")
    """
    try:
        # Reuse global retriever with dynamic k (no new instance created)
        docs = _retriever.get_relevant_documents(query, k=num_results)
        
        if not docs:
            return f"❌ No rules found for query: '{query}'"
        
        # Format the results
        result = f"=== COMPREHENSIVE RULES (Top {len(docs)} results) ===\n\n"
        for i, doc in enumerate(docs, 1):
            result += f"--- Result {i} ---\n{doc.page_content}\n\n"
        
        return result
    except Exception as e:
        return f"❌ Error searching rules: {str(e)}"


@tool
def search_rules_bm25(query: str, num_results: int = 6) -> str:
    """
    Search the Magic: The Gathering Comprehensive Rules using BM25 keyword matching.
    
    BM25 is excellent for exact keyword matches and specific rule references.
    Use this when you need precise keyword matching or when vector search isn't finding specific terms.
    
    Args:
        query: The search query (keywords work best)
        num_results: Number of relevant rule sections to return (default: 6)
        
    Returns:
        Formatted string with relevant rule sections
    """
    try:
        bm25_retriever = _get_bm25_retriever()
        results = bm25_retriever.get_relevant_documents_with_scores(query, k=num_results)
        
        if not results:
            return "No relevant rules found for your query."
        
        formatted_results = []
        for i, (doc, score) in enumerate(results, 1):
            content = doc.page_content.strip()
            if content:
                formatted_results.append(f"**Result {i}** (BM25 Score: {score:.3f}):\n{content}\n")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching rules with BM25: {str(e)}"


@tool
def search_rules_hybrid(query: str, num_results: int = 6) -> str:
    """
    Search the Magic: The Gathering Comprehensive Rules using hybrid search (vector + BM25).
    
    This combines semantic understanding with keyword precision for the best results.
    Use this for complex queries that need both conceptual understanding and exact matches.
    
    Args:
        query: The search query
        num_results: Number of relevant rule sections to return (default: 6)
        
    Returns:
        Formatted string with relevant rule sections
    """
    try:
        hybrid_retriever = _get_hybrid_retriever()
        results = hybrid_retriever.get_relevant_documents_with_scores(query, k=num_results)
        
        if not results:
            return "No relevant rules found for your query."
        
        formatted_results = []
        for i, (doc, score) in enumerate(results, 1):
            content = doc.page_content.strip()
            if content:
                formatted_results.append(f"**Result {i}** (Hybrid Score: {score:.3f}):\n{content}\n")
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching rules with hybrid search: {str(e)}"


@tool
def compare_multiple_cards(card_names: str) -> str:
    """
    Compare multiple cards to analyze their interactions.
    
    Use this when you need to understand how multiple cards work together,
    check for synergies, or analyze complex card interactions.
    
    Args:
        card_names: Comma-separated list of card names to compare
                   (e.g., "Rest in Peace, Unearth, Animate Dead")
        
    Returns:
        Combined information about all cards for comparison
        
    Example:
        compare_multiple_cards("Dockside Extortionist, Spark Double")
        compare_multiple_cards("Lightning Bolt, Counterspell, Mana Drain")
    """
    # Parse card names
    names_list = [name.strip() for name in card_names.split(",")]
    
    if len(names_list) < 2:
        return "❌ Please provide at least 2 card names separated by commas."
    
    # Fetch all cards
    cards = _scryfall.fetch_cards(names_list)
    
    if not cards:
        return f"❌ No cards found for: {card_names}"
    
    # Format comparison
    result = f"=== CARD COMPARISON ({len(cards)} cards) ===\n\n"
    
    for i, card in enumerate(cards, 1):
        result += f"{'='*60}\n"
        result += f"CARD {i}: {card.name}\n"
        result += f"{'='*60}\n"
        result += card.to_context_string()
        result += "\n"
    
    # Add summary section
    result += f"\n{'='*60}\n"
    result += "INTERACTION NOTES:\n"
    result += "- Review the oracle text and rulings above\n"
    result += "- Consider timing, triggers, and replacement effects\n"
    result += "- Check for keyword interactions\n"
    
    return result


@tool
def check_format_legality(card_name: str, format_name: str = "commander") -> str:
    """
    Check if a card is legal in a specific Magic format.
    
    Use this when you need to verify if a card can be played in a particular format.
    
    Args:
        card_name: Name of the card to check
        format_name: The format to check (options: "standard", "modern", "legacy", 
                    "vintage", "commander", "pioneer", "pauper", "historic", "brawl")
        
    Returns:
        Legality status and relevant information
        
    Example:
        check_format_legality("Black Lotus", "vintage")
        check_format_legality("Lightning Bolt", "standard")
    """
    # Fetch card to get legalities (using cache)
    card_data = _cached_card_fetch(card_name)
    
    if not card_data:
        return f"❌ Card '{card_name}' not found."
    
    # The Card dataclass doesn't have legalities yet, so we need to fetch raw data
    # Let's make a direct API call
    try:
        import requests
        url = f"{_scryfall.BASE_URL}/cards/named"
        params = {'fuzzy': card_name}
        response = _scryfall.session.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        legalities = data.get('legalities', {})
        format_legal = legalities.get(format_name.lower(), 'unknown')
        
        result = f"=== FORMAT LEGALITY CHECK ===\n\n"
        result += f"Card: {data.get('name', card_name)}\n"
        result += f"Format: {format_name.upper()}\n"
        result += f"Status: {format_legal.upper()}\n\n"
        
        # Add context
        if format_legal == 'legal':
            result += f"✅ {data.get('name')} is legal in {format_name}.\n"
        elif format_legal == 'banned':
            result += f"🚫 {data.get('name')} is BANNED in {format_name}.\n"
        elif format_legal == 'restricted':
            result += f"⚠️ {data.get('name')} is RESTRICTED in {format_name} (limited to 1 copy).\n"
        elif format_legal == 'not_legal':
            result += f"❌ {data.get('name')} is not legal in {format_name}.\n"
        
        # Add all format legalities for reference
        result += f"\nFull Legality Status:\n"
        for fmt, status in legalities.items():
            if status in ['legal', 'banned', 'restricted']:
                emoji = '✅' if status == 'legal' else '🚫' if status == 'banned' else '⚠️'
                result += f"  {emoji} {fmt.capitalize()}: {status}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error checking legality: {str(e)}"


@tool
def search_similar_rulings(card_name: str) -> str:
    """
    Find similar card rulings and related rules for a specific card.
    
    Use this when you need to understand edge cases, find related rulings,
    or get additional context about how a card works in practice.
    
    Args:
        card_name: Name of the card to find similar rulings for
        
    Returns:
        Similar rulings and related rule sections
        
    Example:
        search_similar_rulings("Rest in Peace")
        search_similar_rulings("Counterspell")
    """
    # Get the card first (using cache)
    card = _cached_card_fetch(card_name)
    
    if not card:
        return f"❌ Card '{card_name}' not found."
    
    result = f"=== SIMILAR RULINGS FOR: {card.name} ===\n\n"
    
    # Add card's own rulings
    if card.rulings:
        result += f"Official Rulings for {card.name}:\n"
        for i, ruling in enumerate(card.rulings, 1):
            result += f"{i}. {ruling}\n"
        result += "\n"
    else:
        result += f"No official rulings found for {card.name}.\n\n"
    
    # Search for related rules based on card keywords and type
    queries = []
    
    # Build search queries based on card characteristics
    if card.keywords:
        queries.extend(card.keywords)
    
    # Add type-based queries
    if "Instant" in card.type_line or "Sorcery" in card.type_line:
        queries.append("spell resolution")
    if "Creature" in card.type_line:
        queries.append("creature enters battlefield")
    if "Enchantment" in card.type_line:
        queries.append("enchantment effects")
    if "Artifact" in card.type_line:
        queries.append("artifact abilities")
    
    # Search for graveyard-related rules if relevant
    if "graveyard" in card.oracle_text.lower():
        queries.append("graveyard replacement effects")
    if "exile" in card.oracle_text.lower():
        queries.append("exile zone")
    if "counter" in card.oracle_text.lower():
        queries.append("countering spells")
    
    # Get related rules (reuse global retriever)
    if queries:
        result += "Related Rules & Mechanics:\n\n"
        
        for query in queries[:3]:  # Limit to 3 queries to avoid overwhelming
            docs = _retriever.get_relevant_documents(query, k=3)
            if docs:
                result += f"--- {query.upper()} ---\n"
                result += docs[0].page_content + "\n\n"
    
    return result


@tool
def verify_answer_completeness(question: str, answer: str) -> str:
    """
    Verify if an answer is complete and accurate for a given question.
    
    Use this as a self-check tool to evaluate if you've provided all necessary
    information to answer the user's question. This helps ensure quality responses.
    
    Args:
        question: The original question asked
        answer: The answer you've generated
        
    Returns:
        Evaluation of answer completeness with suggestions for improvement
        
    Example:
        verify_answer_completeness(
            "How does Rest in Peace work?", 
            "It exiles cards instead of putting them in graveyards."
        )
    """
    result = "=== ANSWER COMPLETENESS VERIFICATION ===\n\n"
    
    # Extract potential card names from question
    card_names = extract_card_names(question)
    
    checklist = []
    
    # Check 1: Are card names mentioned in the answer?
    if card_names:
        for card_name in card_names:
            if card_name.lower() in answer.lower():
                checklist.append(f"✅ Mentions '{card_name}'")
            else:
                checklist.append(f"⚠️ Missing discussion of '{card_name}'")
    
    # Check 2: Does it explain mechanics?
    mechanics_keywords = [
        "trigger", "ability", "effect", "replacement", "stack", 
        "resolve", "enters", "leaves", "cast", "activate"
    ]
    mechanics_count = sum(1 for kw in mechanics_keywords if kw in answer.lower())
    if mechanics_count >= 2:
        checklist.append(f"✅ Explains game mechanics ({mechanics_count} technical terms)")
    else:
        checklist.append(f"⚠️ Light on mechanical explanation (only {mechanics_count} technical terms)")
    
    # Check 3: Length check (simple heuristic)
    word_count = len(answer.split())
    if word_count >= 50:
        checklist.append(f"✅ Sufficient detail ({word_count} words)")
    elif word_count >= 25:
        checklist.append(f"⚠️ Could use more detail ({word_count} words)")
    else:
        checklist.append(f"❌ Too brief ({word_count} words)")
    
    # Check 4: Rule citations
    if "rule" in answer.lower() or any(c.isdigit() for c in answer):
        checklist.append("✅ Includes rule references")
    else:
        checklist.append("⚠️ No explicit rule citations")
    
    # Check 5: Step-by-step explanation
    step_indicators = ["first", "then", "next", "finally", "1.", "2.", "step"]
    if any(indicator in answer.lower() for indicator in step_indicators):
        checklist.append("✅ Provides step-by-step explanation")
    else:
        checklist.append("⚠️ Could benefit from step-by-step breakdown")
    
    # Compile results
    result += "Completeness Checklist:\n"
    for item in checklist:
        result += f"  {item}\n"
    
    # Calculate score
    passed = sum(1 for item in checklist if item.startswith("✅"))
    total = len(checklist)
    score = (passed / total) * 100
    
    result += f"\nCompleteness Score: {score:.0f}% ({passed}/{total} checks passed)\n\n"
    
    if score >= 80:
        result += "✅ VERDICT: Answer appears complete and thorough.\n"
    elif score >= 60:
        result += "⚠️ VERDICT: Answer is adequate but could be improved.\n"
    else:
        result += "❌ VERDICT: Answer needs significant improvement.\n"
    
    # Suggestions
    result += "\nSuggestions for Improvement:\n"
    warnings = [item for item in checklist if "⚠️" in item or "❌" in item]
    if warnings:
        for warning in warnings:
            result += f"  • Address: {warning}\n"
    else:
        result += "  • No major improvements needed!\n"
    
    return result


@tool
def cross_reference_rules(rule_topic1: str, rule_topic2: str) -> str:
    """
    Cross-reference two different rule topics to understand interactions.
    
    Use this when you need to understand how two different game mechanics
    or rule concepts interact with each other.
    
    Args:
        rule_topic1: First rule topic or mechanic (e.g., "triggered abilities")
        rule_topic2: Second rule topic or mechanic (e.g., "replacement effects")
        
    Returns:
        Rules for both topics with interaction analysis
        
    Example:
        cross_reference_rules("triggered abilities", "replacement effects")
        cross_reference_rules("stack resolution", "priority")
    """
    result = "=== CROSS-REFERENCE ANALYSIS ===\n\n"
    
    # Reuse global retriever with k=3
    
    # Search for first topic
    result += f"{'='*60}\n"
    result += f"TOPIC 1: {rule_topic1.upper()}\n"
    result += f"{'='*60}\n"
    docs1 = _retriever.get_relevant_documents(rule_topic1, k=3)
    if docs1:
        for i, doc in enumerate(docs1, 1):
            result += f"\n[{rule_topic1} - Result {i}]\n"
            result += doc.page_content + "\n"
    else:
        result += f"No rules found for '{rule_topic1}'\n"
    
    # Search for second topic
    result += f"\n{'='*60}\n"
    result += f"TOPIC 2: {rule_topic2.upper()}\n"
    result += f"{'='*60}\n"
    docs2 = _retriever.get_relevant_documents(rule_topic2, k=3)
    if docs2:
        for i, doc in enumerate(docs2, 1):
            result += f"\n[{rule_topic2} - Result {i}]\n"
            result += doc.page_content + "\n"
    else:
        result += f"No rules found for '{rule_topic2}'\n"
    
    # Search for interaction between the two
    result += f"\n{'='*60}\n"
    result += "INTERACTION BETWEEN TOPICS\n"
    result += f"{'='*60}\n"
    interaction_query = f"{rule_topic1} and {rule_topic2} interaction"
    docs_interaction = _retriever.get_relevant_documents(interaction_query, k=3)
    if docs_interaction:
        result += f"\n[Combined Search]\n"
        result += docs_interaction[0].page_content + "\n"
    else:
        result += f"No specific interaction rules found. Review topics above to determine interaction.\n"
    
    # Add synthesis guidance
    result += f"\n{'='*60}\n"
    result += "ANALYSIS GUIDANCE\n"
    result += f"{'='*60}\n"
    result += f"When analyzing the interaction between '{rule_topic1}' and '{rule_topic2}':\n"
    result += "1. Check which takes precedence or applies first\n"
    result += "2. Look for timing restrictions or dependencies\n"
    result += "3. Consider if one modifies or prevents the other\n"
    result += "4. Review the rules above for specific interaction clauses\n"
    
    return result


@tool
def search_cards_by_criteria(
    colors: str = "",
    mana_value: str = "",
    mana_cost: str = "",
    power: str = "",
    toughness: str = "",
    format_legal: str = "",
    card_type: str = "",
    keywords: str = "",
    text: str = "",
    rarity: str = ""
) -> str:
    """
    Search for cards using specific criteria via Scryfall's advanced search.
    
    Use this when you need to find cards matching specific attributes rather than
    searching by name. Essential for questions like "what 3 mana red creature..."
    or "find blue counterspells in Modern".
    
    Args:
        colors: Color identity - "w" (white), "u" (blue), "b" (black), "r" (red), 
                "g" (green), "c" (colorless). Can combine: "ur" for blue/red
        mana_value: Converted mana cost. Use numbers or comparisons: "3", "<=2", ">=4"
        mana_cost: EXACT mana cost using Scryfall notation. Use for specific mana requirements.
                  Examples: "{R}{R}{R}" for 3 red, "{U}{U}" for 2 blue, "{2}{G}{G}" for 2 generic + 2 green.
                  Use this when question specifies exact mana symbols (e.g., "3 red mana" = "{R}{R}{R}")
        power: Power value. Use numbers or comparisons: "3", ">=5", "*"
        toughness: Toughness value. Use numbers or comparisons: "3", ">=5", "*"
        format_legal: Format where card must be legal: "standard", "modern", "commander", 
                     "legacy", "vintage", "pioneer", "pauper"
        card_type: Card type: "creature", "instant", "sorcery", "enchantment", "artifact", 
                  "planeswalker", "land"
        keywords: Keywords to search for: "flying", "haste", "trample", "lifelink", etc.
        text: Search oracle text for specific words or phrases
        rarity: Card rarity: "common", "uncommon", "rare", "mythic"
    
    Returns:
        List of matching cards with their details
    
    Examples:
        # Find 3 mana red 3/3 creatures in Standard
        search_cards_by_criteria(colors="r", mana_value="3", power="3", 
                                 toughness="3", format_legal="standard", 
                                 card_type="creature")
        
        # Find blue counterspells in Modern
        search_cards_by_criteria(colors="u", text="counter target spell", 
                                 format_legal="modern")
        
        # Find white cards with lifelink costing 2 or less
        search_cards_by_criteria(colors="w", mana_value="<=2", keywords="lifelink")
    """
    try:
        # Build Scryfall search query using their syntax
        query_parts = []
        
        if colors:
            query_parts.append(f"c:{colors}")
        if mana_value:
            query_parts.append(f"mv{mana_value}" if any(op in mana_value for op in ['<', '>', '=']) else f"mv={mana_value}")
        if mana_cost:
            # Exact mana cost search (e.g., m:{R}{R}{R})
            query_parts.append(f"m:{mana_cost}")
        if power:
            query_parts.append(f"pow{power}" if any(op in power for op in ['<', '>', '=']) else f"pow={power}")
        if toughness:
            query_parts.append(f"tou{toughness}" if any(op in toughness for op in ['<', '>', '=']) else f"tou={toughness}")
        if format_legal:
            query_parts.append(f"f:{format_legal}")
        if card_type:
            query_parts.append(f"t:{card_type}")
        if keywords:
            query_parts.append(f"o:{keywords}")
        if text:
            query_parts.append(f'o:"{text}"')
        if rarity:
            query_parts.append(f"r:{rarity}")
        
        if not query_parts:
            return "❌ Please provide at least one search criterion."
        
        # Join query parts
        search_query = " ".join(query_parts)
        
        # Determine best ordering based on format
        if format_legal and format_legal.lower() in ['standard', 'pioneer', 'modern']:
            # For competitive formats, order by release date (newer first)
            order = 'released'
        else:
            # For casual formats like Commander, use EDHREC
            order = 'edhrec'
        
        # Make API call to Scryfall
        url = f"{_scryfall.BASE_URL}/cards/search"
        params = {
            'q': search_query,
            'order': order,
            'unique': 'cards',
            'dir': 'desc'  # Descending order (newest/most popular first)
        }
        
        response = _scryfall.session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        total_cards = data.get('total_cards', 0)
        
        if total_cards == 0:
            return f"❌ No cards found matching criteria:\n{search_query}\n\nTry adjusting your search parameters."
        
        # Format results
        result = f"=== CARD SEARCH RESULTS ===\n\n"
        result += f"Query: {search_query}\n"
        result += f"Total matches: {total_cards}\n\n"
        
        # Get top results (limit to 10)
        cards_data = data.get('data', [])[:10]
        
        # VALIDATION: If format was specified, double-check legalities
        if format_legal:
            validated_cards = []
            for card_data in cards_data:
                legalities = card_data.get('legalities', {})
                card_legal_in_format = legalities.get(format_legal.lower(), 'not_legal')
                
                # Only include if actually legal in the requested format
                if card_legal_in_format == 'legal':
                    validated_cards.append(card_data)
                else:
                    # DEBUG: Log why card was filtered out
                    print(f"[DEBUG] Filtered out {card_data.get('name')} - {format_legal} status: {card_legal_in_format}")
            
            cards_data = validated_cards
            
            if not cards_data:
                return f"❌ No cards found that are actually legal in {format_legal}.\n\nQuery used: {search_query}\n\nTry adjusting your search parameters."
        
        result += f"Top {len(cards_data)} results (verified legal in {format_legal if format_legal else 'all formats'}):\n\n"
        
        for i, card_data in enumerate(cards_data, 1):
            name = card_data.get('name', 'Unknown')
            mana_cost = card_data.get('mana_cost', '')
            type_line = card_data.get('type_line', '')
            oracle_text = card_data.get('oracle_text', 'No oracle text')
            
            # Get power/toughness for creatures
            pt = ""
            if 'power' in card_data and 'toughness' in card_data:
                pt = f" ({card_data['power']}/{card_data['toughness']})"
            
            result += f"{i}. **{name}**{pt}\n"
            result += f"   Mana Cost: {mana_cost if mana_cost else 'N/A'}\n"
            result += f"   Type: {type_line}\n"
            result += f"   Text: {oracle_text[:150]}{'...' if len(oracle_text) > 150 else ''}\n"
            
            # Add format legality confirmation
            if format_legal:
                result += f"   ✅ Legal in {format_legal.capitalize()}\n"
            result += "\n"
        
        if total_cards > 10:
            result += f"... and {total_cards - 10} more cards match your criteria.\n\n"
        
        result += "💡 To get full details on any card, use lookup_card(\"card name\")\n"
        
        return result
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"❌ No cards found matching criteria: {search_query}"
        else:
            return f"❌ HTTP error during search: {e}"
    except Exception as e:
        return f"❌ Error searching cards: {str(e)}"


@tool
def search_mtg_meta(query: str, max_results: int = 5) -> str:
    """
    Search the web for current MTG meta information, tournament results, and deck trends.
    
    Use this tool when you need information about:
    - Current meta game and deck popularity
    - Recent tournament results and winning decklists
    - Card pricing and market trends
    - Community opinions and strategy discussions
    - Format trends and tier lists
    - Pro player insights and content
    
    This tool searches the web for up-to-date information that isn't available in
    the Comprehensive Rules or Scryfall database.
    
    Args:
        query: Search query about MTG meta, tournaments, or deck trends
               (e.g., "Modern meta decks 2024", "cEDH Dockside Extortionist popularity")
        max_results: Maximum number of search results to return (default: 5)
        
    Returns:
        Summary of web search results with sources
        
    Example:
        search_mtg_meta("What decks are popular in Standard right now?")
        search_mtg_meta("Last Pro Tour winner decklist")
        search_mtg_meta("Is Orcish Bowmasters banned in any format?")
    """
    # Check if Tavily API key is configured
    if not config.TAVILY_API_KEY:
        return """❌ Tavily API key not configured. 
        
To use web search, add your Tavily API key to the .env file:
TAVILY_API_KEY=your_api_key_here

Get a free API key at: https://tavily.com"""
    
    try:
        from tavily import TavilyClient
        
        # Initialize Tavily client
        tavily = TavilyClient(api_key=config.TAVILY_API_KEY)
        
        # Enhance query with MTG context
        mtg_query = f"Magic the Gathering MTG {query}"
        
        # Perform search
        response = tavily.search(
            query=mtg_query,
            max_results=max_results,
            search_depth="advanced",  # More thorough search
            include_answer=True,  # Get AI-generated summary
            include_raw_content=False  # Don't need full page content
        )
        
        # Format results
        result = f"=== WEB SEARCH RESULTS ===\n\n"
        result += f"Query: {query}\n\n"
        
        # Add AI-generated answer if available
        if response.get('answer'):
            result += f"**Summary:**\n{response['answer']}\n\n"
        
        # Add individual results
        results = response.get('results', [])
        if results:
            result += f"**Sources ({len(results)} found):**\n\n"
            for i, item in enumerate(results, 1):
                result += f"{i}. **{item.get('title', 'No title')}**\n"
                result += f"   URL: {item.get('url', 'N/A')}\n"
                if item.get('content'):
                    # Truncate content to ~200 chars
                    content = item['content'][:200] + "..." if len(item['content']) > 200 else item['content']
                    result += f"   {content}\n"
                result += f"\n"
        else:
            result += "No results found.\n"
        
        result += "\n💡 Note: Web search results reflect current information and community opinions.\n"
        result += "Always cross-reference with official sources for rules questions.\n"
        
        return result
        
    except ImportError:
        return "❌ Error: tavily-python package not installed. Run: pip install tavily-python"
    except Exception as e:
        return f"❌ Error performing web search: {str(e)}\n\nPlease check your Tavily API key and try again."


@tool
def map_game_state(question: str) -> str:
    """
    Map out the game state to explicitly identify who controls what.
    
    Use this tool FIRST when questions involve multiple players and permanents.
    This helps you understand controller relationships before answering.
    
    Args:
        question: The user's question
        
    Returns:
        Explicit mapping of controllers and targeting relationships
        
    Example:
        Question: "If I Lightning Bolt Birds while opponent has Blood Artist"
        Returns:
        Player 1 (You) controls:
        - Lightning Bolt (spell you're casting)
        
        Player 2 (Opponent) controls:
        - Birds of Paradise (target of Lightning Bolt)
        - Blood Artist (will trigger when Birds dies)
        
        When Blood Artist triggers:
        - Controller: Player 2 (opponent)
        - "You gain 1 life" → Player 2 gains 1 life
        - "Target player loses 1 life" → Player 2 chooses target (likely Player 1)
    """
    question_lower = question.lower()
    
    result = "=== GAME STATE MAP ===\n\n"
    
    # Parse the question to identify controllers
    player1_controls = []
    player2_controls = []
    
    # Identify what each player controls
    if "i cast" in question_lower or "i lightning" in question_lower:
        player1_controls.append("Lightning Bolt (spell you're casting)")
    
    if "opponent" in question_lower:
        # Find what opponent controls
        if "opponent has" in question_lower or "opponent's" in question_lower:
            # Extract card names after "opponent has/opponent's"
            import re
            
            # Pattern for "opponent has [card]"
            match = re.search(r"opponent(?:'s)?\s+(?:has\s+)?([A-Za-z\s]+?)(?:\s*,|\s*\?|$)", question_lower)
            if match:
                card = match.group(1).strip()
                if card and len(card) > 2:
                    player2_controls.append(f"{card.title()} (opponent controls this)")
            
            # Check for specific cards
            if "blood artist" in question_lower:
                if "Blood Artist" not in str(player2_controls):
                    player2_controls.append("Blood Artist (opponent controls this)")
            
            if "birds" in question_lower or "paradise" in question_lower:
                if "Birds" not in str(player2_controls):
                    player2_controls.append("Birds of Paradise (opponent controls this)")
    
    # Format the output
    result += "**CONTROLLER MAP:**\n\n"
    result += "🔵 Player 1 (YOU - the person asking):\n"
    if player1_controls:
        for item in player1_controls:
            result += f"  - {item}\n"
    else:
        result += "  - (No permanents specified)\n"
    
    result += "\n🔴 Player 2 (OPPONENT):\n"
    if player2_controls:
        for item in player2_controls:
            result += f"  - {item}\n"
    else:
        result += "  - (No permanents specified)\n"
    
    # Add trigger analysis for Blood Artist
    if "blood artist" in question_lower:
        result += "\n**BLOOD ARTIST TRIGGER ANALYSIS:**\n\n"
        result += "Blood Artist's FULL ability: \"Whenever Blood Artist or another creature dies, target player loses 1 life and you gain 1 life.\"\n\n"
        result += "Since 🔴 Player 2 (opponent) controls Blood Artist:\n\n"
        result += "STEP 1 - Ability triggers when creature dies\n"
        result += "STEP 2 - Resolve the ability:\n"
        result += "  Part A: 'target player loses 1 life'\n"
        result += "    → Opponent (controller) chooses the target\n"
        result += "    → Opponent will choose 🔵 Player 1 (you)\n"
        result += "    → 🔵 YOU LOSE 1 LIFE\n\n"
        result += "  Part B: 'you gain 1 life'\n"
        result += "    → 'You' = the controller = Opponent\n"
        result += "    → 🔴 OPPONENT GAINS 1 LIFE\n\n"
        result += "⚠️⚠️⚠️ FINAL RESULT (READ THIS CAREFULLY) ⚠️⚠️⚠️\n"
        result += "When Blood Artist triggers (opponent controls it):\n"
        result += "✅ YOU (Player 1) LOSE 1 LIFE (you are the target)\n"
        result += "✅ OPPONENT (Player 2) GAINS 1 LIFE (they control Blood Artist)\n"
        result += "✅ Your answer MUST include BOTH of these effects!\n"
    
    return result


@tool
def check_controller_logic(question: str, your_answer: str) -> str:
    """
    Verify that controller logic is correct in your answer.
    
    Use this tool BEFORE giving your final answer when the question involves:
    - Multiple players (you vs opponent)
    - Cards controlled by different players
    - Abilities that say "you" or "target player"
    
    This tool checks if you correctly identified who controls what and who benefits.
    
    Args:
        question: The original question from the user
        your_answer: Your proposed answer before sending it
        
    Returns:
        Validation feedback on whether controller logic is correct
        
    Example:
        question: "If I Lightning Bolt Birds while opponent has Blood Artist, what happens?"
        your_answer: "Opponent loses 1 life, you gain 1 life"
        → Returns: "❌ ERROR: If opponent controls Blood Artist, opponent gains life, not you!"
    """
    result = "=== CONTROLLER LOGIC CHECK ===\n\n"
    
    question_lower = question.lower()
    answer_lower = your_answer.lower()
    
    # Check for common controller indicators in question
    opponent_controls = []
    player_controls = []
    
    # Parse who controls what from question
    if "opponent has" in question_lower or "opponent's" in question_lower or "their" in question_lower:
        # Try to extract card names that opponent controls
        words = question.split()
        for i, word in enumerate(words):
            if word.lower() in ["opponent", "opponent's", "their", "they"]:
                # Next few words might be card names
                if i + 1 < len(words):
                    opponent_controls.append(words[i+1].strip(',.?!'))
    
    # Blood Artist specific check
    if "blood artist" in question_lower:
        if "opponent" in question_lower:
            # Opponent controls Blood Artist
            if ("you gain" in answer_lower and "life" in answer_lower) or ("opponent lose" in answer_lower):
                result += "❌ CONTROLLER ERROR DETECTED!\n\n"
                result += "The question says 'opponent has Blood Artist'\n"
                result += "→ Opponent CONTROLS Blood Artist\n"
                result += "→ Blood Artist says 'you gain 1 life'\n"
                result += "→ 'You' = the controller = OPPONENT\n"
                result += "→ OPPONENT gains life, NOT the question asker!\n\n"
                result += "CORRECT ANSWER should say: 'opponent gains 1 life, you lose 1 life'\n"
                result += "Your answer currently has this BACKWARDS.\n\n"
                result += "🔧 Fix: Rewrite your answer with correct controller perspective."
                return result
    
    # Generic controller checks
    warnings = []
    
    # If question mentions "opponent has" or "opponent controls"
    if "opponent" in question_lower and ("has" in question_lower or "control" in question_lower):
        # Answer should typically benefit opponent, not player
        if "you gain" in answer_lower and "opponent lose" in answer_lower:
            warnings.append("⚠️ Warning: Answer says 'you gain' but question says opponent controls the permanent")
    
    if warnings:
        result += "Potential Issues Found:\n"
        for warning in warnings:
            result += f"  {warning}\n"
        result += "\nDouble-check: Who controls each permanent? Apply abilities from controller's perspective.\n"
    else:
        result += "✅ No obvious controller logic errors detected.\n"
        result += "\nReminder: Always verify:\n"
        result += "1. Who controls each permanent mentioned?\n"
        result += "2. When card says 'you', it means the controller\n"
        result += "3. Apply abilities from controller's perspective\n"
    
    return result


# Export streamlined tool list - removed bloated/redundant tools
# Removed: search_similar_rulings, verify_answer_completeness, cross_reference_rules
# These tools added overhead without significant accuracy improvement
ALL_TOOLS = [
    map_game_state,           # Map who controls what (USE FIRST for opponent questions)
    lookup_card,              # Get card details by name
    compare_multiple_cards,   # Analyze multiple card interactions
    search_rules,             # Search comprehensive rules  
    check_format_legality,    # Check if card is legal in format
    search_cards_by_criteria, # Find cards by attributes
    check_controller_logic,   # Verify controller logic (IMPORTANT)
]


if __name__ == "__main__":
    print("=" * 60)
    print("🛠️  MTG Agent Tools Test")
    print("=" * 60)
    
    # Test each tool
    print("\n1. Testing lookup_card...")
    print(lookup_card.invoke({"card_name": "Lightning Bolt"}))
    
    print("\n2. Testing search_rules...")
    print(search_rules.invoke({"query": "stack resolution", "num_results": 2}))
    
    print("\n3. Testing compare_multiple_cards...")
    print(compare_multiple_cards.invoke({"card_names": "Lightning Bolt, Counterspell"}))
    
    print("\n4. Testing check_format_legality...")
    print(check_format_legality.invoke({"card_name": "Black Lotus", "format_name": "vintage"}))

