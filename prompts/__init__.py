"""
Prompts package for specialized domain expertise and reasoning systems.
"""

from .domain_expertise import (
    FRONTEND_EXPERT_PROMPT,
    UIUX_EXPERT_PROMPT,
    SYSTEM_DESIGN_PROMPT,
    DEVOPS_EXPERT_PROMPT,
    API_DESIGN_PROMPT,
    DOMAIN_PROMPTS,
    get_domain_prompt,
    get_combined_prompt,
)

from .hierarchical_reasoning import (
    HierarchicalReasoner,
    ReasoningLevel,
    ReasoningNode,
    ReasoningTrace,
    chain_of_thought,
    self_consistency,
    reflexion,
)

__all__ = [
    # Domain prompts
    "FRONTEND_EXPERT_PROMPT",
    "UIUX_EXPERT_PROMPT", 
    "SYSTEM_DESIGN_PROMPT",
    "DEVOPS_EXPERT_PROMPT",
    "API_DESIGN_PROMPT",
    "DOMAIN_PROMPTS",
    "get_domain_prompt",
    "get_combined_prompt",
    # Reasoning
    "HierarchicalReasoner",
    "ReasoningLevel",
    "ReasoningNode",
    "ReasoningTrace",
    "chain_of_thought",
    "self_consistency",
    "reflexion",
]
