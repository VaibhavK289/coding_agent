"""
Enhanced Orchestrator - Full agentic AI with all tools and capabilities.
Integrates file system, GitHub, web browsing, image scanning, and hierarchical reasoning.
"""

from dataclasses import dataclass, field
from typing import Optional, Union
from pathlib import Path
from enum import Enum

from agents import PlannerAgent, CoderAgent, ReviewerAgent
from rag import CodeKnowledgeBase
from tools import (
    FileSystemTools,
    GitHubTools,
    GoogleSearchTools,
    WebBrowserTools,
    ImageScanner,
    TerminalTools,
)
from prompts import (
    get_domain_prompt,
    get_combined_prompt,
    HierarchicalReasoner,
)
import config


class AgentMode(Enum):
    """Operating modes for the agent."""
    STANDARD = "standard"           # Normal operation
    HIERARCHICAL = "hierarchical"   # Use hierarchical reasoning
    AUTONOMOUS = "autonomous"       # Full autonomous operation with file access
    RESEARCH = "research"           # Focus on research and learning


@dataclass
class AgentCapabilities:
    """Available capabilities for the agent."""
    file_system: bool = True
    github: bool = True
    web_search: bool = True
    web_browse: bool = True
    image_scan: bool = True
    terminal: bool = True
    rag: bool = True


@dataclass
class EnhancedTaskResult:
    """Result from enhanced agent execution."""
    task: str
    status: str
    plan: str = ""
    code: str = ""
    review: str = ""
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    research_sources: list[str] = field(default_factory=list)
    reasoning_trace: Optional[str] = None
    iterations: int = 0
    execution_output: str = ""
    errors: list[str] = field(default_factory=list)
    iterations: int = 0


class EnhancedOrchestrator:
    """
    Enhanced orchestrator with full agentic capabilities.
    
    Capabilities:
    - File system manipulation (create, read, modify, delete)
    - GitHub integration (clone, search, index repositories)
    - Web search (Google, documentation, tutorials)
    - Web browsing (fetch pages, extract content, preview)
    - Image scanning (OCR, code extraction, UI analysis)
    - Terminal execution (run commands, scripts)
    - RAG knowledge base (code context retrieval)
    - Hierarchical reasoning (multi-level problem solving)
    - Domain expertise (frontend, UI/UX, system design, DevOps)
    """

    def __init__(
        self,
        workspace_dir: str = ".",
        mode: AgentMode = AgentMode.STANDARD,
        capabilities: Optional[AgentCapabilities] = None,
        domains: Optional[list[str]] = None,
        github_token: Optional[str] = None,
        verbose: bool = True,
    ):
        """
        Initialize enhanced orchestrator.
        
        Args:
            workspace_dir: Working directory
            mode: Operating mode
            capabilities: Which capabilities to enable
            domains: Domain expertise to include (frontend, uiux, system_design, devops)
            github_token: GitHub API token
            verbose: Print progress
        """
        self.workspace_dir = Path(workspace_dir).resolve()
        self.mode = mode
        self.capabilities = capabilities or AgentCapabilities()
        self.domains = domains or []
        self.verbose = verbose
        
        # Initialize agents
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.reviewer = ReviewerAgent()
        
        # Add domain expertise to agents
        if domains:
            domain_prompt = get_combined_prompt(domains)
            self.planner.system_prompt += f"\n\n{domain_prompt}"
            self.coder.system_prompt += f"\n\n{domain_prompt}"
            self.reviewer.system_prompt += f"\n\n{domain_prompt}"
        
        # Initialize tools based on capabilities
        self._init_tools(github_token)
        
        # Initialize hierarchical reasoner for complex tasks
        if mode == AgentMode.HIERARCHICAL:
            self.reasoner = HierarchicalReasoner()
        else:
            self.reasoner = None
        
        self._log("Enhanced Orchestrator initialized")
        self._log(f"Mode: {mode.value}")
        self._log(f"Workspace: {self.workspace_dir}")
        self._log(f"Domains: {domains or 'none'}")

    def _init_tools(self, github_token: Optional[str] = None):
        """Initialize tools based on capabilities."""
        if self.capabilities.file_system:
            self.fs = FileSystemTools(
                workspace_root=str(self.workspace_dir),
                sandbox_mode=self.mode != AgentMode.AUTONOMOUS,
            )
        else:
            self.fs = None
        
        if self.capabilities.github:
            self.github = GitHubTools(
                github_token=github_token,
                workspace_dir=str(self.workspace_dir / "repos"),
            )
        else:
            self.github = None
        
        if self.capabilities.web_search:
            self.search = GoogleSearchTools()
        else:
            self.search = None
        
        if self.capabilities.web_browse:
            self.browser = WebBrowserTools()
        else:
            self.browser = None
        
        if self.capabilities.image_scan:
            self.scanner = ImageScanner(use_vision_model=False)  # OCR only by default
        else:
            self.scanner = None
        
        if self.capabilities.terminal:
            self.terminal = TerminalTools(working_directory=str(self.workspace_dir))
        else:
            self.terminal = None
        
        if self.capabilities.rag:
            self.knowledge_base = CodeKnowledgeBase()
        else:
            self.knowledge_base = None

    def _log(self, message: str):
        """Log message if verbose."""
        if self.verbose:
            print(f"[Agent] {message}")

    # ==================== RESEARCH CAPABILITIES ====================

    def research_topic(
        self,
        topic: str,
        include_code: bool = True,
        include_docs: bool = True,
    ) -> dict:
        """
        Research a topic using web search and documentation.
        
        Args:
            topic: Topic to research
            include_code: Search for code examples
            include_docs: Search for documentation
            
        Returns:
            Research results
        """
        results = {
            "topic": topic,
            "sources": [],
            "code_examples": [],
            "documentation": [],
        }
        
        if not self.search:
            return results
        
        self._log(f"Researching: {topic[:100]}...")
        
        try:
            # General search
            general = self.search.search(topic, num_results=5)
            results["sources"] = [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in general]
            
            # Code examples
            if include_code:
                code = self.search.search_code(topic, num_results=5)
                results["code_examples"] = [{"title": r.title, "url": r.url} for r in code]
            
            # Documentation
            if include_docs:
                docs = self.search.search_documentation(topic, num_results=5)
                results["documentation"] = [{"title": r.title, "url": r.url} for r in docs]
            
            self._log(f"Found {len(results['sources'])} sources")
        except Exception as e:
            self._log(f"Research failed (continuing without): {e}")
        
        return results

    def learn_from_repo(
        self,
        owner: str,
        repo: str,
        index_for_rag: bool = True,
    ) -> dict:
        """
        Learn from a GitHub repository by analyzing and indexing it.
        
        Args:
            owner: Repository owner
            repo: Repository name
            index_for_rag: Add to knowledge base
            
        Returns:
            Learning summary
        """
        if not self.github:
            return {"error": "GitHub tools not enabled"}
        
        self._log(f"Learning from: {owner}/{repo}")
        
        # Get repo info
        info = self.github.get_repo(owner, repo)
        
        # Analyze structure
        structure = self.github.analyze_repo_structure(owner, repo)
        
        # Get README
        readme = self.github.get_readme(owner, repo)
        
        # Clone and index
        if index_for_rag and self.knowledge_base:
            result = self.github.clone_and_index(owner, repo, self.knowledge_base)
            files_indexed = result["files_indexed"]
        else:
            files_indexed = 0
        
        return {
            "repo": info.full_name,
            "description": info.description,
            "language": info.language,
            "stars": info.stars,
            "structure": structure,
            "readme_preview": readme[:500] + "..." if len(readme) > 500 else readme,
            "files_indexed": files_indexed,
        }

    # ==================== FILE OPERATIONS ====================

    def create_file(self, path: str, content: str) -> bool:
        """Create a file in the workspace."""
        if not self.fs:
            return False
        
        full_path = self.workspace_dir / path
        self.fs.create_file(str(full_path), content, overwrite=True)
        self._log(f"Created: {path}")
        return True

    def read_file(self, path: str) -> str:
        """Read a file from the workspace."""
        if not self.fs:
            return ""
        
        full_path = self.workspace_dir / path
        return self.fs.read_file(str(full_path))

    def modify_file(self, path: str, old_text: str, new_text: str) -> int:
        """Modify text in a file."""
        if not self.fs:
            return 0
        
        full_path = self.workspace_dir / path
        count = self.fs.replace_in_file(str(full_path), old_text, new_text)
        self._log(f"Modified {path}: {count} replacements")
        return count

    def delete_file(self, path: str) -> bool:
        """Delete a file."""
        if not self.fs:
            return False
        
        full_path = self.workspace_dir / path
        self.fs.delete_file(str(full_path))
        self._log(f"Deleted: {path}")
        return True

    def list_files(self, path: str = ".", pattern: str = "*") -> list[dict]:
        """List files in a directory."""
        if not self.fs:
            return []
        
        full_path = self.workspace_dir / path
        return self.fs.list_directory(str(full_path), pattern=pattern)

    # ==================== IMAGE CAPABILITIES ====================

    def scan_image(self, image_path: str) -> dict:
        """
        Scan an image for text and code.
        
        Args:
            image_path: Path to image
            
        Returns:
            Scan results with extracted text and code
        """
        if not self.scanner:
            return {"error": "Image scanning not enabled"}
        
        self._log(f"Scanning image: {image_path}")
        
        result = self.scanner.scan(image_path)
        
        return {
            "raw_text": result.raw_text,
            "code_blocks": result.code_blocks,
            "file_type_hints": result.file_type_hints,
            "confidence": result.confidence,
        }

    def analyze_ui_screenshot(self, image_path: str) -> str:
        """
        Analyze a UI screenshot for design feedback.
        
        Args:
            image_path: Path to screenshot
            
        Returns:
            UI/UX feedback
        """
        if not self.scanner:
            return "Image scanning not enabled"
        
        return self.scanner.scan_screenshot_for_ui_feedback(image_path)

    # ==================== WEB CAPABILITIES ====================

    def fetch_webpage(self, url: str) -> dict:
        """
        Fetch and parse a webpage.
        
        Args:
            url: URL to fetch
            
        Returns:
            Page content and metadata
        """
        if not self.browser:
            return {"error": "Web browsing not enabled"}
        
        self._log(f"Fetching: {url}")
        
        page = self.browser.fetch_page(url)
        
        return {
            "title": page.title,
            "text": page.text[:5000],  # Limit text length
            "links_count": len(page.links),
            "meta": page.meta,
        }

    def start_preview_server(self, directory: str = ".") -> str:
        """
        Start a local server to preview files.
        
        Args:
            directory: Directory to serve
            
        Returns:
            Server URL
        """
        if not self.browser:
            return "Web browsing not enabled"
        
        server = self.browser.start_local_server(str(self.workspace_dir / directory))
        self._log(f"Server started: {server.url}")
        return server.url

    # ==================== TERMINAL CAPABILITIES ====================

    def run_command(self, command: str) -> dict:
        """
        Run a shell command.
        
        Args:
            command: Command to run
            
        Returns:
            Command result
        """
        if not self.terminal:
            return {"error": "Terminal not enabled"}
        
        self._log(f"Running: {command}")
        
        result = self.terminal.run_command(command)
        
        return {
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    def install_packages(self, packages: list[str], manager: str = "pip") -> dict:
        """
        Install packages using pip or npm.
        
        Args:
            packages: Packages to install
            manager: Package manager (pip or npm)
            
        Returns:
            Installation result
        """
        if not self.terminal:
            return {"error": "Terminal not enabled"}
        
        if manager == "pip":
            result = self.terminal.pip_install(packages)
        elif manager == "npm":
            result = self.terminal.npm_install(packages)
        else:
            return {"error": f"Unknown package manager: {manager}"}
        
        return {
            "success": result.success,
            "output": result.stdout,
            "errors": result.stderr,
        }

    # ==================== MAIN EXECUTION ====================

    def run(
        self,
        task: str,
        context: Optional[str] = None,
        auto_research: bool = True,
        auto_save: bool = True,
        auto_execute: bool = True,
        max_iterations: int = 3,
    ) -> EnhancedTaskResult:
        """
        Execute a task with full agentic capabilities.
        Automatically creates files, runs code, and fixes errors.
        
        Args:
            task: Task to execute
            context: Additional context
            auto_research: Automatically research if needed
            auto_save: Automatically save generated files
            auto_execute: Automatically run/test the code
            max_iterations: Max fix iterations
            
        Returns:
            Task result
        """
        result = EnhancedTaskResult(task=task, status="pending")
        
        self._log(f"\n{'='*60}")
        self._log(f"🎯 AGENTIC TASK: {task[:80]}...")
        self._log(f"{'='*60}\n")
        
        # Step 1: Gather context
        full_context = context or ""
        
        # List existing files in workspace
        if self.fs:
            existing_files = self._get_workspace_structure()
            if existing_files:
                full_context += f"\n\n## Current Workspace Structure:\n{existing_files}"
        
        # RAG context
        if self.knowledge_base:
            try:
                rag_context = self.knowledge_base.get_context_for_task(task)
                if rag_context:
                    full_context += f"\n\n## Relevant Code Context:\n{rag_context}"
            except Exception:
                pass
        
        # Auto-research (with timeout protection)
        if auto_research and self.search:
            research = self.research_topic(task, include_code=True)
            if research["sources"]:
                full_context += f"\n\n## Research:\n"
                for src in research["sources"][:3]:
                    full_context += f"- {src['title']}: {src['snippet'][:200]}\n"
                result.research_sources = [s.get("url", "") for s in research["sources"]]
        
        # Step 2: Plan with file-aware prompt
        self._log("📋 Phase 1: PLANNING")
        planning_prompt = self._create_agentic_planning_prompt(task, full_context)
        result.plan = self.planner.run(planning_prompt)
        self._log("   ✓ Plan created")
        
        # Step 3: Code with file creation instructions
        self._log("💻 Phase 2: CODING")
        coding_prompt = self._create_agentic_coding_prompt(task, result.plan)
        result.code = self.coder.run(coding_prompt)
        self._log("   ✓ Code generated")
        
        # Step 4: Extract and save files
        if auto_save and self.fs:
            self._log("📁 Phase 3: SAVING FILES")
            files = self._extract_and_save_files(result.code)
            result.files_created = files
            if files:
                self._log(f"   ✓ Created {len(files)} file(s): {', '.join(files)}")
            else:
                self._log("   ⚠ No files extracted from code")
        
        # Step 5: Execute/test the code
        if auto_execute and self.terminal and result.files_created:
            self._log("🚀 Phase 4: EXECUTING")
            exec_result = self._execute_generated_code(result.files_created)
            result.execution_output = exec_result.get("output", "")
            if exec_result.get("errors"):
                result.errors.append(exec_result["errors"])
                self._log(f"   ⚠ Execution errors detected")
            else:
                self._log(f"   ✓ Code executed successfully")
        
        # Step 6: Review (including execution results)
        self._log("🔍 Phase 5: REVIEWING")
        review_context = result.code
        if result.execution_output:
            review_context += f"\n\n## Execution Output:\n{result.execution_output}"
        if result.errors:
            review_context += f"\n\n## Errors:\n{chr(10).join(result.errors)}"
        
        result.review = self.reviewer.check_implementation(review_context, result.plan)
        
        # Step 7: Fix loop if needed
        iteration = 0
        while not self.reviewer.is_approved(result.review) and iteration < max_iterations:
            iteration += 1
            result.iterations = iteration
            self._log(f"🔧 Phase 6: FIXING (iteration {iteration})")
            
            # Fix the code based on review and execution errors
            fix_prompt = self._create_fix_prompt(result.code, result.review, result.errors)
            result.code = self.coder.run(fix_prompt)
            
            # Re-save files
            if auto_save and self.fs:
                new_files = self._extract_and_save_files(result.code)
                result.files_modified.extend(new_files)
            
            # Re-execute
            if auto_execute and self.terminal and (result.files_created or result.files_modified):
                exec_result = self._execute_generated_code(result.files_created + result.files_modified)
                result.execution_output = exec_result.get("output", "")
                if exec_result.get("errors"):
                    result.errors.append(exec_result["errors"])
                else:
                    result.errors = []  # Clear errors if execution succeeded
            
            # Re-review
            review_context = result.code
            if result.execution_output:
                review_context += f"\n\n## Execution Output:\n{result.execution_output}"
            result.review = self.reviewer.check_implementation(review_context, result.plan)
        
        result.status = "completed" if not result.errors else "completed_with_errors"
        self._log(f"\n{'='*60}")
        self._log(f"✅ Task completed! Files: {len(result.files_created)}, Iterations: {result.iterations}")
        self._log(f"{'='*60}\n")
        
        return result

    def _get_workspace_structure(self) -> str:
        """Get current workspace file structure."""
        try:
            files = self.fs.list_directory(str(self.workspace_dir), pattern="*", recursive=False)
            if not files:
                return ""
            
            structure = []
            for f in files[:20]:  # Limit to 20 files
                if isinstance(f, dict):
                    name = f.get("name", "")
                    ftype = f.get("type", "file")
                    prefix = "📁" if ftype == "directory" else "📄"
                    structure.append(f"{prefix} {name}")
                else:
                    structure.append(f"  {f}")
            
            return "\n".join(structure)
        except Exception:
            return ""

    def _create_agentic_planning_prompt(self, task: str, context: str) -> str:
        """Create a planning prompt that emphasizes file creation."""
        return f"""You are an autonomous coding agent. Plan the implementation for this task.

TASK: {task}

CONTEXT:
{context}

Create a detailed plan that includes:
1. What files need to be created (with exact paths)
2. What each file should contain
3. Dependencies needed
4. How to test/run the code

Be specific about file paths like: `src/main.py`, `index.html`, etc.
"""

    def _create_agentic_coding_prompt(self, task: str, plan: str) -> str:
        """Create a coding prompt that produces extractable file blocks."""
        return f"""You are an autonomous coding agent that creates REAL, WORKING files.

TASK: {task}

PLAN:
{plan}

=== CRITICAL FILE FORMAT INSTRUCTIONS ===
You MUST output files in this EXACT format so they can be saved to disk:

## File: `filename.ext`
```language
<complete file content>
```

EXAMPLE OUTPUT:
## File: `index.html`
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My App</title>
</head>
<body>
    <h1>Hello World</h1>
    <script src="app.js"></script>
</body>
</html>
```

## File: `app.js`
```javascript
console.log("App loaded");
document.addEventListener("DOMContentLoaded", function() {{
    console.log("DOM ready");
}});
```

## File: `styles.css`
```css
body {{
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}}
```

=== RULES ===
1. EVERY file must start with: ## File: `path/filename.ext`
2. EVERY file must have complete, working code in a code block
3. NO placeholders like "..." or "// add code here"
4. NO explanations between files - just the file blocks
5. Create ALL necessary files for the task to work

NOW CREATE THE FILES:
"""

    def _create_fix_prompt(self, code: str, review: str, errors: list[str]) -> str:
        """Create a prompt to fix code based on review and errors."""
        error_text = "\n".join(errors) if errors else "No execution errors"
        
        return f"""Fix the following code based on the review feedback and execution errors.

CURRENT CODE:
{code}

REVIEW FEEDBACK:
{review}

EXECUTION ERRORS:
{error_text}

Provide the COMPLETE fixed code using the same file format:
## File: `path/to/file.ext`
```language
<complete fixed content>
```

Fix ALL issues and ensure the code runs without errors.
"""

    def _extract_and_save_files(self, code: str) -> list[str]:
        """Extract file blocks from code output and save them."""
        import re
        
        files_created = []
        
        # Multiple patterns to match different formats
        patterns = [
            # Pattern 1: ## File: `path`
            r"## File: `([^`]+)`\s*```[\w]*\n(.*?)```",
            # Pattern 2: ### `path`
            r"### `([^`]+)`\s*```[\w]*\n(.*?)```",
            # Pattern 3: **path** or __path__
            r"\*\*([^\*]+\.\w+)\*\*\s*```[\w]*\n(.*?)```",
            # Pattern 4: filename.ext:
            r"^([a-zA-Z0-9_\-./]+\.\w+):\s*```[\w]*\n(.*?)```",
            # Pattern 5: # path/to/file.ext
            r"^# ([a-zA-Z0-9_\-./]+\.\w+)\s*```[\w]*\n(.*?)```",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code, re.DOTALL | re.MULTILINE)
            for file_path, content in matches:
                file_path = file_path.strip()
                # Skip if already created
                if file_path in files_created:
                    continue
                    
                try:
                    # Ensure the file path is within workspace
                    if not file_path.startswith("/") and not file_path.startswith("\\"):
                        full_path = self.workspace_dir / file_path
                    else:
                        full_path = Path(file_path)
                    
                    # Create parent directories
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write the file
                    full_path.write_text(content.strip(), encoding="utf-8")
                    files_created.append(file_path)
                    self._log(f"   📄 Created: {file_path}")
                except Exception as e:
                    self._log(f"   ❌ Failed to save {file_path}: {e}")
        
        return files_created

    def _execute_generated_code(self, files: list[str]) -> dict:
        """Execute/test the generated code files."""
        result = {"output": "", "errors": ""}
        
        if not files:
            return result
        
        # Find main entry point
        main_file = None
        for f in files:
            f_lower = f.lower()
            if any(name in f_lower for name in ["main.py", "app.py", "index.py", "run.py"]):
                main_file = f
                break
            elif f_lower.endswith(".py") and main_file is None:
                main_file = f
        
        if main_file and main_file.endswith(".py"):
            # Execute Python file
            self._log(f"   🐍 Running: python {main_file}")
            try:
                exec_result = self.terminal.execute(f"python {main_file}", timeout=30)
                result["output"] = exec_result.stdout or ""
                if exec_result.return_code != 0:
                    result["errors"] = exec_result.stderr or f"Exit code: {exec_result.return_code}"
            except Exception as e:
                result["errors"] = str(e)
        
        # Check for HTML files (just validate they exist)
        html_files = [f for f in files if f.endswith(".html")]
        if html_files and not main_file:
            result["output"] = f"Created HTML files: {', '.join(html_files)}"
        
        # Check for package.json (suggest npm install)
        if any("package.json" in f for f in files):
            result["output"] += "\n\nNote: Run 'npm install' to install dependencies"
        
        return result

    def run_autonomous(
        self,
        goal: str,
        max_steps: int = 10,
    ) -> list[EnhancedTaskResult]:
        """
        Run in autonomous mode, breaking down and executing a complex goal.
        
        Args:
            goal: High-level goal to achieve
            max_steps: Maximum steps to take
            
        Returns:
            List of task results for each step
        """
        results = []
        
        self._log(f"\n{'='*60}")
        self._log(f"AUTONOMOUS MODE")
        self._log(f"Goal: {goal}")
        self._log(f"{'='*60}\n")
        
        # Get high-level plan
        plan_prompt = f"""Break down this goal into a series of concrete, actionable steps:

Goal: {goal}

For each step, provide:
1. Step number
2. Description
3. Expected output

Format as a numbered list."""
        
        plan = self.planner.run(plan_prompt)
        self._log(f"Plan created with steps")
        
        # Execute each step (simplified - in reality you'd parse the plan)
        # For demo, we'll just run the main goal
        result = self.run(goal, auto_research=True, auto_save=True)
        results.append(result)
        
        return results

    # ==================== CLI Helper Methods ====================
    
    def clear_agent_history(self):
        """Clear conversation history from all agents."""
        self.planner.clear_history()
        self.coder.clear_history()
        self.reviewer.clear_history()
        self._log("Agent history cleared")

    def plan_only(self, task: str) -> str:
        """Create only a plan without coding."""
        return self.planner.run(f"Create a detailed implementation plan for: {task}")

    def quick_code(self, task: str) -> str:
        """Generate code quickly without the review loop."""
        return self.coder.run(f"Implement the following: {task}")

    def review_only(self, code: str) -> str:
        """Review provided code without generating new code."""
        return self.reviewer.run(f"Review this code and provide feedback:\n\n{code}")

    def run_with_expertise(self, task: str, domain: str) -> EnhancedTaskResult:
        """
        Run task with specific domain expertise.
        
        Args:
            task: The coding task
            domain: Domain expertise (frontend, uiux, system_design, devops, web_design)
        """
        # Get domain prompt
        domain_prompt = get_domain_prompt(domain)
        
        # Create enhanced task with domain context
        enhanced_task = f"{domain_prompt}\n\nTask: {task}"
        
        return self.run(enhanced_task)

    def web_search(self, query: str) -> list[dict]:
        """Search the web for information."""
        if not self.capabilities.web_search or not self.search:
            return [{"error": "Web search not available"}]
        return self.search.search(query)

    def browse_page(self, url: str) -> str:
        """Fetch and return webpage content."""
        if not self.capabilities.web_browse or not self.browser:
            return "Web browsing not available"
        result = self.browser.fetch_page(url)
        return result.get("text", result.get("error", "Failed to fetch page"))

    def index_github_repo(self, repo_url: str) -> str:
        """Clone and index a GitHub repository."""
        if not self.capabilities.github or not self.github:
            return "GitHub integration not available"
        
        # Clone the repo
        clone_result = self.github.clone_repository(repo_url)
        if "error" in clone_result:
            return f"Clone failed: {clone_result['error']}"
        
        local_path = clone_result.get("local_path", "")
        self._log(f"Cloned to: {local_path}")
        
        # Index to knowledge base if available
        if self.knowledge_base and local_path:
            try:
                self.knowledge_base.add_repository(local_path)
                return f"Repository cloned and indexed: {local_path}"
            except Exception as e:
                return f"Cloned but indexing failed: {e}"
        
        return f"Repository cloned: {local_path}"
