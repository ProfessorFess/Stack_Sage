#!/usr/bin/env python3
"""
Reset the vector store when switching embedding models.

Run this when changing from OpenAI embeddings to HuggingFace (or vice versa)
since they have different vector dimensions.
"""

import shutil
from pathlib import Path

def reset_vector_store():
    """Delete the existing vector store to allow recreation with new embeddings."""
    
    storage_path = Path(__file__).parent / "backend" / "data" / "qdrant_storage"
    
    print("="*80)
    print("🔄 RESET VECTOR STORE")
    print("="*80)
    print(f"\nThis will delete: {storage_path}")
    print("\nYou'll need to rebuild the vector store after this.")
    print("\nThis is necessary when switching embedding models (OpenAI ↔ HuggingFace)")
    
    confirm = input("\n⚠️  Are you sure? Type 'yes' to continue: ")
    
    if confirm.lower() != 'yes':
        print("\n❌ Cancelled.")
        return
    
    if storage_path.exists():
        print(f"\n🗑️  Deleting {storage_path}...")
        shutil.rmtree(storage_path)
        print("✅ Vector store deleted!")
        print("\n📝 Next steps:")
        print("1. Install sentence-transformers: pip install sentence-transformers")
        print("2. Run the app: python stack_sage.py")
        print("3. The vector store will be recreated with FREE embeddings on first run")
    else:
        print(f"\n✅ No vector store found at {storage_path}")
        print("Nothing to delete.")

if __name__ == "__main__":
    reset_vector_store()

