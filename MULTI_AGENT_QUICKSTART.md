# Multi-Agent Stack Sage - Quick Start Guide

## What Changed?

Stack Sage has been rebuilt with a **multi-agent architecture**:

- **Before**: Single agent with tools
- **After**: 8 specialized agents working together
  - Planner (routes queries)
  - Card Agent (Scryfall lookups)
  - Rules Agent (comprehensive rules search)
  - Interaction Agent (reasoning and drafting)
  - Judge Agent (verification and controller logic)
  - Deck Agent (deck validation)
  - Meta Agent (metagame information)
  - Finalizer (answer formatting)

## New Features

### 1. Deck Validation ✨
Validate your deck against format rules:
- Standard, Modern, Pioneer, Legacy, Vintage
- Commander (100 cards, singleton)
- Pauper, Brawl

### 2. Meta Information 🔥
Get current metagame data:
- "What's good in Standard right now?"
- Cached for 24 hours
- Freshness warnings for stale data

### 3. Improved Controller Logic ✅
Better handling of "opponent controls X" questions:
- Automatic game state mapping
- Judge agent verification
- Corrections for controller errors

## Getting Started

### 1. Start the Backend

```bash
# Activate virtual environment
cd /Users/professormyhre/projects/Stack_Sage
source backend/venv/bin/activate

# Start the server
python backend/api/server.py
```

Server runs on: http://localhost:8000
API docs: http://localhost:8000/docs

### 2. Start the Frontend

```bash
# In a new terminal
cd /Users/professormyhre/projects/Stack_Sage/frontend
npm run dev
```

Frontend runs on: http://localhost:5173

### 3. Test the System

```bash
# Run the test script
python test_multi_agent.py
```

## Using the New Features

### Chat Mode (Default)
Ask questions like before:
- "What is the effect of Rest in Peace?"
- "How does Dockside Extortionist work with Spark Double?"
- "If I Lightning Bolt my opponent's Birds while they have Blood Artist, what happens?"

### Deck Validator Mode
1. Click "🃏 Deck Validator" button
2. Select format (Standard, Modern, Commander, etc.)
3. Enter deck list:
   ```
   4 Lightning Bolt
   4 Counterspell
   52 Island
   ```
4. Click "Validate Deck"
5. View results (errors and warnings)

### Meta Queries
Ask about the metagame:
- "What's good in Standard right now?"
- "What decks are popular in Modern?"
- "Is [card] good in [format]?"

## API Endpoints

### Existing Endpoints
- `POST /ask` - Ask a question
- `GET /health` - Health check
- `GET /examples` - Get example questions

### New Endpoints
- `POST /validate_deck` - Validate a deck
  ```json
  {
    "decklist": "4 Lightning Bolt\n4 Counterspell\n52 Island",
    "format": "modern"
  }
  ```
- `GET /formats` - Get supported formats
- `GET /meta/{format}` - Get cached meta data
- `POST /meta/refresh?format_name={format}` - Refresh meta data

## Agent Flow

When you ask a question, here's what happens:

1. **Planner** analyzes your question
2. **Specialist agents** gather information:
   - Card Agent fetches card details
   - Rules Agent searches comprehensive rules
   - Deck Agent validates decks
   - Meta Agent searches web for meta info
3. **Interaction Agent** drafts the answer
4. **Judge Agent** verifies correctness
5. **Finalizer** formats the response

You'll see which agents were used at the bottom of each answer!

## Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the virtual environment
source backend/venv/bin/activate
```

### "API is offline"
```bash
# Check if backend is running
curl http://localhost:8000/health
```

### Frontend not loading
```bash
# Reinstall dependencies
cd frontend
npm install
npm run dev
```

### Deck validation not working
- Make sure deck list format is correct: "4 Lightning Bolt" (quantity + card name)
- One card per line
- Format must be selected

## Performance Notes

- **Typical query**: 2-5 seconds
- **Complex interactions**: 5-10 seconds
- **Deck validation**: 5-15 seconds (checks card legality via API)
- **Meta queries**: 3-8 seconds (web search if not cached)

Agent timing is shown in the response for debugging.

## What's Next?

The system is ready for:
- Card pricing integration (TCGPlayer API)
- Advanced deck analysis (mana curve, synergies)
- Better meta caching and tier lists
- Parallel agent execution
- More comprehensive testing

## Need Help?

- Check `MULTI_AGENT_REBUILD_SUMMARY.md` for detailed implementation info
- Check `PRODUCTION_FEATURES.md` for full feature roadmap
- Run `test_multi_agent.py` to verify system is working

Enjoy the new multi-agent Stack Sage! 🎉

