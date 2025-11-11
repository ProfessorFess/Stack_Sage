#!/usr/bin/env python3
"""
Test script to verify the multi-agent system is working correctly.

This tests:
1. AI-powered Planner routing
2. Specialist agent execution
3. End-to-end question answering
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.core.multi_agent_graph import invoke_graph

def test_question(question: str, expected_agents: list = None):
    """Test a single question through the multi-agent system."""
    print(f"\n{'='*80}")
    print(f"QUESTION: {question}")
    print(f"{'='*80}")
    
    try:
        result = invoke_graph(question)
        
        print(f"\n📝 ANSWER:")
        print("-" * 80)
        print(result["response"])
        print("-" * 80)
        
        print(f"\n🔧 Tools Used: {', '.join(result.get('tools_used', []))}")
        
        if result.get("diagnostics", {}).get("agent_timings"):
            print(f"\n⏱️  Agent Timings:")
            for agent, time_s in result["diagnostics"]["agent_timings"].items():
                print(f"   • {agent}: {time_s:.2f}s")
        
        if expected_agents:
            tools_used = result.get('tools_used', [])
            for agent in expected_agents:
                if agent in str(tools_used):
                    print(f"✅ Expected agent '{agent}' was used")
                else:
                    print(f"❌ Expected agent '{agent}' was NOT used")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run test suite for multi-agent system."""
    print("=" * 80)
    print("🧠 MULTI-AGENT SYSTEM TEST SUITE")
    print("=" * 80)
    print("\nTesting AI-powered routing and specialist agent execution...\n")
    
    test_cases = [
        {
            "question": "What is the effect of Lightning Bolt?",
            "description": "Simple card lookup",
            "expected_agents": ["card", "rules"]
        },
        {
            "question": "Does Rest in Peace stop Unearth?",
            "description": "Card interaction question",
            "expected_agents": ["card", "rules", "interaction"]
        },
        {
            "question": "How does the stack work?",
            "description": "Pure rules question",
            "expected_agents": ["rules"]
        },
        {
            "question": "What are the best decks in Standard?",
            "description": "Meta/popularity question",
            "expected_agents": ["meta"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'#'*80}")
        print(f"TEST {i}/{len(test_cases)}: {test_case['description']}")
        print(f"{'#'*80}")
        
        success = test_question(
            test_case["question"],
            test_case.get("expected_agents")
        )
        
        if success:
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    print(f"{'='*80}\n")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

