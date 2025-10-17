#!/usr/bin/env python3
"""
Test script for the agentic Stack Sage system.

This script tests the new agentic RAG pipeline with various questions.
"""

from backend.core.rag_pipeline import graph


def test_agent(question: str):
    """Test the agent with a question."""
    print(f"\n{'='*80}")
    print(f"QUESTION: {question}")
    print(f"{'='*80}\n")
    
    try:
        result = graph.invoke({"question": question})
        response = result.get("response", "No response generated")
        print(response)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║          🧪 STACK SAGE AGENTIC TEST SUITE 🧪         ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Test 1: Simple card lookup
    test_agent("What is Lightning Bolt?")
    
    # Test 2: Card interaction
    test_agent("How does Rest in Peace interact with Unearth?")
    
    # Test 3: Rules question
    test_agent("How does the stack work?")
    
    # Test 4: Complex interaction
    test_agent('What happens when I copy "Dockside Extortionist" with "Spark Double"?')
    
    # Test 5: Format legality
    test_agent("Is Black Lotus legal in Commander?")
    
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                   Testing Complete!                   ║
    ╚═══════════════════════════════════════════════════════╝
    """)

