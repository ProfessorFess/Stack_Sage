"""
Vector store implementation using Qdrant for MTG rules embeddings.
"""

from pathlib import Path
from typing import List, Optional

from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from backend.core.config import config


class MTGVectorStore:
    """Manages the Qdrant vector store for MTG Comprehensive Rules."""
    
    def __init__(
        self, 
        collection_name: str = "mtg_rules",
        embedding_model: str = "text-embedding-3-small",
        use_local: bool = True,
        use_free_embeddings: bool = False  # Using OpenAI embeddings (high quality)
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the Qdrant collection
            embedding_model: Embedding model to use
            use_local: If True, uses local file-based storage
            use_free_embeddings: If True, uses free HuggingFace embeddings instead of OpenAI
        """
        self.collection_name = collection_name
        
        # Initialize embeddings (FREE local model by default)
        if use_free_embeddings:
            print(f"🆓 Using FREE local embeddings: {embedding_model}")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'},  # Use CPU (no GPU needed)
                encode_kwargs={'normalize_embeddings': True}
            )
            self.vector_size = 384  # all-MiniLM-L6-v2 produces 384-dim vectors
        else:
            print(f"💰 Using OpenAI embeddings: {embedding_model}")
            self.embeddings = OpenAIEmbeddings(
                model=embedding_model,
                openai_api_key=config.OPENAI_API_KEY
            )
            self.vector_size = 1536  # OpenAI embeddings are 1536-dim
        
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
        
        # Check if collection exists and has wrong dimensions - delete if so
        self._ensure_correct_dimensions()
        
        # Create collection if it doesn't exist
        self._ensure_collection_exists()
        
        # Initialize vector store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
    
    def _ensure_correct_dimensions(self):
        """Check if existing collection has wrong dimensions and delete if needed."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name in collection_names:
                # Get collection info
                collection_info = self.client.get_collection(self.collection_name)
                
                # Check vector dimensions
                if hasattr(collection_info.config, 'params') and hasattr(collection_info.config.params, 'vectors'):
                    vectors_config = collection_info.config.params.vectors
                    if hasattr(vectors_config, 'size'):
                        existing_size = vectors_config.size
                    elif isinstance(vectors_config, dict) and 'size' in vectors_config:
                        existing_size = vectors_config['size']
                    else:
                        # Can't determine size, skip check
                        return
                    
                    if existing_size != self.vector_size:
                        print(f"⚠️  Collection has {existing_size} dimensions, but embeddings are {self.vector_size}-dimensional")
                        print(f"🗑️  Deleting old collection to recreate with correct dimensions...")
                        self.client.delete_collection(self.collection_name)
                        print(f"✅ Old collection deleted")
        except Exception as e:
            # If there's any error checking, just continue - collection creation will handle it
            print(f"Note: {e}")
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
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


def initialize_vector_store(force_rebuild: bool = False) -> MTGVectorStore:
    """
    Initialize and return a vector store instance.
    
    Args:
        force_rebuild: If True, rebuild index with improved chunking
    
    Returns:
        Configured MTGVectorStore instance with hybrid search support
    """
    store = MTGVectorStore(collection_name="mtg_rules")
    
    # Check if we should rebuild with improved chunking
    if force_rebuild:
        print("🔄 Rebuilding vector store with improved rule-aware chunking...")
        from backend.core.document_loader import load_pdf
        from backend.core.chunker import chunk_mtg_rules
        
        # Load the rules
        docs = load_pdf()
        full_text = "\n\n".join([doc.page_content for doc in docs])
        
        # Chunk with metadata
        chunks = chunk_mtg_rules(full_text, chunk_size=800, chunk_overlap=150)
        
        print(f"✅ Created {len(chunks)} rule-aware chunks with metadata")
        
        # Delete old collection and recreate
        try:
            store.client.delete_collection("mtg_rules")
            print(f"🗑️  Deleted old collection")
        except:
            pass
        
        # Recreate collection
        store._ensure_collection_exists()
        
        # Add documents with metadata
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        store.add_texts(texts, metadatas=metadatas)
        print(f"✅ Added {len(chunks)} chunks with metadata to vector store")
    
    return store


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
