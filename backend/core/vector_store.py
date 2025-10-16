"""
Vector store implementation using Qdrant for MTG rules embeddings.
"""

from pathlib import Path
from typing import List, Optional

from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from backend.core.config import config


class MTGVectorStore:
    """Manages the Qdrant vector store for MTG Comprehensive Rules."""
    
    def __init__(
        self, 
        collection_name: str = "mtg_rules",
        embedding_model: str = "text-embedding-3-small",
        use_local: bool = True
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the Qdrant collection
            embedding_model: OpenAI embedding model to use
            use_local: If True, uses local file-based storage
        """
        self.collection_name = collection_name
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=config.OPENAI_API_KEY
        )
        
        # Initialize Qdrant client
        if use_local:
            storage_path = Path(__file__).parent.parent / "data" / "qdrant_storage"
            storage_path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(storage_path))
            print(f"📂 Using local Qdrant at: {storage_path}")
        else:
            # For remote Qdrant server
            self.client = QdrantClient(url="http://localhost:6333")
            print("🌐 Connected to Qdrant server at http://localhost:6333")
        
        # Create collection if it doesn't exist
        self._ensure_collection_exists()
        
        # Initialize vector store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
                print(f"✨ Created collection: {self.collection_name}")
            else:
                print(f"✓ Collection '{self.collection_name}' already exists")
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[str]:
        """
        Add text chunks to the vector store.
        
        Args:
            texts: List of text chunks
            metadatas: Optional metadata for each chunk
            
        Returns:
            List of IDs for added documents
        """
        print(f"📝 Adding {len(texts)} chunks to vector store...")
        ids = self.vector_store.add_texts(texts=texts, metadatas=metadatas)
        print(f"✅ Successfully added {len(ids)} chunks")
        return ids
    
    def search(self, query: str, k: int = 5) -> List[tuple]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        results = self.vector_store.similarity_search_with_score(query, k=k)
        return results
    
    def get_collection_info(self) -> dict:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            return {"error": str(e)}
    
    def delete_collection(self):
        """Delete the entire collection."""
        self.client.delete_collection(self.collection_name)
        print(f"🗑️  Deleted collection: {self.collection_name}")


def initialize_vector_store() -> MTGVectorStore:
    """
    Initialize and return a vector store instance.
    
    Returns:
        Configured MTGVectorStore instance
    """
    return MTGVectorStore(collection_name="mtg_rules")


# Example usage / testing
if __name__ == "__main__":
    from backend.core.document_loader import load_pdf
    from backend.core.chunker import chunk_text
    
    print("=" * 60)
    print("🚀 Initializing MTG Vector Store")
    print("=" * 60)
    
    # Initialize vector store
    store = initialize_vector_store()
    
    # Check collection status
    info = store.get_collection_info()
    print(f"\n📊 Collection Info:")
    print(f"   Name: {info.get('name')}")
    print(f"   Points: {info.get('points_count', 0)}")
    print(f"   Status: {info.get('status')}")
    
    # If empty, load and add documents
    if info.get('points_count', 0) == 0:
        print("\n📚 Collection is empty. Loading documents...")
        
        # Load PDF
        docs = load_pdf()
        print(f"   Loaded {len(docs)} pages")
        
        # Combine and chunk
        full_text = "\n\n".join([doc.page_content for doc in docs])
        chunks = chunk_text(full_text, chunk_size=700, chunk_overlap=100)
        print(f"   Created {len(chunks)} chunks")
        
        # Add to vector store
        store.add_texts(chunks)
        
        # Show updated info
        info = store.get_collection_info()
        print(f"\n✨ Updated Collection Info:")
        print(f"   Points: {info.get('points_count', 0)}")
    
    # Test search
    print("\n" + "=" * 60)
    print("🔍 Testing Search")
    print("=" * 60)
    
    query = "What happens when a player loses the game?"
    print(f"\nQuery: '{query}'")
    
    results = store.search(query, k=3)
    print(f"\nTop {len(results)} results:\n")
    
    for i, (doc, score) in enumerate(results, 1):
        print(f"{i}. Score: {score:.4f}")
        print(f"   {doc.page_content[:200]}...")
        print()
