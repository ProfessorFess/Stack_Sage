#!/usr/bin/env python3
"""
Debug the search_cards_by_criteria tool to see what it's actually returning.
"""

from backend.core.tools import search_cards_by_criteria

print("="*80)
print("TESTING: search_cards_by_criteria tool directly")
print("="*80)

# Test the exact query that should be used for "3 mana red creature in Standard"
result = search_cards_by_criteria.invoke({
    "colors": "r",
    "mana_value": "3",
    "format_legal": "standard",
    "card_type": "creature"
})

print("\n📋 FULL TOOL OUTPUT:")
print("-"*80)
print(result)
print("-"*80)

# Check if Guttersnipe appears
if "Guttersnipe" in result:
    print("\n⚠️  WARNING: Guttersnipe found in results!")
    print("   Guttersnipe is NOT Standard legal - tool is returning wrong cards!")
else:
    print("\n✅ Guttersnipe NOT in results (good)")

# Check for actual Standard-legal 3-mana red creatures
standard_legal_cards = [
    "Screaming Nemesis",
    "Solphim, Mayhem Dominus",
    "Questing Druid",
    "Mindsplice Apparatus"
]

print("\n📊 Checking for known Standard-legal 3-mana red creatures:")
for card in standard_legal_cards:
    if card in result:
        print(f"   ✅ Found: {card}")
    else:
        print(f"   ❌ Missing: {card}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)

if "Guttersnipe" in result:
    print("❌ PROBLEM: Tool is returning non-Standard-legal cards")
    print("   The 'format_legal' parameter is not working correctly")
    print("   Need to fix the Scryfall query syntax")
else:
    print("✅ Tool appears to be filtering correctly")
    print("   The agent might be picking the wrong card from results")

