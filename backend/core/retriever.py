"""
Retriever for MTG rules using the vector store.
"""

from typing import List
from langchain_core.documents import Document
from backend.core.vector_store import initialize_vector_store


class MTGRetriever:
    """Retriever for MTG Comprehensive Rules."""
    
    def __init__(self, k: int = 8):  # Increased from 5 to 8 for better coverage
        """
        Initialize the retriever.
        
        Args:
            k: Number of results to retrieve (default: 8)
        """
        self.vector_store = initialize_vector_store()
        self._k = k
        # Store the base retriever - we'll update k dynamically
        self._retriever = None
        self._update_retriever()
    
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
    
    def get_relevant_documents(self, query: str, k: int = None) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The query text
            k: Optional override for number of results (uses self.k if not provided)
            
        Returns:
            List of relevant documents
        """
        if k is not None and k != self._k:
            # Temporarily update k for this query
            old_k = self._k
            self.k = k
            results = self._retriever.invoke(query)
            self.k = old_k  # Restore original k
            return results
        return self._retriever.invoke(query)
    
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
