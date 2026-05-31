import json
import time
import random
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .agent_memory import MemoryManager, MemoryEntry
from .agent_reasoning import ReasoningEngine, Thought, Action


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Task:
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: float = 1.0
    dependencies: List[str] = field(default_factory=list)
    subtasks: List['Task'] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Reflection:
    task_id: str
    success: bool
    observations: List[str]
    improvements: List[str]
    timestamp: float = field(default_factory=time.time)


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, func: Callable, description: str = "",
                 parameters: Dict[str, Any] = None):
        self.tools[name] = func
        self.tool_metadata[name] = {
            "description": description,
            "parameters": parameters or {}
        }

    def get(self, name: str) -> Optional[Callable]:
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        return self.tool_metadata.get(name)

    def select_tool(self, task_description: str) -> Optional[str]:
        scores = {}
        for name, metadata in self.tool_metadata.items():
            desc = metadata.get("description", "").lower()
            task_lower = task_description.lower()

            score = 0
            words = task_lower.split()
            for word in words:
                if word in desc:
                    score += 1

            if score > 0:
                scores[name] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return None


class SelfReflection:
    def __init__(self):
        self.reflections: List[Reflection] = []
        self.performance_history: List[Dict[str, Any]] = []

    def reflect(self, task: Task, execution_trace: List[Dict]) -> Reflection:
        success = task.status == TaskStatus.COMPLETED

        observations = []
        if success:
            observations.append(f"Task '{task.description}' completed successfully")
            if task.retry_count > 0:
                observations.append(f"Required {task.retry_count} retries")
        else:
            observations.append(f"Task '{task.description}' failed: {task.error}")

        execution_time = 0
        if task.completed_at and task.created_at:
            execution_time = task.completed_at - task.created_at

        observations.append(f"Execution time: {execution_time:.2f}s")

        improvements = self._suggest_improvements(task, execution_trace)

        reflection = Reflection(
            task_id=task.id,
            success=success,
            observations=observations,
            improvements=improvements
        )

        self.reflections.append(reflection)
        self.performance_history.append({
            "task_id": task.id,
            "success": success,
            "execution_time": execution_time,
            "retry_count": task.retry_count
        })

        return reflection

    def _suggest_improvements(self, task: Task, execution_trace: List[Dict]) -> List[str]:
        improvements = []

        if task.retry_count > 0:
            improvements.append("Consider pre-validating inputs to reduce retries")

        if task.error and "timeout" in task.error.lower():
            improvements.append("Increase timeout duration for similar tasks")

        if task.error and "memory" in task.error.lower():
            improvements.append("Optimize memory usage or increase available resources")

        if not improvements:
            improvements.append("No specific improvements suggested")

        return improvements

    def get_success_rate(self, window: int = 100) -> float:
        recent = self.performance_history[-window:]
        if not recent:
            return 0.0
        successes = sum(1 for p in recent if p["success"])
        return successes / len(recent)

    def get_common_failures(self) -> Dict[str, int]:
        failures = {}
        for reflection in self.reflections:
            if not reflection.success:
                key = reflection.task_id.split("_")[0] if "_" in reflection.task_id else "unknown"
                failures[key] = failures.get(key, 0) + 1
        return failures


class GoalDecomposer:
    def __init__(self):
        self.patterns = {
            "research": ["gather_sources", "analyze_content", "synthesize_findings"],
            "implementation": ["design_architecture", "write_code", "test_implementation"],
            "analysis": ["collect_data", "process_data", "generate_insights"],
            "debugging": ["reproduce_issue", "identify_cause", "implement_fix", "verify_solution"]
        }

    def decompose(self, goal: str) -> List[Task]:
        goal_lower = goal.lower()
        pattern = None

        for key in self.patterns:
            if key in goal_lower:
                pattern = self.patterns[key]
                break

        if not pattern:
            pattern = ["analyze_requirements", "execute_task", "verify_result"]

        tasks = []
        for i, step in enumerate(pattern):
            task = Task(
                id=f"{step}_{int(time.time() * 1000)}_{i}",
                description=f"{step.replace('_', ' ').title()}: {goal}",
                priority=1.0 - (i * 0.1),
                dependencies=[tasks[-1].id] if tasks else []
            )
            tasks.append(task)

        return tasks

    def estimate_complexity(self, goal: str) -> Tuple[int, str]:
        words = len(goal.split())
        complexity_keywords = ["complex", "difficult", "challenging", "advanced", "sophisticated"]
        keyword_count = sum(1 for kw in complexity_keywords if kw in goal.lower())

        score = words + (keyword_count * 5)

        if score < 10:
            return score, "low"
        elif score < 20:
            return score, "medium"
        else:
            return score, "high"


class ErrorRecovery:
    def __init__(self, max_retries: int = 3, backoff_base: float = 2.0):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.error_patterns: Dict[str, Callable] = {}

    def register_handler(self, error_pattern: str, handler: Callable):
        self.error_patterns[error_pattern] = handler

    def recover(self, task: Task, error: Exception) -> Tuple[bool, float]:
        if task.retry_count >= self.max_retries:
            return False, 0

        error_str = str(error).lower()

        for pattern, handler in self.error_patterns.items():
            if pattern in error_str:
                try:
                    handler(task, error)
                    return True, self._calculate_backoff(task.retry_count)
                except:
                    pass

        return True, self._calculate_backoff(task.retry_count)

    def _calculate_backoff(self, retry_count: int) -> float:
        return self.backoff_base ** retry_count + random.uniform(0, 1)

    def should_retry(self, error: Exception) -> bool:
        retryable_errors = [
            "timeout", "connection", "temporary", "rate limit",
            "service unavailable", "too many requests"
        ]
        error_str = str(error).lower()
        return any(err in error_str for err in retryable_errors)


class AutonomousAgentCore:
    def __init__(self, memory_path: Optional[str] = None):
        self.memory = MemoryManager(memory_path)
        self.reasoning = ReasoningEngine()
        self.tools = ToolRegistry()
        self.reflection = SelfReflection()
        self.decomposer = GoalDecomposer()
        self.error_recovery = ErrorRecovery()
        self.tasks: Dict[str, Task] = {}
        self.current_task: Optional[Task] = None
        self.chain_of_thought: List[str] = []

    def register_tool(self, name: str, func: Callable, description: str = "",
                      parameters: Dict[str, Any] = None):
        self.tools.register(name, func, description, parameters)

    def think(self, context: str) -> str:
        thought = f"Analyzing: {context}\n"
        thought += f"Current task: {self.current_task.description if self.current_task else 'None'}\n"
        thought += f"Available tools: {self.tools.list_tools()}\n"
        thought += f"Working memory: {len(self.memory.get_working_memory())} items\n"

        self.chain_of_thought.append(thought)
        return thought

    def plan(self, goal: str) -> List[Task]:
        self.think(f"Planning for goal: {goal}")

        complexity_score, complexity_level = self.decomposer.estimate_complexity(goal)
        self.memory.update_context("complexity", complexity_level)

        subtasks = self.decomposer.decompose(goal)

        for task in subtasks:
            self.tasks[task.id] = task

        return subtasks

    def execute_task(self, task: Task) -> Any:
        task.status = TaskStatus.IN_PROGRESS
        self.current_task = task

        execution_trace = []

        try:
            tool_name = self.tools.select_tool(task.description)

            if tool_name:
                tool = self.tools.get(tool_name)
                self.think(f"Selected tool: {tool_name}")

                params = self._extract_params(task.description)
                result = tool(**params)

                execution_trace.append({
                    "tool": tool_name,
                    "params": params,
                    "result": result
                })
            else:
                result = self._execute_direct(task)

            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()

        except Exception as e:
            task.error = str(e)
            execution_trace.append({"error": str(e)})

            should_retry, delay = self.error_recovery.recover(task, e)

            if should_retry and self.error_recovery.should_retry(e):
                task.status = TaskStatus.RETRYING
                task.retry_count += 1
                time.sleep(delay)
                return self.execute_task(task)
            else:
                task.status = TaskStatus.FAILED

        reflection = self.reflection.reflect(task, execution_trace)
        self.memory.store_interaction(
            task.description,
            str(task.result) if task.result else str(task.error),
            metadata={"reflection": reflection.__dict__}
        )

        return task.result

    def _extract_params(self, description: str) -> Dict[str, Any]:
        return {"query": description}

    def _execute_direct(self, task: Task) -> Any:
        return f"Executed: {task.description}"

    def self_improve(self) -> List[str]:
        improvements = []

        success_rate = self.reflection.get_success_rate()
        if success_rate < 0.8:
            improvements.append(f"Success rate {success_rate:.2%} below threshold. Review error patterns.")

        common_failures = self.reflection.get_common_failures()
        if common_failures:
            improvements.append(f"Common failure patterns: {common_failures}")

        if len(self.chain_of_thought) > 100:
            improvements.append("Chain of thought growing large. Consider summarization.")

        return improvements

    def run_autonomous(self, goal: str) -> Dict[str, Any]:
        start_time = time.time()

        plan = self.plan(goal)
        results = []

        for task in plan:
            if all(self.tasks.get(dep, Task("", "")).status == TaskStatus.COMPLETED
                   for dep in task.dependencies):
                result = self.execute_task(task)
                results.append({
                    "task": task.description,
                    "status": task.status.value,
                    "result": result
                })

        improvements = self.self_improve()

        return {
            "goal": goal,
            "plan": [t.description for t in plan],
            "results": results,
            "execution_time": time.time() - start_time,
            "improvements": improvements,
            "success_rate": self.reflection.get_success_rate(),
            "chain_of_thought": self.chain_of_thought
        }

    def save_state(self, path: str):
        self.memory.save(path)

    def load_state(self, path: str):
        self.memory.load(path)
