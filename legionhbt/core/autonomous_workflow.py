import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict

from .autonomous_agent_core import AutonomousAgentCore, Task, TaskStatus


class WorkflowState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowNode:
    id: str
    task: Task
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    execution_time: float = 0.0


@dataclass
class WorkflowResult:
    workflow_id: str
    success: bool
    results: Dict[str, Any]
    execution_time: float
    completed_nodes: List[str]
    failed_nodes: List[str]
    timestamp: float = field(default_factory=time.time)


class TaskExecutionEngine:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running_tasks: Dict[str, threading.Thread] = {}
        self.task_states: Dict[str, TaskStatus] = {}

    def execute(self, task: Task, agent: AutonomousAgentCore) -> Any:
        self.task_states[task.id] = TaskStatus.IN_PROGRESS

        try:
            result = agent.execute_task(task)
            self.task_states[task.id] = TaskStatus.COMPLETED
            return result
        except Exception as e:
            self.task_states[task.id] = TaskStatus.FAILED
            raise e

    def execute_async(self, task: Task, agent: AutonomousAgentCore) -> threading.Thread:
        def run_task():
            self.execute(task, agent)

        thread = threading.Thread(target=run_task)
        self.running_tasks[task.id] = thread
        thread.start()
        return thread

    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> bool:
        if task_id in self.running_tasks:
            self.running_tasks[task_id].join(timeout)
            return not self.running_tasks[task_id].is_alive()
        return True

    def get_task_status(self, task_id: str) -> TaskStatus:
        return self.task_states.get(task_id, TaskStatus.PENDING)

    def shutdown(self):
        self.executor.shutdown(wait=True)


class DynamicWorkflowGenerator:
    def __init__(self):
        self.workflow_patterns = {
            "sequential": self._generate_sequential,
            "parallel": self._generate_parallel,
            "map_reduce": self._generate_map_reduce,
            "conditional": self._generate_conditional
        }

    def generate(self, goal: str, pattern: str = "sequential",
                 context: Dict[str, Any] = None) -> List[WorkflowNode]:
        generator = self.workflow_patterns.get(pattern, self._generate_sequential)
        return generator(goal, context or {})

    def _generate_sequential(self, goal: str, context: Dict[str, Any]) -> List[WorkflowNode]:
        steps = [
            f"Analyze requirements for: {goal}",
            f"Design solution for: {goal}",
            f"Implement: {goal}",
            f"Verify: {goal}"
        ]

        nodes = []
        prev_id = None

        for i, step in enumerate(steps):
            task = Task(
                id=f"seq_{i}_{int(time.time() * 1000)}",
                description=step,
                priority=1.0 - (i * 0.1)
            )

            deps = {prev_id} if prev_id else set()
            node = WorkflowNode(
                id=task.id,
                task=task,
                dependencies=deps
            )

            if prev_id and nodes:
                nodes[-1].dependents.add(task.id)

            nodes.append(node)
            prev_id = task.id

        return nodes

    def _generate_parallel(self, goal: str, context: Dict[str, Any]) -> List[WorkflowNode]:
        subtasks = context.get("subtasks", ["task_a", "task_b", "task_c"])

        nodes = []
        for i, subtask in enumerate(subtasks):
            task = Task(
                id=f"par_{i}_{int(time.time() * 1000)}",
                description=f"{subtask}: {goal}",
                priority=1.0
            )
            node = WorkflowNode(id=task.id, task=task)
            nodes.append(node)

        return nodes

    def _generate_map_reduce(self, goal: str, context: Dict[str, Any]) -> List[WorkflowNode]:
        items = context.get("items", [])

        nodes = []
        map_ids = []

        for i, item in enumerate(items):
            task = Task(
                id=f"map_{i}_{int(time.time() * 1000)}",
                description=f"Process {item}",
                priority=1.0
            )
            node = WorkflowNode(id=task.id, task=task)
            nodes.append(node)
            map_ids.append(task.id)

        reduce_task = Task(
            id=f"reduce_{int(time.time() * 1000)}",
            description=f"Aggregate results for: {goal}",
            priority=0.9
        )
        reduce_node = WorkflowNode(
            id=reduce_task.id,
            task=reduce_task,
            dependencies=set(map_ids)
        )

        for map_id in map_ids:
            for node in nodes:
                if node.id == map_id:
                    node.dependents.add(reduce_task.id)

        nodes.append(reduce_node)
        return nodes

    def _generate_conditional(self, goal: str, context: Dict[str, Any]) -> List[WorkflowNode]:
        condition = context.get("condition", "check_status")

        check_task = Task(
            id=f"cond_check_{int(time.time() * 1000)}",
            description=f"Check condition: {condition}",
            priority=1.0
        )
        check_node = WorkflowNode(id=check_task.id, task=check_task)

        true_task = Task(
            id=f"cond_true_{int(time.time() * 1000)}",
            description=f"Execute if true: {goal}",
            priority=0.9,
            dependencies=[check_task.id]
        )
        true_node = WorkflowNode(
            id=true_task.id,
            task=true_task,
            dependencies={check_task.id}
        )

        false_task = Task(
            id=f"cond_false_{int(time.time() * 1000)}",
            description=f"Execute if false: {goal}",
            priority=0.9,
            dependencies=[check_task.id]
        )
        false_node = WorkflowNode(
            id=false_task.id,
            task=false_task,
            dependencies={check_task.id}
        )

        check_node.dependents.update([true_task.id, false_task.id])

        return [check_node, true_node, false_node]


class ResultAggregator:
    def __init__(self):
        self.aggregation_strategies = {
            "concat": self._concat_results,
            "sum": self._sum_results,
            "average": self._average_results,
            "vote": self._vote_results,
            "merge": self._merge_results
        }

    def aggregate(self, results: Dict[str, Any], strategy: str = "concat") -> Any:
        aggregator = self.aggregation_strategies.get(strategy, self._concat_results)
        return aggregator(results)

    def _concat_results(self, results: Dict[str, Any]) -> str:
        return "\n".join(str(r) for r in results.values())

    def _sum_results(self, results: Dict[str, Any]) -> float:
        values = [float(r) for r in results.values() if isinstance(r, (int, float))]
        return sum(values) if values else 0.0

    def _average_results(self, results: Dict[str, Any]) -> float:
        values = [float(r) for r in results.values() if isinstance(r, (int, float))]
        return sum(values) / len(values) if values else 0.0

    def _vote_results(self, results: Dict[str, Any]) -> str:
        from collections import Counter
        votes = [str(r) for r in results.values()]
        most_common = Counter(votes).most_common(1)
        return most_common[0][0] if most_common else ""

    def _merge_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        merged = {}
        for r in results.values():
            if isinstance(r, dict):
                merged.update(r)
        return merged

    def resolve_conflicts(self, results: Dict[str, Any],
                         confidence_scores: Dict[str, float]) -> Any:
        if not confidence_scores:
            return list(results.values())[0] if results else None

        best_key = max(confidence_scores.items(), key=lambda x: x[1])[0]
        return results.get(best_key)


class AutonomousWorkflow:
    def __init__(self, agent: AutonomousAgentCore, max_workers: int = 4):
        self.agent = agent
        self.execution_engine = TaskExecutionEngine(max_workers)
        self.workflow_generator = DynamicWorkflowGenerator()
        self.result_aggregator = ResultAggregator()
        self.nodes: Dict[str, WorkflowNode] = {}
        self.state = WorkflowState.IDLE
        self.workflow_id: Optional[str] = None

    def create_workflow(self, goal: str, pattern: str = "sequential",
                        context: Dict[str, Any] = None) -> str:
        self.workflow_id = f"wf_{int(time.time() * 1000)}"
        nodes = self.workflow_generator.generate(goal, pattern, context)

        for node in nodes:
            self.nodes[node.id] = node
            self.agent.tasks[node.task.id] = node.task

        return self.workflow_id

    def execute_workflow(self, workflow_id: str) -> WorkflowResult:
        if workflow_id != self.workflow_id:
            raise ValueError(f"Workflow {workflow_id} not found")

        self.state = WorkflowState.RUNNING
        start_time = time.time()

        completed = set()
        failed = set()
        results = {}

        ready_nodes = [n for n in self.nodes.values()
                      if not n.dependencies]

        while ready_nodes and self.state == WorkflowState.RUNNING:
            current_batch = ready_nodes[:self.execution_engine.max_workers]
            ready_nodes = ready_nodes[len(current_batch):]

            threads = []
            for node in current_batch:
                thread = self.execution_engine.execute_async(node.task, self.agent)
                threads.append((node, thread))

            for node, thread in threads:
                thread.join()

                if node.task.status == TaskStatus.COMPLETED:
                    completed.add(node.id)
                    results[node.id] = node.task.result
                    node.status = TaskStatus.COMPLETED
                    node.result = node.task.result

                    for dependent_id in node.dependents:
                        dependent = self.nodes.get(dependent_id)
                        if dependent:
                            dependent.dependencies.discard(node.id)
                            if not dependent.dependencies:
                                ready_nodes.append(dependent)
                else:
                    failed.add(node.id)
                    node.status = TaskStatus.FAILED

        self.state = WorkflowState.COMPLETED if not failed else WorkflowState.FAILED

        return WorkflowResult(
            workflow_id=workflow_id,
            success=len(failed) == 0,
            results=results,
            execution_time=time.time() - start_time,
            completed_nodes=list(completed),
            failed_nodes=list(failed)
        )

    def execute_parallel(self, tasks: List[Task]) -> Dict[str, Any]:
        results = {}

        with ThreadPoolExecutor(max_workers=self.execution_engine.max_workers) as executor:
            future_to_task = {
                executor.submit(self.agent.execute_task, task): task
                for task in tasks
            }

            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.id] = result
                except Exception as e:
                    results[task.id] = f"Error: {str(e)}"

        return results

    def aggregate_results(self, results: Dict[str, Any],
                         strategy: str = "concat") -> Any:
        return self.result_aggregator.aggregate(results, strategy)

    def synthesize_output(self, workflow_result: WorkflowResult,
                         synthesis_type: str = "summary") -> str:
        if synthesis_type == "summary":
            return self._generate_summary(workflow_result)
        elif synthesis_type == "detailed":
            return self._generate_detailed_report(workflow_result)
        elif synthesis_type == "executive":
            return self._generate_executive_summary(workflow_result)
        else:
            return str(workflow_result.results)

    def _generate_summary(self, result: WorkflowResult) -> str:
        lines = [
            f"Workflow {result.workflow_id} Summary:",
            f"Status: {'Success' if result.success else 'Failed'}",
            f"Completed: {len(result.completed_nodes)} tasks",
            f"Failed: {len(result.failed_nodes)} tasks",
            f"Execution Time: {result.execution_time:.2f}s",
            "Results:",
            *[f"  {k}: {v}" for k, v in result.results.items()]
        ]
        return "\n".join(lines)

    def _generate_detailed_report(self, result: WorkflowResult) -> str:
        return self._generate_summary(result)

    def _generate_executive_summary(self, result: WorkflowResult) -> str:
        return f"Workflow {result.workflow_id}: {'Completed' if result.success else 'Failed'} in {result.execution_time:.2f}s"

    def pause(self):
        self.state = WorkflowState.PAUSED

    def resume(self):
        if self.state == WorkflowState.PAUSED:
            self.state = WorkflowState.RUNNING

    def cancel(self):
        self.state = WorkflowState.FAILED
        self.execution_engine.shutdown()

    def get_workflow_status(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "state": self.state.value,
            "total_nodes": len(self.nodes),
            "completed": len([n for n in self.nodes.values() if n.status == TaskStatus.COMPLETED]),
            "failed": len([n for n in self.nodes.values() if n.status == TaskStatus.FAILED]),
            "pending": len([n for n in self.nodes.values() if n.status == TaskStatus.PENDING])
        }
