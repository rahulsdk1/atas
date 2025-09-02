#!/usr/bin/env python3
"""
Test script to verify search middleware functionality
"""
from search_middleware import FastSearchMiddleware

def test_search():
    print("Testing search middleware...")

    # Initialize search middleware
    search_hook = FastSearchMiddleware(timeout=10, max_results=3)

    # Test queries
    test_queries = [
        "Who is the current Prime Minister of India?",
        "What is the weather in Delhi?",
        "What is machine learning?"
    ]

    for query in test_queries:
        print(f"\n--- Testing query: {query} ---")
        try:
            result = search_hook.process_user_query(query)
            if result:
                print(f"✅ Search successful!")
                print(f"Result: {result[:200]}...")
            else:
                print("❌ Search returned None")
        except Exception as e:
            print(f"❌ Search failed with error: {e}")

if __name__ == "__main__":
    test_search()