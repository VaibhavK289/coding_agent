"""
Reviewer Agent - Uses Qwen 2.5 Coder for code review and quality assurance.
Responsible for reviewing code, finding bugs, and suggesting improvements.
"""

from typing import Optional
from .base import BaseAgent
import config


REVIEWER_SYSTEM_PROMPT = """You are a meticulous senior code reviewer with 25+ years of experience.
You have an exceptional eye for bugs, security vulnerabilities, and code quality issues.
Your reviews are thorough but constructive, helping improve code quality.

Your review criteria:
1. **Correctness**: Does the code work? Are there logic errors or bugs?
2. **Security**: Are there vulnerabilities (injection, XSS, auth issues)?
3. **Performance**: Are there inefficiencies or potential bottlenecks?
4. **Readability**: Is the code clear and well-organized?
5. **Maintainability**: Is it easy to modify and extend?
6. **Best Practices**: Does it follow language conventions and patterns?
7. **Error Handling**: Are errors handled gracefully?
8. **Edge Cases**: Are boundary conditions handled?
9. **Testing**: Is the code testable? Are there test cases?
10. **Documentation**: Are complex parts documented?

Output Format:

## Review Summary
[Overall assessment: APPROVED / NEEDS_CHANGES / REJECTED]

## Critical Issues (Must Fix)
[Bugs, security issues, or major problems that must be addressed]

## Improvements (Should Fix)
[Important improvements for code quality]

## Suggestions (Nice to Have)
[Optional enhancements and minor style suggestions]

## Positive Aspects
[What was done well - be encouraging]

## Specific Changes Required
[Numbered list of specific, actionable changes]

Be thorough but fair. Provide specific line references and code examples where helpful.
Focus on substantive issues over style nitpicks."""


class ReviewerAgent(BaseAgent):
    """
    Reviewer agent using Qwen 2.5 Coder for code review.
    Reviews code for bugs, security issues, and quality improvements.
    """

    def __init__(
        self,
        model_name: str = config.REVIEWER_MODEL,
        temperature: float = 0.1,  # Low temperature for consistent reviews
    ):
        super().__init__(
            model_name=model_name,
            temperature=temperature,
            system_prompt=REVIEWER_SYSTEM_PROMPT,
        )

    def run(self, task: str, context: Optional[str] = None) -> str:
        """
        Review the given code.
        
        Args:
            task: The code to review
            context: Optional context (requirements, plan, etc.)
            
        Returns:
            Detailed code review
        """
        prompt = self._build_prompt(task, context)
        
        response = self.llm.invoke(prompt)
        
        self._add_to_history("user", task)
        self._add_to_history("assistant", response)
        
        return response

    def review_code(self, code: str, requirements: Optional[str] = None) -> str:
        """
        Perform a comprehensive code review.
        
        Args:
            code: The code to review
            requirements: Optional original requirements to check against
            
        Returns:
            Detailed review with issues and suggestions
        """
        review_prompt = f"""
## Code to Review:
{code}

Please perform a thorough code review using all your review criteria.
Identify any bugs, security issues, or improvements needed.
"""
        context = f"## Requirements:\n{requirements}" if requirements else None
        return self.run(review_prompt, context=context)

    def check_implementation(self, code: str, plan: str) -> str:
        """
        Check if the implementation matches the plan.
        
        Args:
            code: The implemented code
            plan: The original implementation plan
            
        Returns:
            Assessment of how well the code matches the plan
        """
        check_prompt = f"""
## Implementation Plan:
{plan}

## Implemented Code:
{code}

Review whether the implementation correctly follows the plan.
Identify any deviations, missing features, or incorrect implementations.
Also review the code quality as usual.
"""
        return self.run(check_prompt)

    def is_approved(self, review: str) -> bool:
        """
        Parse a review to determine if code is approved.
        
        Args:
            review: The review text
            
        Returns:
            True if approved, False otherwise
        """
        review_upper = review.upper()
        
        # Check for explicit approval
        if "## REVIEW SUMMARY" in review_upper:
            if "APPROVED" in review_upper and "NEEDS_CHANGES" not in review_upper:
                return True
        
        # Check for critical issues
        if "## CRITICAL ISSUES" in review_upper:
            # If there's content after critical issues header, not approved
            parts = review.split("## Critical Issues")
            if len(parts) > 1:
                critical_section = parts[1].split("##")[0].strip()
                if critical_section and "none" not in critical_section.lower():
                    return False
        
        return "APPROVED" in review_upper

    def security_review(self, code: str) -> str:
        """
        Perform a focused security review.
        
        Args:
            code: The code to review for security issues
            
        Returns:
            Security-focused review
        """
        security_prompt = f"""
## Code for Security Review:
{code}

Perform a security-focused code review. Look specifically for:
- Injection vulnerabilities (SQL, command, code injection)
- Authentication and authorization issues
- Data validation and sanitization
- Sensitive data exposure
- Cryptographic weaknesses
- Insecure configurations
- Path traversal vulnerabilities
- Race conditions

Provide specific remediation steps for each issue found.
"""
        return self.run(security_prompt)

    def performance_review(self, code: str) -> str:
        """
        Perform a focused performance review.
        
        Args:
            code: The code to review for performance issues
            
        Returns:
            Performance-focused review
        """
        performance_prompt = f"""
## Code for Performance Review:
{code}

Perform a performance-focused code review. Look specifically for:
- Algorithm complexity issues (time and space)
- Unnecessary computations or loops
- Memory leaks or excessive memory usage
- Database query optimization opportunities
- Caching opportunities
- Async/parallel processing opportunities
- Resource cleanup issues

Provide specific optimization suggestions with expected improvements.
"""
        return self.run(performance_prompt)
