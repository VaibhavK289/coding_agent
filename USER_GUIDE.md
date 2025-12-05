# 🤖 Coding Agent - Complete User Guide

> A multi-agent AI system that writes code like a senior developer with 25+ years of experience.

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Understanding the Architecture](#understanding-the-architecture)
6. [Usage Modes](#usage-modes)
7. [Commands Reference](#commands-reference)
8. [Configuration](#configuration)
9. [Advanced Features](#advanced-features)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Examples](#examples)

---

## Introduction

**Coding Agent** is an AI-powered code generation system that mimics how senior developers work. Instead of a single AI generating code, it uses three specialized agents that collaborate:

| Agent | Model | Responsibility |
|-------|-------|----------------|
| 🧠 **Planner** | DeepSeek-R1 (8B) | Thinks through architecture, breaks down problems, creates implementation plans |
| 💻 **Coder** | Qwen 2.5 Coder (7B) | Writes production-quality code based on plans |
| 🔍 **Reviewer** | Qwen 2.5 Coder (7B) | Reviews code for bugs, security issues, and improvements |

### The Multi-Loop Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│   │  PLAN    │───▶│   CODE   │───▶│  REVIEW  │             │
│   │(DeepSeek)│    │ (Qwen)   │    │  (Qwen)  │             │
│   └──────────┘    └──────────┘    └────┬─────┘             │
│                                        │                    │
│                         ┌──────────────┼──────────────┐     │
│                         │              │              │     │
│                         ▼              ▼              │     │
│                    ┌─────────┐   ┌──────────┐         │     │
│                    │APPROVED │   │  ISSUES  │─────────┘     │
│                    │  ✓ Done │   │   FIX    │               │
│                    └─────────┘   └──────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

This **Plan → Code → Critique → Fix** loop continues until:
- The reviewer approves the code, OR
- Maximum iterations are reached (default: 3)

---

## System Requirements

### Hardware
- **RAM**: Minimum 16GB (32GB recommended for smooth operation)
- **Storage**: ~20GB for models
- **GPU**: Optional but recommended (NVIDIA with CUDA support)

### Software
- **Python**: 3.10 or higher
- **Ollama**: Latest version
- **Conda**: Recommended for environment management

### Required Ollama Models

| Model | Size | Purpose |
|-------|------|---------|
| `deepseek-r1:8b` | ~5GB | Planner agent |
| `qwen2.5-coder:7b` | ~4.7GB | Coder & Reviewer agents |
| `nomic-embed-text` | ~270MB | RAG embeddings |

---

## Installation

### Step 1: Install Ollama

Download from [ollama.ai](https://ollama.ai) and install.

Verify installation:
```powershell
ollama --version
```

### Step 2: Pull Required Models

```powershell
# Pull all required models
ollama pull deepseek-r1:8b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text

# Verify models are installed
ollama list
```

Expected output:
```
NAME                    ID              SIZE
deepseek-r1:8b          xxxxx           5.4 GB
qwen2.5-coder:7b        xxxxx           4.7 GB
nomic-embed-text        xxxxx           274 MB
```

### Step 3: Set Up Python Environment

```powershell
# Navigate to project directory
cd D:\coding_agent

# Create conda environment
conda create -n coding_agent_env python=3.11 -y

# Activate environment
conda activate coding_agent_env

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation

```powershell
# Test imports
python -c "from orchestrator import CodingOrchestrator; print('Ready!')"
```

If you see "Ready!", you're all set!

---

## Quick Start

### 1. Start Interactive Mode

```powershell
conda activate coding_agent_env
cd D:\coding_agent
python main.py
```

### 2. Enter Your First Task

```
🎯 Task: Create a Python function that validates email addresses using regex
```

### 3. Watch the Magic

The system will:
1. **Plan** the implementation (architecture, edge cases, approach)
2. **Code** the solution (complete, runnable code)
3. **Review** for bugs and improvements
4. **Fix** any issues found
5. Return the final, polished code

---

## Understanding the Architecture

### Agent Details

#### 🧠 Planner Agent (DeepSeek-R1)

**Purpose**: Strategic thinking and architecture design

**Capabilities**:
- Analyzes complex requirements
- Breaks down tasks into manageable steps
- Designs clean, scalable architecture
- Identifies edge cases and potential issues
- Creates detailed implementation plans

**Output Format**:
```
## Task Analysis
[Understanding of requirements]

## Architecture Design
[High-level design and components]

## Implementation Plan
[Step-by-step guide]

## File Structure
[Proposed organization]

## Technical Considerations
[Edge cases, performance notes]

## Success Criteria
[How to verify correctness]
```

#### 💻 Coder Agent (Qwen 2.5 Coder)

**Purpose**: Write production-quality code

**Capabilities**:
- Implements code following the plan
- Follows SOLID principles and design patterns
- Adds proper error handling
- Includes type hints and documentation
- Writes clean, maintainable code

**Output Format**:
```
## File: `path/to/file.py`
```python
# Complete, runnable code
```

## Explanation
[Key implementation decisions]
```

#### 🔍 Reviewer Agent (Qwen 2.5 Coder)

**Purpose**: Quality assurance and bug detection

**Review Criteria**:
1. **Correctness** - Does the code work?
2. **Security** - Any vulnerabilities?
3. **Performance** - Efficient implementation?
4. **Readability** - Clear and organized?
5. **Maintainability** - Easy to modify?
6. **Best Practices** - Following conventions?
7. **Error Handling** - Graceful failure?
8. **Edge Cases** - Boundary conditions?
9. **Testing** - Is it testable?
10. **Documentation** - Complex parts explained?

**Output Format**:
```
## Review Summary
[APPROVED / NEEDS_CHANGES / REJECTED]

## Critical Issues (Must Fix)
[Bugs, security issues]

## Improvements (Should Fix)
[Quality improvements]

## Suggestions (Nice to Have)
[Optional enhancements]

## Positive Aspects
[What was done well]

## Specific Changes Required
[Numbered list of fixes]
```

### Knowledge Base (RAG)

The system includes a **ChromaDB vector database** with **nomic-embed-text** embeddings:

- **Stores** previously generated code for reference
- **Retrieves** relevant context for new tasks
- **Learns** from successful implementations
- **Persists** between sessions (stored in `./chroma_db/`)

---

## Usage Modes

### Mode 1: Interactive Mode (Default)

Best for: Exploratory coding, multiple tasks, iterative development

```powershell
python main.py
```

Features:
- Continuous conversation with the agents
- Multiple commands available
- History preserved during session

### Mode 2: Single Task Mode

Best for: Automation, scripts, one-off tasks

```powershell
# Basic task
python main.py -t "Create a binary search function"

# Save output to file
python main.py -t "Create a FastAPI server" -o api_server.py

# Custom iterations
python main.py -t "Build a complex system" --iterations 5
```

### Mode 3: Quick Code (Skip Review Loop)

Best for: Simple tasks where you trust the first output

```powershell
# In interactive mode
🎯 Task: /code Create a hello world function
```

### Mode 4: Plan Only

Best for: Understanding approach before committing to implementation

```powershell
# In interactive mode
🎯 Task: /plan Design a microservices architecture for e-commerce
```

### Mode 5: Review Only

Best for: Reviewing existing code

```powershell
# In interactive mode
🎯 Task: /review
# Then paste your code, end with 'END' on a new line
```

---

## Commands Reference

### CLI Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--task` | `-t` | Task to execute | None (interactive) |
| `--output` | `-o` | Save code to file | None |
| `--iterations` | | Max Plan-Code-Review-Fix cycles | 3 |
| `--no-rag` | | Disable knowledge base | False |
| `--quiet` | `-q` | Less verbose output | False |

### Interactive Commands

| Command | Description |
|---------|-------------|
| `/plan <task>` | Create implementation plan only |
| `/code <task>` | Quick code without review loop |
| `/review` | Review pasted code |
| `/clear` | Clear agent conversation history |
| `/help` | Show available commands |
| `quit` or `exit` | Exit the program |

---

## Configuration

### config.py Settings

```python
# Model Configuration
PLANNER_MODEL = "deepseek-r1:8b"      # Change to different model
CODER_MODEL = "qwen2.5-coder:7b"      # Change to different model
REVIEWER_MODEL = "qwen2.5-coder:7b"   # Can use same or different
EMBEDDING_MODEL = "nomic-embed-text"   # For RAG

# Generation Parameters
TEMPERATURE = 0.2    # Lower = more deterministic (0.0-1.0)
MAX_TOKENS = 4096    # Maximum response length

# ChromaDB Settings
CHROMA_COLLECTION_NAME = "code_knowledge_base"
CHROMA_PERSIST_DIRECTORY = "./chroma_db"

# Workflow Settings
MAX_ITERATIONS = 3   # Max review-fix cycles
```

### Using Different Models

You can swap models based on your hardware:

**For lower RAM (8-16GB)**:
```python
PLANNER_MODEL = "deepseek-r1:1.5b"
CODER_MODEL = "qwen2.5-coder:3b"
REVIEWER_MODEL = "qwen2.5-coder:3b"
```

**For higher RAM/GPU (32GB+)**:
```python
PLANNER_MODEL = "deepseek-r1:14b"
CODER_MODEL = "qwen2.5-coder:14b"
REVIEWER_MODEL = "qwen2.5-coder:14b"
```

---

## Advanced Features

### 1. Adding Code to Knowledge Base

Build context from your existing codebase:

```python
from rag import CodeKnowledgeBase

kb = CodeKnowledgeBase()

# Add a single file
kb.add_code_file("path/to/your/code.py")

# Add entire directory
kb.add_directory("./src", extensions=[".py", ".js"])

# Add code snippet with metadata
kb.add_code(
    code="def example(): pass",
    metadata={"purpose": "utility function"},
    file_path="utils.py"
)

# Check how many documents stored
print(f"Knowledge base has {kb.count()} documents")
```

### 2. Programmatic Usage

Use the orchestrator in your own scripts:

```python
from orchestrator import CodingOrchestrator

# Initialize
orchestrator = CodingOrchestrator(
    max_iterations=3,
    use_rag=True,
    verbose=True
)

# Full workflow
result = orchestrator.run("Create a REST API for user management")
print(result.code)
print(result.review)
print(f"Completed in {result.iterations} iterations")

# Quick code only
code = orchestrator.quick_code("Create a sorting function")

# Plan only
plan = orchestrator.plan_only("Design a chat application")

# Review existing code
review = orchestrator.review_only(my_code, requirements="Must handle errors")
```

### 3. Agent Direct Access

Use individual agents for specific tasks:

```python
from agents import PlannerAgent, CoderAgent, ReviewerAgent

# Create agents
planner = PlannerAgent()
coder = CoderAgent()
reviewer = ReviewerAgent()

# Use planner
plan = planner.run("Design a caching system")
plan = planner.refine_plan(plan, "Add Redis support")

# Use coder
code = coder.implement_plan(plan)
code = coder.fix_code(code, issues="Handle connection errors")
code = coder.refactor(code, "Improve performance")

# Use reviewer
review = reviewer.review_code(code)
is_good = reviewer.is_approved(review)
security = reviewer.security_review(code)
performance = reviewer.performance_review(code)
```

### 4. Custom Prompts

Modify agent behavior by editing system prompts in:
- `agents/planner.py` → `PLANNER_SYSTEM_PROMPT`
- `agents/coder.py` → `CODER_SYSTEM_PROMPT`
- `agents/reviewer.py` → `REVIEWER_SYSTEM_PROMPT`

---

## Best Practices

### 1. Writing Good Task Descriptions

❌ **Bad**:
```
make a function
```

✅ **Good**:
```
Create a Python function that:
- Validates credit card numbers using the Luhn algorithm
- Accepts a string input
- Returns True if valid, False otherwise
- Handles edge cases like spaces and dashes in the input
```

### 2. Iterative Development

For complex systems, break down into phases:

```
Phase 1: /plan Design a complete e-commerce backend
Phase 2: Create the user authentication module
Phase 3: Create the product catalog module
Phase 4: Create the shopping cart module
Phase 5: Create the order processing module
```

### 3. Building Context

Before complex tasks, add relevant code to knowledge base:

```python
from rag import CodeKnowledgeBase
kb = CodeKnowledgeBase()
kb.add_directory("./existing_project")
```

### 4. Review the Plan First

For important features, use `/plan` first:

```
🎯 Task: /plan Create a payment processing system

[Review the plan, then proceed with full implementation]

🎯 Task: Create a payment processing system following the plan above
```

### 5. Leverage Specialized Reviews

```
🎯 Task: /review
[paste your code]
END

# Then ask for specific reviews
🎯 Task: Perform a security review of the code above
🎯 Task: Perform a performance review of the code above
```

---

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError"

**Problem**: Missing Python packages

**Solution**:
```powershell
conda activate coding_agent_env
pip install -r requirements.txt
```

#### 2. "Connection refused" / "Ollama not running"

**Problem**: Ollama server not started

**Solution**:
```powershell
# Start Ollama (it runs as a service, but sometimes needs restart)
ollama serve
```

#### 3. "Model not found"

**Problem**: Required model not pulled

**Solution**:
```powershell
ollama pull deepseek-r1:8b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

#### 4. Slow Response Times

**Causes & Solutions**:
- **CPU-only**: Normal, consider GPU
- **Large models**: Use smaller variants (3b instead of 7b)
- **First run**: Models load into memory, subsequent calls faster

#### 5. "Execution Policy" Error (PowerShell)

**Problem**: Conda activation blocked

**Solution**:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

#### 6. Out of Memory

**Problem**: Not enough RAM for models

**Solutions**:
- Close other applications
- Use smaller models in `config.py`
- Add swap space

#### 7. ChromaDB Errors

**Problem**: Corrupted vector database

**Solution**:
```powershell
# Remove and recreate
Remove-Item -Recurse -Force .\chroma_db
python main.py  # Will recreate automatically
```

### Getting Help

1. Check Ollama is running: `ollama list`
2. Verify Python environment: `conda activate coding_agent_env && python --version`
3. Test imports: `python -c "from orchestrator import CodingOrchestrator"`

---

## Examples

### Example 1: Create a Utility Function

```
🎯 Task: Create a Python decorator that retries a function with exponential backoff
```

**Expected Output**:
- Implementation plan with retry logic design
- Complete decorator code with configurable parameters
- Unit tests for the decorator
- Documentation

### Example 2: Build a REST API

```
🎯 Task: Create a FastAPI REST API for a todo list application with:
- CRUD operations for todos
- SQLite database with SQLAlchemy
- Pydantic models for validation
- Proper error handling
```

**Expected Output**:
- Project structure plan
- Main API file with routes
- Database models
- Pydantic schemas
- Example usage

### Example 3: Data Processing Script

```
🎯 Task: Create a Python script that:
- Reads CSV files from a directory
- Cleans and validates the data
- Combines them into a single DataFrame
- Exports to both CSV and Parquet formats
- Includes logging and error handling
```

### Example 4: Design Before Coding

```
🎯 Task: /plan Design a real-time chat application with:
- WebSocket support
- User authentication
- Message persistence
- Read receipts
- Typing indicators
```

*Review the plan, then:*

```
🎯 Task: Implement the WebSocket server from the plan above
```

### Example 5: Code Review

```
🎯 Task: /review
def calc(x,y,op):
    if op=='+':return x+y
    if op=='-':return x-y
    if op=='*':return x*y
    if op=='/':return x/y
END
```

**Expected Review**:
- Issues: Division by zero, no type hints, poor naming
- Suggestions: Use match statement, add docstring
- Refactored code example

---

## Summary

The Coding Agent transforms how you write code by:

1. **Thinking first** - Planner creates solid architecture
2. **Implementing well** - Coder writes production-quality code
3. **Catching mistakes** - Reviewer finds bugs before you do
4. **Learning continuously** - Knowledge base grows with usage

Start with simple tasks, build up context in the knowledge base, and gradually tackle more complex projects. The more you use it, the better it becomes at understanding your coding style and project context.

Happy coding! 🚀
