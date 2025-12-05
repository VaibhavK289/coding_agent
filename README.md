# 🤖 Coding Agent

A multi-agent AI system for senior-level code generation using locally hosted LLMs via Ollama.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                              │
│                 Plan → Code → Critique → Fix                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │   PLANNER    │   │    CODER     │   │   REVIEWER   │         │
│  │ DeepSeek-R1  │──▶│ Qwen2.5-Coder│──▶│ Qwen2.5-Coder│         │
│  │  (8B)        │   │   (7B)       │   │    (7B)      │         │
│  └──────────────┘   └──────────────┘   └──────────────┘         │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │                                     │
│                   ┌────────▼────────┐                            │
│                   │  KNOWLEDGE BASE │                            │
│                   │    ChromaDB +   │                            │
│                   │ nomic-embed-text│                            │
│                   └─────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

## Agents

| Agent | Model | Role |
|-------|-------|------|
| **Planner** | DeepSeek-R1 (8B) | Analyzes tasks, designs architecture, creates implementation plans |
| **Coder** | Qwen 2.5 Coder (7B) | Implements production-quality code based on plans |
| **Reviewer** | Qwen 2.5 Coder (7B) | Reviews code for bugs, security issues, and improvements |

## Workflow

The system follows a **multi-loop approach** mimicking how senior developers work:

1. **Plan** - Planner analyzes requirements and creates a detailed implementation plan
2. **Code** - Coder implements the plan with production-quality code
3. **Critique** - Reviewer checks for bugs, security issues, and improvements
4. **Fix** - If issues found, Coder fixes them and returns to step 3

This loop continues until the code is approved or max iterations are reached (default: 3).

## Prerequisites

### 1. Install Ollama

Download and install [Ollama](https://ollama.ai/).

### 2. Pull Required Models

```bash
ollama pull deepseek-r1:8b
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

Verify models are available:
```bash
ollama list
```

### 3. Install Python Dependencies

```bash
# Create and activate conda environment
conda create -n coding_agent_env python=3.11 -y
conda activate coding_agent_env

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Interactive Mode

```bash
python main.py
```

This opens an interactive prompt where you can enter coding tasks.

**Commands:**
- `/plan <task>` - Only create a plan without coding
- `/code <task>` - Quick code generation without review loop
- `/review` - Review code (paste code after command)
- `/clear` - Clear agent conversation history
- `quit` - Exit the program

### Single Task Mode

```bash
# Run a task
python main.py -t "Create a Python REST API with FastAPI for user management"

# Save output to file
python main.py -t "Create a binary search function" -o search.py

# Set max iterations
python main.py -t "Build a task queue system" --iterations 5
```

### Options

| Flag | Description |
|------|-------------|
| `-t, --task` | Coding task to execute |
| `-o, --output` | Output file to save generated code |
| `--no-rag` | Disable RAG (knowledge base) |
| `--iterations N` | Max Plan-Code-Review-Fix iterations (default: 3) |
| `-q, --quiet` | Less verbose output |

## Project Structure

```
coding_agent/
├── agents/
│   ├── __init__.py
│   ├── base.py          # Base agent class
│   ├── planner.py       # Planner agent (DeepSeek-R1)
│   ├── coder.py         # Coder agent (Qwen 2.5 Coder)
│   └── reviewer.py      # Reviewer agent (Qwen 2.5 Coder)
├── rag/
│   ├── __init__.py
│   └── knowledge_base.py # ChromaDB + nomic-embed-text
├── chroma_db/           # Vector database storage (auto-created)
├── config.py            # Configuration settings
├── orchestrator.py      # Multi-agent workflow coordinator
├── main.py              # CLI entry point
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Configuration

Edit `config.py` to customize:

```python
# Model names (must match Ollama)
PLANNER_MODEL = "deepseek-r1:8b"
CODER_MODEL = "qwen2.5-coder:7b"
REVIEWER_MODEL = "qwen2.5-coder:7b"
EMBEDDING_MODEL = "nomic-embed-text"

# Generation parameters
TEMPERATURE = 0.2
MAX_TOKENS = 4096

# Multi-loop settings
MAX_ITERATIONS = 3
```

## Examples

### Example 1: Create a Data Structure

```bash
python main.py -t "Implement a thread-safe LRU cache in Python with O(1) operations"
```

### Example 2: Build an API

```bash
python main.py -t "Create a FastAPI REST API for a todo list with CRUD operations, SQLite database, and Pydantic models"
```

### Example 3: Interactive Session

```
🎯 Task: Create a decorator for retrying failed functions with exponential backoff

[Orchestrator] Starting task: Create a decorator...
[Orchestrator] Phase 1: PLANNING (DeepSeek-R1)
[Orchestrator] Plan created successfully
[Orchestrator] Phase 2: CODING (Qwen 2.5 Coder)
[Orchestrator] Code generated successfully
[Orchestrator] Phase 3: REVIEWING (Qwen 2.5 Coder)
[Orchestrator] ✓ Code APPROVED by reviewer!
```

## RAG (Knowledge Base)

The system uses ChromaDB with `nomic-embed-text` embeddings to:

- Store previously generated code for reference
- Provide relevant context for new tasks
- Learn from successful implementations

To add existing code to the knowledge base:

```python
from orchestrator import CodingOrchestrator

orchestrator = CodingOrchestrator()
orchestrator.add_to_knowledge_base(
    code="def example(): pass",
    file_path="example.py"
)
```

Or add a directory:

```python
from rag import CodeKnowledgeBase

kb = CodeKnowledgeBase()
kb.add_directory("./src", extensions=[".py"])
```

## License

MIT
