"""
GitHub Integration Tools - Access GitHub repositories, clone, search, and analyze code.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass
from datetime import datetime

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class RepoInfo:
    """GitHub repository information."""
    name: str
    full_name: str
    description: str
    url: str
    clone_url: str
    default_branch: str
    stars: int
    forks: int
    language: str
    topics: list[str]
    updated_at: str


@dataclass
class FileContent:
    """GitHub file content."""
    path: str
    name: str
    content: str
    size: int
    sha: str
    url: str


class GitHubTools:
    """
    GitHub integration tools for accessing repositories and code.
    
    Features:
    - Repository search and discovery
    - Clone repositories
    - Fetch file contents
    - Analyze repository structure
    - Search code across GitHub
    - Get trending repositories
    """

    def __init__(
        self,
        github_token: Optional[str] = None,
        workspace_dir: str = "./repos",
    ):
        """
        Initialize GitHub tools.
        
        Args:
            github_token: GitHub personal access token (optional, for higher rate limits)
            workspace_dir: Directory to clone repositories into
        """
        self.token = github_token or os.environ.get("GITHUB_TOKEN")
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.api_base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def _check_requests(self):
        """Check if requests library is available."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required. Install with: pip install requests")

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict:
        """Make an API request to GitHub."""
        self._check_requests()
        
        url = f"{self.api_base}{endpoint}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            params=params,
            json=data,
        )
        
        if response.status_code == 404:
            raise ValueError(f"Resource not found: {endpoint}")
        elif response.status_code == 403:
            raise PermissionError("Rate limit exceeded or access denied")
        elif response.status_code >= 400:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
        
        return response.json()

    # ==================== REPOSITORY OPERATIONS ====================

    def get_repo(self, owner: str, repo: str) -> RepoInfo:
        """
        Get information about a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            RepoInfo object
        """
        data = self._make_request(f"/repos/{owner}/{repo}")
        
        return RepoInfo(
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description") or "",
            url=data["html_url"],
            clone_url=data["clone_url"],
            default_branch=data["default_branch"],
            stars=data["stargazers_count"],
            forks=data["forks_count"],
            language=data.get("language") or "Unknown",
            topics=data.get("topics") or [],
            updated_at=data["updated_at"],
        )

    def search_repos(
        self,
        query: str,
        language: Optional[str] = None,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 10,
    ) -> list[RepoInfo]:
        """
        Search GitHub repositories.
        
        Args:
            query: Search query
            language: Filter by programming language
            sort: Sort by (stars, forks, updated)
            order: Sort order (asc, desc)
            per_page: Number of results
            
        Returns:
            List of RepoInfo objects
        """
        q = query
        if language:
            q += f" language:{language}"
        
        data = self._make_request(
            "/search/repositories",
            params={
                "q": q,
                "sort": sort,
                "order": order,
                "per_page": per_page,
            },
        )
        
        results = []
        for item in data.get("items", []):
            results.append(RepoInfo(
                name=item["name"],
                full_name=item["full_name"],
                description=item.get("description") or "",
                url=item["html_url"],
                clone_url=item["clone_url"],
                default_branch=item["default_branch"],
                stars=item["stargazers_count"],
                forks=item["forks_count"],
                language=item.get("language") or "Unknown",
                topics=item.get("topics") or [],
                updated_at=item["updated_at"],
            ))
        
        return results

    def get_trending(
        self,
        language: Optional[str] = None,
        since: str = "daily",
    ) -> list[RepoInfo]:
        """
        Get trending repositories.
        
        Args:
            language: Filter by language
            since: Time range (daily, weekly, monthly)
            
        Returns:
            List of trending repos
        """
        # Use search API with date filter as a proxy for trending
        from datetime import datetime, timedelta
        
        days = {"daily": 1, "weekly": 7, "monthly": 30}.get(since, 7)
        date_threshold = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        query = f"created:>{date_threshold}"
        
        return self.search_repos(
            query=query,
            language=language,
            sort="stars",
            per_page=20,
        )

    # ==================== FILE OPERATIONS ====================

    def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> FileContent:
        """
        Get contents of a file from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository
            ref: Branch, tag, or commit SHA
            
        Returns:
            FileContent object
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if ref:
            params["ref"] = ref
        
        data = self._make_request(endpoint, params=params)
        
        if data.get("type") != "file":
            raise ValueError(f"Path is not a file: {path}")
        
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")
        
        return FileContent(
            path=data["path"],
            name=data["name"],
            content=content,
            size=data["size"],
            sha=data["sha"],
            url=data["html_url"],
        )

    def get_directory_contents(
        self,
        owner: str,
        repo: str,
        path: str = "",
        ref: Optional[str] = None,
    ) -> list[dict]:
        """
        List contents of a directory in a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Directory path
            ref: Branch, tag, or commit SHA
            
        Returns:
            List of file/directory info
        """
        endpoint = f"/repos/{owner}/{repo}/contents/{path}"
        params = {}
        if ref:
            params["ref"] = ref
        
        data = self._make_request(endpoint, params=params)
        
        if isinstance(data, dict):
            # Single file
            return [data]
        
        return [
            {
                "path": item["path"],
                "name": item["name"],
                "type": item["type"],
                "size": item.get("size"),
                "sha": item["sha"],
            }
            for item in data
        ]

    def get_repo_tree(
        self,
        owner: str,
        repo: str,
        ref: str = "main",
        recursive: bool = True,
    ) -> list[dict]:
        """
        Get the full file tree of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch or commit
            recursive: Get full tree recursively
            
        Returns:
            List of all files/directories
        """
        endpoint = f"/repos/{owner}/{repo}/git/trees/{ref}"
        params = {"recursive": "1"} if recursive else {}
        
        data = self._make_request(endpoint, params=params)
        
        return [
            {
                "path": item["path"],
                "type": "file" if item["type"] == "blob" else "directory",
                "size": item.get("size"),
                "sha": item["sha"],
            }
            for item in data.get("tree", [])
        ]

    # ==================== CLONE OPERATIONS ====================

    def clone_repo(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        depth: Optional[int] = 1,
    ) -> Path:
        """
        Clone a repository to local workspace.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to clone
            depth: Clone depth (shallow clone)
            
        Returns:
            Path to cloned repository
        """
        clone_url = f"https://github.com/{owner}/{repo}.git"
        target_dir = self.workspace_dir / f"{owner}_{repo}"
        
        if target_dir.exists():
            # Pull latest changes
            subprocess.run(
                ["git", "pull"],
                cwd=target_dir,
                capture_output=True,
            )
            return target_dir
        
        cmd = ["git", "clone"]
        
        if depth:
            cmd.extend(["--depth", str(depth)])
        
        if branch:
            cmd.extend(["--branch", branch])
        
        cmd.extend([clone_url, str(target_dir)])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Clone failed: {result.stderr}")
        
        return target_dir

    def clone_and_index(
        self,
        owner: str,
        repo: str,
        knowledge_base,  # CodeKnowledgeBase instance
        extensions: Optional[list[str]] = None,
    ) -> dict:
        """
        Clone a repository and add it to the knowledge base.
        
        Args:
            owner: Repository owner
            repo: Repository name
            knowledge_base: CodeKnowledgeBase instance
            extensions: File extensions to index
            
        Returns:
            Indexing statistics
        """
        repo_path = self.clone_repo(owner, repo)
        
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c"]
        
        results = knowledge_base.add_directory(str(repo_path), extensions=extensions)
        
        return {
            "repo": f"{owner}/{repo}",
            "path": str(repo_path),
            "files_indexed": len(results),
            "extensions": extensions,
        }

    # ==================== CODE SEARCH ====================

    def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        repo: Optional[str] = None,
        per_page: int = 10,
    ) -> list[dict]:
        """
        Search code across GitHub.
        
        Args:
            query: Search query
            language: Filter by language
            repo: Limit to specific repo (owner/repo)
            per_page: Number of results
            
        Returns:
            List of code matches
        """
        q = query
        if language:
            q += f" language:{language}"
        if repo:
            q += f" repo:{repo}"
        
        data = self._make_request(
            "/search/code",
            params={
                "q": q,
                "per_page": per_page,
            },
        )
        
        results = []
        for item in data.get("items", []):
            results.append({
                "name": item["name"],
                "path": item["path"],
                "repo": item["repository"]["full_name"],
                "url": item["html_url"],
                "sha": item["sha"],
            })
        
        return results

    # ==================== ANALYSIS ====================

    def analyze_repo_structure(
        self,
        owner: str,
        repo: str,
    ) -> dict:
        """
        Analyze repository structure and provide summary.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Analysis results
        """
        info = self.get_repo(owner, repo)
        tree = self.get_repo_tree(owner, repo, info.default_branch)
        
        # Analyze file types
        file_types = {}
        total_files = 0
        directories = set()
        
        for item in tree:
            if item["type"] == "file":
                total_files += 1
                ext = Path(item["path"]).suffix or "no_extension"
                file_types[ext] = file_types.get(ext, 0) + 1
            else:
                directories.add(item["path"])
        
        # Detect project type
        project_indicators = {
            "python": ["setup.py", "pyproject.toml", "requirements.txt"],
            "javascript": ["package.json", "yarn.lock"],
            "typescript": ["tsconfig.json"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod"],
            "java": ["pom.xml", "build.gradle"],
            "docker": ["Dockerfile", "docker-compose.yml"],
        }
        
        detected_types = []
        file_paths = [item["path"] for item in tree]
        
        for project_type, indicators in project_indicators.items():
            if any(ind in file_paths for ind in indicators):
                detected_types.append(project_type)
        
        return {
            "repo": info.full_name,
            "description": info.description,
            "language": info.language,
            "stars": info.stars,
            "total_files": total_files,
            "total_directories": len(directories),
            "file_types": dict(sorted(file_types.items(), key=lambda x: -x[1])),
            "detected_project_types": detected_types,
            "topics": info.topics,
        }

    def get_readme(self, owner: str, repo: str) -> str:
        """
        Get the README content of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            README content
        """
        try:
            content = self.get_file_content(owner, repo, "README.md")
            return content.content
        except ValueError:
            try:
                content = self.get_file_content(owner, repo, "readme.md")
                return content.content
            except ValueError:
                return "No README found"

    def get_repo_languages(self, owner: str, repo: str) -> dict:
        """
        Get language breakdown of a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dict of language -> bytes
        """
        return self._make_request(f"/repos/{owner}/{repo}/languages")
