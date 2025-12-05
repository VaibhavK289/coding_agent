"""
Tools package for the Coding Agent.
Provides various capabilities for file system, web, GitHub, and more.
"""

from .file_system import FileSystemTools
from .github_tools import GitHubTools
from .google_search import GoogleSearchTools
from .web_browser import WebBrowserTools
from .image_scanner import ImageScanner, scan_image
from .terminal import TerminalTools

__all__ = [
    "FileSystemTools",
    "GitHubTools", 
    "GoogleSearchTools",
    "WebBrowserTools",
    "ImageScanner",
    "scan_image",
    "TerminalTools",
]
