#!/usr/bin/env python3
"""
Final test to verify hallucination is fixed.
"""

from backend.core.tools import search_cards_by_criteria
from backend.core.rag_pipeline import graph

print("""
╔═══════════════════════════════════════════════════════════════╗
║              FINAL HALLUCINATION FIX TEST                      ║
╚═══════════════════════════════════════════════════════════════╝
""")

# Test 1: Direct tool test
print("="*80)
print("TEST 1: Testing search_cards_by_criteria tool directly")
print("="*80)
print("\nSearching for: 3 mana red creatures in Standard\n")

tool_result = search_cards_by_criteria.invoke({
    "colors": "r",
    "mana_value": "3",
    "format_legal": "standard",
    "card_type": "creature"
})

print(tool_result)

# Check for known issues
if "Guttersnipe" in tool_result:
    print("\n❌ PROBLEM: Guttersnipe found in results (not Standard legal)")
elif "Screaming Nemesis" in tool_result:
    print("\n✅ GOOD: Found Screaming Nemesis (actual Standard legal card)")
else:
    print("\n⚠️  Results don't include expected cards")

input("\n\nPress Enter to test the full agent...")

# Test 2: Full agent test
print("\n" + "="*80)
print("TEST 2: Testing full agent with the problematic question")
print("="*80)

question = "what 3-mana red creature is good in standard"
print(f"\nQuestion: {question}\n")

result = graph.invoke({"question": question})
answer = result.get("response", "No response")

print("Agent's Answer:")
print("-"*80)
print(answer)
print("-"*80)

# Validate answer
print("\n📊 VALIDATION:")

# Check for hallucinations
hallucinations = {
    "Guttersnipe": "Not Standard legal",
    "Scorching Shot": "This is a burn spell, not a creature",
    "Bloodghast": "Not Standard legal, wrong mana cost, wrong color"
}

found_hallucination = False
for card_name, reason in hallucinations.items():
    if card_name in answer:
        print(f"❌ HALLUCINATION DETECTED: {card_name}")
        print(f"   Reason it's wrong: {reason}")
        found_hallucination = True

# Check for correct cards
correct_cards = [
    "Screaming Nemesis",
    "Solphim",
    "Squee"
]

found_correct = False
for card_name in correct_cards:
    if card_name in answer:
        print(f"✅ Found correct card: {card_name}")
        found_correct = True

if not found_hallucination and found_correct:
    print("\n🎉 SUCCESS: Agent provided accurate, verified answer!")
elif not found_hallucination and not found_correct:
    print("\n⚠️  No known cards found in answer")
    print("   This might be okay if new cards are in Standard")
else:
    print("\n❌ FAILURE: Agent still hallucinating")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)

