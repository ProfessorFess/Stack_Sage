"""
Scryfall API integration for fetching MTG card data.

This module provides functions to fetch card information from the Scryfall API,
including oracle text, card types, rulings, and more.
"""

import re
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Card:
    """Represents a Magic: The Gathering card."""
    
    name: str
    oracle_text: str
    type_line: str
    mana_cost: str
    colors: List[str]
    keywords: List[str]
    rulings: List[str]
    
    def to_context_string(self) -> str:
        """Convert card to a formatted string for LLM context."""
        context = f"**{self.name}**\n"
        context += f"Type: {self.type_line}\n"
        if self.mana_cost:
            context += f"Mana Cost: {self.mana_cost}\n"
        context += f"Oracle Text: {self.oracle_text}\n"
        
        if self.keywords:
            context += f"Keywords: {', '.join(self.keywords)}\n"
        
        if self.rulings:
            context += f"\nRulings:\n"
            for i, ruling in enumerate(self.rulings[:3], 1):  # Limit to 3 rulings
                context += f"  {i}. {ruling}\n"
        
        return context


class ScryfallAPI:
    """Interface for the Scryfall API."""
    
    BASE_URL = "https://api.scryfall.com"
    
    def __init__(self):
        """Initialize the Scryfall API client."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StackSage-MTG-Assistant/1.0'
        })
    
    def fetch_card(self, card_name: str) -> Optional[Card]:
        """
        Fetch a single card by name using fuzzy matching.
        
        Args:
            card_name: Name of the card to fetch
            
        Returns:
            Card object if found, None otherwise
        """
        try:
            url = f"{self.BASE_URL}/cards/named"
            params = {'fuzzy': card_name}
            
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            # Fetch rulings if available
            rulings = self._fetch_rulings(data.get('id', ''))
            
            return Card(
                name=data.get('name', card_name),
                oracle_text=data.get('oracle_text', 'No oracle text available.'),
                type_line=data.get('type_line', 'Unknown type'),
                mana_cost=data.get('mana_cost', ''),
                colors=data.get('colors', []),
                keywords=data.get('keywords', []),
                rulings=rulings
            )
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Card not found: {card_name}")
            else:
                print(f"HTTP error fetching card '{card_name}': {e}")
            return None
        except Exception as e:
            print(f"Error fetching card '{card_name}': {e}")
            return None
    
    def _fetch_rulings(self, card_id: str) -> List[str]:
        """
        Fetch rulings for a card.
        
        Args:
            card_id: Scryfall ID of the card
            
        Returns:
            List of ruling texts
        """
        if not card_id:
            return []
        
        try:
            url = f"{self.BASE_URL}/cards/{card_id}/rulings"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            rulings = [ruling['comment'] for ruling in data.get('data', [])]
            return rulings
            
        except Exception as e:
            print(f"Error fetching rulings: {e}")
            return []
    
    def fetch_cards(self, card_names: List[str]) -> List[Card]:
        """
        Fetch multiple cards by name.
        
        Args:
            card_names: List of card names to fetch
            
        Returns:
            List of Card objects (excluding cards not found)
        """
        cards = []
        for name in card_names:
            card = self.fetch_card(name)
            if card:
                cards.append(card)
        return cards


def extract_card_names(query: str) -> List[str]:
    """
    Extract potential card names from a query.
    
    Uses heuristics to identify card names:
    - Capitalized words/phrases
    - Words in quotes
    - Known MTG card patterns
    
    Args:
        query: User query string
        
    Returns:
        List of potential card names
    """
    card_names = []
    
    # Extract quoted strings (high confidence)
    quoted_pattern = r'"([^"]+)"'
    quoted_matches = re.findall(quoted_pattern, query)
    card_names.extend(quoted_matches)
    
    # Extract capitalized sequences (can include lowercase words like "of", "the", "in")
    # This catches things like "Rest in Peace", "Wrath of God", "Dockside Extortionist"
    capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+(?:of|the|in|from|to|with|and|or)?\s*[A-Z][a-z]+)+\b'
    capitalized_matches = re.findall(capitalized_pattern, query)
    
    # Filter out common false positives
    false_positives = {'Magic The Gathering', 'The Stack', 'The Battlefield'}
    capitalized_matches = [m for m in capitalized_matches if m not in false_positives]
    
    card_names.extend(capitalized_matches)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_names = []
    for name in card_names:
        if name.lower() not in seen:
            seen.add(name.lower())
            unique_names.append(name)
    
    return unique_names


def get_card_context(query: str) -> str:
    """
    Get formatted card context from a query.
    
    Extracts card names and fetches their information from Scryfall.
    
    Args:
        query: User query string
        
    Returns:
        Formatted string with card information
    """
    # Extract card names
    card_names = extract_card_names(query)
    
    if not card_names:
        return ""
    
    # Fetch cards from Scryfall
    scryfall = ScryfallAPI()
    cards = scryfall.fetch_cards(card_names)
    
    if not cards:
        return ""
    
    # Format context
    context = "=== RELEVANT CARDS ===\n\n"
    for card in cards:
        context += card.to_context_string()
        context += "\n" + "="*50 + "\n\n"
    
    return context


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("🃏 Scryfall API Test")
    print("=" * 60)
    
    # Test card name extraction
    test_queries = [
        "How does Rest in Peace work?",
        'What happens when I copy "Dockside Extortionist" with Spark Double?',
        "Does the stack resolve when Lightning Bolt targets a creature?",
    ]
    
    print("\n📝 Testing Card Name Extraction:\n")
    for query in test_queries:
        card_names = extract_card_names(query)
        print(f"Query: {query}")
        print(f"Extracted: {card_names}\n")
    
    # Test fetching a specific card
    print("\n" + "=" * 60)
    print("🔍 Fetching Card: 'Rest in Peace'")
    print("=" * 60 + "\n")
    
    scryfall = ScryfallAPI()
    card = scryfall.fetch_card("Rest in Peace")
    
    if card:
        print(card.to_context_string())
    
    # Test full context generation
    print("\n" + "=" * 60)
    print("🎯 Full Context Generation")
    print("=" * 60 + "\n")
    
    query = 'How does "Dockside Extortionist" work with "Spark Double"?'
    print(f"Query: {query}\n")
    
    context = get_card_context(query)
    print(context)

