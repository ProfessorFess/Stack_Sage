# Testing Guide for Multi-Agent Stack Sage

## Quick Test Options

### Option 1: Run the Automated Test Script (Fastest)
```bash
cd /Users/professormyhre/projects/Stack_Sage
source backend/venv/bin/activate
python test_multi_agent.py
```

This tests:
- Simple card lookups
- Multi-card interactions
- Controller logic (critical!)
- Rules queries
- Format legality

### Option 2: Test via Python REPL (Interactive)
```bash
cd /Users/professormyhre/projects/Stack_Sage
source backend/venv/bin/activate
python
```

Then in Python:
```python
from backend.core.rag_pipeline import graph

# Test 1: Simple card lookup
result = graph.invoke({"question": "What is the effect of Rest in Peace?"})
print(result["response"])

# Test 2: Controller logic (critical test!)
result = graph.invoke({"question": "If I Lightning Bolt my opponent's Birds while they have Blood Artist, what happens?"})
print(result["response"])

# Test 3: Multi-card interaction
result = graph.invoke({"question": "How does Dockside Extortionist work with Spark Double?"})
print(result["response"])
```

### Option 3: Test via API (Full Stack)
```bash
# Terminal 1: Start backend
cd /Users/professormyhre/projects/Stack_Sage
source backend/venv/bin/activate
python backend/api/server.py

# Terminal 2: Test with curl
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the effect of Rest in Peace?"}'

# Test deck validation
curl -X POST http://localhost:8000/validate_deck \
  -H "Content-Type: application/json" \
  -d '{
    "decklist": "4 Lightning Bolt\n4 Counterspell\n52 Island",
    "format": "modern"
  }'

# Test formats endpoint
curl http://localhost:8000/formats
```

### Option 4: Test via Frontend (Visual)
```bash
# Terminal 1: Start backend
cd /Users/professormyhre/projects/Stack_Sage
source backend/venv/bin/activate
python backend/api/server.py

# Terminal 2: Start frontend
cd /Users/professormyhre/projects/Stack_Sage/frontend
npm run dev

# Open browser: http://localhost:5173
# Try the example questions
# Switch to Deck Validator mode and test deck validation
```

## Detailed Test Cases

### 1. Card Lookup Tests
```python
from backend.core.rag_pipeline import graph

# Test single card
result = graph.invoke({"question": "What does Lightning Bolt do?"})
print(result["response"])
# Expected: Should describe Lightning Bolt's effect
# Tools used: planner, lookup_card, interaction_reasoner, judge_verification

# Test card with complex text
result = graph.invoke({"question": "Explain Dockside Extortionist"})
print(result["response"])
# Expected: Should explain the treasure token creation
```

### 2. Multi-Card Interaction Tests
```python
# Test 2-card interaction
result = graph.invoke({"question": "How do Rest in Peace and Animate Dead interact?"})
print(result["response"])
# Expected: Should explain that Animate Dead can't target anything
# Tools used: planner, lookup_card, search_rules_hybrid, interaction_reasoner, judge_verification

# Test 3-card interaction
result = graph.invoke({"question": "What happens with Doubling Season, Dockside Extortionist, and Spark Double?"})
print(result["response"])
# Expected: Should explain token doubling and ETB triggers
```

### 3. Controller Logic Tests (CRITICAL)
```python
# Test opponent controls permanent
result = graph.invoke({"question": "If my opponent controls Blood Artist and a creature dies, what happens?"})
print(result["response"])
# Expected: "Opponent gains 1 life, you lose 1 life"
# Should include controller correction from Judge agent

# Test complex controller scenario
result = graph.invoke({"question": "I Lightning Bolt my opponent's Birds of Paradise while they have Blood Artist. What happens?"})
print(result["response"])
# Expected: Birds dies, Blood Artist triggers, opponent gains 1 life, you lose 1 life
# Judge agent should verify controller logic
```

### 4. Rules Query Tests
```python
# Test conceptual rules
result = graph.invoke({"question": "How does the stack work?"})
print(result["response"])
# Expected: Explanation of LIFO stack resolution
# Tools used: planner, search_rules_hybrid, interaction_reasoner

# Test specific rule
result = graph.invoke({"question": "What are state-based actions?"})
print(result["response"])
# Expected: Rule 704 explanation

# Test priority
result = graph.invoke({"question": "How does priority work in Magic?"})
print(result["response"])
# Expected: Explanation of priority passing
```

### 5. Format Legality Tests
```python
# Test banned card
result = graph.invoke({"question": "Is Black Lotus legal in Commander?"})
print(result["response"])
# Expected: Should say it's banned

# Test legal card
result = graph.invoke({"question": "Is Sol Ring legal in Commander?"})
print(result["response"])
# Expected: Should say it's legal

# Test format-specific
result = graph.invoke({"question": "Is Lightning Bolt legal in Standard?"})
print(result["response"])
# Expected: Depends on current Standard rotation
```

### 6. Deck Validation Tests
```python
from backend.core.deck_models import Deck, parse_decklist
from backend.core.deck_validator import validate_deck

# Test valid Modern deck
decklist = """
4 Lightning Bolt
4 Counterspell
4 Brainstorm
48 Island
"""
mainboard, sideboard = parse_decklist(decklist)
deck = Deck(name="Test", format="modern", mainboard=mainboard, sideboard=sideboard)
result = validate_deck(deck)
print(f"Legal: {result.is_legal}")
print(f"Errors: {result.errors}")

# Test invalid deck (too many copies)
decklist = """
5 Lightning Bolt
55 Island
"""
mainboard, sideboard = parse_decklist(decklist)
deck = Deck(name="Test", format="modern", mainboard=mainboard, sideboard=sideboard)
result = validate_deck(deck)
print(f"Legal: {result.is_legal}")
print(f"Errors: {result.errors}")
# Expected: Error about too many Lightning Bolts

# Test Commander deck
decklist = """
1 Sol Ring
99 Island
"""
mainboard, sideboard = parse_decklist(decklist)
deck = Deck(name="Test", format="commander", mainboard=mainboard, sideboard=sideboard, commander="Urza, Lord High Artificer")
result = validate_deck(deck)
print(f"Legal: {result.is_legal}")
```

### 7. Meta Query Tests (Requires Tavily API Key)
```python
# Test meta query
result = graph.invoke({"question": "What's good in Standard right now?"})
print(result["response"])
# Expected: Meta information or note that Tavily is not configured

# Test format-specific meta
result = graph.invoke({"question": "What are the top Modern decks?"})
print(result["response"])
```

### 8. Agent Routing Tests
```python
# These tests verify the Planner routes correctly

# Should route to CardAgent + RulesAgent
result = graph.invoke({"question": "How does Rest in Peace work?"})
tools = result.get("tools_used", [])
print(f"Tools used: {tools}")
# Expected: planner, lookup_card, search_rules_hybrid, interaction_reasoner, judge_verification

# Should route to RulesAgent only
result = graph.invoke({"question": "Explain the stack"})
tools = result.get("tools_used", [])
print(f"Tools used: {tools}")
# Expected: planner, search_rules_hybrid, interaction_reasoner

# Should route to CardAgent only (for simple lookup)
result = graph.invoke({"question": "What is Lightning Bolt?"})
tools = result.get("tools_used", [])
print(f"Tools used: {tools}")
# Expected: planner, lookup_card, interaction_reasoner, judge_verification
```

## Performance Testing

### Test Response Times
```python
import time
from backend.core.rag_pipeline import graph

questions = [
    "What is Lightning Bolt?",
    "How does the stack work?",
    "How do Rest in Peace and Animate Dead interact?",
]

for question in questions:
    start = time.time()
    result = graph.invoke({"question": question})
    elapsed = time.time() - start
    
    print(f"\nQuestion: {question}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Tools: {result.get('tools_used', [])}")
    
    # Check agent timings
    timings = result.get('diagnostics', {}).get('agent_timings', {})
    if timings:
        print("Agent timings:")
        for agent, duration in timings.items():
            print(f"  {agent}: {duration:.2f}s")
```

## Error Handling Tests

### Test Invalid Inputs
```python
# Test empty question
result = graph.invoke({"question": ""})
print(result["response"])
# Expected: "Please ask a question..."

# Test nonsense question
result = graph.invoke({"question": "asdfghjkl"})
print(result["response"])
# Expected: Should handle gracefully

# Test very long question
result = graph.invoke({"question": "What is " + "Lightning Bolt " * 100 + "?"})
print(result["response"])
# Expected: Should handle or timeout gracefully
```

### Test Missing Context
```python
# Test card that doesn't exist
result = graph.invoke({"question": "What does Fake Card Name do?"})
print(result["response"])
# Expected: Should say card not found

# Test obscure rules question
result = graph.invoke({"question": "What is rule 999.999?"})
print(result["response"])
# Expected: Should say no information found
```

## Grounding Verification Tests

### Test Judge Agent
```python
# Test that Judge catches hallucinations
# The Judge agent should reject answers that aren't grounded in context

# This should work (grounded in card text)
result = graph.invoke({"question": "What is Lightning Bolt's mana cost?"})
print(result["response"])
# Expected: Should correctly state {R}

# Test controller logic verification
result = graph.invoke({"question": "If my opponent has Blood Artist, who gains life?"})
print(result["response"])
# Expected: Should correctly say opponent gains life
# Judge should verify this is correct
```

## Integration Tests

### Test Full Stack
```bash
# 1. Start backend
python backend/api/server.py &
BACKEND_PID=$!

# 2. Wait for startup
sleep 3

# 3. Test health
curl http://localhost:8000/health

# 4. Test ask endpoint
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Lightning Bolt?"}'

# 5. Test deck validation
curl -X POST http://localhost:8000/validate_deck \
  -H "Content-Type: application/json" \
  -d '{"decklist": "4 Lightning Bolt\n56 Mountain", "format": "modern"}'

# 6. Cleanup
kill $BACKEND_PID
```

## Regression Tests

### Test Backward Compatibility
```python
# The old interface should still work
from backend.core.rag_pipeline import graph

# Old-style invocation
result = graph.invoke({"question": "What is Rest in Peace?"})
assert "response" in result
assert isinstance(result["response"], str)
print("✅ Backward compatibility maintained")
```

## Visual Testing Checklist

When testing the frontend:

- [ ] Chat mode loads correctly
- [ ] Example questions are displayed
- [ ] Can ask questions and get responses
- [ ] Responses are formatted with markdown
- [ ] "Tools Used" section appears
- [ ] Can switch to Deck Validator mode
- [ ] Format dropdown is populated
- [ ] Can enter deck list
- [ ] Validation results display correctly
- [ ] Errors are shown in red
- [ ] Warnings are shown in yellow
- [ ] Can switch back to Chat mode
- [ ] API status indicator works

## Expected Behavior Summary

### What Should Work
✅ Simple card lookups (< 2s)
✅ Multi-card interactions (< 5s)
✅ Controller logic with verification (< 5s)
✅ Rules queries (< 3s)
✅ Format legality checks (< 3s)
✅ Deck validation (< 15s, depends on card count)
✅ Meta queries (< 8s if Tavily configured)
✅ Agent routing and timing
✅ Error handling for invalid inputs
✅ Backward compatibility with old API

### What Might Not Work Yet
⚠️ Meta queries without Tavily API key (will show warning)
⚠️ Very complex multi-card interactions (may hit recursion limit)
⚠️ Deck validation with > 20 unique cards (only checks first 20 for legality)

## Troubleshooting Test Failures

### "Module not found"
```bash
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

### "OpenAI API key not found"
```bash
echo "OPENAI_API_KEY=your_key_here" > backend/.env
```

### "Qdrant collection not found"
```bash
python rebuild_vector_store.py
```

### Tests timeout
- Increase timeout in test script
- Check OpenAI API rate limits
- Verify internet connection for Scryfall API

### Controller logic tests fail
- This is the most critical test
- Check Judge agent logs
- Verify controller correction is being applied

## Next Steps

After testing, you can:
1. Add more test cases to `test_multi_agent.py`
2. Set up continuous integration (GitHub Actions)
3. Add RAGAS evaluation for answer quality
4. Create performance benchmarks
5. Add unit tests for individual agents

Happy testing! 🧪

