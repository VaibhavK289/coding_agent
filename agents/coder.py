"""
Coder Agent - Uses Qwen 2.5 Coder for writing production-quality code.
Responsible for implementing the plans created by the Planner agent.
"""

from typing import Optional
from .base import BaseAgent
import config


CODER_SYSTEM_PROMPT = """You are an elite software developer with 25+ years of experience across multiple languages and frameworks.
Your code quality matches that of a senior principal engineer at a top tech company.

Your coding principles:
1. Write clean, readable, self-documenting code
2. Follow SOLID principles and appropriate design patterns
3. Include proper error handling and input validation
4. Write efficient, optimized code without premature optimization
5. Add clear, concise comments for complex logic only
6. Follow language-specific conventions and best practices
7. Include type hints/annotations where applicable
8. Write code that is easy to test and maintain

Output Format:
When writing code, always use this format:

## File: `path/to/file.ext`
```language
[complete code here]
```

## Explanation
[Brief explanation of key implementation decisions]

Important:
- Write COMPLETE, RUNNABLE code - never use placeholders like "// TODO" or "pass"
- Include all necessary imports
- Handle edge cases and errors gracefully
- If multiple files are needed, provide all of them
- Follow the implementation plan closely but improve upon it when you see better approaches"""


class CoderAgent(BaseAgent):
    """
    Coder agent using Qwen 2.5 Coder for implementation.
    Writes production-quality code based on plans and specifications.
    """

    def __init__(
        self,
        model_name: str = config.CODER_MODEL,
        temperature: float = 0.1,  # Low temperature for consistent code
    ):
        super().__init__(
            model_name=model_name,
            temperature=temperature,
            system_prompt=CODER_SYSTEM_PROMPT,
        )

    def run(self, task: str, context: Optional[str] = None) -> str:
        """
        Generate code implementation for the given task.
        
        Args:
            task: The coding task or implementation plan
            context: Optional relevant context (existing code, plan, etc.)
            
        Returns:
            Complete code implementation
        """
        prompt = self._build_prompt(task, context)
        
        response = self.llm.invoke(prompt)
        
        self._add_to_history("user", task)
        self._add_to_history("assistant", response)
        
        return response

    def implement_plan(self, plan: str, existing_code: Optional[str] = None) -> str:
        """
        Implement code based on a plan from the Planner agent.
        
        Args:
            plan: Implementation plan from PlannerAgent
            existing_code: Optional existing code to build upon
            
        Returns:
            Complete code implementation
        """
        implementation_prompt = f"""
## Implementation Plan to Follow:
{plan}

Please implement this plan completely. Write all necessary code files.
Ensure the code is production-ready, well-structured, and follows best practices.
"""
        return self.run(implementation_prompt, context=existing_code)

    def fix_code(self, code: str, issues: str) -> str:
        """
        Fix code based on issues identified by the Reviewer.
        
        Args:
            code: The original code with issues
            issues: List of issues from ReviewerAgent
            
        Returns:
            Fixed code implementation
        """
        fix_prompt = f"""
## Code with Issues:
{code}

## Issues to Fix:
{issues}

Please fix ALL the identified issues. Provide the complete corrected code.
Explain each fix briefly.
"""
        return self.run(fix_prompt)

    def refactor(self, code: str, refactor_goals: str) -> str:
        """
        Refactor existing code based on specific goals.
        
        Args:
            code: The code to refactor
            refactor_goals: What improvements to make
            
        Returns:
            Refactored code
        """
        refactor_prompt = f"""
## Code to Refactor:
{code}

## Refactoring Goals:
{refactor_goals}

Please refactor the code to achieve these goals. 
Maintain functionality while improving the code quality.
Provide complete refactored code.
"""
        return self.run(refactor_prompt)

    def add_feature(self, existing_code: str, feature_spec: str) -> str:
        """
        Add a new feature to existing code.
        
        Args:
            existing_code: The current codebase
            feature_spec: Specification for the new feature
            
        Returns:
            Updated code with new feature
        """
        feature_prompt = f"""
## Feature to Add:
{feature_spec}

Please add this feature to the existing code.
Integrate it seamlessly while maintaining code quality.
Provide the complete updated code.
"""
        return self.run(feature_prompt, context=existing_code)
