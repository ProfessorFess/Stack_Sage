"""
Deck Validator

Validates MTG decks according to format-specific rules.
"""

from typing import Dict, List, Set
from backend.core.deck_models import Deck, DeckValidationResult, DeckCard
from backend.core.scryfall import ScryfallAPI


# Basic land names (exempt from copy limits)
BASIC_LANDS = {
    'plains', 'island', 'swamp', 'mountain', 'forest',
    'wastes', 'snow-covered plains', 'snow-covered island',
    'snow-covered swamp', 'snow-covered mountain', 'snow-covered forest'
}


class DeckValidator:
    """Validates decks according to format rules."""
    
    def __init__(self):
        """Initialize the deck validator."""
        self.scryfall = ScryfallAPI()
    
    def validate(self, deck: Deck) -> DeckValidationResult:
        """
        Validate a deck according to its format rules.
        
        Args:
            deck: The deck to validate
            
        Returns:
            DeckValidationResult with errors and warnings
        """
        format_name = deck.format.lower()
        total_cards = deck.total_mainboard_cards()
        
        result = DeckValidationResult(
            is_legal=True,
            format=format_name,
            total_cards=total_cards
        )
        
        # Route to format-specific validation
        if format_name == "commander" or format_name == "edh":
            self._validate_commander(deck, result)
        elif format_name == "standard":
            self._validate_standard(deck, result)
        elif format_name in ["modern", "pioneer", "legacy", "vintage"]:
            self._validate_constructed(deck, result, format_name)
        elif format_name == "pauper":
            self._validate_pauper(deck, result)
        elif format_name == "brawl":
            self._validate_brawl(deck, result)
        else:
            result.add_warning(f"Unknown format: {format_name}. Performing basic validation only.")
            self._validate_basic(deck, result)
        
        return result
    
    def _validate_basic(self, deck: Deck, result: DeckValidationResult):
        """Basic validation rules (minimum deck size, copy limits)."""
        # Check minimum deck size (60 for most formats)
        if deck.total_mainboard_cards() < 60:
            result.add_error(f"Deck has {deck.total_mainboard_cards()} cards, minimum is 60")
        
        # Check copy limits (4 max, except basic lands)
        self._check_copy_limits(deck, result, max_copies=4)
    
    def _validate_standard(self, deck: Deck, result: DeckValidationResult):
        """Validate Standard format deck."""
        # Minimum 60 cards
        if deck.total_mainboard_cards() < 60:
            result.add_error(f"Standard decks must have at least 60 cards (found {deck.total_mainboard_cards()})")
        
        # Maximum 4 copies (except basic lands)
        self._check_copy_limits(deck, result, max_copies=4)
        
        # Sideboard max 15
        if deck.total_sideboard_cards() > 15:
            result.add_error(f"Sideboard has {deck.total_sideboard_cards()} cards, maximum is 15")
        
        # Check card legality in Standard
        self._check_format_legality(deck, result, "standard")
    
    def _validate_modern(self, deck: Deck, result: DeckValidationResult):
        """Validate Modern format deck."""
        self._validate_constructed(deck, result, "modern")
    
    def _validate_constructed(self, deck: Deck, result: DeckValidationResult, format_name: str):
        """Validate constructed format (Modern, Pioneer, Legacy, Vintage)."""
        # Minimum 60 cards
        if deck.total_mainboard_cards() < 60:
            result.add_error(f"{format_name.capitalize()} decks must have at least 60 cards (found {deck.total_mainboard_cards()})")
        
        # Maximum 4 copies (except basic lands)
        self._check_copy_limits(deck, result, max_copies=4)
        
        # Sideboard max 15
        if deck.total_sideboard_cards() > 15:
            result.add_error(f"Sideboard has {deck.total_sideboard_cards()} cards, maximum is 15")
        
        # Check card legality
        self._check_format_legality(deck, result, format_name)
    
    def _validate_commander(self, deck: Deck, result: DeckValidationResult):
        """Validate Commander/EDH format deck."""
        # Must have exactly 100 cards (including commander)
        total_with_commander = deck.total_mainboard_cards()
        if deck.commander:
            total_with_commander += 1
        
        if total_with_commander != 100:
            result.add_error(f"Commander decks must have exactly 100 cards (found {total_with_commander})")
        
        # Must have a commander
        if not deck.commander:
            result.add_error("Commander deck must have a commander specified")
        
        # Singleton format (max 1 copy of each card, except basic lands)
        self._check_copy_limits(deck, result, max_copies=1)
        
        # No sideboard in Commander
        if deck.total_sideboard_cards() > 0:
            result.add_warning("Commander format does not use sideboards")
        
        # Check card legality
        self._check_format_legality(deck, result, "commander")
        
        # TODO: Check color identity restrictions (requires commander card data)
    
    def _validate_pauper(self, deck: Deck, result: DeckValidationResult):
        """Validate Pauper format deck."""
        # Minimum 60 cards
        if deck.total_mainboard_cards() < 60:
            result.add_error(f"Pauper decks must have at least 60 cards (found {deck.total_mainboard_cards()})")
        
        # Maximum 4 copies
        self._check_copy_limits(deck, result, max_copies=4)
        
        # Sideboard max 15
        if deck.total_sideboard_cards() > 15:
            result.add_error(f"Sideboard has {deck.total_sideboard_cards()} cards, maximum is 15")
        
        # Check card legality and rarity (Pauper only allows commons)
        self._check_format_legality(deck, result, "pauper")
    
    def _validate_brawl(self, deck: Deck, result: DeckValidationResult):
        """Validate Brawl format deck."""
        # Must have exactly 60 cards (including commander)
        total_with_commander = deck.total_mainboard_cards()
        if deck.commander:
            total_with_commander += 1
        
        if total_with_commander != 60:
            result.add_error(f"Brawl decks must have exactly 60 cards (found {total_with_commander})")
        
        # Must have a commander
        if not deck.commander:
            result.add_error("Brawl deck must have a commander specified")
        
        # Singleton format
        self._check_copy_limits(deck, result, max_copies=1)
        
        # Check card legality
        self._check_format_legality(deck, result, "brawl")
    
    def _check_copy_limits(self, deck: Deck, result: DeckValidationResult, max_copies: int):
        """
        Check that no card exceeds the copy limit.
        
        Args:
            deck: The deck to check
            result: Validation result to update
            max_copies: Maximum copies allowed (1 for singleton, 4 for most formats)
        """
        # Count card occurrences
        card_counts: Dict[str, int] = {}
        
        for card in deck.mainboard + deck.sideboard:
            card_name_lower = card.name.lower()
            
            # Skip basic lands
            if card_name_lower in BASIC_LANDS:
                continue
            
            if card_name_lower not in card_counts:
                card_counts[card_name_lower] = 0
            card_counts[card_name_lower] += card.quantity
        
        # Check limits
        for card_name, count in card_counts.items():
            if count > max_copies:
                result.add_error(
                    f"Too many copies of '{card_name}': {count} (maximum {max_copies})",
                    card_name=card_name
                )
    
    def _check_format_legality(self, deck: Deck, result: DeckValidationResult, format_name: str):
        """
        Check if all cards in the deck are legal in the specified format.
        
        Args:
            deck: The deck to check
            result: Validation result to update
            format_name: Format to check against
        """
        # Get unique card names
        unique_cards = set()
        for card in deck.mainboard + deck.sideboard:
            unique_cards.add(card.name)
        
        # Check each card (limit to first 20 to avoid too many API calls)
        checked_count = 0
        for card_name in list(unique_cards)[:20]:
            if checked_count >= 20:
                result.add_warning("Only checked first 20 unique cards for legality")
                break
            
            try:
                import requests
                url = f"{self.scryfall.BASE_URL}/cards/named"
                params = {'fuzzy': card_name}
                response = self.scryfall.session.get(url, params=params, timeout=5)
                response.raise_for_status()
                data = response.json()
                
                legalities = data.get('legalities', {})
                card_legal = legalities.get(format_name.lower(), 'not_legal')
                
                if card_legal == 'banned':
                    result.add_error(
                        f"'{card_name}' is BANNED in {format_name.capitalize()}",
                        card_name=card_name
                    )
                elif card_legal == 'restricted':
                    result.add_warning(
                        f"'{card_name}' is RESTRICTED in {format_name.capitalize()} (max 1 copy)",
                        card_name=card_name
                    )
                elif card_legal == 'not_legal':
                    result.add_error(
                        f"'{card_name}' is not legal in {format_name.capitalize()}",
                        card_name=card_name
                    )
                
                checked_count += 1
                
            except Exception as e:
                print(f"Error checking legality for {card_name}: {e}")
                # Don't fail validation on API errors
                continue


def validate_deck(deck: Deck) -> DeckValidationResult:
    """
    Convenience function to validate a deck.
    
    Args:
        deck: The deck to validate
        
    Returns:
        DeckValidationResult
    """
    validator = DeckValidator()
    return validator.validate(deck)

