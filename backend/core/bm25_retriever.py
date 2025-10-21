"""
BM25 retriever for MTG rules using keyword-based search.

This module provides a BM25 (Best Matching 25) retriever that complements
the existing vector-based retrieval with traditional keyword matching.
"""

import re
import math
from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict
from langchain_core.documents import Document
import pickle
import os
from pathlib import Path


class BM25Retriever:
    """
    BM25 retriever for MTG Comprehensive Rules.
    
    BM25 is a probabilistic ranking function used by search engines to estimate
    the relevance of documents to a given search query. It's particularly good
    at exact keyword matches and handles term frequency and document length well.
    """
    
    def __init__(self, k1: float = 1.2, b: float = 0.75, k: int = 8):
        """
        Initialize BM25 retriever.
        
        Args:
            k1: Controls term frequency saturation (1.2 is standard)
            b: Controls length normalization (0.75 is standard)
            k: Number of results to retrieve
        """
        self.k1 = k1
        self.b = b
        self.k = k
        
        # BM25 components
        self.documents: List[str] = []
        self.doc_metadata: List[Dict] = []
        self.vocabulary: set = set()
        self.doc_freqs: Dict[str, int] = defaultdict(int)  # Document frequency
        self.term_freqs: List[Dict[str, int]] = []  # Term frequency per document
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        
        # Cache for processed documents
        self.cache_file = Path("backend/data/bm25_cache.pkl")
        
    def _preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text for BM25 indexing.
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            List of processed tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep alphanumeric and spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into tokens and remove empty strings
        tokens = [token.strip() for token in text.split() if token.strip()]
        
        # Remove very short tokens (likely noise)
        tokens = [token for token in tokens if len(token) > 1]
        
        return tokens
    
    def _load_documents_from_vector_store(self) -> Tuple[List[str], List[Dict]]:
        """
        Load documents from the existing vector store.
        
        Returns:
            Tuple of (document_texts, metadata_list)
        """
        try:
            from backend.core.vector_store import initialize_vector_store
            
            print("📚 Loading documents from vector store for BM25 indexing...")
            
            # Try to initialize vector store with a new instance
            try:
                vector_store = initialize_vector_store()
            except Exception as e:
                if "already accessed by another instance" in str(e):
                    print("⚠️ Qdrant already in use, trying alternative approach...")
                    # Try to load from existing retriever instead
                    from backend.core.retriever import MTGRetriever
                    retriever = MTGRetriever(k=1000)  # Get many documents
                    all_docs = retriever.get_relevant_documents("magic the gathering rules comprehensive", k=1000)
                else:
                    raise e
            else:
                # Get all documents from the vector store
                # We'll use a broad query to get all documents
                all_docs = vector_store.vector_store.similarity_search(
                    "magic the gathering rules comprehensive", 
                    k=1000  # Get a large number to capture most/all documents
                )
            
            documents = []
            metadata = []
            
            for doc in all_docs:
                documents.append(doc.page_content)
                metadata.append(doc.metadata)
            
            print(f"✅ Loaded {len(documents)} documents for BM25 indexing")
            return documents, metadata
            
        except Exception as e:
            print(f"❌ Error loading documents: {e}")
            return [], []
    
    def _build_index(self, documents: List[str], metadata: List[Dict]):
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of document texts
            metadata: List of document metadata
        """
        print("🔨 Building BM25 index...")
        
        self.documents = documents
        self.doc_metadata = metadata
        self.term_freqs = []
        self.doc_lengths = []
        
        # Process each document
        for doc_text in documents:
            tokens = self._preprocess_text(doc_text)
            
            # Count term frequencies in this document
            term_freq = Counter(tokens)
            self.term_freqs.append(term_freq)
            self.doc_lengths.append(len(tokens))
            
            # Update vocabulary and document frequencies
            for term in term_freq.keys():
                self.vocabulary.add(term)
                self.doc_freqs[term] += 1
        
        # Calculate average document length
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        
        print(f"✅ BM25 index built:")
        print(f"   - Documents: {len(self.documents)}")
        print(f"   - Vocabulary size: {len(self.vocabulary)}")
        print(f"   - Average doc length: {self.avg_doc_length:.1f} tokens")
    
    def _calculate_bm25_score(self, query_terms: List[str], doc_idx: int) -> float:
        """
        Calculate BM25 score for a document given query terms.
        
        Args:
            query_terms: List of query terms
            doc_idx: Document index
            
        Returns:
            BM25 score
        """
        if doc_idx >= len(self.term_freqs):
            return 0.0
        
        score = 0.0
        doc_length = self.doc_lengths[doc_idx]
        term_freq = self.term_freqs[doc_idx]
        
        for term in query_terms:
            if term in term_freq:
                # Term frequency in document
                tf = term_freq[term]
                
                # Document frequency (how many docs contain this term)
                df = self.doc_freqs[term]
                
                # Inverse document frequency
                idf = math.log((len(self.documents) - df + 0.5) / (df + 0.5))
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_length / self.avg_doc_length))
                
                score += idf * (numerator / denominator)
        
        return score
    
    def _load_cache(self) -> bool:
        """
        Load BM25 index from cache if available.
        
        Returns:
            True if cache loaded successfully, False otherwise
        """
        if not self.cache_file.exists():
            return False
        
        try:
            print("📂 Loading BM25 index from cache...")
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.documents = cache_data['documents']
            self.doc_metadata = cache_data['metadata']
            self.vocabulary = cache_data['vocabulary']
            self.doc_freqs = cache_data['doc_freqs']
            self.term_freqs = cache_data['term_freqs']
            self.doc_lengths = cache_data['doc_lengths']
            self.avg_doc_length = cache_data['avg_doc_length']
            
            print(f"✅ BM25 cache loaded: {len(self.documents)} documents")
            return True
            
        except Exception as e:
            print(f"❌ Error loading BM25 cache: {e}")
            return False
    
    def _save_cache(self):
        """Save BM25 index to cache."""
        try:
            # Ensure directory exists
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                'documents': self.documents,
                'metadata': self.doc_metadata,
                'vocabulary': self.vocabulary,
                'doc_freqs': self.doc_freqs,
                'term_freqs': self.term_freqs,
                'doc_lengths': self.doc_lengths,
                'avg_doc_length': self.avg_doc_length
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"💾 BM25 index cached to: {self.cache_file}")
            
        except Exception as e:
            print(f"❌ Error saving BM25 cache: {e}")
    
    def initialize(self, force_rebuild: bool = False):
        """
        Initialize the BM25 retriever.
        
        Args:
            force_rebuild: If True, rebuild index even if cache exists
        """
        # Try to load from cache first
        if not force_rebuild and self._load_cache():
            return
        
        # Load documents and build index
        documents, metadata = self._load_documents_from_vector_store()
        
        if not documents:
            print("❌ No documents found to index")
            return
        
        self._build_index(documents, metadata)
        self._save_cache()
    
    def search(self, query: str, k: Optional[int] = None) -> List[Tuple[Document, float]]:
        """
        Search for relevant documents using BM25.
        
        Args:
            query: Search query
            k: Number of results to return (uses self.k if not provided)
            
        Returns:
            List of (Document, BM25_score) tuples
        """
        if not self.documents:
            print("⚠️ BM25 index not initialized. Call initialize() first.")
            return []
        
        k_value = k if k is not None else self.k
        query_terms = self._preprocess_text(query)
        
        if not query_terms:
            return []
        
        # Calculate BM25 scores for all documents
        scores = []
        for doc_idx in range(len(self.documents)):
            score = self._calculate_bm25_score(query_terms, doc_idx)
            if score > 0:  # Only include documents with positive scores
                scores.append((doc_idx, score))
        
        # Sort by score (descending) and take top k
        scores.sort(key=lambda x: x[1], reverse=True)
        top_scores = scores[:k_value]
        
        # Convert to Document objects
        results = []
        for doc_idx, score in top_scores:
            doc = Document(
                page_content=self.documents[doc_idx],
                metadata=self.doc_metadata[doc_idx] if doc_idx < len(self.doc_metadata) else {}
            )
            results.append((doc, score))
        
        return results
    
    def get_relevant_documents(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Get relevant documents (without scores) for compatibility with existing code.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        results = self.search(query, k)
        return [doc for doc, score in results]
    
    def get_relevant_documents_with_scores(self, query: str, k: Optional[int] = None) -> List[Tuple[Document, float]]:
        """
        Get relevant documents with BM25 scores.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (Document, BM25_score) tuples
        """
        return self.search(query, k)


class HybridRetriever:
    """
    Hybrid retriever that combines vector search and BM25.
    
    This class combines the semantic understanding of vector search
    with the keyword precision of BM25 for better retrieval results.
    """
    
    def __init__(self, vector_weight: float = 0.7, bm25_weight: float = 0.3, k: int = 8):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_weight: Weight for vector search results (0.0-1.0)
            bm25_weight: Weight for BM25 results (0.0-1.0)
            k: Number of results to return
        """
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.k = k
        
        # Initialize retrievers
        from backend.core.retriever import MTGRetriever
        self.vector_retriever = MTGRetriever(k=k)
        self.bm25_retriever = BM25Retriever(k=k)
        
        # Initialize BM25
        self.bm25_retriever.initialize()
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to 0-1 range using min-max normalization.
        
        Args:
            scores: List of raw scores
            
        Returns:
            List of normalized scores
        """
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        return [(score - min_score) / (max_score - min_score) for score in scores]
    
    def search(self, query: str, k: Optional[int] = None) -> List[Tuple[Document, float]]:
        """
        Perform hybrid search combining vector and BM25 results.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (Document, combined_score) tuples
        """
        k_value = k if k is not None else self.k
        
        # Get vector search results
        vector_results = self.vector_retriever.get_relevant_documents_with_scores(query, k=k_value)
        
        # Get BM25 results
        bm25_results = self.bm25_retriever.search(query, k=k_value)
        
        # Combine results
        doc_scores = {}
        
        # Add vector results
        vector_scores = [score for _, score in vector_results]
        normalized_vector_scores = self._normalize_scores(vector_scores)
        
        for i, (doc, _) in enumerate(vector_results):
            doc_key = doc.page_content[:100]  # Use first 100 chars as key
            doc_scores[doc_key] = {
                'doc': doc,
                'vector_score': normalized_vector_scores[i] if i < len(normalized_vector_scores) else 0.0,
                'bm25_score': 0.0
            }
        
        # Add BM25 results
        bm25_scores = [score for _, score in bm25_results]
        normalized_bm25_scores = self._normalize_scores(bm25_scores)
        
        for i, (doc, _) in enumerate(bm25_results):
            doc_key = doc.page_content[:100]
            if doc_key in doc_scores:
                doc_scores[doc_key]['bm25_score'] = normalized_bm25_scores[i] if i < len(normalized_bm25_scores) else 0.0
            else:
                doc_scores[doc_key] = {
                    'doc': doc,
                    'vector_score': 0.0,
                    'bm25_score': normalized_bm25_scores[i] if i < len(normalized_bm25_scores) else 0.0
                }
        
        # Calculate combined scores
        combined_results = []
        for doc_data in doc_scores.values():
            combined_score = (
                self.vector_weight * doc_data['vector_score'] + 
                self.bm25_weight * doc_data['bm25_score']
            )
            combined_results.append((doc_data['doc'], combined_score))
        
        # Sort by combined score and return top k
        combined_results.sort(key=lambda x: x[1], reverse=True)
        return combined_results[:k_value]
    
    def get_relevant_documents(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Get relevant documents using hybrid search.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        results = self.search(query, k)
        return [doc for doc, score in results]
    
    def get_relevant_documents_with_scores(self, query: str, k: Optional[int] = None) -> List[Tuple[Document, float]]:
        """
        Get relevant documents with combined scores.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (Document, combined_score) tuples
        """
        return self.search(query, k)


# Factory functions for easy integration
def make_bm25_retriever(k: int = 8) -> BM25Retriever:
    """
    Create and initialize a BM25 retriever.
    
    Args:
        k: Number of results to retrieve
        
    Returns:
        Initialized BM25Retriever instance
    """
    retriever = BM25Retriever(k=k)
    retriever.initialize()
    return retriever


def make_hybrid_retriever(vector_weight: float = 0.7, bm25_weight: float = 0.3, k: int = 8) -> HybridRetriever:
    """
    Create and initialize a hybrid retriever.
    
    Args:
        vector_weight: Weight for vector search results
        bm25_weight: Weight for BM25 results
        k: Number of results to retrieve
        
    Returns:
        Initialized HybridRetriever instance
    """
    return HybridRetriever(vector_weight=vector_weight, bm25_weight=bm25_weight, k=k)


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("🔍 BM25 Retriever Test")
    print("=" * 60)
    
    # Test BM25 retriever
    print("\n1. Testing BM25 Retriever:")
    print("-" * 40)
    
    bm25_retriever = make_bm25_retriever(k=3)
    
    test_queries = [
        "stack resolution",
        "mana cost",
        "triggered ability"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = bm25_retriever.search(query, k=2)
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"  {i}. Score: {score:.4f}")
            print(f"     Text: {doc.page_content[:100]}...")
    
    # Test hybrid retriever
    print("\n\n2. Testing Hybrid Retriever:")
    print("-" * 40)
    
    hybrid_retriever = make_hybrid_retriever(k=3)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = hybrid_retriever.search(query, k=2)
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"  {i}. Score: {score:.4f}")
            print(f"     Text: {doc.page_content[:100]}...")
