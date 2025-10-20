"""
Retriever for MTG rules using the vector store with hybrid search.
"""

from typing import List, Dict
from langchain_core.documents import Document
from backend.core.vector_store import initialize_vector_store
import re


class MTGRetriever:
    """Retriever for MTG Comprehensive Rules."""
    
    def __init__(self, k: int = 8):  # Increased from 5 to 8 for better coverage
        """
        Initialize the retriever with hybrid search capabilities.
        
        Args:
            k: Number of results to retrieve (default: 8)
        """
        self.vector_store = initialize_vector_store()
        self._k = k
        # Store the base retriever - we'll update k dynamically
        self._retriever = None
        self._update_retriever()
        
        # Query expansion mappings for common MTG terms
        self.query_expansions = {
            "stack": ["405", "resolve", "resolution", "last in first out", "LIFO"],
            "priority": ["117", "passing priority", "holding priority"],
            "state-based actions": ["704", "SBA", "state based", "check"],
            "combat": ["506", "507", "508", "509", "510", "declare attackers", "declare blockers", "combat damage"],
            "mana": ["106", "mana pool", "mana ability", "mana cost"],
            "tap": ["701.21", "tapping", "untap"],
            "triggered ability": ["603", "trigger", "when", "whenever", "at"],
            "activated ability": ["602", "activation", "colon"],
            "static ability": ["604", "continuous effect"],
            "replacement effect": ["614", "instead", "as", "enters"],
            "phase": ["500", "beginning", "precombat", "combat", "postcombat", "ending"],
            "turn": ["500", "turn structure", "active player"],
            "damage": ["120", "deal damage", "prevent"],
            "counter": ["122", "+1/+1", "-1/-1", "loyalty"],
        }
    
    @property
    def k(self) -> int:
        """Get current k value."""
        return self._k
    
    @k.setter
    def k(self, value: int):
        """Set k value and update retriever if needed."""
        if value != self._k:
            self._k = value
            self._update_retriever()
    
    def _update_retriever(self):
        """Update the retriever with current k value."""
        self._retriever = self.vector_store.vector_store.as_retriever(
            search_kwargs={"k": self._k}
        )
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query by lowercasing and removing punctuation."""
        return re.sub(r'[^\w\s]', ' ', query.lower()).strip()
    
    def _expand_query(self, query: str) -> str:
        """
        Expand query with synonyms and rule numbers.
        
        Args:
            query: Original query
            
        Returns:
            Expanded query with additional terms
        """
        normalized = self._normalize_query(query)
        expanded_terms = [query]  # Keep original
        
        # Check for known concepts and add expansions
        for concept, expansions in self.query_expansions.items():
            if concept in normalized:
                expanded_terms.extend(expansions)
        
        # If query contains rule numbers, prioritize them
        rule_numbers = re.findall(r'\b(\d{3,}\.?\w*)\b', query)
        if rule_numbers:
            expanded_terms.extend([f"rule {num}" for num in rule_numbers])
        
        return " ".join(expanded_terms)
    
    def _detect_rule_number(self, query: str) -> str:
        """
        Detect if query explicitly mentions a rule number.
        
        Returns:
            Rule number if found, None otherwise
        """
        # Match patterns like "405", "405.1", "rule 405"
        match = re.search(r'(?:rule\s+)?(\d{3,}\.\w*|\d{3,})', query, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _hybrid_search(self, query: str, k: int) -> List[Document]:
        """
        Perform hybrid semantic + keyword search.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            List of documents combining semantic and keyword matches
        """
        # Expand query with synonyms
        expanded_query = self._expand_query(query)
        
        # Get semantic search results
        semantic_results = self.vector_store.vector_store.similarity_search(
            expanded_query, 
            k=k
        )
        
        # Check if query mentions specific rule number
        rule_number = self._detect_rule_number(query)
        
        if rule_number:
            # Prioritize chunks that contain this rule number
            rule_specific = self.vector_store.vector_store.similarity_search(
                f"rule {rule_number}",
                k=3
            )
            
            # Merge and deduplicate
            seen = set()
            results = []
            
            # First add rule-specific matches
            for doc in rule_specific:
                doc_id = doc.page_content[:100]
                if doc_id not in seen:
                    results.append(doc)
                    seen.add(doc_id)
            
            # Then add semantic matches
            for doc in semantic_results:
                doc_id = doc.page_content[:100]
                if doc_id not in seen and len(results) < k:
                    results.append(doc)
                    seen.add(doc_id)
            
            return results
        
        return semantic_results
    
    def get_relevant_documents(self, query: str, k: int = None) -> List[Document]:
        """
        Retrieve relevant documents using hybrid search.
        
        Uses semantic search + keyword matching + query expansion.
        
        Args:
            query: The query text
            k: Optional override for number of results (uses self.k if not provided)
            
        Returns:
            List of relevant documents with rule-aware ranking
        """
        k_value = k if k is not None else self._k
        return self._hybrid_search(query, k_value)
    
    def get_relevant_documents_with_scores(self, query: str, k: int = None, min_score: float = 0.0) -> List[tuple]:
        """
        Retrieve relevant documents with similarity scores.
        
        Args:
            query: The query text
            k: Optional override for number of results (uses self.k if not provided)
            min_score: Minimum similarity score threshold (0.0-1.0). Filters out low-relevance results.
            
        Returns:
            List of (Document, score) tuples filtered by min_score
        """
        k_value = k if k is not None else self._k
        results = self.vector_store.vector_store.similarity_search_with_score(query, k=k_value)
        
        # Filter by minimum score if specified
        if min_score > 0.0:
            results = [(doc, score) for doc, score in results if score >= min_score]
        
        return results


def make_retriever(k: int = 8) -> MTGRetriever:
    """
    Create a retriever instance.
    
    Args:
        k: Number of results to retrieve
        
    Returns:
        MTGRetriever instance
    """
    return MTGRetriever(k=k)


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("🔍 MTG Rules Retriever Test")
    print("=" * 60)
    
    # Initialize retriever
    print("\nInitializing retriever...")
    retriever = make_retriever(k=3)
    
    # Test queries
    queries = [
        "What happens when a player loses the game?",
        "How does Rest in Peace work?",
        "What is the stack?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}: '{query}'")
        print(f"{'='*60}")
        
        # Get relevant documents with scores
        results = retriever.get_relevant_documents_with_scores(query)
        
        print(f"\nTop {len(results)} results:\n")
        for j, (doc, score) in enumerate(results, 1):
            print(f"{j}. Score: {score:.4f}")
            print(f"   Text: {doc.page_content[:150]}...")
            print()
