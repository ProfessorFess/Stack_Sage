"""
Deck Data Models

Data structures for representing MTG decks and validation results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class DeckCard:
    """Represents a card in a deck with quantity."""
    name: str
    quantity: int
    is_commander: bool = False
    is_sideboard: bool = False


@dataclass
class Deck:
    """Represents a Magic: The Gathering deck."""
    name: str
    format: str  # standard, modern, commander, etc.
    mainboard: List[DeckCard] = field(default_factory=list)
    sideboard: List[DeckCard] = field(default_factory=list)
    commander: Optional[str] = None
    companion: Optional[str] = None
    
    def total_mainboard_cards(self) -> int:
        """Calculate total number of cards in mainboard."""
        return sum(card.quantity for card in self.mainboard)
    
    def total_sideboard_cards(self) -> int:
        """Calculate total number of cards in sideboard."""
        return sum(card.quantity for card in self.sideboard)
    
    def get_card_count(self, card_name: str) -> int:
        """Get the total count of a specific card across mainboard and sideboard."""
        count = 0
        for card in self.mainboard + self.sideboard:
            if card.name.lower() == card_name.lower():
                count += card.quantity
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert deck to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "format": self.format,
            "mainboard": [
                {"name": card.name, "quantity": card.quantity}
                for card in self.mainboard
            ],
            "sideboard": [
                {"name": card.name, "quantity": card.quantity}
                for card in self.sideboard
            ],
            "commander": self.commander,
            "companion": self.companion,
            "total_cards": self.total_mainboard_cards()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Deck':
        """Create deck from dictionary."""
        mainboard = [
            DeckCard(name=card["name"], quantity=card["quantity"])
            for card in data.get("mainboard", [])
        ]
        sideboard = [
            DeckCard(name=card["name"], quantity=card["quantity"], is_sideboard=True)
            for card in data.get("sideboard", [])
        ]
        
        return cls(
            name=data.get("name", "Untitled Deck"),
            format=data.get("format", "unknown"),
            mainboard=mainboard,
            sideboard=sideboard,
            commander=data.get("commander"),
            companion=data.get("companion")
        )


@dataclass
class ValidationError:
    """Represents a deck validation error."""
    severity: str  # "error" or "warning"
    message: str
    card_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "message": self.message,
            "card_name": self.card_name
        }


@dataclass
class DeckValidationResult:
    """Result of deck validation."""
    is_legal: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    format: str = ""
    total_cards: int = 0
    
    def add_error(self, message: str, card_name: Optional[str] = None):
        """Add an error to the validation result."""
        self.errors.append(ValidationError(severity="error", message=message, card_name=card_name))
        self.is_legal = False
    
    def add_warning(self, message: str, card_name: Optional[str] = None):
        """Add a warning to the validation result."""
        self.warnings.append(ValidationError(severity="warning", message=message, card_name=card_name))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_legal": self.is_legal,
            "format": self.format,
            "total_cards": self.total_cards,
            "errors": [error.to_dict() for error in self.errors],
            "warnings": [warning.to_dict() for warning in self.warnings],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }


def parse_decklist(decklist_text: str) -> tuple[List[DeckCard], List[DeckCard]]:
    """
    Parse a decklist from text format.
    
    Supports formats like:
    - "4 Lightning Bolt"
    - "4x Lightning Bolt"
    - "Lightning Bolt" (assumes 1)
    
    Sideboard is indicated by a line containing "sideboard" or "sb:"
    
    Args:
        decklist_text: Text representation of the deck
        
    Returns:
        Tuple of (mainboard_cards, sideboard_cards)
    """
    import re
    
    mainboard = []
    sideboard = []
    current_list = mainboard
    
    lines = decklist_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        
        # Check for sideboard marker
        if 'sideboard' in line.lower() or line.lower().startswith('sb:'):
            current_list = sideboard
            continue
        
        # Parse card line: "4 Lightning Bolt" or "4x Lightning Bolt"
        match = re.match(r'^(\d+)x?\s+(.+)$', line)
        if match:
            quantity = int(match.group(1))
            card_name = match.group(2).strip()
            current_list.append(DeckCard(
                name=card_name,
                quantity=quantity,
                is_sideboard=(current_list is sideboard)
            ))
        else:
            # Assume quantity of 1 if no number specified
            if line:
                current_list.append(DeckCard(
                    name=line,
                    quantity=1,
                    is_sideboard=(current_list is sideboard)
                ))
    
    return mainboard, sideboard

