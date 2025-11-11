"""
Rules Retrieval Agent

This agent handles rules queries by wrapping the existing retrieval
tools and providing structured rules context with coverage scoring.
"""

from typing import Dict, Any, List
from backend.core.agent_state import AgentState, add_rules_context, add_tool_used, add_citation, update_coverage_score
from backend.core.retriever import MTGRetriever
from backend.core.bm25_retriever import make_bm25_retriever, make_hybrid_retriever


# Initialize retrievers (lazy loading)
_vector_retriever = None
_bm25_retriever = None
_hybrid_retriever = None


def _get_vector_retriever():
    """Get or create vector retriever instance."""
    global _vector_retriever
    if _vector_retriever is None:
        _vector_retriever = MTGRetriever(k=6)
    return _vector_retriever


def _get_bm25_retriever():
    """Get or create BM25 retriever instance."""
    global _bm25_retriever
    if _bm25_retriever is None:
        _bm25_retriever = make_bm25_retriever(k=6)
    return _bm25_retriever


def _get_hybrid_retriever():
    """Get or create hybrid retriever instance."""
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = make_hybrid_retriever(k=6)
    return _hybrid_retriever


def rules_agent(state: AgentState) -> AgentState:
    """
    Fetch relevant rules based on the user's question.
    
    Uses hybrid search (vector + BM25) by default for best results.
    Falls back to BM25 for exact keyword matching if needed.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with rules context and coverage score
    """
    question = state.get("user_question", "")
    
    print(f"[RulesAgent] Searching rules for: {question}")
    
    # Use hybrid search by default (best overall performance)
    retriever = _get_hybrid_retriever()
    results = retriever.get_relevant_documents_with_scores(question, k=6)
    
    if not results:
        print("[RulesAgent] No rules found")
        return state
    
    # Convert results to structured format
    rules_data = []
    for i, (doc, score) in enumerate(results):
        rule_dict = {
            "content": doc.page_content,
            "score": float(score),
            "rank": i + 1,
            "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
        }
        rules_data.append(rule_dict)
        
        # Add citation (try to extract rule number from content)
        rule_id = _extract_rule_number(doc.page_content)
        state = add_citation(state, "rule", rule_id or f"rule_{i+1}", "")
    
    # Add to state context
    state = add_rules_context(state, rules_data)
    state = add_tool_used(state, "search_rules_hybrid")
    
    # Calculate coverage score (simple heuristic: avg score)
    avg_score = sum(r["score"] for r in rules_data) / len(rules_data) if rules_data else 0.0
    coverage = min(avg_score / 10.0, 1.0)  # Normalize to 0-1 range
    state = update_coverage_score(state, coverage)
    
    print(f"[RulesAgent] Found {len(rules_data)} rules, coverage: {coverage:.2f}")
    
    return state


def search_rules_vector(state: AgentState, query: str, k: int = 6) -> AgentState:
    """
    Search rules using vector similarity (semantic search).
    
    Good for conceptual questions like "how does the stack work?"
    
    Args:
        state: Current agent state
        query: Search query
        k: Number of results to return
        
    Returns:
        Updated state with rules context
    """
    print(f"[RulesAgent] Vector search: {query}")
    
    retriever = _get_vector_retriever()
    docs = retriever.get_relevant_documents(query, k=k)
    
    rules_data = []
    for i, doc in enumerate(docs):
        rule_dict = {
            "content": doc.page_content,
            "score": 1.0,  # Vector search doesn't return scores in this interface
            "rank": i + 1,
            "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
        }
        rules_data.append(rule_dict)
        
        rule_id = _extract_rule_number(doc.page_content)
        state = add_citation(state, "rule", rule_id or f"rule_{i+1}", "")
    
    state = add_rules_context(state, rules_data)
    state = add_tool_used(state, "search_rules")
    
    print(f"[RulesAgent] Vector search found {len(rules_data)} rules")
    
    return state


def search_rules_bm25(state: AgentState, query: str, k: int = 6) -> AgentState:
    """
    Search rules using BM25 keyword matching.
    
    Excellent for exact keyword matches and specific rule references.
    
    Args:
        state: Current agent state
        query: Search query
        k: Number of results to return
        
    Returns:
        Updated state with rules context
    """
    print(f"[RulesAgent] BM25 search: {query}")
    
    retriever = _get_bm25_retriever()
    results = retriever.get_relevant_documents_with_scores(query, k=k)
    
    rules_data = []
    for i, (doc, score) in enumerate(results):
        rule_dict = {
            "content": doc.page_content,
            "score": float(score),
            "rank": i + 1,
            "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
        }
        rules_data.append(rule_dict)
        
        rule_id = _extract_rule_number(doc.page_content)
        state = add_citation(state, "rule", rule_id or f"rule_{i+1}", "")
    
    state = add_rules_context(state, rules_data)
    state = add_tool_used(state, "search_rules_bm25")
    
    print(f"[RulesAgent] BM25 search found {len(rules_data)} rules")
    
    return state


def _extract_rule_number(content: str) -> str:
    """
    Extract rule number from rule content.
    
    Args:
        content: Rule text
        
    Returns:
        Rule number (e.g., "104.3a") or empty string
    """
    import re
    # Look for patterns like "104.3a" or "702.15"
    match = re.search(r'\b(\d{3}\.\d+[a-z]?)\b', content)
    if match:
        return match.group(1)
    return ""


def format_rules_context_for_llm(rules: List[Dict[str, Any]]) -> str:
    """
    Format rules context for LLM consumption.
    
    Args:
        rules: List of rule dictionaries
        
    Returns:
        Formatted string with rules information
    """
    if not rules:
        return ""
    
    context = "=== COMPREHENSIVE RULES ===\n\n"
    
    for rule in rules:
        context += f"[Rule {rule['rank']}] (Relevance: {rule['score']:.2f})\n"
        context += rule['content']
        context += "\n\n" + "="*60 + "\n\n"
    
    return context

