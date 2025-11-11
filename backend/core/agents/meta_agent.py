"""
Metagame Agent

This agent handles metagame queries by wrapping the search_mtg_meta tool
and providing structured meta context with freshness checking.
"""

from typing import Dict, Any
from datetime import datetime
from backend.core.agent_state import AgentState, add_tool_used
from backend.core.meta_cache import get_cached_meta, cache_meta_data, is_meta_stale
from backend.core.config import config


def meta_agent(state: AgentState) -> AgentState:
    """
    Fetch metagame information based on the user's question.
    
    Checks cache first, then performs web search if needed.
    Adds freshness disclaimers for stale data.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with metagame context
    """
    question = state.get("user_question", "").lower()
    
    # Detect format from question
    format_name = _detect_format(question)
    
    if not format_name:
        format_name = "standard"  # Default to Standard
    
    print(f"[MetaAgent] Fetching meta for format: {format_name}")
    
    # Check cache first
    cached_meta = get_cached_meta(format_name)
    
    if cached_meta:
        # Check if stale (> 7 days old)
        if is_meta_stale(format_name, stale_hours=168):
            print(f"[MetaAgent] Cached data is stale (> 7 days old)")
            cached_meta["freshness_warning"] = "This meta data is more than 7 days old and may be outdated."
        
        # Add to state context
        if "context" not in state:
            state["context"] = {}
        state["context"]["metagame"] = cached_meta
        state = add_tool_used(state, "meta_cache")
        
        # Generate answer from cached meta data
        state["draft_answer"] = _generate_meta_answer(state)
        
        return state
    
    # No cache hit - perform web search
    meta_data = _fetch_meta_from_web(format_name, question)
    
    if meta_data:
        # Cache the result
        cache_meta_data(format_name, meta_data, ttl=86400)  # 24 hour TTL
        
        # Add to state context
        if "context" not in state:
            state["context"] = {}
        state["context"]["metagame"] = meta_data
        state = add_tool_used(state, "search_mtg_meta")
    else:
        print(f"[MetaAgent] No meta data found for {format_name}")
        # Set empty meta data
        if "context" not in state:
            state["context"] = {}
        state["context"]["metagame"] = {
            "format": format_name,
            "summary": "No meta data available",
            "sources": []
        }
    
    # Generate answer from meta data
    state["draft_answer"] = _generate_meta_answer(state)
    
    return state


def _detect_format(question: str) -> str:
    """
    Detect the format from the question.
    
    Args:
        question: User's question (lowercase)
        
    Returns:
        Format name or empty string
    """
    formats = {
        "standard": ["standard"],
        "modern": ["modern"],
        "pioneer": ["pioneer"],
        "legacy": ["legacy"],
        "vintage": ["vintage"],
        "commander": ["commander", "edh", "cedh"],
        "pauper": ["pauper"],
        "brawl": ["brawl"]
    }
    
    for format_name, keywords in formats.items():
        if any(keyword in question for keyword in keywords):
            return format_name
    
    return ""


def _fetch_meta_from_web(format_name: str, question: str) -> Dict[str, Any]:
    """
    Fetch metagame data from web search.
    
    Args:
        format_name: Format to search for
        question: Original question
        
    Returns:
        Meta data dictionary
    """
    # Check if Tavily API is configured
    if not config.TAVILY_API_KEY:
        print("[MetaAgent] Tavily API key not configured")
        return {
            "format": format_name,
            "snapshot_date": datetime.now().isoformat(),
            "summary": "Web search not available (Tavily API key not configured)",
            "sources": [],
            "freshness_warning": "Unable to fetch current meta data"
        }
    
    try:
        from tavily import TavilyClient
        
        # Initialize Tavily client
        tavily = TavilyClient(api_key=config.TAVILY_API_KEY)
        
        # Build search query
        search_query = f"Magic the Gathering {format_name} metagame decks tier list"
        
        # Perform search
        response = tavily.search(
            query=search_query,
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False
        )
        
        # Extract results
        meta_data = {
            "format": format_name,
            "snapshot_date": datetime.now().isoformat(),
            "summary": response.get("answer", "No summary available"),
            "sources": []
        }
        
        # Add sources
        for result in response.get("results", []):
            meta_data["sources"].append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content", "")[:200]
            })
        
        print(f"[MetaAgent] Fetched meta data with {len(meta_data['sources'])} sources")
        
        return meta_data
        
    except ImportError:
        print("[MetaAgent] Tavily package not installed")
        return {
            "format": format_name,
            "snapshot_date": datetime.now().isoformat(),
            "summary": "Web search not available (tavily-python not installed)",
            "sources": [],
            "freshness_warning": "Install tavily-python to enable meta search"
        }
    except Exception as e:
        print(f"[MetaAgent] Error fetching meta data: {e}")
        return {
            "format": format_name,
            "snapshot_date": datetime.now().isoformat(),
            "summary": f"Error fetching meta data: {str(e)}",
            "sources": [],
            "freshness_warning": "Unable to fetch current meta data"
        }


def format_meta_context_for_llm(meta_data: Dict[str, Any]) -> str:
    """
    Format metagame context for LLM consumption.
    
    Args:
        meta_data: Meta data dictionary
        
    Returns:
        Formatted string
    """
    if not meta_data:
        return ""
    
    context = "=== METAGAME INFORMATION ===\n\n"
    context += f"Format: {meta_data.get('format', 'Unknown').upper()}\n"
    context += f"Data Date: {meta_data.get('snapshot_date', 'Unknown')}\n\n"
    
    if meta_data.get("freshness_warning"):
        context += f"⚠️ {meta_data['freshness_warning']}\n\n"
    
    context += f"Summary:\n{meta_data.get('summary', 'No summary available')}\n\n"
    
    sources = meta_data.get("sources", [])
    if sources:
        context += "Sources:\n"
        for i, source in enumerate(sources[:3], 1):  # Limit to 3 sources
            context += f"{i}. {source.get('title', 'Unknown')}\n"
            context += f"   {source.get('snippet', '')}\n"
            context += f"   URL: {source.get('url', '')}\n\n"
    
    return context


def _generate_meta_answer(state: AgentState) -> str:
    """
    Generate a natural language answer from metagame data.
    
    Args:
        state: Current agent state with metagame context
        
    Returns:
        Formatted answer string
    """
    meta_data = state.get("context", {}).get("metagame", {})
    question = state.get("user_question", "").lower()
    
    if not meta_data:
        return "I couldn't find any metagame information for your query."
    
    format_name = meta_data.get("format", "").title()
    summary = meta_data.get("summary", "")
    sources = meta_data.get("sources", [])
    freshness_warning = meta_data.get("freshness_warning", "")
    
    # Check if user is asking for a specific decklist
    is_decklist_request = any(phrase in question for phrase in [
        'decklist', 'deck list', 'give me', 'show me', 'what does', 'example'
    ])
    
    # Build answer
    answer_parts = []
    
    if is_decklist_request:
        # User wants a specific decklist
        answer_parts.append(f"**{format_name} Deck Information:**\n")
        
        if summary:
            answer_parts.append(f"{summary}\n")
        
        answer_parts.append("\n**To get a complete decklist, check these resources:**")
        
        if sources:
            for i, source in enumerate(sources[:3], 1):
                if isinstance(source, dict):
                    title = source.get('title', 'Unknown')
                    url = source.get('url', '')
                    snippet = source.get('snippet', '')
                    
                    answer_parts.append(f"\n{i}. **{title}**")
                    if url:
                        answer_parts.append(f"   🔗 {url}")
                    if snippet and 'decklist' in snippet.lower() or 'mainboard' in snippet.lower():
                        # Show snippet if it looks like it contains decklist info
                        answer_parts.append(f"   📝 {snippet[:200]}...")
                else:
                    answer_parts.append(f"\n{i}. {source}")
        
        answer_parts.append("\n\n💡 **Tip:** Visit MTGGoldfish, MTG Arena Zone, or Moxfield for complete, up-to-date decklists with card quantities and sideboards.")
        
    else:
        # General meta query
        if summary:
            answer_parts.append(f"**{format_name} Metagame:**\n\n{summary}")
        else:
            answer_parts.append(f"I couldn't find specific metagame information for {format_name}.")
        
        # Add sources
        if sources:
            answer_parts.append(f"\n\n**Sources:**")
            for i, source in enumerate(sources[:3], 1):
                if isinstance(source, dict):
                    title = source.get('title', 'Unknown')
                    url = source.get('url', '')
                    answer_parts.append(f"{i}. {title}")
                    if url:
                        answer_parts.append(f"   {url}")
                else:
                    answer_parts.append(f"{i}. {source}")
    
    # Add freshness warning if present
    if freshness_warning:
        answer_parts.append(f"\n\n⚠️ *{freshness_warning}*")
    
    return "\n".join(answer_parts)

