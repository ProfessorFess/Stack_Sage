#!/usr/bin/env python3
"""
Test if the agent is actually using tools or hallucinating.
"""

from backend.core.rag_pipeline import agent
from langchain_core.messages import HumanMessage

def test_with_logging(question):
    """Test a question and show what tools were called."""
    print(f"\n{'='*80}")
    print(f"TESTING: {question}")
    print(f"{'='*80}\n")
    
    # Invoke agent
    result = agent.invoke({
        "messages": [HumanMessage(content=question)]
    })
    
    # Analyze messages to see tool usage
    print("📋 MESSAGE TRACE:")
    print("-" * 80)
    
    tool_calls_made = []
    for i, msg in enumerate(result.get("messages", []), 1):
        msg_type = msg.type if hasattr(msg, 'type') else type(msg).__name__
        
        print(f"\nMessage {i} [{msg_type}]:")
        
        # Check for tool calls
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_name = tc.get("name", "unknown")
                tool_args = tc.get("args", {})
                tool_calls_made.append(tool_name)
                print(f"  🔧 TOOL CALL: {tool_name}")
                print(f"     Args: {tool_args}")
        
        # Show content (truncated)
        if hasattr(msg, 'content') and msg.content:
            content = str(msg.content)
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  💬 Content: {preview}")
    
    print("\n" + "="*80)
    print(f"📊 SUMMARY:")
    print(f"   Tools called: {tool_calls_made if tool_calls_made else '❌ NONE (PROBLEM!)'}")
    
    # Get final answer
    messages = result.get("messages", [])
    if messages:
        final_answer = messages[-1].content
        print(f"\n📜 FINAL ANSWER:")
        print("-" * 80)
        print(final_answer)
        print("-" * 80)
        
        # Check for hallucination indicators
        hallucination_indicators = [
            "Scorching Shot",  # Known hallucination
            "Bloodghast",      # Previous hallucination
            "varies based on", # Vague language
            "typically",       # Uncertainty
            "generally",       # Uncertainty
        ]
        
        for indicator in hallucination_indicators:
            if indicator.lower() in final_answer.lower():
                print(f"\n⚠️  WARNING: Potential hallucination detected: '{indicator}'")
    
    if not tool_calls_made:
        print("\n❌ CRITICAL ERROR: Agent did not use ANY tools!")
        print("   The agent is answering from training data (hallucinating)")
    else:
        print(f"\n✅ Agent used {len(tool_calls_made)} tool(s)")
        
        # Check if correct tool was used
        if "search_cards_by_criteria" in tool_calls_made:
            print("   ✅ Used search_cards_by_criteria (correct for this question type)")
        else:
            print("   ⚠️  Did NOT use search_cards_by_criteria (might be wrong tool)")
    
    print("\n" + "="*80 + "\n")
    
    return tool_calls_made


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         STACK SAGE - TOOL USAGE DIAGNOSTIC TEST               ║
╚═══════════════════════════════════════════════════════════════╝

This script tests if the agent is actually using tools or hallucinating.
    """)
    
    # Test 1: The problematic question
    test_with_logging("what 3-mana red creature is good in standard")
    
    input("\nPress Enter to test another question...")
    
    # Test 2: Variant phrasing
    test_with_logging("Find me a good 3 mana red creature for Standard format")
    
    input("\nPress Enter to test a card lookup...")
    
    # Test 3: Direct card lookup (should definitely use lookup_card)
    test_with_logging("What is Lightning Bolt?")
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                       TESTING COMPLETE                        ║
╚═══════════════════════════════════════════════════════════════╝

If you see "❌ NONE" for tool calls, the agent is hallucinating.
The agent MUST call search_cards_by_criteria for attribute-based questions.
    """)

