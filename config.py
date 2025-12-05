"""
Configuration for the multi-agent coding system.
Models, parameters, and ChromaDB settings.
"""

# Ollama model names (must match your local Ollama installation)
PLANNER_MODEL = "deepseek-r1:8b"
CODER_MODEL = "qwen2.5-coder:7b"
REVIEWER_MODEL = "qwen2.5-coder:7b"
EMBEDDING_MODEL = "nomic-embed-text"

# Generation parameters
TEMPERATURE = 0.2
MAX_TOKENS = 4096

# ChromaDB settings
CHROMA_COLLECTION_NAME = "code_knowledge_base"
CHROMA_PERSIST_DIRECTORY = "./chroma_db"

# Multi-loop settings
MAX_ITERATIONS = 3  # Maximum Plan -> Code -> Critique -> Fix cycles
