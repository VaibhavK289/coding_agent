"""
Google Search Tools - Web search capabilities for the AI agent.
Uses multiple search backends (SerpAPI, Google Custom Search, DuckDuckGo).
"""

import os
import json
from typing import Optional, Union
from dataclasses import dataclass
from urllib.parse import quote_plus

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class SearchResult:
    """Search result item."""
    title: str
    url: str
    snippet: str
    source: str


class GoogleSearchTools:
    """
    Web search tools using multiple backends.
    
    Backends:
    - SerpAPI (requires API key)
    - Google Custom Search (requires API key + CX ID)
    - DuckDuckGo (free, no API key)
    """

    def __init__(
        self,
        serpapi_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        google_cx: Optional[str] = None,
    ):
        """
        Initialize search tools.
        
        Args:
            serpapi_key: SerpAPI key (optional)
            google_api_key: Google Custom Search API key (optional)
            google_cx: Google Custom Search CX ID (optional)
        """
        self.serpapi_key = serpapi_key or os.environ.get("SERPAPI_KEY")
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        self.google_cx = google_cx or os.environ.get("GOOGLE_CX")

    def _check_requests(self):
        """Check if requests is available."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required. Install with: pip install requests")

    def search_serpapi(
        self,
        query: str,
        num_results: int = 10,
    ) -> list[SearchResult]:
        """
        Search using SerpAPI (Google results).
        
        Args:
            query: Search query
            num_results: Number of results
            
        Returns:
            List of SearchResult
        """
        self._check_requests()
        
        if not self.serpapi_key:
            raise ValueError("SerpAPI key required. Set SERPAPI_KEY environment variable.")
        
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "api_key": self.serpapi_key,
                "num": num_results,
            },
        )
        
        data = response.json()
        results = []
        
        for item in data.get("organic_results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="serpapi",
            ))
        
        return results

    def search_google_custom(
        self,
        query: str,
        num_results: int = 10,
    ) -> list[SearchResult]:
        """
        Search using Google Custom Search API.
        
        Args:
            query: Search query
            num_results: Number of results
            
        Returns:
            List of SearchResult
        """
        self._check_requests()
        
        if not self.google_api_key or not self.google_cx:
            raise ValueError(
                "Google API key and CX ID required. "
                "Set GOOGLE_API_KEY and GOOGLE_CX environment variables."
            )
        
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": self.google_api_key,
                "cx": self.google_cx,
                "q": query,
                "num": min(num_results, 10),
            },
        )
        
        data = response.json()
        results = []
        
        for item in data.get("items", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="google_custom",
            ))
        
        return results

    def search_duckduckgo(
        self,
        query: str,
        num_results: int = 10,
    ) -> list[SearchResult]:
        """
        Search using DuckDuckGo (no API key required).
        
        Args:
            query: Search query
            num_results: Number of results
            
        Returns:
            List of SearchResult
        """
        self._check_requests()
        
        try:
            # DuckDuckGo Instant Answer API
            response = requests.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
                timeout=10,
            )
            
            if response.status_code != 200:
                return []
            
            # Check if response is JSON
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type and 'text/json' not in content_type:
                # Try to parse anyway, but handle errors
                pass
            
            data = response.json()
            results = []
            
            # Abstract (main result)
            if data.get("Abstract"):
                results.append(SearchResult(
                    title=data.get("Heading", ""),
                    url=data.get("AbstractURL", ""),
                    snippet=data.get("Abstract", ""),
                    source="duckduckgo",
                ))
            
            # Related topics
            for topic in data.get("RelatedTopics", [])[:num_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(SearchResult(
                        title=topic.get("Text", "")[:100],
                        url=topic.get("FirstURL", ""),
                        snippet=topic.get("Text", ""),
                        source="duckduckgo",
                    ))
            
            return results[:num_results]
        except Exception as e:
            # Return empty results on any error
            return []

    def search(
        self,
        query: str,
        num_results: int = 10,
        backend: str = "auto",
    ) -> list[SearchResult]:
        """
        Search using the best available backend.
        
        Args:
            query: Search query
            num_results: Number of results
            backend: Backend to use (auto, serpapi, google, duckduckgo)
            
        Returns:
            List of SearchResult
        """
        if backend == "auto":
            # Try backends in order of quality
            if self.serpapi_key:
                backend = "serpapi"
            elif self.google_api_key and self.google_cx:
                backend = "google"
            else:
                backend = "duckduckgo"
        
        if backend == "serpapi":
            return self.search_serpapi(query, num_results)
        elif backend == "google":
            return self.search_google_custom(query, num_results)
        elif backend == "duckduckgo":
            return self.search_duckduckgo(query, num_results)
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        num_results: int = 10,
    ) -> list[SearchResult]:
        """
        Search for code examples and documentation.
        
        Args:
            query: Search query
            language: Programming language to focus on
            num_results: Number of results
            
        Returns:
            List of SearchResult
        """
        # Add code-focused terms
        enhanced_query = f"{query} code example"
        if language:
            enhanced_query += f" {language}"
        enhanced_query += " site:stackoverflow.com OR site:github.com OR site:dev.to"
        
        return self.search(enhanced_query, num_results)

    def search_documentation(
        self,
        library: str,
        topic: Optional[str] = None,
        num_results: int = 10,
    ) -> list[SearchResult]:
        """
        Search for library/framework documentation.
        
        Args:
            library: Library or framework name
            topic: Specific topic to search
            num_results: Number of results
            
        Returns:
            List of SearchResult
        """
        query = f"{library} documentation"
        if topic:
            query += f" {topic}"
        query += " official"
        
        return self.search(query, num_results)

    def search_tutorials(
        self,
        topic: str,
        level: str = "beginner",
        num_results: int = 10,
    ) -> list[SearchResult]:
        """
        Search for tutorials on a topic.
        
        Args:
            topic: Tutorial topic
            level: Skill level (beginner, intermediate, advanced)
            num_results: Number of results
            
        Returns:
            List of SearchResult
        """
        query = f"{topic} tutorial {level}"
        return self.search(query, num_results)

    def search_error_solution(
        self,
        error_message: str,
        technology: Optional[str] = None,
        num_results: int = 10,
    ) -> list[SearchResult]:
        """
        Search for solutions to an error message.
        
        Args:
            error_message: The error message
            technology: Related technology
            num_results: Number of results
            
        Returns:
            List of SearchResult
        """
        # Clean up error message
        error_clean = error_message.strip()[:200]  # Limit length
        
        query = f'"{error_clean}"'
        if technology:
            query += f" {technology}"
        query += " solution fix"
        
        return self.search(query, num_results)

    def search_best_practices(
        self,
        topic: str,
        technology: Optional[str] = None,
        num_results: int = 10,
    ) -> list[SearchResult]:
        """
        Search for best practices on a topic.
        
        Args:
            topic: Topic (e.g., "API design", "security")
            technology: Specific technology
            num_results: Number of results
            
        Returns:
            List of SearchResult
        """
        query = f"{topic} best practices"
        if technology:
            query += f" {technology}"
        query += " 2024"  # Prefer recent content
        
        return self.search(query, num_results)
