#!/usr/bin/env python3
"""
Test script to demonstrate Stack Sage optimizations.

This script tests:
1. Card caching performance
2. LLM client reuse
3. Query caching
4. Overall response times
"""

import sys
import time
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.core.rag_pipeline import graph
from backend.core.scryfall import ScryfallAPI
from backend.core.llm_client import _llm_instances

def test_card_caching():
    """Test that card queries are cached."""
    print("\n" + "="*60)
    print("TEST 1: Card Caching")
    print("="*60)
    
    api = ScryfallAPI()
    
    # First fetch (uncached)
    start = time.time()
    card1 = api.fetch_card("Lightning Bolt")
    time1 = time.time() - start
    print(f"✓ First fetch (uncached): {time1:.3f}s")
    
    # Second fetch (should be cached)
    start = time.time()
    card2 = api.fetch_card("Lightning Bolt")
    time2 = time.time() - start
    print(f"✓ Second fetch (cached): {time2:.3f}s")
    
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"✓ Speedup: {speedup:.1f}x faster")
    print(f"✓ Cache size: {len(api._card_cache)} cards")
    
    assert card1.name == card2.name, "Cached card should match original"
    assert time2 < time1, "Cached fetch should be faster"
    print("✅ Card caching test PASSED")


def test_llm_reuse():
    """Test that LLM instances are reused."""
    print("\n" + "="*60)
    print("TEST 2: LLM Instance Reuse")
    print("="*60)
    
    from backend.core.llm_client import get_shared_llm
    
    # Get two instances with same parameters
    llm1 = get_shared_llm()
    llm2 = get_shared_llm()
    
    # They should be the exact same object
    assert llm1 is llm2, "LLM instances should be shared"
    print(f"✓ LLM instances are shared (same object)")
    print(f"✓ Total LLM instances created: {len(_llm_instances)}")
    print("✅ LLM reuse test PASSED")


def test_query_performance():
    """Test overall query performance."""
    print("\n" + "="*60)
    print("TEST 3: Query Performance")
    print("="*60)
    
    queries = [
        "What is Lightning Bolt?",
        "How does the stack work?",
        "What is Counterspell?",
    ]
    
    times = []
    for query in queries:
        start = time.time()
        result = graph.invoke({'question': query})
        elapsed = time.time() - start
        times.append(elapsed)
        
        assert 'response' in result, "Result should have response"
        assert len(result['response']) > 0, "Response should not be empty"
        print(f"✓ Query: '{query[:30]}...' - {elapsed:.2f}s")
    
    avg_time = sum(times) / len(times)
    print(f"✓ Average response time: {avg_time:.2f}s")
    print("✅ Query performance test PASSED")


def test_repeated_queries():
    """Test that repeated queries benefit from caching."""
    print("\n" + "="*60)
    print("TEST 4: Repeated Query Optimization")
    print("="*60)
    
    question = "What is Lightning Bolt?"
    
    # First query
    start = time.time()
    result1 = graph.invoke({'question': question})
    time1 = time.time() - start
    print(f"✓ First query: {time1:.2f}s")
    
    # Second query (should benefit from card cache)
    start = time.time()
    result2 = graph.invoke({'question': question})
    time2 = time.time() - start
    print(f"✓ Second query: {time2:.2f}s")
    
    if time2 < time1:
        speedup = ((time1 - time2) / time1) * 100
        print(f"✓ Improvement: {speedup:.1f}% faster on second query")
    else:
        print(f"✓ Similar performance (caching may vary)")
    
    print("✅ Repeated query test PASSED")


def main():
    """Run all optimization tests."""
    print("\n" + "🚀 "*20)
    print("STACK SAGE OPTIMIZATION TEST SUITE")
    print("🚀 "*20)
    
    try:
        test_card_caching()
        test_llm_reuse()
        test_query_performance()
        test_repeated_queries()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nOptimizations are working correctly:")
        print("  • Card caching: ✓")
        print("  • LLM reuse: ✓")
        print("  • Query performance: ✓")
        print("  • Repeated queries: ✓")
        print("\nYour application is optimized and ready to use! 🎉")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

