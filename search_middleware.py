# search_middleware.py
"""
Middleware to intercept user queries and route information requests to the search_web tool for accurate answers.
No changes required to original code. Import and use hooks as needed.
"""
from tools import search_web
import re

# Simple keywords and patterns to detect info-seeking queries
INFO_KEYWORDS = [
    'who', 'what', 'when', 'where', 'why', 'how', 'current', 'latest', 'news', 'update', 'fact', 'information', 'tell me about', 'show me', 'find', 'search', 'google', 'duckduckgo'
]

class SearchMiddleware:
    def __init__(self):
        pass

    def needs_web_search(self, text):
        text_lower = text.lower()
        return any(kw in text_lower for kw in INFO_KEYWORDS)

    def get_web_result(self, query):
        try:
            # Use your existing search_web tool
                result = search_web(query)
                return result if result else "No web results found."
        except Exception as e:
            return f"Web search error: {e}"

    def process_user_query(self, text):
        if self.needs_web_search(text):
            return self.get_web_result(text)
        return None

# Usage:
# search_hook = SearchMiddleware()
# web_result = search_hook.process_user_query(user_text)
# If web_result is not None, use it as the agent's reply

# Patch: Fast, robust web search with friendly error handling
import concurrent.futures

class FastSearchMiddleware:
    """
    Fast web search with timeout and friendly error handling.
    Does not touch original code.
    """
    def __init__(self, timeout=5):
        self.timeout = timeout

    def get_web_result(self, query):
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(search_web, query)
                result = future.result(timeout=self.timeout)
                # If result contains error message, return friendly message
                if not result or 'error' in str(result).lower():
                    return "Sorry, I couldn't find information right now. Please try again."
                return result
        except Exception:
            return "Sorry, I couldn't find information right now. Please try again."

    def process_user_query(self, text):
        if SearchMiddleware().needs_web_search(text):
            return self.get_web_result(text)
        return None

# Usage:
# fast_search = FastSearchMiddleware(timeout=5)
# web_result = fast_search.process_user_query(user_text)
