# 🤖 Stack Sage - Agentic Features

## Overview

Stack Sage has been upgraded to a **fully agentic system** using LangGraph's ReAct (Reasoning + Acting) agent framework. The agent now has autonomous decision-making capabilities and can dynamically choose which tools to use based on your question.

## What Changed?

### Before (Fixed Pipeline):
```
Question → Fetch Cards → Retrieve Rules → Generate Answer
```
Every question went through the same steps, regardless of what you asked.

### After (Agentic System):
```
Question → Agent Analysis → Dynamic Tool Selection → Reasoning → Answer
```
The agent decides which tools to use based on your specific question.

## Available Tools

The agent has access to 9 specialized tools:

### 1. **lookup_card**
- Look up detailed card information
- Returns oracle text, rulings, card type, mana cost
- Use case: "What is Lightning Bolt?"

### 2. **search_rules**
- Search the MTG Comprehensive Rules
- Returns relevant rule sections
- Use case: "How does the stack work?"

### 3. **compare_multiple_cards**
- Analyze interactions between multiple cards
- Returns combined information for comparison
- Use case: "How do Rest in Peace and Unearth interact?"

### 4. **check_format_legality**
- Verify if a card is legal in a specific format
- Supports: Standard, Modern, Legacy, Vintage, Commander, etc.
- Use case: "Is Black Lotus legal in Commander?"

### 5. **search_similar_rulings**
- Find related rulings and edge cases for a card
- Returns official rulings plus related mechanics
- Use case: "What are common edge cases with Dockside Extortionist?"

### 6. **verify_answer_completeness**
- Self-evaluation tool for the agent
- Checks if the answer is thorough and accurate
- The agent can use this to improve its responses

### 7. **cross_reference_rules**
- Understand how two different mechanics interact
- Cross-references rule topics
- Use case: "How do triggered abilities and replacement effects interact?"

### 8. **search_cards_by_criteria** 🆕
- Search for cards by specific attributes (color, mana cost, P/T, format, etc.)
- Essential for "what [attributes] card" questions
- Use case: "What 3 mana red 3/3 creatures are in Standard?"
- **Prevents hallucination** - finds actual cards instead of guessing

### 9. **search_mtg_meta**
- Search the web for current meta information
- Returns tournament results, deck trends, popularity data
- Use case: "What decks are popular in Modern right now?"
- **Note**: Requires Tavily API key (free tier available)

## How the Agent Thinks

The agent uses a **ReAct (Reasoning + Acting)** pattern:

1. **Thought**: Analyzes the question
2. **Action**: Chooses a tool to use
3. **Observation**: Processes the tool's output
4. **Repeat**: If needed, uses more tools
5. **Final Answer**: Synthesizes all information

### Example Reasoning Flow:

**Question**: "How does Dockside Extortionist work with Spark Double?"

```
Thought: This question involves two specific cards. I need their details.
Action: lookup_card("Dockside Extortionist")
Observation: [Gets card info with ETB trigger]

Thought: Now I need Spark Double to understand the copy effect.
Action: lookup_card("Spark Double")
Observation: [Gets card info about copying]

Thought: I need to understand copy effects and ETB triggers.
Action: search_rules("copy effects enter the battlefield")
Observation: [Gets relevant rules]

Thought: I have enough information now.
Final Answer: [Comprehensive explanation]
```

## Key Differences from Before

| Aspect | Old Pipeline | New Agentic System |
|--------|-------------|-------------------|
| **Decision Making** | Fixed sequence | Dynamic, adaptive |
| **Tool Usage** | Always all tools | Only needed tools |
| **Efficiency** | Consistent, predictable | Optimized per question |
| **Complexity Handling** | Single-pass | Multi-step reasoning |
| **Self-Improvement** | No feedback | Can verify own answers |

## Usage

### CLI (No changes needed!)

The CLI interface remains the same:

```bash
python stack_sage.py
```

Ask questions naturally, and the agent will handle the rest!

### Programmatic Usage

```python
from backend.core.rag_pipeline import graph

# Ask a question
result = graph.invoke({"question": "What is Lightning Bolt?"})
print(result["response"])
```

### Direct Agent Access

For advanced usage, you can access the agent directly:

```python
from backend.core.rag_pipeline import agent
from langchain_core.messages import HumanMessage

# Get full message history (shows reasoning)
result = agent.invoke({
    "messages": [HumanMessage(content="How does the stack work?")]
})

# See the agent's thought process
for message in result["messages"]:
    print(f"{message.type}: {message.content}")
```

## Benefits of the Agentic Approach

✅ **More Intelligent**: Makes decisions based on context  
✅ **More Efficient**: Only uses tools when needed  
✅ **More Thorough**: Can verify and refine answers  
✅ **More Flexible**: Handles complex multi-part questions  
✅ **More Transparent**: Can show reasoning process  
✅ **Self-Correcting**: Can evaluate and improve responses  

## Example Questions

The agent excels at various types of questions:

### Simple Card Lookups
```
"What is Lightning Bolt?"
"Tell me about Counterspell"
```

### Card Interactions
```
"How do Rest in Peace and Unearth interact?"
"What happens when I copy Dockside Extortionist with Spark Double?"
```

### Rules Questions
```
"How does the stack work?"
"What are replacement effects?"
"Explain priority in Magic"
```

### Format Legality
```
"Is Sol Ring legal in Modern?"
"Can I play Black Lotus in Vintage?"
```

### Complex Multi-Part Questions
```
"How does Spark Double copy Dockside Extortionist, and is this combo legal in Commander?"
```
The agent will:
1. Look up both cards
2. Search copy effect rules
3. Check Commander legality
4. Synthesize a complete answer

### Meta and Tournament Questions 🆕
```
"What decks are popular in Modern right now?"
"What won the last Pro Tour?"
"Is Orcish Bowmasters seeing play in competitive?"
```
The agent will:
1. Use web search to find current meta data
2. Return tournament results and deck trends
3. Cite sources for verification

## Testing

Run the test suite to see the agent in action:

```bash
python test_agentic.py
```

This will run several test questions and show how the agent responds.

## Technical Details

### Architecture

```
Stack Sage Agentic System
├── LangGraph ReAct Agent
│   ├── ChatOpenAI (GPT-4)
│   └── Tool Belt (7 tools)
├── Tools Module (tools.py)
│   ├── Scryfall API Integration
│   └── Vector Store Retrieval
└── Legacy Wrapper (backward compatibility)
```

### Files Modified/Created

**New Files:**
- `backend/core/tools.py` - All agent tools
- `test_agentic.py` - Test suite
- `AGENTIC_FEATURES.md` - This document

**Modified Files:**
- `backend/core/rag_pipeline.py` - Converted to agentic system
- Maintains backward compatibility with CLI

### Dependencies

All existing dependencies work. The agent uses:
- `langgraph` - For agentic framework
- `langchain-openai` - For LLM
- `langchain.tools` - For tool decorators

## Future Enhancements

Potential improvements to the agentic system:

1. **Memory**: Remember conversation history across questions
2. **Planning**: Break complex questions into sub-questions
3. **Custom Tools**: Add tools for specific formats (Commander, cEDH, etc.)
4. **Web Search**: Search for recent tournament data or meta information
5. **Multi-Agent**: Specialized agents for different aspects (rules, gameplay, deck building)

## Troubleshooting

### Agent seems to make unnecessary tool calls
This is normal! The agent is designed to be thorough. It may verify information even if it seems obvious.

### Responses are slower than before
Agentic systems take longer because they reason through the problem. The trade-off is higher quality answers.

### Agent didn't use a tool I expected
The agent makes autonomous decisions. If it doesn't use a tool, it likely determined it wasn't needed for that specific question.

## Questions?

The agentic system is designed to be drop-in compatible with the existing CLI. Try it out and see how it performs!

For technical details about the implementation, see:
- `backend/core/tools.py` - Tool implementations
- `backend/core/rag_pipeline.py` - Agent creation and wrapper

