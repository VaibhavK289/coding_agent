"""
Hierarchical Reasoning System.
Implements structured multi-level reasoning for complex problem solving.
Based on modern LLM reasoning paradigms (Chain-of-Thought, Tree-of-Thought, etc.)
"""

from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import json

from langchain_ollama.llms import OllamaLLM


class ReasoningLevel(Enum):
    """Levels of reasoning depth."""
    STRATEGIC = "strategic"      # High-level goals and approach
    TACTICAL = "tactical"        # Mid-level planning and decisions
    OPERATIONAL = "operational"  # Low-level implementation details
    REFLECTIVE = "reflective"    # Meta-reasoning and self-correction


@dataclass
class ReasoningNode:
    """A node in the reasoning tree."""
    id: str
    level: ReasoningLevel
    thought: str
    confidence: float
    children: list["ReasoningNode"] = field(default_factory=list)
    parent_id: Optional[str] = None
    selected: bool = False
    evaluation: str = ""


@dataclass
class ReasoningTrace:
    """Complete reasoning trace for a problem."""
    problem: str
    root_nodes: list[ReasoningNode]
    final_answer: str
    reasoning_path: list[str]
    total_nodes_explored: int
    selected_path: list[str]


class HierarchicalReasoner:
    """
    Implements hierarchical multi-level reasoning.
    
    This system uses a tree-of-thought approach with:
    1. Strategic Level: Understand the problem, define goals
    2. Tactical Level: Break down into sub-problems, plan approach
    3. Operational Level: Concrete implementation steps
    4. Reflective Level: Evaluate, correct, improve
    
    Based on research:
    - Chain-of-Thought (CoT) prompting
    - Tree-of-Thoughts (ToT)
    - Self-Consistency
    - Reflexion
    """

    def __init__(
        self,
        model_name: str = "deepseek-r1:8b",
        temperature: float = 0.3,
        max_depth: int = 4,
        branching_factor: int = 3,
    ):
        self.model = OllamaLLM(model=model_name, temperature=temperature)
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.node_counter = 0

    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        self.node_counter += 1
        return f"node_{self.node_counter}"

    def _strategic_prompt(self, problem: str) -> str:
        """Generate strategic-level reasoning prompt."""
        return f"""You are analyzing a complex problem at the STRATEGIC level.

PROBLEM:
{problem}

At this level, focus on:
1. What is the core problem being solved?
2. What are the constraints and requirements?
3. What are the high-level goals?
4. What domains/expertise does this require?
5. What are the potential approaches?

Think step-by-step and provide 2-3 distinct strategic approaches.
For each approach, assess its viability (0-1 confidence score).

Format your response as JSON:
{{
  "problem_understanding": "your understanding",
  "key_requirements": ["req1", "req2"],
  "approaches": [
    {{
      "name": "approach name",
      "description": "brief description",
      "pros": ["pro1", "pro2"],
      "cons": ["con1"],
      "confidence": 0.8
    }}
  ]
}}"""

    def _tactical_prompt(self, problem: str, strategic_context: str) -> str:
        """Generate tactical-level reasoning prompt."""
        return f"""You are breaking down a solution at the TACTICAL level.

ORIGINAL PROBLEM:
{problem}

STRATEGIC CONTEXT:
{strategic_context}

At this level, focus on:
1. How do we break this into sub-problems?
2. What is the order of operations?
3. What are the dependencies between parts?
4. What tools/technologies are needed?
5. What are the potential risks?

Provide a detailed tactical plan with 3-5 concrete steps.

Format your response as JSON:
{{
  "sub_problems": [
    {{
      "name": "sub-problem name",
      "description": "what needs to be done",
      "dependencies": ["depends on X"],
      "estimated_complexity": "low/medium/high"
    }}
  ],
  "execution_order": ["step1", "step2"],
  "risks": ["risk1"],
  "confidence": 0.8
}}"""

    def _operational_prompt(self, problem: str, tactical_context: str, sub_problem: str) -> str:
        """Generate operational-level reasoning prompt."""
        return f"""You are implementing a solution at the OPERATIONAL level.

ORIGINAL PROBLEM:
{problem}

TACTICAL CONTEXT:
{tactical_context}

CURRENT SUB-PROBLEM:
{sub_problem}

At this level, focus on:
1. What is the exact implementation?
2. What code/configuration is needed?
3. What are the edge cases?
4. How do we handle errors?
5. How do we test this?

Provide concrete, actionable implementation details.

Format your response as JSON:
{{
  "implementation": {{
    "description": "what to implement",
    "code_outline": "pseudocode or actual code",
    "files_affected": ["file1.py"],
    "edge_cases": ["edge case 1"],
    "error_handling": "how to handle errors"
  }},
  "testing": {{
    "unit_tests": ["test1"],
    "integration_tests": ["test1"]
  }},
  "confidence": 0.8
}}"""

    def _reflective_prompt(self, problem: str, reasoning_so_far: str) -> str:
        """Generate reflective-level reasoning prompt."""
        return f"""You are evaluating the reasoning process at the REFLECTIVE level.

ORIGINAL PROBLEM:
{problem}

REASONING SO FAR:
{reasoning_so_far}

At this level, focus on:
1. Is the reasoning sound and complete?
2. Are there any logical gaps or errors?
3. What could be improved?
4. Are there alternative approaches we missed?
5. What is our confidence in the solution?

Provide a critical evaluation and any corrections needed.

Format your response as JSON:
{{
  "evaluation": {{
    "strengths": ["strength1"],
    "weaknesses": ["weakness1"],
    "gaps": ["gap1"],
    "corrections_needed": ["correction1"]
  }},
  "alternative_approaches": ["approach1"],
  "overall_confidence": 0.8,
  "recommendation": "proceed/revise/restart"
}}"""

    def _parse_json_response(self, response: str) -> dict:
        """Extract and parse JSON from response."""
        try:
            # Try to find JSON in the response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return {"raw_response": response, "confidence": 0.5}

    def _generate_strategic_nodes(self, problem: str) -> list[ReasoningNode]:
        """Generate strategic-level reasoning nodes."""
        prompt = self._strategic_prompt(problem)
        response = self.model.invoke(prompt)
        parsed = self._parse_json_response(response)
        
        nodes = []
        approaches = parsed.get("approaches", [{"description": response, "confidence": 0.7}])
        
        for i, approach in enumerate(approaches):
            node = ReasoningNode(
                id=self._generate_node_id(),
                level=ReasoningLevel.STRATEGIC,
                thought=json.dumps(approach) if isinstance(approach, dict) else str(approach),
                confidence=approach.get("confidence", 0.7) if isinstance(approach, dict) else 0.7,
            )
            nodes.append(node)
        
        return nodes

    def _expand_tactical(self, strategic_node: ReasoningNode, problem: str) -> list[ReasoningNode]:
        """Expand a strategic node with tactical reasoning."""
        prompt = self._tactical_prompt(problem, strategic_node.thought)
        response = self.model.invoke(prompt)
        parsed = self._parse_json_response(response)
        
        nodes = []
        sub_problems = parsed.get("sub_problems", [{"description": response}])
        
        for sub in sub_problems:
            node = ReasoningNode(
                id=self._generate_node_id(),
                level=ReasoningLevel.TACTICAL,
                thought=json.dumps(sub) if isinstance(sub, dict) else str(sub),
                confidence=parsed.get("confidence", 0.7),
                parent_id=strategic_node.id,
            )
            nodes.append(node)
        
        strategic_node.children = nodes
        return nodes

    def _expand_operational(
        self,
        tactical_node: ReasoningNode,
        problem: str,
        strategic_context: str,
    ) -> list[ReasoningNode]:
        """Expand a tactical node with operational reasoning."""
        prompt = self._operational_prompt(problem, strategic_context, tactical_node.thought)
        response = self.model.invoke(prompt)
        parsed = self._parse_json_response(response)
        
        node = ReasoningNode(
            id=self._generate_node_id(),
            level=ReasoningLevel.OPERATIONAL,
            thought=json.dumps(parsed) if parsed else response,
            confidence=parsed.get("confidence", 0.7),
            parent_id=tactical_node.id,
        )
        
        tactical_node.children = [node]
        return [node]

    def _reflect(self, problem: str, reasoning_trace: str) -> ReasoningNode:
        """Perform reflective reasoning on the trace."""
        prompt = self._reflective_prompt(problem, reasoning_trace)
        response = self.model.invoke(prompt)
        parsed = self._parse_json_response(response)
        
        return ReasoningNode(
            id=self._generate_node_id(),
            level=ReasoningLevel.REFLECTIVE,
            thought=json.dumps(parsed) if parsed else response,
            confidence=parsed.get("overall_confidence", 0.7),
            evaluation=parsed.get("recommendation", "proceed"),
        )

    def _select_best_path(self, nodes: list[ReasoningNode]) -> ReasoningNode:
        """Select the best node based on confidence."""
        return max(nodes, key=lambda n: n.confidence)

    def reason(self, problem: str, verbose: bool = True) -> ReasoningTrace:
        """
        Perform hierarchical reasoning on a problem.
        
        Args:
            problem: The problem to reason about
            verbose: Whether to print progress
            
        Returns:
            Complete reasoning trace
        """
        self.node_counter = 0
        all_nodes = []
        reasoning_path = []
        
        if verbose:
            print(f"\n{'='*60}")
            print("HIERARCHICAL REASONING")
            print(f"{'='*60}\n")
        
        # Level 1: Strategic reasoning
        if verbose:
            print("🎯 Level 1: STRATEGIC reasoning...")
        strategic_nodes = self._generate_strategic_nodes(problem)
        all_nodes.extend(strategic_nodes)
        
        best_strategic = self._select_best_path(strategic_nodes)
        best_strategic.selected = True
        reasoning_path.append(f"Strategic: {best_strategic.thought[:200]}...")
        
        if verbose:
            print(f"   Generated {len(strategic_nodes)} approaches")
            print(f"   Selected: confidence={best_strategic.confidence:.2f}")
        
        # Level 2: Tactical reasoning
        if verbose:
            print("\n📋 Level 2: TACTICAL reasoning...")
        tactical_nodes = self._expand_tactical(best_strategic, problem)
        all_nodes.extend(tactical_nodes)
        
        # Process each tactical node
        operational_nodes = []
        for tactical in tactical_nodes:
            if verbose:
                print(f"   Processing: {tactical.thought[:100]}...")
            
            # Level 3: Operational reasoning
            ops = self._expand_operational(
                tactical,
                problem,
                best_strategic.thought,
            )
            operational_nodes.extend(ops)
            all_nodes.extend(ops)
        
        if verbose:
            print(f"\n⚙️  Level 3: OPERATIONAL reasoning...")
            print(f"   Generated {len(operational_nodes)} implementation plans")
        
        # Level 4: Reflective reasoning
        if verbose:
            print("\n🔍 Level 4: REFLECTIVE reasoning...")
        
        # Compile reasoning trace
        trace_text = "\n\n".join([
            f"[{n.level.value.upper()}] {n.thought}"
            for n in all_nodes if n.selected or n.parent_id
        ])
        
        reflective_node = self._reflect(problem, trace_text)
        all_nodes.append(reflective_node)
        
        if verbose:
            print(f"   Evaluation: {reflective_node.evaluation}")
            print(f"   Confidence: {reflective_node.confidence:.2f}")
        
        # Compile final answer
        final_answer = self._compile_final_answer(problem, all_nodes)
        
        selected_path = [n.id for n in all_nodes if n.selected]
        
        if verbose:
            print(f"\n{'='*60}")
            print("REASONING COMPLETE")
            print(f"Total nodes explored: {len(all_nodes)}")
            print(f"{'='*60}\n")
        
        return ReasoningTrace(
            problem=problem,
            root_nodes=strategic_nodes,
            final_answer=final_answer,
            reasoning_path=reasoning_path,
            total_nodes_explored=len(all_nodes),
            selected_path=selected_path,
        )

    def _compile_final_answer(self, problem: str, nodes: list[ReasoningNode]) -> str:
        """Compile the final answer from reasoning nodes."""
        # Get the operational nodes (implementation details)
        op_nodes = [n for n in nodes if n.level == ReasoningLevel.OPERATIONAL]
        reflective = [n for n in nodes if n.level == ReasoningLevel.REFLECTIVE]
        
        answer_parts = ["## Solution\n"]
        
        for op in op_nodes:
            try:
                parsed = json.loads(op.thought)
                if "implementation" in parsed:
                    impl = parsed["implementation"]
                    answer_parts.append(f"### {impl.get('description', 'Implementation')}\n")
                    if impl.get("code_outline"):
                        answer_parts.append(f"```\n{impl['code_outline']}\n```\n")
                else:
                    answer_parts.append(op.thought)
            except:
                answer_parts.append(op.thought)
        
        if reflective:
            try:
                refl = json.loads(reflective[0].thought)
                answer_parts.append("\n## Notes\n")
                for strength in refl.get("evaluation", {}).get("strengths", []):
                    answer_parts.append(f"- ✓ {strength}\n")
                for weakness in refl.get("evaluation", {}).get("weaknesses", []):
                    answer_parts.append(f"- ⚠ {weakness}\n")
            except:
                pass
        
        return "".join(answer_parts)


# ============================================================
# CHAIN OF THOUGHT HELPERS
# ============================================================

def chain_of_thought(llm, problem: str, steps: int = 5) -> str:
    """
    Simple chain-of-thought prompting.
    
    Args:
        llm: Language model
        problem: Problem to solve
        steps: Number of reasoning steps
        
    Returns:
        Final answer with reasoning
    """
    prompt = f"""Solve this problem step by step. Show your reasoning at each step.

Problem: {problem}

Let's think through this step by step:

Step 1:"""
    
    response = llm.invoke(prompt)
    return response


def self_consistency(llm, problem: str, num_samples: int = 3) -> str:
    """
    Self-consistency: Generate multiple reasoning paths and take majority vote.
    
    Args:
        llm: Language model
        problem: Problem to solve
        num_samples: Number of reasoning samples
        
    Returns:
        Most consistent answer
    """
    responses = []
    
    for i in range(num_samples):
        prompt = f"""Solve this problem. Show your reasoning, then give a final answer.

Problem: {problem}

Reasoning:"""
        response = llm.invoke(prompt)
        responses.append(response)
    
    # In a full implementation, you'd extract and compare final answers
    # For now, return the first response
    return responses[0]


def reflexion(llm, problem: str, max_iterations: int = 3) -> str:
    """
    Reflexion: Self-reflect and improve answers iteratively.
    
    Args:
        llm: Language model  
        problem: Problem to solve
        max_iterations: Max improvement iterations
        
    Returns:
        Refined answer
    """
    # Initial attempt
    prompt = f"""Solve this problem:

{problem}

Solution:"""
    
    answer = llm.invoke(prompt)
    
    for i in range(max_iterations - 1):
        # Reflect on the answer
        reflect_prompt = f"""Review this solution for errors or improvements:

Problem: {problem}

Current Solution:
{answer}

Critique (be specific about any errors or improvements):"""
        
        critique = llm.invoke(reflect_prompt)
        
        # Check if we should improve
        if "correct" in critique.lower() and "error" not in critique.lower():
            break
        
        # Improve based on reflection
        improve_prompt = f"""Improve this solution based on the critique:

Problem: {problem}

Current Solution:
{answer}

Critique:
{critique}

Improved Solution:"""
        
        answer = llm.invoke(improve_prompt)
    
    return answer
