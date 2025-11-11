#!/usr/bin/env python3
"""
Individual Agent Testing Script

Tests each agent in isolation to verify they work correctly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.core.agent_state import initialize_state
from backend.core.agents.planner import planner_agent
from backend.core.agents.card_agent import card_agent
from backend.core.agents.rules_agent import rules_agent
from backend.core.agents.interaction_agent import interaction_agent
from backend.core.agents.judge_agent import judge_agent


def test_planner():
    """Test the Planner agent."""
    print("\n" + "="*80)
    print("TEST: Planner Agent")
    print("="*80)
    
    test_cases = [
        ("What is Lightning Bolt?", ["cards"]),
        ("How does the stack work?", ["rules"]),
        ("How do Rest in Peace and Animate Dead interact?", ["cards", "rules"]),
        ("Is Black Lotus legal in Commander?", ["cards"]),
    ]
    
    for question, expected_tasks in test_cases:
        print(f"\nQuestion: {question}")
        state = initialize_state(question)
        result = planner_agent(state)
        task_plan = result.get("task_plan", [])
        print(f"Task Plan: {task_plan}")
        
        # Check if expected tasks are in plan
        for task in expected_tasks:
            if task in task_plan:
                print(f"  ✅ {task} in plan")
            else:
                print(f"  ❌ {task} NOT in plan")
    
    print("\n" + "="*80)


def test_card_agent():
    """Test the Card Agent."""
    print("\n" + "="*80)
    print("TEST: Card Agent")
    print("="*80)
    
    test_cases = [
        "What is Lightning Bolt?",
        "How does Rest in Peace work?",
        "Explain Dockside Extortionist",
    ]
    
    for question in test_cases:
        print(f"\nQuestion: {question}")
        state = initialize_state(question)
        result = card_agent(state)
        
        cards = result.get("context", {}).get("cards", [])
        print(f"Cards fetched: {len(cards)}")
        for card in cards:
            print(f"  - {card['name']}")
        
        if cards:
            print("  ✅ Card agent working")
        else:
            print("  ❌ No cards fetched")
    
    print("\n" + "="*80)


def test_rules_agent():
    """Test the Rules Agent."""
    print("\n" + "="*80)
    print("TEST: Rules Agent")
    print("="*80)
    
    test_cases = [
        "How does the stack work?",
        "What are state-based actions?",
        "Explain priority",
    ]
    
    for question in test_cases:
        print(f"\nQuestion: {question}")
        state = initialize_state(question)
        result = rules_agent(state)
        
        rules = result.get("context", {}).get("rules", [])
        coverage = result.get("diagnostics", {}).get("coverage_score", 0)
        
        print(f"Rules fetched: {len(rules)}")
        print(f"Coverage score: {coverage:.2f}")
        
        if rules:
            print("  ✅ Rules agent working")
            # Show first rule snippet
            if rules[0].get("content"):
                snippet = rules[0]["content"][:100]
                print(f"  First rule: {snippet}...")
        else:
            print("  ❌ No rules fetched")
    
    print("\n" + "="*80)


def test_interaction_agent():
    """Test the Interaction Agent."""
    print("\n" + "="*80)
    print("TEST: Interaction Agent")
    print("="*80)
    
    # Set up state with card and rules context
    question = "What does Lightning Bolt do?"
    state = initialize_state(question)
    
    # Add card context
    state = card_agent(state)
    
    # Add rules context
    state = rules_agent(state)
    
    # Generate answer
    print(f"\nQuestion: {question}")
    result = interaction_agent(state)
    
    draft_answer = result.get("draft_answer", "")
    missing = result.get("diagnostics", {}).get("missing_context", [])
    
    if draft_answer:
        print(f"✅ Generated answer ({len(draft_answer)} chars)")
        print(f"Preview: {draft_answer[:150]}...")
    else:
        print("❌ No answer generated")
    
    if missing:
        print(f"⚠️  Missing context: {missing}")
    
    print("\n" + "="*80)


def test_judge_agent():
    """Test the Judge Agent."""
    print("\n" + "="*80)
    print("TEST: Judge Agent")
    print("="*80)
    
    # Test 1: Grounded answer
    print("\nTest 1: Grounded answer")
    question = "What does Lightning Bolt do?"
    state = initialize_state(question)
    state = card_agent(state)
    state = interaction_agent(state)
    result = judge_agent(state)
    
    judge_report = result.get("judge_report", {})
    print(f"Grounded: {judge_report.get('grounded', False)}")
    print(f"Controller OK: {judge_report.get('controller_ok', False)}")
    
    if judge_report.get('grounded'):
        print("✅ Grounding verification working")
    else:
        print("❌ Grounding verification failed")
    
    # Test 2: Controller logic
    print("\nTest 2: Controller logic")
    question = "If my opponent controls Blood Artist and a creature dies, what happens?"
    state = initialize_state(question)
    state = card_agent(state)
    state = interaction_agent(state)
    
    # Manually set a wrong answer to test correction
    state["draft_answer"] = "You gain 1 life and opponent loses 1 life"
    
    result = judge_agent(state)
    judge_report = result.get("judge_report", {})
    
    print(f"Controller OK: {judge_report.get('controller_ok', False)}")
    if judge_report.get('corrections'):
        print("✅ Controller correction applied")
        print(f"Correction: {judge_report['corrections'][:100]}...")
    else:
        print("⚠️  No controller correction (might be OK if answer was correct)")
    
    print("\n" + "="*80)


def test_full_pipeline():
    """Test the full agent pipeline."""
    print("\n" + "="*80)
    print("TEST: Full Pipeline")
    print("="*80)
    
    question = "What is Lightning Bolt?"
    print(f"\nQuestion: {question}")
    
    # Run through all agents
    state = initialize_state(question)
    print("1. Initialized state")
    
    state = planner_agent(state)
    print(f"2. Planner: {state.get('task_plan', [])}")
    
    state = card_agent(state)
    cards = len(state.get("context", {}).get("cards", []))
    print(f"3. Card Agent: {cards} cards")
    
    state = rules_agent(state)
    rules = len(state.get("context", {}).get("rules", []))
    print(f"4. Rules Agent: {rules} rules")
    
    state = interaction_agent(state)
    has_answer = bool(state.get("draft_answer"))
    print(f"5. Interaction Agent: {'✅' if has_answer else '❌'} answer generated")
    
    state = judge_agent(state)
    grounded = state.get("judge_report", {}).get("grounded", False)
    print(f"6. Judge Agent: {'✅' if grounded else '❌'} grounded")
    
    final_answer = state.get("final_answer", "")
    if final_answer:
        print(f"\n✅ Full pipeline working!")
        print(f"Answer preview: {final_answer[:150]}...")
    else:
        print("\n❌ Pipeline failed to generate answer")
    
    print("\n" + "="*80)


def main():
    """Run all agent tests."""
    print("\n" + "="*80)
    print("INDIVIDUAL AGENT TEST SUITE")
    print("="*80)
    
    try:
        test_planner()
        test_card_agent()
        test_rules_agent()
        test_interaction_agent()
        test_judge_agent()
        test_full_pipeline()
        
        print("\n" + "="*80)
        print("✅ ALL AGENT TESTS COMPLETE")
        print("="*80 + "\n")
        
        return 0
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

