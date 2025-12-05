"""
Base agent class providing common functionality for all agents.
"""

from abc import ABC, abstractmethod
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional

import config


class BaseAgent(ABC):
    """Abstract base class for all agents in the multi-agent system."""

    def __init__(
        self,
        model_name: str,
        temperature: float = config.TEMPERATURE,
        system_prompt: str = "",
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.llm = OllamaLLM(
            model=model_name,
            temperature=temperature,
        )
        self.conversation_history: list[dict] = []

    def _build_prompt(self, user_input: str, context: Optional[str] = None) -> str:
        """Build the full prompt with system prompt, context, and user input."""
        parts = [self.system_prompt]
        
        if context:
            parts.append(f"\n\n## Relevant Context:\n{context}")
        
        if self.conversation_history:
            parts.append("\n\n## Conversation History:")
            for entry in self.conversation_history[-5:]:  # Last 5 exchanges
                parts.append(f"\n{entry['role'].upper()}: {entry['content']}")
        
        parts.append(f"\n\n## Current Task:\n{user_input}")
        
        return "\n".join(parts)

    def _add_to_history(self, role: str, content: str):
        """Add an exchange to conversation history."""
        self.conversation_history.append({"role": role, "content": content})

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    @abstractmethod
    def run(self, task: str, context: Optional[str] = None) -> str:
        """Execute the agent's primary function."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name})"
