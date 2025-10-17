# Tavily Web Search Integration

## Overview

Stack Sage now includes **web search capabilities** via Tavily to answer meta-game questions, tournament data, and deck popularity that aren't available in static rules or card databases.

## What Can It Do?

The `search_mtg_meta` tool enables the agent to answer questions like:

✅ "What decks are popular in Modern right now?"  
✅ "What won the last Pro Tour?"  
✅ "Is Dockside Extortionist seeing play in cEDH?"  
✅ "What's the current Standard meta?"  
✅ "Is Orcish Bowmasters banned anywhere?"  
✅ "Best budget Commander deck 2024"  

## Setup Instructions

### 1. Get a Tavily API Key (Free!)

1. Go to [https://tavily.com](https://tavily.com)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier includes 1,000 searches/month

### 2. Add to Your .env File

Add the following line to your `.env` file:

```bash
TAVILY_API_KEY=your_api_key_here
```

### 3. Install Dependencies

```bash
pip install tavily-python
```

Or reinstall from requirements:

```bash
pip install -r backend/requirements.txt
```

## How It Works

### Agent Decision Making

The agent automatically decides when to use web search:

**Question**: "What decks are popular in Modern?"  
→ Agent thinks: *"This is about current meta, not rules"*  
→ Uses `search_mtg_meta` tool  
→ Returns current tournament data and deck trends

**Question**: "How does the stack work?"  
→ Agent thinks: *"This is a rules question"*  
→ Uses `search_rules` tool  
→ Returns Comprehensive Rules sections

### Tool Features

- **MTG-Focused**: Automatically adds "Magic the Gathering MTG" to queries
- **Advanced Search**: Uses Tavily's "advanced" depth for thorough results
- **AI Summary**: Gets Tavily's AI-generated answer summary
- **Source Citations**: Includes URLs and snippets from top results
- **Smart Limits**: Configurable max results (default: 5)

## Example Usage

### Via CLI

```bash
python stack_sage.py
```

Then ask:
```
🃏 Your question: What decks won the most recent Pro Tour?
```

The agent will:
1. Recognize this needs current tournament data
2. Use `search_mtg_meta("recent Pro Tour winner decklist")`
3. Return results with sources

### Programmatically

```python
from backend.core.tools import search_mtg_meta

# Direct tool usage
result = search_mtg_meta.invoke({
    "query": "Modern meta tier list 2024",
    "max_results": 5
})
print(result)
```

## What Gets Searched?

Tavily indexes:
- MTG tournament sites (StarCityGames, TCGPlayer, etc.)
- Reddit MTG communities
- MTG strategy articles and blogs
- Official WotC announcements
- Pro player content
- Deck database sites

## Tool Behavior

### When API Key is Missing

```
❌ Tavily API key not configured. 

To use web search, add your Tavily API key to the .env file:
TAVILY_API_KEY=your_api_key_here

Get a free API key at: https://tavily.com
```

The agent can still function using other tools - web search is **optional**.

### When Package Not Installed

```
❌ Error: tavily-python package not installed. 
Run: pip install tavily-python
```

## Response Format

```
=== WEB SEARCH RESULTS ===

Query: Modern meta decks 2024

**Summary:**
The Modern metagame in 2024 is dominated by Rakdos Scam, 
4-Color Control, and Living End. Orcish Bowmasters has 
significantly impacted the format...

**Sources (5 found):**

1. **Modern Metagame Breakdown - November 2024**
   URL: https://www.mtggoldfish.com/metagame/modern
   Modern's metagame continues to evolve with Rakdos 
   Scam maintaining its position as the most played deck...

2. **Pro Tour Results Analysis**
   URL: https://magic.wizards.com/...
   [content snippet]

💡 Note: Web search results reflect current information 
and community opinions. Always cross-reference with 
official sources for rules questions.
```

## Integration with Other Tools

The agent can combine web search with other tools:

**Question**: "Is Orcish Bowmasters good in Modern and is it legal?"

Agent workflow:
1. `check_format_legality("Orcish Bowmasters", "modern")` ✓ Legal
2. `search_mtg_meta("Orcish Bowmasters Modern play rate")` → Popular, tier 1
3. `lookup_card("Orcish Bowmasters")` → Get card details
4. Synthesize complete answer

## Benefits

✅ **Current Information**: Not limited to static databases  
✅ **Meta Insights**: Real tournament data and trends  
✅ **Community Knowledge**: Reddit discussions, pro insights  
✅ **Flexible**: Handles questions beyond rules adjudication  
✅ **Source Citations**: Provides URLs for verification  
✅ **Optional**: Works even without Tavily (other tools still function)  

## Cost Considerations

**Free Tier**:
- 1,000 searches/month
- Perfect for personal use
- No credit card required

**Paid Plans**:
- More searches if needed
- See [tavily.com/pricing](https://tavily.com/pricing)

## Privacy

- Searches go through Tavily's API
- Tavily has privacy-focused design
- See [Tavily Privacy Policy](https://tavily.com/privacy)

## Limitations

⚠️ **Not for Rules Questions**: Use `search_rules` for game mechanics  
⚠️ **Results Vary**: Web content changes constantly  
⚠️ **Community Opinions**: Not official rulings  
⚠️ **API Limits**: Free tier has monthly quota  

## Troubleshooting

### "API key not configured"
- Add `TAVILY_API_KEY` to your `.env` file
- Restart the application

### "tavily-python not installed"
- Run: `pip install tavily-python`
- Or: `pip install -r backend/requirements.txt`

### "Rate limit exceeded"
- You've hit the free tier limit
- Wait until next month or upgrade plan
- Agent will still work with other tools

### "No results found"
- Try rephrasing your query
- Be more specific
- Check if the topic has recent coverage

## Files Modified

1. **backend/requirements.txt** - Added `tavily-python==0.5.0`
2. **backend/core/config.py** - Added `TAVILY_API_KEY` config
3. **backend/core/tools.py** - Added `search_mtg_meta` tool
4. **backend/core/rag_pipeline.py** - Updated system prompt

## Next Steps

1. Get your Tavily API key: [tavily.com](https://tavily.com)
2. Add to `.env`: `TAVILY_API_KEY=your_key`
3. Install: `pip install tavily-python`
4. Test: Ask "What's popular in Modern right now?"

---

**Status**: ✅ Implemented and Ready  
**Optional**: Yes, all other tools work without it  
**Cost**: Free tier available (1,000/month)

