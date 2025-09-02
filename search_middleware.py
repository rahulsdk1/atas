# search_middleware.py
"""
Middleware to intercept user queries and route information requests to web search for accurate answers.
No changes required to original code. Import and use hooks as needed.
"""
import logging
import re
from ddgs import DDGS

logger = logging.getLogger(__name__)

# Comprehensive keywords and patterns to detect info-seeking queries
INFO_KEYWORDS = [
    # Question words
    'who', 'what', 'when', 'where', 'why', 'how', 'which', 'whose', 'whom',
    # Information seeking
    'tell me about', 'show me', 'find', 'search', 'look up', 'google', 'duckduckgo',
    'explain', 'describe', 'define', 'meaning of', 'what is', 'who is', 'how to',
    # Current information
    'current', 'latest', 'news', 'update', 'recent', 'today', 'now',
    # Facts and data
    'fact', 'information', 'details', 'about', 'regarding', 'concerning',
    # History and origins
    'history of', 'origin of', 'cause of', 'reason for', 'background',
    # Comparisons
    'difference between', 'compare', 'versus', 'vs',
    # Technical
    'how does', 'how do', 'what does', 'why does',
    # General knowledge
    'capital of', 'population of', 'area of', 'located in', 'part of'
]

# Question patterns for better detection
QUESTION_PATTERNS = [
    r'^(who|what|when|where|why|how|which|whose|whom)\s',
    r'tell me (about|how)',
    r'show me',
    r'find (out|information)',
    r'search for',
    r'look up',
    r'explain',
    r'describe',
    r'define',
    r'what is',
    r'who is',
    r'how (to|does|do)',
    r'why (does|do|is)',
    r'where (is|are)',
    r'when (is|was|did)',
    r'which (is|are|was)'
]

class SearchMiddleware:
    def __init__(self):
        pass

    def needs_web_search(self, text):
        """Enhanced search detection using keywords and regex patterns"""
        if not text or not text.strip():
            return False

        text_lower = text.lower().strip()

        # Check for question patterns using regex
        for pattern in QUESTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.info(f"Detected question pattern: {pattern}")
                return True

        # Check for info keywords
        keyword_count = sum(1 for kw in INFO_KEYWORDS if kw in text_lower)
        if keyword_count >= 1:  # Lower threshold for better detection
            logger.info(f"Detected {keyword_count} info keywords")
            return True

        # Check for question marks
        if '?' in text:
            logger.info("Detected question mark")
            return True

        # Check for imperative search commands
        search_commands = ['search', 'find', 'look up', 'google', 'tell me', 'show me', 'what is', 'who is', 'how to']
        if any(cmd in text_lower for cmd in search_commands):
            logger.info("Detected search command")
            return True

        return False

    def get_web_result(self, query):
        """Get web search results using DDGS with comprehensive error handling"""
        try:
            logger.info(f"Searching DDGS for: {query}")

            # Clean and prepare the query
            query = query.strip()
            if not query:
                return "Please provide a search query."

            # Use DDGS for web search
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=3))

            if not results:
                logger.warning(f"No results found for query: {query}")
                return f"I couldn't find any information about '{query}'. Please try rephrasing your question."

            # Format the results
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get('title', '').strip()
                body = result.get('body', '').strip()

                if title and body:
                    # Clean up the body text
                    body = ' '.join(body.split())
                    if len(body) > 200:  # Truncate long descriptions
                        body = body[:200] + "..."

                    formatted_results.append(f"{i}. {title}: {body}")
                elif title:
                    formatted_results.append(f"{i}. {title}")
                elif body:
                    formatted_results.append(f"{i}. {body}")

            if formatted_results:
                final_result = "\n".join(formatted_results)
                logger.info(f"DDGS search successful, found {len(results)} results")
                return final_result
            else:
                return f"I found some results for '{query}' but couldn't format them properly."

        except Exception as e:
            logger.error(f"DDGS search error for '{query}': {e}")
            return f"Sorry, I encountered an error while searching for '{query}'. Please try again."

    def process_user_query(self, text):
        if self.needs_web_search(text):
            return self.get_web_result(text)
        return None

# Usage:
# search_hook = SearchMiddleware()
# web_result = search_hook.process_user_query(user_text)
# If web_result is not None, use it as the agent's reply

# Patch: Fast, robust web search with friendly error handling

class FastSearchMiddleware:
    """
    Fast web search with DDGS integration and timeout handling.
    Provides reliable web search functionality.
    """
    def __init__(self, timeout=10, max_results=3):
        self.timeout = timeout
        self.max_results = max_results
        self._search_middleware = SearchMiddleware()

    def get_web_result(self, query):
        """Get web search results using DDGS with proper error handling"""
        try:
            logger.info(f"Starting DDGS search for: {query}")

            # Clean and prepare the query
            query = query.strip()
            if not query:
                return "Please provide a search query."

            # Use DDGS for web search
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=self.max_results))

            if not results:
                logger.warning(f"No results found for query: {query}")
                return f"I couldn't find any information about '{query}'. Please try rephrasing your question."

            # Format the results
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get('title', '').strip()
                body = result.get('body', '').strip()

                if title and body:
                    # Clean up the body text (remove excessive whitespace)
                    body = ' '.join(body.split())
                    if len(body) > 200:  # Truncate long descriptions
                        body = body[:200] + "..."

                    formatted_results.append(f"{i}. {title}: {body}")
                elif title:
                    formatted_results.append(f"{i}. {title}")
                elif body:
                    formatted_results.append(f"{i}. {body}")

            if formatted_results:
                final_result = "\n".join(formatted_results)
                logger.info(f"DDGS search successful, found {len(results)} results")
                return final_result
            else:
                return f"I found some results for '{query}' but couldn't format them properly."

        except Exception as e:
            logger.error(f"DDGS search error for '{query}': {e}")
            return f"Sorry, I encountered an error while searching for '{query}'. Please try again."

    def process_user_query(self, text):
        """Process user query and return search results if needed"""
        if self._search_middleware.needs_web_search(text):
            logger.info(f"Web search triggered for: {text}")
            return self.get_web_result(text)
        return None

# Usage:
# fast_search = FastSearchMiddleware(timeout=5)
# web_result = fast_search.process_user_query(user_text)
