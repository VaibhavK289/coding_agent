"""
Planner Agent - Uses DeepSeek-R1 for architectural thinking and planning.
Responsible for breaking down tasks, designing architecture, and creating implementation plans.
"""

from typing import Optional
from .base import BaseAgent
import config


PLANNER_SYSTEM_PROMPT = """You are an expert software architect and technical lead with 25+ years of experience.
Your role is to analyze coding tasks and create detailed, actionable implementation plans.

Your responsibilities:
1. Understand the requirements thoroughly
2. Break down complex tasks into smaller, manageable steps
3. Design clean, scalable architecture
4. Consider edge cases, error handling, and best practices
5. Provide clear file structure and module organization
6. Suggest appropriate design patterns when relevant

Output Format:
## Task Analysis
[Your understanding of what needs to be built]

## Architecture Design
[High-level architecture and component interactions]

## Implementation Plan
[Step-by-step implementation guide with specific tasks]

## File Structure
[Proposed file/folder organization]

## Technical Considerations
[Edge cases, potential issues, performance considerations]

## Success Criteria
[How to verify the implementation is correct]

Think step by step. Be thorough but concise. Focus on practical, implementable solutions."""


class PlannerAgent(BaseAgent):
    """
    Planner agent using DeepSeek-R1 for architectural thinking.
    Creates detailed implementation plans from high-level requirements.
    """

    def __init__(
        self,
        model_name: str = config.PLANNER_MODEL,
        temperature: float = 0.3,  # Slightly higher for creative thinking
    ):
        super().__init__(
            model_name=model_name,
            temperature=temperature,
            system_prompt=PLANNER_SYSTEM_PROMPT,
        )

    def run(self, task: str, context: Optional[str] = None) -> str:
        """
        Generate an implementation plan for the given task.
        
        Args:
            task: The coding task or feature to plan
            context: Optional relevant context (existing code, requirements, etc.)
            
        Returns:
            Detailed implementation plan
        """
        prompt = self._build_prompt(task, context)
        
        response = self.llm.invoke(prompt)
        
        self._add_to_history("user", task)
        self._add_to_history("assistant", response)
        
        return response

    def refine_plan(self, original_plan: str, feedback: str) -> str:
        """
        Refine an existing plan based on feedback from other agents.
        
        Args:
            original_plan: The original implementation plan
            feedback: Feedback from Coder or Reviewer agents
            
        Returns:
            Refined implementation plan
        """
        refinement_prompt = f"""
## Original Plan:
{original_plan}

## Feedback Received:
{feedback}

Please refine the implementation plan based on the feedback above.
Address all concerns and improve the plan accordingly.
Maintain the same output format but update the relevant sections.
"""
        return self.run(refinement_prompt)

    def analyze_codebase(self, code_summary: str) -> str:
        """
        Analyze existing codebase and suggest improvements or next steps.
        
        Args:
            code_summary: Summary of existing code/architecture
            
        Returns:
            Analysis and recommendations
        """
        analysis_prompt = f"""
Analyze the following codebase summary and provide:
1. Current architecture assessment
2. Potential improvements
3. Technical debt identification
4. Suggested next features or refactoring

Codebase Summary:
{code_summary}
"""
        return self.run(analysis_prompt)
