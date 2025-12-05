"""
Coding Agent - Multi-Agent AI System for Senior-Level Code Generation

This system uses three specialized agents:
- Planner (DeepSeek-R1): Architectural thinking and planning
- Coder (Qwen 2.5 Coder): Production-quality code implementation
- Reviewer (Qwen 2.5 Coder): Code review and quality assurance

Workflow: Plan -> Code -> Critique -> Fix (iterative)
"""

import argparse
import sys
from pathlib import Path

from orchestrator import CodingOrchestrator, TaskResult


def print_banner():
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                    🤖 CODING AGENT                             ║
║         Multi-Agent AI System for Code Generation              ║
║                                                                ║
║  Planner: DeepSeek-R1    | Coder: Qwen 2.5 Coder              ║
║  Reviewer: Qwen 2.5 Coder | RAG: ChromaDB + nomic-embed-text  ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def interactive_mode(orchestrator: CodingOrchestrator):
    """Run the agent in interactive mode."""
    print("\n📝 Interactive Mode - Type your coding tasks (type 'quit' to exit)\n")
    print("Commands:")
    print("  /plan <task>   - Only create a plan")
    print("  /code <task>   - Quick code without review loop")
    print("  /review        - Review code (paste code after command)")
    print("  /clear         - Clear agent conversation history")
    print("  /help          - Show this help")
    print("  quit           - Exit the program")
    print("-" * 60)
    
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
            print("\nCommands:")
            print("  /plan <task>   - Only create a plan")
            print("  /code <task>   - Quick code without review loop")
            print("  /review        - Review code (paste code after command)")
            print("  /clear         - Clear agent conversation history")
            print("  quit           - Exit the program")
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
                print("\n" + "=" * 60)
                print("📋 IMPLEMENTATION PLAN")
                print("=" * 60)
                print(plan)
            continue
        
        if user_input.startswith("/code "):
            task = user_input[6:].strip()
            if task:
                print("\n🔄 Generating code (quick mode)...\n")
                code = orchestrator.quick_code(task)
                print("\n" + "=" * 60)
                print("💻 GENERATED CODE")
                print("=" * 60)
                print(code)
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
                print("\n" + "=" * 60)
                print("📝 CODE REVIEW")
                print("=" * 60)
                print(review)
            continue
        
        # Full workflow
        print("\n🔄 Starting full Plan -> Code -> Critique -> Fix workflow...\n")
        result = orchestrator.run(user_input)
        
        print("\n" + "=" * 60)
        print("📋 FINAL RESULT")
        print("=" * 60)
        print(f"Status: {result.status.value}")
        print(f"Iterations: {result.iterations}")
        print("\n--- Generated Code ---")
        print(result.code)
        print("\n--- Final Review ---")
        print(result.review)


def run_task(orchestrator: CodingOrchestrator, task: str, output_file: str = None):
    """Run a single task and optionally save output."""
    result = orchestrator.run(task)
    
    print("\n" + "=" * 60)
    print("📋 RESULT")
    print("=" * 60)
    print(f"Status: {result.status.value}")
    print(f"Iterations: {result.iterations}")
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
        description="Coding Agent - Multi-Agent AI System for Code Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Interactive mode
  python main.py -t "Create a REST API"   # Run a single task
  python main.py -t "..." -o output.py    # Save generated code to file
  python main.py --no-rag                 # Disable RAG context
  python main.py --iterations 5           # Set max iterations
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
    
    args = parser.parse_args()
    
    print_banner()
    
    # Initialize orchestrator
    print("🚀 Initializing agents...")
    orchestrator = CodingOrchestrator(
        max_iterations=args.iterations,
        use_rag=not args.no_rag,
        verbose=not args.quiet,
    )
    print("✓ Agents ready!\n")
    
    if args.task:
        # Single task mode
        run_task(orchestrator, args.task, args.output)
    else:
        # Interactive mode
        interactive_mode(orchestrator)


if __name__ == "__main__":
    main()