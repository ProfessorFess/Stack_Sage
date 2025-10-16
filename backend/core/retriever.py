"""
Retriever for MTG rules using the vector store.
"""

from typing import List
from langchain_core.documents import Document
from backend.core.vector_store import initialize_vector_store


class MTGRetriever:
    """Retriever for MTG Comprehensive Rules."""
    
    def __init__(self, k: int = 5):
        """
        Initialize the retriever.
        
        Args:
            k: Number of results to retrieve
        """
        self.vector_store = initialize_vector_store()
        self.k = k
        # Get the retriever from the vector store
        self.retriever = self.vector_store.vector_store.as_retriever(
            search_kwargs={"k": k}
        )
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The query text
            
        Returns:
            List of relevant documents
        """
        return self.retriever.invoke(query)
    
    def get_relevant_documents_with_scores(self, query: str) -> List[tuple]:
        """
        Retrieve relevant documents with similarity scores.
        
        Args:
            query: The query text
            
        Returns:
            List of (Document, score) tuples
        """
        return self.vector_store.search(query, k=self.k)


def make_retriever(k: int = 5) -> MTGRetriever:
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
