"""
Coding Agent - Multi-Agent AI System for Senior-Level Code Generation

This system uses three specialized agents:
- Planner (DeepSeek-R1): Architectural thinking and planning
- Coder (Qwen 2.5 Coder): Production-quality code implementation
- Reviewer (Qwen 2.5 Coder): Code review and quality assurance

Enhanced with:
- Domain expertise (Frontend, UI/UX, System Design, DevOps, Web Design)
- File system manipulation (create, read, modify, delete files)
- Web browsing and search capabilities
- GitHub integration
- Image scanning (OCR)
- Hierarchical reasoning
- Terminal command execution

Workflow: Plan -> Code -> Critique -> Fix (iterative)
"""

import argparse
import sys
from pathlib import Path

from enhanced_orchestrator import EnhancedOrchestrator, EnhancedTaskResult


def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                         🤖 ENHANCED CODING AGENT                           ║
║              Multi-Agent AI System for Senior-Level Code Generation        ║
║                                                                             ║
║  Agents:   Planner (DeepSeek-R1) | Coder (Qwen 2.5) | Reviewer (Qwen 2.5) ║
║  RAG:      ChromaDB + nomic-embed-text                                     ║
║  Tools:    File System | Web Browser | GitHub | Search | OCR | Terminal   ║
║  Domains:  Frontend | UI/UX | System Design | DevOps | Web Design         ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def interactive_mode(orchestrator: EnhancedOrchestrator):
    """Run the agent in interactive mode."""
    print("\n📝 Interactive Mode - Type your coding tasks (type 'quit' to exit)\n")
    print("Basic Commands:")
    print("  /plan <task>      - Only create a plan")
    print("  /code <task>      - Quick code without review loop")
    print("  /review           - Review code (paste code after command)")
    print("  /clear            - Clear agent conversation history")
    print("  /help             - Show this help")
    print("  quit              - Exit the program")
    print("\nDomain Expertise:")
    print("  /frontend <task>  - Frontend development expertise")
    print("  /uiux <task>      - UI/UX design expertise")
    print("  /sysdesign <task> - System design expertise")
    print("  /devops <task>    - DevOps expertise")
    print("  /webdesign <task> - Web design expertise")
    print("\nTools:")
    print("  /search <query>   - Web search")
    print("  /browse <url>     - Fetch webpage content")
    print("  /github <url>     - Clone and index GitHub repo")
    print("  /scan <path>      - OCR scan image")
    print("  /files <path>     - List files in directory")
    print("  /run <command>    - Execute terminal command")
    print("-" * 70)
    
    while True:
        try:
            user_input = input("\n🎯 Task: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("quit", "exit", "q"):
            print("\nGoodbye! 👋")
            break
        
        if user_input.startswith("/help"):
            print("\nBasic Commands:")
            print("  /plan <task>      - Only create a plan")
            print("  /code <task>      - Quick code without review loop")
            print("  /review           - Review code (paste code after command)")
            print("  /clear            - Clear agent conversation history")
            print("  quit              - Exit the program")
            print("\nDomain Expertise:")
            print("  /frontend <task>  - Frontend development expertise")
            print("  /uiux <task>      - UI/UX design expertise")
            print("  /sysdesign <task> - System design expertise")
            print("  /devops <task>    - DevOps expertise")
            print("  /webdesign <task> - Web design expertise")
            print("\nTools:")
            print("  /search <query>   - Web search")
            print("  /browse <url>     - Fetch webpage content")
            print("  /github <url>     - Clone and index GitHub repo")
            print("  /scan <path>      - OCR scan image")
            print("  /files <path>     - List files in directory")
            print("  /run <command>    - Execute terminal command")
            continue
        
        if user_input.startswith("/clear"):
            orchestrator.clear_agent_history()
            print("✓ Conversation history cleared")
            continue
        
        if user_input.startswith("/plan "):
            task = user_input[6:].strip()
            if task:
                print("\n🔄 Creating implementation plan...\n")
                plan = orchestrator.plan_only(task)
                print("\n" + "=" * 70)
                print("📋 IMPLEMENTATION PLAN")
                print("=" * 70)
                print(plan)
            continue
        
        if user_input.startswith("/code "):
            task = user_input[6:].strip()
            if task:
                print("\n🔄 Generating code (quick mode)...\n")
                code = orchestrator.quick_code(task)
                print("\n" + "=" * 70)
                print("💻 GENERATED CODE")
                print("=" * 70)
                print(code)
            continue
        
        # Domain expertise commands
        if user_input.startswith("/frontend "):
            task = user_input[10:].strip()
            if task:
                print("\n🔄 Running with Frontend expertise...\n")
                result = orchestrator.run_with_expertise(task, "frontend")
                _print_result(result)
            continue
        
        if user_input.startswith("/uiux "):
            task = user_input[6:].strip()
            if task:
                print("\n🔄 Running with UI/UX expertise...\n")
                result = orchestrator.run_with_expertise(task, "uiux")
                _print_result(result)
            continue
        
        if user_input.startswith("/sysdesign "):
            task = user_input[11:].strip()
            if task:
                print("\n🔄 Running with System Design expertise...\n")
                result = orchestrator.run_with_expertise(task, "system_design")
                _print_result(result)
            continue
        
        if user_input.startswith("/devops "):
            task = user_input[8:].strip()
            if task:
                print("\n🔄 Running with DevOps expertise...\n")
                result = orchestrator.run_with_expertise(task, "devops")
                _print_result(result)
            continue
        
        if user_input.startswith("/webdesign "):
            task = user_input[11:].strip()
            if task:
                print("\n🔄 Running with Web Design expertise...\n")
                result = orchestrator.run_with_expertise(task, "web_design")
                _print_result(result)
            continue
        
        # Tool commands
        if user_input.startswith("/search "):
            query = user_input[8:].strip()
            if query:
                print("\n🔍 Searching the web...\n")
                results = orchestrator.web_search(query)
                print("=" * 70)
                print("🌐 SEARCH RESULTS")
                print("=" * 70)
                for i, result in enumerate(results[:5], 1):
                    print(f"\n{i}. {result.get('title', 'No title')}")
                    print(f"   {result.get('link', result.get('href', 'No link'))}")
                    print(f"   {result.get('snippet', result.get('body', 'No description'))[:200]}")
            continue
        
        if user_input.startswith("/browse "):
            url = user_input[8:].strip()
            if url:
                print(f"\n🌐 Fetching {url}...\n")
                content = orchestrator.browse_page(url)
                print("=" * 70)
                print("📄 PAGE CONTENT")
                print("=" * 70)
                print(content[:2000] + "..." if len(content) > 2000 else content)
            continue
        
        if user_input.startswith("/github "):
            repo_url = user_input[8:].strip()
            if repo_url:
                print(f"\n📦 Cloning and indexing {repo_url}...\n")
                try:
                    result = orchestrator.index_github_repo(repo_url)
                    print(f"✓ Repository indexed: {result}")
                except Exception as e:
                    print(f"✗ Error: {e}")
            continue
        
        if user_input.startswith("/scan "):
            image_path = user_input[6:].strip()
            if image_path:
                print(f"\n🔍 Scanning image: {image_path}...\n")
                result = orchestrator.scan_image(image_path)
                print("=" * 70)
                print("📝 EXTRACTED TEXT")
                print("=" * 70)
                if isinstance(result, dict):
                    if "error" in result:
                        print(f"Error: {result['error']}")
                    else:
                        print(result.get("raw_text", "No text extracted"))
                        if result.get("code_blocks"):
                            print("\n--- Code Blocks Found ---")
                            for block in result["code_blocks"]:
                                print(block)
                else:
                    print(result)
            continue
        
        if user_input.startswith("/files "):
            path = user_input[7:].strip()
            if path:
                files = orchestrator.list_files(path)
                print("=" * 70)
                print(f"📁 FILES IN {path}")
                print("=" * 70)
                if not files:
                    print("  (empty or not found)")
                else:
                    for f in files:
                        if isinstance(f, dict):
                            name = f.get("name", str(f))
                            file_type = f.get("type", "")
                            size = f.get("size", "")
                            prefix = "📁" if file_type == "directory" else "📄"
                            print(f"  {prefix} {name}")
                        else:
                            print(f"  {f}")
            continue
        
        if user_input.startswith("/run "):
            command = user_input[5:].strip()
            if command:
                print(f"\n⚡ Executing: {command}\n")
                result = orchestrator.run_command(command)
                print("=" * 70)
                print("💻 COMMAND OUTPUT")
                print("=" * 70)
                if isinstance(result, dict):
                    if result.get("success"):
                        print(result.get("stdout", ""))
                    else:
                        print(f"Error: {result.get('stderr', result.get('error', 'Unknown error'))}")
                else:
                    print(result)
            continue
        
        if user_input.startswith("/review"):
            print("Paste your code below (end with a line containing only 'END'):")
            code_lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                code_lines.append(line)
            
            if code_lines:
                code = "\n".join(code_lines)
                print("\n🔄 Reviewing code...\n")
                review = orchestrator.review_only(code)
                print("\n" + "=" * 70)
                print("📝 CODE REVIEW")
                print("=" * 70)
                print(review)
            continue
        
        # Full workflow
        print("\n🔄 Starting full Plan -> Code -> Critique -> Fix workflow...\n")
        result = orchestrator.run(user_input)
        _print_result(result)


def _print_result(result: EnhancedTaskResult):
    """Helper to print task results."""
    print("\n" + "=" * 70)
    print("📋 FINAL RESULT")
    print("=" * 70)
    print(f"Status: {result.status}")
    print(f"Iterations: {result.iterations}")
    
    if result.files_created:
        print(f"\n📁 Files Created ({len(result.files_created)}):")
        for f in result.files_created:
            print(f"   ✓ {f}")
    
    if result.files_modified:
        print(f"\n📝 Files Modified ({len(result.files_modified)}):")
        for f in result.files_modified:
            print(f"   ✓ {f}")
    
    if result.execution_output:
        print("\n🚀 Execution Output:")
        print(result.execution_output[:500])
    
    if result.errors:
        print("\n⚠️ Errors:")
        for e in result.errors:
            print(f"   {e[:200]}")
    
    print("\n--- Final Review ---")
    print(result.review[:1000] if len(result.review) > 1000 else result.review)


def run_task(orchestrator: EnhancedOrchestrator, task: str, output_file: str = None, domain: str = None):
    """Run a single task and optionally save output."""
    if domain:
        result = orchestrator.run_with_expertise(task, domain)
    else:
        result = orchestrator.run(task)
    
    print("\n" + "=" * 70)
    print("📋 RESULT")
    print("=" * 70)
    print(f"Status: {result.status}")
    print(f"Iterations: {result.iterations}")
    if result.files_created:
        print(f"Files Created: {', '.join(result.files_created)}")
    if result.files_modified:
        print(f"Files Modified: {', '.join(result.files_modified)}")
    print("\n--- Plan ---")
    print(result.plan[:500] + "..." if len(result.plan) > 500 else result.plan)
    print("\n--- Code ---")
    print(result.code)
    print("\n--- Review ---")
    print(result.review)
    
    if output_file:
        output_path = Path(output_file)
        output_path.write_text(result.code, encoding="utf-8")
        print(f"\n✓ Code saved to {output_file}")
    
    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced Coding Agent - Multi-Agent AI System for Senior-Level Code Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Interactive mode
  python main.py -t "Create a REST API"       # Run a single task
  python main.py -t "..." -o output.py        # Save generated code to file
  python main.py --no-rag                     # Disable RAG context
  python main.py --iterations 5               # Set max iterations
  python main.py -t "..." --domain frontend   # Use frontend expertise
  python main.py -t "..." --domain uiux       # Use UI/UX expertise
  python main.py -t "..." --domain sysdesign  # Use system design expertise
  python main.py -t "..." --domain devops     # Use DevOps expertise
  python main.py -t "..." --domain webdesign  # Use web design expertise
        """,
    )
    
    parser.add_argument(
        "-t", "--task",
        type=str,
        help="Coding task to execute (if not provided, runs interactive mode)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file to save generated code",
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG (retrieval-augmented generation)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Maximum Plan-Code-Review-Fix iterations (default: 3)",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode (less verbose output)",
    )
    parser.add_argument(
        "--domain",
        type=str,
        choices=["frontend", "uiux", "sysdesign", "devops", "webdesign"],
        help="Domain expertise to use (frontend, uiux, sysdesign, devops, webdesign)",
    )
    parser.add_argument(
        "--github-token",
        type=str,
        help="GitHub personal access token for API access",
    )
    parser.add_argument(
        "--work-dir",
        type=str,
        default=".",
        help="Working directory for file operations (default: current directory)",
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Initialize orchestrator
    print("🚀 Initializing enhanced coding agent...")
    orchestrator = EnhancedOrchestrator(
        workspace_dir=args.work_dir,
        verbose=not args.quiet,
        github_token=args.github_token,
        domains=[args.domain] if args.domain else None,
    )
    print("✓ Agent ready with all tools enabled!\n")
    
    if args.task:
        # Single task mode
        run_task(orchestrator, args.task, args.output, args.domain)
    else:
        # Interactive mode
        interactive_mode(orchestrator)


if __name__ == "__main__":
    main()