# Multi-Agent System Documentation

## Overview

Stack Sage now uses an **intelligent multi-agent architecture** powered by LangGraph. Instead of a single agent making all decisions, we have specialized agents that collaborate based on AI-powered routing.

## Architecture

```
User Question
     ↓
[Planner Agent] ← AI analyzes question & decides routing
     ↓
  Routes to specialist agents based on intent:
     ↓
├─→ [Card Agent]        (Card lookups & details)
├─→ [Rules Agent]       (Comprehensive rules search)
├─→ [Interaction Agent] (Card interaction analysis)
├─→ [Judge Agent]       (Answer verification & grounding)
├─→ [Meta Agent]        (Metagame & deck popularity)
└─→ [Deck Agent]        (Deck validation - not yet connected)
     ↓
[Finalizer]
     ↓
Final Answer with citations & metadata
```

## How It Works

### 1. AI-Powered Planning

The **Planner Agent** uses an LLM to:
- **Extract card names** from the question (intelligently, not regex)
- **Classify intent**: 
  - `card_interaction` - Questions about cards
  - `rules` - Questions about game mechanics
  - `meta` - Questions about popular decks/formats
  - `deck_validation` - Deck legality checks
- **Build a dynamic task plan** routing to relevant specialist agents

### 2. Specialist Agents

Each agent has a specific role:

#### Card Agent
- Fetches card details from Scryfall
- Provides oracle text, mana costs, types
- Handles multiple card lookups

#### Rules Agent  
- Searches the Comprehensive Rules
- Uses hybrid vector + BM25 search
- Retrieves relevant rules sections

#### Interaction Agent
- Analyzes how multiple cards interact
- Resolves complex game states
- Considers controller relationships

#### Judge Agent
- Verifies answers are grounded in retrieved facts
- Checks for hallucinations
- Validates controller logic

#### Meta Agent
- Web searches for metagame info
- Finds popular decks and strategies
- Tournament results & trends

### 3. Conditional Routing

The graph uses **conditional edges** to route between agents based on:
- Task plan from Planner
- Context gathered so far
- Missing information detected

## Example Routing Decisions

### Question: "What is Lightning Bolt?"
```
Planner Analysis:
  - Card names: ["Lightning Bolt"]
  - Intent: card_interaction
  
Route: Planner → Card Agent → Rules Agent → Interaction → Judge → Finalizer
```

### Question: "How does the stack work?"
```
Planner Analysis:
  - Card names: []
  - Intent: rules
  
Route: Planner → Rules Agent → Finalizer
```

### Question: "What are the best decks in Standard?"
```
Planner Analysis:
  - Card names: []
  - Intent: meta
  
Route: Planner → Meta Agent → Finalizer
```

## Benefits of Multi-Agent Architecture

✅ **Separation of Concerns**: Each agent focuses on one domain
✅ **Better Performance**: Agents can be optimized individually
✅ **Easier Debugging**: Track which agent produced what
✅ **Scalability**: Add new agents without touching existing ones
✅ **AI-Powered Routing**: No brittle regex patterns - LLM decides routing
✅ **Quality Control**: Judge agent verifies all answers

## Configuration

### Enable Verbose Logging

To see agent execution details:

```bash
export STACK_SAGE_VERBOSE=true
python -m backend.api.server
```

This shows:
- Which agents are invoked
- Timing for each agent
- Routing decisions
- Context gathered

### Recursion Limit

The graph has a recursion limit of 15 to prevent infinite loops. If you hit this:
- Question is too complex
- Break into smaller questions
- Check for circular dependencies in routing

## Testing

### Test the Multi-Agent System

```bash
# Run the integration test suite
python test_multi_agent_integration.py
```

This tests:
- Planner routing decisions
- Specialist agent execution
- End-to-end answers for different question types

### Test Individual Agents

```bash
# Test specialist agents in isolation
python test_individual_agents.py
```

## API Integration

The FastAPI server (`backend/api/server.py`) uses the multi-agent system for the `/ask` endpoint:

```python
from backend.core.multi_agent_graph import invoke_graph

result = invoke_graph(question)
# Returns: {"response": str, "tools_used": list, "citations": list, "diagnostics": dict}
```

## Comparison: Old vs New

### Old System (ReAct Agent)
- ❌ Single agent with many tools
- ❌ Less specialized
- ❌ Harder to debug tool chains
- ✅ Simpler architecture
- ✅ Faster for simple questions

### New System (Multi-Agent Graph)
- ✅ Specialized agents for each domain
- ✅ AI-powered intelligent routing
- ✅ Better answer verification (Judge)
- ✅ Cleaner separation of concerns
- ✅ Easier to extend with new agents
- ❌ More complex architecture
- ❌ Slightly slower (more hops)

## Extending the System

### Adding a New Agent

1. Create agent file in `backend/core/agents/your_agent.py`:

```python
from backend.core.agent_state import AgentState, add_tool_used

def your_agent(state: AgentState) -> AgentState:
    question = state["user_question"]
    
    # Your agent logic here
    result = do_something(question)
    
    # Update state
    state["context"]["your_data"] = result
    state = add_tool_used(state, "your_agent")
    
    return state
```

2. Add to `multi_agent_graph.py`:

```python
# Import
from backend.core.agents.your_agent import your_agent

# Add to lazy loader
_agent_modules['your'] = your_agent

# Create node
@timed_agent("YourAgent")
def your_node(state: AgentState) -> AgentState:
    agents = _load_agents()
    return agents['your'](state)

# Add to graph
workflow.add_node("your", your_node)
workflow.add_edge("your", "finalize")
```

3. Update Planner routing to include your agent when appropriate.

## Troubleshooting

### "Recursion limit exceeded"
- Question triggered too many agent hops
- Simplify the question or break into parts
- Check for routing loops

### "Missing context" in diagnostics
- Some information couldn't be retrieved
- Check tool availability (API keys, network)
- May need to add fallback logic

### Agents not being called
- Check Planner's intent classification
- Enable verbose logging to see routing
- Verify agent is in task plan

## Future Enhancements

Potential improvements:
- [ ] Parallel agent execution where possible
- [ ] Agent result caching
- [ ] Confidence scores for routing decisions
- [ ] Dynamic agent selection based on available tools
- [ ] Self-healing: retry with different agents on failure
- [ ] Connect Deck Agent to graph routing

## Summary

The multi-agent system provides:
1. 🧠 **AI-Powered Routing** - LLM decides which agents to use
2. 👥 **Specialist Agents** - Each agent focuses on one domain
3. ✅ **Answer Verification** - Judge agent prevents hallucinations
4. 📊 **Transparency** - See which agents were used
5. 🔧 **Extensibility** - Easy to add new agents

This architecture makes Stack Sage more accurate, maintainable, and scalable!

