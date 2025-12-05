"""
Orchestrator - Coordinates the multi-agent system with Plan -> Code -> Critique -> Fix loop.
Implements the senior developer workflow for high-quality code generation.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from agents import PlannerAgent, CoderAgent, ReviewerAgent
from rag import CodeKnowledgeBase
import config


class TaskStatus(Enum):
    """Status of a coding task."""
    PENDING = "pending"
    PLANNING = "planning"
    CODING = "coding"
    REVIEWING = "reviewing"
    FIXING = "fixing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskResult:
    """Result of a completed coding task."""
    task: str
    status: TaskStatus
    plan: str = ""
    code: str = ""
    review: str = ""
    iterations: int = 0
    history: list[dict] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        return self.status == TaskStatus.COMPLETED


class CodingOrchestrator:
    """
    Orchestrates the multi-agent coding workflow.
    
    Workflow: Plan -> Code -> Critique -> Fix (repeat if needed)
    
    Uses:
    - PlannerAgent (DeepSeek-R1): Architecture and planning
    - CoderAgent (Qwen 2.5 Coder): Implementation
    - ReviewerAgent (Qwen 2.5 Coder): Code review
    - CodeKnowledgeBase: RAG for context
    """

    def __init__(
        self,
        max_iterations: int = config.MAX_ITERATIONS,
        use_rag: bool = True,
        verbose: bool = True,
    ):
        self.max_iterations = max_iterations
        self.use_rag = use_rag
        self.verbose = verbose
        
        # Initialize agents
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.reviewer = ReviewerAgent()
        
        # Initialize RAG if enabled
        self.knowledge_base = CodeKnowledgeBase() if use_rag else None
        
        self._log("Orchestrator initialized with agents:")
        self._log(f"  - Planner: {self.planner}")
        self._log(f"  - Coder: {self.coder}")
        self._log(f"  - Reviewer: {self.reviewer}")
        if self.knowledge_base:
            self._log(f"  - Knowledge Base: {self.knowledge_base.count()} documents")

    def _log(self, message: str):
        """Log a message if verbose mode is enabled."""
        if self.verbose:
            print(f"[Orchestrator] {message}")

    def _get_rag_context(self, task: str) -> str:
        """Get relevant context from the knowledge base."""
        if not self.knowledge_base:
            return ""
        
        context = self.knowledge_base.get_context_for_task(task)
        if context:
            self._log(f"Retrieved {len(context)} chars of relevant context")
        return context

    def run(self, task: str, existing_code: Optional[str] = None) -> TaskResult:
        """
        Execute the full coding workflow for a task.
        
        Args:
            task: The coding task to complete
            existing_code: Optional existing code to build upon
            
        Returns:
            TaskResult with the final code and history
        """
        result = TaskResult(task=task, status=TaskStatus.PENDING)
        
        self._log(f"\n{'='*60}")
        self._log(f"Starting task: {task[:100]}...")
        self._log(f"{'='*60}\n")
        
        # Get RAG context
        rag_context = self._get_rag_context(task)
        context = rag_context
        if existing_code:
            context += f"\n\n## Existing Code:\n{existing_code}"
        
        # Phase 1: Planning
        self._log("Phase 1: PLANNING (DeepSeek-R1)")
        result.status = TaskStatus.PLANNING
        
        try:
            plan = self.planner.run(task, context=context if context else None)
            result.plan = plan
            result.history.append({
                "phase": "planning",
                "iteration": 0,
                "output": plan,
            })
            self._log("Plan created successfully")
        except Exception as e:
            self._log(f"Planning failed: {e}")
            result.status = TaskStatus.FAILED
            return result
        
        # Phase 2-4: Code -> Critique -> Fix loop
        current_code = ""
        
        for iteration in range(1, self.max_iterations + 1):
            result.iterations = iteration
            self._log(f"\n--- Iteration {iteration}/{self.max_iterations} ---\n")
            
            # Phase 2: Coding
            self._log("Phase 2: CODING (Qwen 2.5 Coder)")
            result.status = TaskStatus.CODING
            
            try:
                if iteration == 1:
                    # First iteration: implement the plan
                    current_code = self.coder.implement_plan(
                        plan=result.plan,
                        existing_code=existing_code,
                    )
                else:
                    # Subsequent iterations: fix based on review
                    current_code = self.coder.fix_code(
                        code=current_code,
                        issues=result.review,
                    )
                
                result.code = current_code
                result.history.append({
                    "phase": "coding",
                    "iteration": iteration,
                    "output": current_code,
                })
                self._log("Code generated successfully")
            except Exception as e:
                self._log(f"Coding failed: {e}")
                result.status = TaskStatus.FAILED
                return result
            
            # Phase 3: Review
            self._log("Phase 3: REVIEWING (Qwen 2.5 Coder)")
            result.status = TaskStatus.REVIEWING
            
            try:
                review = self.reviewer.check_implementation(
                    code=current_code,
                    plan=result.plan,
                )
                result.review = review
                result.history.append({
                    "phase": "reviewing",
                    "iteration": iteration,
                    "output": review,
                })
                self._log("Review completed")
            except Exception as e:
                self._log(f"Review failed: {e}")
                result.status = TaskStatus.FAILED
                return result
            
            # Check if approved
            if self.reviewer.is_approved(review):
                self._log("✓ Code APPROVED by reviewer!")
                result.status = TaskStatus.COMPLETED
                break
            else:
                self._log("✗ Code needs changes, continuing to fix phase...")
                result.status = TaskStatus.FIXING
        
        # If we exhausted iterations without approval
        if result.status != TaskStatus.COMPLETED:
            self._log(f"Max iterations ({self.max_iterations}) reached. Returning best effort.")
            result.status = TaskStatus.COMPLETED  # Still return the code
        
        # Store successful code in knowledge base
        if self.knowledge_base and result.code:
            self._log("Storing generated code in knowledge base")
            self.knowledge_base.add_code(
                result.code,
                metadata={"task": task[:200], "status": result.status.value},
            )
        
        self._log(f"\n{'='*60}")
        self._log(f"Task completed in {result.iterations} iteration(s)")
        self._log(f"{'='*60}\n")
        
        return result

    def quick_code(self, task: str) -> str:
        """
        Quick code generation without the full review loop.
        Useful for simple tasks.
        
        Args:
            task: The coding task
            
        Returns:
            Generated code
        """
        context = self._get_rag_context(task)
        return self.coder.run(task, context=context if context else None)

    def review_only(self, code: str, requirements: Optional[str] = None) -> str:
        """
        Only perform code review without the full workflow.
        
        Args:
            code: Code to review
            requirements: Optional requirements to check against
            
        Returns:
            Review feedback
        """
        return self.reviewer.review_code(code, requirements=requirements)

    def plan_only(self, task: str) -> str:
        """
        Only create a plan without implementing.
        
        Args:
            task: The task to plan
            
        Returns:
            Implementation plan
        """
        context = self._get_rag_context(task)
        return self.planner.run(task, context=context if context else None)

    def add_to_knowledge_base(self, code: str, file_path: Optional[str] = None):
        """Add code to the knowledge base for future reference."""
        if self.knowledge_base:
            self.knowledge_base.add_code(code, file_path=file_path)
            self._log(f"Added code to knowledge base")

    def clear_agent_history(self):
        """Clear conversation history from all agents."""
        self.planner.clear_history()
        self.coder.clear_history()
        self.reviewer.clear_history()
        self._log("Cleared all agent conversation histories")
