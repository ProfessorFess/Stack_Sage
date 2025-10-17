# Debugging Hallucination Issues

## Current Problem

Even with strict anti-hallucination rules, the agent is still hallucinating answers:

**Example**:
```
Question: "what 3-mana red creature is good in standard"
Agent Response: "Scorching Shot" (WRONG - this is a burn spell, not a creature)
```

## What We've Done

### Attempt 1: Added search_cards_by_criteria tool
- ✅ Tool works correctly
- ❌ Agent not using it

### Attempt 2: Enhanced system prompt with critical rules
- ✅ Rules are clear
- ❌ Agent ignoring them

### Attempt 3: Made prompt EXTREMELY strict
- ✅ Uses FORBIDDEN, MANDATORY language
- ✅ Explicit pattern matching
- ✅ Lowered temperature to 0.1
- ⏳ Testing needed

## Diagnostic Steps

### 1. Check if Tools Are Being Called

The agent might be answering without using tools. We need to see the reasoning trace.

**Enable Verbose Mode** (add to test script):

```python
from backend.core.rag_pipeline import agent
from langchain_core.messages import HumanMessage

# Enable verbose output
result = agent.invoke(
    {"messages": [HumanMessage(content="what 3-mana red creature is good in standard")]},
    {"verbose": True}  # This might show tool calls
)

# Print all messages to see tool usage
for msg in result["messages"]:
    print(f"\n{msg.type}: {msg.content[:200]}")
```

### 2. Check Tool Call History

```python
# See if any tools were called
for msg in result["messages"]:
    if hasattr(msg, "tool_calls"):
        print(f"Tool calls: {msg.tool_calls}")
```

### 3. Test Tool Directly

Verify the tool works:

```python
from backend.core.tools import search_cards_by_criteria

result = search_cards_by_criteria.invoke({
    "colors": "r",
    "mana_value": "3",
    "format_legal": "standard",
    "card_type": "creature"
})
print(result)
```

## Possible Issues

### Issue 1: Agent Bypassing Tools

**Symptom**: Agent answers directly from training data  
**Why**: LLM has strong priors, ignores system prompt  
**Solution**: Make tool use required, not optional

### Issue 2: Tool Not Registered Correctly

**Symptom**: Agent doesn't see the tool  
**Why**: Tool not in ALL_TOOLS or registration failed  
**Solution**: Verify tool is in list

### Issue 3: LLM Model Limitations

**Symptom**: GPT-4 ignores instructions  
**Why**: Model prioritizes training data over instructions  
**Solution**: Try GPT-4-turbo or Claude

### Issue 4: ReAct Agent Configuration

**Symptom**: Agent not following ReAct pattern  
**Why**: Agent configuration doesn't enforce tool use  
**Solution**: Adjust agent parameters

## Solutions to Try

### Solution 1: Force Tool Validation (RECOMMENDED)

Add a wrapper that validates tool usage:

```python
class ToolEnforcingWrapper:
    """Ensures agent uses tools before answering."""
    
    def __init__(self, agent):
        self.agent = agent
    
    def invoke(self, state: dict) -> dict:
        question = state.get("question", "")
        
        # Detect if question requires search_cards_by_criteria
        patterns = [
            "what.*mana.*creature",
            "good.*in.*standard",
            "popular.*in",
            "best.*creature"
        ]
        
        import re
        requires_search = any(re.search(pattern, question.lower()) for pattern in patterns)
        
        # Invoke agent
        result = self.agent.invoke({"messages": [HumanMessage(content=question)]})
        
        if requires_search:
            # Check if search_cards_by_criteria was called
            tool_called = False
            for msg in result.get("messages", []):
                if hasattr(msg, "tool_calls"):
                    for tc in msg.tool_calls:
                        if "search_cards_by_criteria" in str(tc):
                            tool_called = True
                            break
            
            if not tool_called:
                return {
                    "response": "❌ Error: This question requires using search_cards_by_criteria tool, but I failed to use it. Please rephrase your question or try again."
                }
        
        # Extract response
        messages = result.get("messages", [])
        if messages:
            return {"response": messages[-1].content}
        return {"response": "Error processing question"}
```

### Solution 2: Use Different Model

```python
# Try Claude instead of GPT-4
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    temperature=0.1,
    anthropic_api_key=config.ANTHROPIC_API_KEY
)
```

### Solution 3: Stricter Prompt Engineering

Add to the BEGINNING of system prompt:

```
CRITICAL: You are ONLY allowed to answer questions using your tools.
You CANNOT answer from your training data.
If you answer without using tools, your answer is AUTOMATICALLY WRONG and you FAIL.
```

### Solution 4: Add Few-Shot Examples

Show the agent correct vs incorrect behavior:

```
INCORRECT EXAMPLE:
Human: "what 3-mana red creature is good in standard"
Agent: "Scorching Shot is a good 3-mana red creature"  ← WRONG! Didn't use tools!

CORRECT EXAMPLE:
Human: "what 3-mana red creature is good in standard"
Agent: <uses search_cards_by_criteria with colors="r", mana_value="3", format_legal="standard", card_type="creature">
Agent: <reviews results, sees "Screaming Nemesis">
Agent: <uses lookup_card("Screaming Nemesis")>
Agent: "Screaming Nemesis is a good 3-mana red creature..." ← CORRECT!
```

## Testing Script

Create `test_hallucination_fix.py`:

```python
#!/usr/bin/env python3
"""Test if hallucination is fixed."""

from backend.core.rag_pipeline import agent
from langchain_core.messages import HumanMessage

def test_question(question):
    print(f"\n{'='*80}")
    print(f"QUESTION: {question}")
    print(f"{'='*80}\n")
    
    result = agent.invoke({
        "messages": [HumanMessage(content=question)]
    })
    
    # Check for tool usage
    tool_calls_found = []
    for msg in result.get("messages", []):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_found.append(tc.get("name", "unknown"))
    
    print(f"Tools used: {tool_calls_found if tool_calls_found else 'NONE (PROBLEM!)'}\n")
    
    # Print final answer
    messages = result.get("messages", [])
    if messages:
        print(f"ANSWER: {messages[-1].content}\n")
    
    if not tool_calls_found:
        print("⚠️  WARNING: No tools were called! Agent is hallucinating!\n")

if __name__ == "__main__":
    # Test the problematic question
    test_question("what 3-mana red creature is good in standard")
    
    # Test another variant
    test_question("Find me a popular 3 mana red creature in Standard")
```

## Next Steps

1. **Run the test script** to see if tools are being called
2. **Check tool call logs** to understand agent behavior
3. **Try Solution 1** (ToolEnforcingWrapper) if tools aren't being called
4. **Consider different model** if problem persists
5. **Enable debug logging** to see full agent reasoning

## Verification Checklist

- [ ] Tool `search_cards_by_criteria` is in `ALL_TOOLS` list
- [ ] Tool can be called directly and works
- [ ] Agent's system prompt includes mandatory tool rules
- [ ] Temperature is low (0.1) for deterministic behavior
- [ ] Test question triggers tool usage
- [ ] Agent actually calls the tool (check logs)
- [ ] Response is based on tool output, not training data

## If All Else Fails

Consider these alternatives:

1. **Hard-code routing**: Pre-process questions and route to specific tools
2. **Validation layer**: Post-process answers and reject hallucinations
3. **Ensemble approach**: Run multiple attempts and validate consistency
4. **Different framework**: Try AutoGen or CrewAI instead of LangGraph

---

**Status**: Debugging in progress  
**Current**: Very strict prompt + low temperature  
**Next**: Verify tool usage with logging

