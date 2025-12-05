"""
Web Browser Tools - Fetch, parse, and interact with web pages.
Includes localhost preview capabilities for testing generated websites.
"""

import os
import re
import json
import time
import socket
import subprocess
import threading
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import http.server
import socketserver

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


@dataclass
class PageContent:
    """Extracted web page content."""
    url: str
    title: str
    text: str
    html: str
    links: list[dict]
    images: list[dict]
    meta: dict
    status_code: int


@dataclass
class LocalServer:
    """Local development server info."""
    port: int
    url: str
    directory: str
    process: Optional[subprocess.Popen]


class WebBrowserTools:
    """
    Web browsing and scraping tools for the AI agent.
    
    Features:
    - Fetch and parse web pages
    - Extract text, links, and structured data
    - Take screenshots (with playwright)
    - Run local development servers
    - Preview generated HTML/CSS
    """

    def __init__(
        self,
        user_agent: str = "CodingAgent/1.0 (AI Assistant)",
        timeout: int = 30,
    ):
        """
        Initialize web browser tools.
        
        Args:
            user_agent: User agent string for requests
            timeout: Request timeout in seconds
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self.session = None
        self._local_servers: dict[int, LocalServer] = {}
        
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({"User-Agent": user_agent})

    def _check_dependencies(self, need_bs4: bool = False):
        """Check required dependencies."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests required. Install with: pip install requests")
        if need_bs4 and not BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 required. Install with: pip install beautifulsoup4")

    # ==================== PAGE FETCHING ====================

    def fetch_page(
        self,
        url: str,
        parse: bool = True,
    ) -> PageContent:
        """
        Fetch and optionally parse a web page.
        
        Args:
            url: URL to fetch
            parse: Whether to parse HTML content
            
        Returns:
            PageContent object
        """
        self._check_dependencies(need_bs4=parse)
        
        response = self.session.get(url, timeout=self.timeout)
        html = response.text
        
        if parse:
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract title
            title = ""
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
            
            # Extract text
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator=" ", strip=True)
            
            # Extract links
            links = []
            for a in soup.find_all("a", href=True):
                links.append({
                    "text": a.get_text(strip=True),
                    "href": urljoin(url, a["href"]),
                })
            
            # Extract images
            images = []
            for img in soup.find_all("img"):
                images.append({
                    "src": urljoin(url, img.get("src", "")),
                    "alt": img.get("alt", ""),
                })
            
            # Extract meta tags
            meta = {}
            for tag in soup.find_all("meta"):
                name = tag.get("name") or tag.get("property", "")
                content = tag.get("content", "")
                if name and content:
                    meta[name] = content
        else:
            title = ""
            text = html
            links = []
            images = []
            meta = {}
        
        return PageContent(
            url=url,
            title=title,
            text=text,
            html=html,
            links=links,
            images=images,
            meta=meta,
            status_code=response.status_code,
        )

    def fetch_text(self, url: str) -> str:
        """
        Fetch just the text content of a page.
        
        Args:
            url: URL to fetch
            
        Returns:
            Extracted text
        """
        page = self.fetch_page(url, parse=True)
        return page.text

    def fetch_json(self, url: str) -> dict:
        """
        Fetch JSON from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Parsed JSON
        """
        self._check_dependencies()
        response = self.session.get(url, timeout=self.timeout)
        return response.json()

    def fetch_raw(self, url: str) -> bytes:
        """
        Fetch raw bytes from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Raw bytes
        """
        self._check_dependencies()
        response = self.session.get(url, timeout=self.timeout)
        return response.content

    # ==================== CONTENT EXTRACTION ====================

    def extract_code_blocks(self, url: str) -> list[dict]:
        """
        Extract code blocks from a web page.
        
        Args:
            url: URL to fetch
            
        Returns:
            List of code blocks with language hints
        """
        self._check_dependencies(need_bs4=True)
        
        page = self.fetch_page(url)
        soup = BeautifulSoup(page.html, "html.parser")
        
        code_blocks = []
        
        # Find <pre><code> blocks
        for pre in soup.find_all("pre"):
            code = pre.find("code")
            if code:
                text = code.get_text()
            else:
                text = pre.get_text()
            
            # Try to detect language from class
            language = "unknown"
            classes = (code or pre).get("class", [])
            for cls in classes:
                if cls.startswith("language-") or cls.startswith("lang-"):
                    language = cls.split("-", 1)[1]
                    break
                if cls in ["python", "javascript", "typescript", "java", "cpp", "go", "rust"]:
                    language = cls
                    break
            
            code_blocks.append({
                "code": text,
                "language": language,
            })
        
        return code_blocks

    def extract_article(self, url: str) -> dict:
        """
        Extract main article content from a page.
        
        Args:
            url: URL to fetch
            
        Returns:
            Article content and metadata
        """
        self._check_dependencies(need_bs4=True)
        
        page = self.fetch_page(url)
        soup = BeautifulSoup(page.html, "html.parser")
        
        # Try to find main content area
        article = (
            soup.find("article") or
            soup.find("main") or
            soup.find("div", class_=re.compile(r"(content|article|post)"))
        )
        
        if article:
            content = article.get_text(separator="\n", strip=True)
        else:
            content = page.text
        
        return {
            "title": page.title,
            "content": content,
            "url": url,
            "meta": page.meta,
        }

    def extract_tables(self, url: str) -> list[list[list[str]]]:
        """
        Extract tables from a web page.
        
        Args:
            url: URL to fetch
            
        Returns:
            List of tables (each table is a list of rows)
        """
        self._check_dependencies(need_bs4=True)
        
        page = self.fetch_page(url)
        soup = BeautifulSoup(page.html, "html.parser")
        
        tables = []
        for table in soup.find_all("table"):
            rows = []
            for tr in table.find_all("tr"):
                cells = []
                for td in tr.find_all(["td", "th"]):
                    cells.append(td.get_text(strip=True))
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        
        return tables

    # ==================== LOCAL SERVER ====================

    def _find_free_port(self) -> int:
        """Find a free port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def start_local_server(
        self,
        directory: str = ".",
        port: Optional[int] = None,
    ) -> LocalServer:
        """
        Start a local HTTP server to preview files.
        
        Args:
            directory: Directory to serve
            port: Port to use (auto-select if not provided)
            
        Returns:
            LocalServer info
        """
        directory = str(Path(directory).resolve())
        port = port or self._find_free_port()
        
        # Check if already running
        if port in self._local_servers:
            return self._local_servers[port]
        
        # Start server in background
        process = subprocess.Popen(
            ["python", "-m", "http.server", str(port)],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # Wait a bit for server to start
        time.sleep(0.5)
        
        server = LocalServer(
            port=port,
            url=f"http://localhost:{port}",
            directory=directory,
            process=process,
        )
        
        self._local_servers[port] = server
        return server

    def stop_local_server(self, port: int) -> bool:
        """
        Stop a local server.
        
        Args:
            port: Port of server to stop
            
        Returns:
            True if stopped
        """
        if port in self._local_servers:
            server = self._local_servers[port]
            if server.process:
                server.process.terminate()
                server.process.wait()
            del self._local_servers[port]
            return True
        return False

    def stop_all_servers(self):
        """Stop all local servers."""
        for port in list(self._local_servers.keys()):
            self.stop_local_server(port)

    def preview_html(
        self,
        html: str,
        filename: str = "preview.html",
        directory: str = "./preview",
    ) -> str:
        """
        Save HTML and start a server to preview it.
        
        Args:
            html: HTML content
            filename: Filename to save as
            directory: Directory to save in
            
        Returns:
            URL to preview
        """
        preview_dir = Path(directory)
        preview_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = preview_dir / filename
        file_path.write_text(html)
        
        server = self.start_local_server(str(preview_dir))
        return f"{server.url}/{filename}"

    # ==================== SITE ANALYSIS ====================

    def analyze_page_structure(self, url: str) -> dict:
        """
        Analyze the structure of a web page.
        
        Args:
            url: URL to analyze
            
        Returns:
            Structure analysis
        """
        self._check_dependencies(need_bs4=True)
        
        page = self.fetch_page(url)
        soup = BeautifulSoup(page.html, "html.parser")
        
        # Count elements
        element_counts = {}
        for tag in soup.find_all():
            name = tag.name
            element_counts[name] = element_counts.get(name, 0) + 1
        
        # Find headings structure
        headings = []
        for i in range(1, 7):
            for h in soup.find_all(f"h{i}"):
                headings.append({
                    "level": i,
                    "text": h.get_text(strip=True)[:100],
                })
        
        # Find forms
        forms = []
        for form in soup.find_all("form"):
            forms.append({
                "action": form.get("action", ""),
                "method": form.get("method", "GET"),
                "inputs": [
                    {"name": inp.get("name"), "type": inp.get("type", "text")}
                    for inp in form.find_all("input")
                ],
            })
        
        # CSS and JS resources
        stylesheets = [link["href"] for link in soup.find_all("link", rel="stylesheet")]
        scripts = [script.get("src") for script in soup.find_all("script") if script.get("src")]
        
        return {
            "url": url,
            "title": page.title,
            "element_counts": element_counts,
            "headings": headings,
            "forms": forms,
            "stylesheets": stylesheets,
            "scripts": scripts,
            "links_count": len(page.links),
            "images_count": len(page.images),
        }

    def check_page_accessibility(self, url: str) -> dict:
        """
        Basic accessibility check for a web page.
        
        Args:
            url: URL to check
            
        Returns:
            Accessibility issues
        """
        self._check_dependencies(need_bs4=True)
        
        page = self.fetch_page(url)
        soup = BeautifulSoup(page.html, "html.parser")
        
        issues = []
        
        # Check images for alt text
        images_without_alt = []
        for img in soup.find_all("img"):
            if not img.get("alt"):
                images_without_alt.append(img.get("src", "unknown"))
        if images_without_alt:
            issues.append({
                "type": "missing_alt",
                "severity": "high",
                "message": f"{len(images_without_alt)} images missing alt text",
                "details": images_without_alt[:5],
            })
        
        # Check for heading hierarchy
        headings = [int(h.name[1]) for h in soup.find_all(re.compile(r"^h[1-6]$"))]
        if headings and headings[0] != 1:
            issues.append({
                "type": "heading_hierarchy",
                "severity": "medium",
                "message": "Page should start with h1",
            })
        
        # Check for form labels
        inputs_without_labels = []
        for inp in soup.find_all("input"):
            if inp.get("type") not in ["hidden", "submit", "button"]:
                input_id = inp.get("id")
                if not input_id or not soup.find("label", {"for": input_id}):
                    inputs_without_labels.append(inp.get("name") or inp.get("id") or "unknown")
        if inputs_without_labels:
            issues.append({
                "type": "missing_labels",
                "severity": "high",
                "message": f"{len(inputs_without_labels)} inputs missing labels",
                "details": inputs_without_labels[:5],
            })
        
        # Check for language attribute
        html_tag = soup.find("html")
        if html_tag and not html_tag.get("lang"):
            issues.append({
                "type": "missing_lang",
                "severity": "medium",
                "message": "HTML element missing lang attribute",
            })
        
        return {
            "url": url,
            "issues": issues,
            "issue_count": len(issues),
            "high_severity": sum(1 for i in issues if i["severity"] == "high"),
        }

    def compare_pages(self, url1: str, url2: str) -> dict:
        """
        Compare two web pages.
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            Comparison results
        """
        page1 = self.analyze_page_structure(url1)
        page2 = self.analyze_page_structure(url2)
        
        return {
            "url1": url1,
            "url2": url2,
            "title_match": page1["title"] == page2["title"],
            "element_diff": {
                k: page1["element_counts"].get(k, 0) - page2["element_counts"].get(k, 0)
                for k in set(page1["element_counts"]) | set(page2["element_counts"])
            },
            "links_diff": page1["links_count"] - page2["links_count"],
            "images_diff": page1["images_count"] - page2["images_count"],
        }
