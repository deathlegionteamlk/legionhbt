import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PlanStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class PlanTask:
    task_id: str
    name: str
    description: str
    priority: TaskPriority
    dependencies: List[str] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)
    estimated_duration: float = 0.0
    required_resources: List[str] = field(default_factory=list)
    validation_criteria: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Optional[Any] = None


@dataclass
class Plan:
    plan_id: str
    name: str
    objective: str
    tasks: Dict[str, PlanTask]
    task_order: List[str]
    created_at: str
    updated_at: str
    status: PlanStatus
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1


class C5ULTRAPLAN:
    def __init__(self):
        self._plans: Dict[str, Plan] = {}
        self._plan_history: List[str] = []
        self._templates: Dict[str, Dict] = {}
    
    def create_plan(self, name: str, objective: str, 
                    tasks: List[Dict], metadata: Optional[Dict] = None) -> str:
        plan_id = hashlib.sha256(f"{name}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        now = datetime.utcnow().isoformat()
        
        task_dict = {}
        task_order = []
        
        for i, task_data in enumerate(tasks):
            task_id = f"{plan_id}_task_{i}"
            task = PlanTask(
                task_id=task_id,
                name=task_data.get("name", f"Task {i}"),
                description=task_data.get("description", ""),
                priority=TaskPriority(task_data.get("priority", 2)),
                dependencies=task_data.get("dependencies", []),
                subtasks=task_data.get("subtasks", []),
                estimated_duration=task_data.get("estimated_duration", 0.0),
                required_resources=task_data.get("required_resources", []),
                validation_criteria=task_data.get("validation_criteria", [])
            )
            task_dict[task_id] = task
            task_order.append(task_id)
        
        plan = Plan(
            plan_id=plan_id,
            name=name,
            objective=objective,
            tasks=task_dict,
            task_order=task_order,
            created_at=now,
            updated_at=now,
            status=PlanStatus.DRAFT,
            metadata=metadata or {}
        )
        
        self._plans[plan_id] = plan
        self._plan_history.append(plan_id)
        
        return plan_id
    
    def decompose_objective(self, objective: str, 
                            constraints: Optional[List[str]] = None) -> List[Dict]:
        tasks = []
        
        if "analyze" in objective.lower() or "investigate" in objective.lower():
            tasks.append({
                "name": "Gather Information",
                "description": "Collect relevant data and context",
                "priority": TaskPriority.HIGH.value,
                "dependencies": [],
                "validation_criteria": ["Data collected", "Sources verified"]
            })
            tasks.append({
                "name": "Analyze Patterns",
                "description": "Identify patterns and relationships",
                "priority": TaskPriority.HIGH.value,
                "dependencies": [tasks[0]["name"]],
                "validation_criteria": ["Patterns identified", "Analysis documented"]
            })
        
        if "build" in objective.lower() or "create" in objective.lower() or "implement" in objective.lower():
            tasks.append({
                "name": "Design Architecture",
                "description": "Create system design and architecture",
                "priority": TaskPriority.CRITICAL.value,
                "dependencies": [],
                "validation_criteria": ["Design reviewed", "Architecture approved"]
            })
            tasks.append({
                "name": "Implement Components",
                "description": "Build individual components",
                "priority": TaskPriority.HIGH.value,
                "dependencies": [tasks[-1]["name"]],
                "validation_criteria": ["Components built", "Unit tests pass"]
            })
            tasks.append({
                "name": "Integrate System",
                "description": "Connect all components",
                "priority": TaskPriority.HIGH.value,
                "dependencies": [tasks[-1]["name"]],
                "validation_criteria": ["Integration complete", "End-to-end tests pass"]
            })
        
        if "verify" in objective.lower() or "test" in objective.lower() or "validate" in objective.lower():
            tasks.append({
                "name": "Define Test Cases",
                "description": "Create comprehensive test cases",
                "priority": TaskPriority.HIGH.value,
                "dependencies": [],
                "validation_criteria": ["Test cases defined", "Coverage acceptable"]
            })
            tasks.append({
                "name": "Execute Tests",
                "description": "Run all test cases",
                "priority": TaskPriority.HIGH.value,
                "dependencies": [tasks[-1]["name"]],
                "validation_criteria": ["Tests executed", "Results recorded"]
            })
        
        if not tasks:
            tasks.append({
                "name": "Execute Objective",
                "description": f"Complete: {objective}",
                "priority": TaskPriority.MEDIUM.value,
                "dependencies": [],
                "validation_criteria": ["Objective completed"]
            })
        
        tasks.append({
            "name": "Final Review",
            "description": "Review and validate all work",
            "priority": TaskPriority.MEDIUM.value,
            "dependencies": [t["name"] for t in tasks],
            "validation_criteria": ["Review complete", "Sign-offs obtained"]
        })
        
        return tasks
    
    def optimize_plan(self, plan_id: str) -> bool:
        if plan_id not in self._plans:
            return False
        
        plan = self._plans[plan_id]
        
        task_list = list(plan.tasks.values())
        task_list.sort(key=lambda t: (t.priority.value, -t.estimated_duration))
        
        optimized_order = []
        completed = set()
        
        while len(optimized_order) < len(task_list):
            progress = False
            for task in task_list:
                if task.task_id in completed:
                    continue
                
                deps_satisfied = all(
                    plan.tasks.get(d) and d in completed 
                    for d in task.dependencies
                )
                
                if deps_satisfied or not task.dependencies:
                    optimized_order.append(task.task_id)
                    completed.add(task.task_id)
                    progress = True
            
            if not progress:
                for task in task_list:
                    if task.task_id not in completed:
                        optimized_order.append(task.task_id)
                        completed.add(task.task_id)
                        break
        
        plan.task_order = optimized_order
        plan.updated_at = datetime.utcnow().isoformat()
        plan.version += 1
        
        return True
    
    def get_next_task(self, plan_id: str) -> Optional[PlanTask]:
        if plan_id not in self._plans:
            return None
        
        plan = self._plans[plan_id]
        
        for task_id in plan.task_order:
            task = plan.tasks.get(task_id)
            if task and task.status == "pending":
                deps_complete = all(
                    plan.tasks.get(d) and plan.tasks[d].status == "completed"
                    for d in task.dependencies
                )
                if deps_complete:
                    return task
        
        return None
    
    def update_task_status(self, plan_id: str, task_id: str, 
                           status: str, result: Any = None) -> bool:
        if plan_id not in self._plans:
            return False
        
        plan = self._plans[plan_id]
        if task_id not in plan.tasks:
            return False
        
        plan.tasks[task_id].status = status
        if result is not None:
            plan.tasks[task_id].result = result
        
        plan.updated_at = datetime.utcnow().isoformat()
        
        return True
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        return self._plans.get(plan_id)
    
    def get_plan_status(self, plan_id: str) -> Dict:
        plan = self._plans.get(plan_id)
        if not plan:
            return {}
        
        total = len(plan.tasks)
        completed = sum(1 for t in plan.tasks.values() if t.status == "completed")
        failed = sum(1 for t in plan.tasks.values() if t.status == "failed")
        pending = sum(1 for t in plan.tasks.values() if t.status == "pending")
        
        return {
            "plan_id": plan_id,
            "name": plan.name,
            "status": plan.status.value,
            "progress": completed / total if total > 0 else 0,
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "version": plan.version
        }
    
    def save_plan_template(self, name: str, plan_id: str) -> bool:
        if plan_id not in self._plans:
            return False
        
        plan = self._plans[plan_id]
        self._templates[name] = {
            "name": plan.name,
            "objective": plan.objective,
            "tasks": [
                {
                    "name": t.name,
                    "description": t.description,
                    "priority": t.priority.value,
                    "dependencies": t.dependencies,
                    "estimated_duration": t.estimated_duration,
                    "required_resources": t.required_resources,
                    "validation_criteria": t.validation_criteria
                }
                for t in plan.tasks.values()
            ]
        }
        
        return True
    
    def load_plan_template(self, name: str, new_name: Optional[str] = None) -> Optional[str]:
        if name not in self._templates:
            return None
        
        template = self._templates[name]
        return self.create_plan(
            name=new_name or template["name"],
            objective=template["objective"],
            tasks=template["tasks"]
        )
    
    def list_plans(self) -> List[str]:
        return list(self._plans.keys())
