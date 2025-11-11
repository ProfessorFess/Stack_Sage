#!/usr/bin/env python3
"""
Test script for the multi-agent Stack Sage system.

This script tests various query types to verify the multi-agent
system is working correctly.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.core.rag_pipeline import graph


def test_query(question: str, description: str):
    """Test a single query."""
    print(f"\n{'='*80}")
    print(f"TEST: {description}")
    print(f"{'='*80}")
    print(f"Question: {question}")
    print(f"{'='*80}\n")
    
    try:
        result = graph.invoke({"question": question})
        print(result["response"])
        print(f"\n{'─'*80}")
        print(f"Tools Used: {result.get('tools_used', [])}")
        print(f"{'='*80}\n")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"{'='*80}\n")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("MULTI-AGENT STACK SAGE TEST SUITE")
    print("="*80)
    
    tests = [
        # Test 1: Simple card lookup
        ("What is the effect of Rest in Peace?", "Simple card lookup"),
        
        # Test 2: Multi-card interaction
        ("How does Dockside Extortionist work with Spark Double?", "Multi-card interaction"),
        
        # Test 3: Controller logic (critical test)
        ("If I Lightning Bolt my opponent's Birds of Paradise while they have Blood Artist, what happens?", 
         "Controller logic test"),
        
        # Test 4: Rules query
        ("How does the stack resolve?", "Rules query"),
        
        # Test 5: Format legality
        ("Is Black Lotus legal in Commander?", "Format legality check"),
    ]
    
    passed = 0
    failed = 0
    
    for question, description in tests:
        if test_query(question, description):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    print("="*80 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

