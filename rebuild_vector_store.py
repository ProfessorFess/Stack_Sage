#!/usr/bin/env python3
"""
Rebuild vector store with improved rule-aware chunking.

This script rebuilds the MTG rules vector database with:
- Rule-number-aware splitting
- Metadata preservation (rule numbers, titles, keywords)
- Better semantic recall for natural language queries
"""

import sys
from backend.core.vector_store import initialize_vector_store

def main():
    print("=" * 70)
    print("🔄 REBUILDING VECTOR STORE WITH IMPROVED RAG")
    print("=" * 70)
    print("\nThis will:")
    print("  1. Delete the old vector store")
    print("  2. Re-chunk the Comprehensive Rules with rule-aware splitting")
    print("  3. Add metadata (rule numbers, titles, keywords)")
    print("  4. Rebuild the vector database for better retrieval")
    print("\n⚠️  This will take 2-3 minutes.\n")
    
    response = input("Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        sys.exit(0)
    
    print("\n" + "=" * 70)
    
    try:
        # Rebuild with improved chunking
        store = initialize_vector_store(force_rebuild=True)
        
        # Verify
        info = store.get_collection_info()
        print("\n" + "=" * 70)
        print("✅ REBUILD COMPLETE!")
        print("=" * 70)
        print(f"\n📊 New Vector Store Stats:")
        print(f"   Collection: {info.get('name')}")
        print(f"   Total chunks: {info.get('points_count', 0)}")
        print(f"   Status: {info.get('status')}")
        
        print("\n🎯 Improvements:")
        print("   ✅ Rule-number aware chunking (e.g., 405. The Stack)")
        print("   ✅ Metadata extraction (rule numbers, titles, keywords)")
        print("   ✅ Query expansion (e.g., 'stack' → includes '405')")
        print("   ✅ Hybrid search (semantic + keyword matching)")
        print("   ✅ Better recall for natural language queries")
        
        print("\n🧪 Test it:")
        print('   Ask: "How does the stack resolve?"')
        print('   Ask: "What are state-based actions?"')
        print('   Ask: "Explain priority"')
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure backend server is stopped")
        print("  2. Check that MagicCompRules.pdf exists in backend/data/")
        print("  3. Ensure you have OpenAI API key in backend/.env")
        sys.exit(1)


if __name__ == "__main__":
    main()

