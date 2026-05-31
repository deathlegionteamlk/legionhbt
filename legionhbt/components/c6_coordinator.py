import threading
import queue
import time
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class WorkerRole(Enum):
    ANALYZER = "analyzer"
    BUILDER = "builder"
    VERIFIER = "verifier"
    TESTER = "tester"
    RESEARCHER = "researcher"
    OPTIMIZER = "optimizer"
    GENERAL = "general"


class WorkerState(Enum):
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    ERROR = "error"


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Worker:
    worker_id: str
    role: WorkerRole
    state: WorkerState
    capabilities: List[str]
    current_task: Optional[str] = None
    completed_tasks: List[str] = field(default_factory=list)
    performance_score: float = 1.0
    created_at: str = ""


@dataclass
class Task:
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: int
    required_role: Optional[WorkerRole]
    required_capabilities: List[str]
    status: TaskStatus
    assigned_worker: Optional[str] = None
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Any = None
    error: Optional[str] = None


class C6Coordinator:
    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers
        self._workers: Dict[str, Worker] = {}
        self._tasks: Dict[str, Task] = {}
        self._task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._lock = threading.Lock()
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._worker_pools: Dict[WorkerRole, Set[str]] = {
            role: set() for role in WorkerRole
        }
        self._task_handlers: Dict[str, Callable[[Dict], Any]] = {}
        self._worker_threads: Dict[str, threading.Thread] = {}
    
    def start(self):
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
    
    def stop(self):
        self._running = False
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2.0)
        
        for thread in self._worker_threads.values():
            thread.join(timeout=1.0)
    
    def spawn_worker(self, role: WorkerRole, 
                     capabilities: Optional[List[str]] = None) -> str:
        worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        caps = capabilities or []
        if role == WorkerRole.ANALYZER:
            caps.extend(["analysis", "pattern_recognition", "data_processing"])
        elif role == WorkerRole.BUILDER:
            caps.extend(["implementation", "coding", "architecture"])
        elif role == WorkerRole.VERIFIER:
            caps.extend(["verification", "validation", "testing"])
        elif role == WorkerRole.TESTER:
            caps.extend(["testing", "qa", "bug_detection"])
        elif role == WorkerRole.RESEARCHER:
            caps.extend(["research", "information_gathering", "synthesis"])
        elif role == WorkerRole.OPTIMIZER:
            caps.extend(["optimization", "performance_tuning", "refactoring"])
        else:
            caps.extend(["general_purpose", "adaptable"])
        
        worker = Worker(
            worker_id=worker_id,
            role=role,
            state=WorkerState.IDLE,
            capabilities=list(set(caps)),
            created_at=now
        )
        
        with self._lock:
            self._workers[worker_id] = worker
            self._worker_pools[role].add(worker_id)
        
        return worker_id
    
    def submit_task(self, task_type: str, payload: Dict[str, Any],
                    priority: int = 5,
                    required_role: Optional[WorkerRole] = None,
                    required_capabilities: Optional[List[str]] = None) -> str:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            priority=priority,
            required_role=required_role,
            required_capabilities=required_capabilities or [],
            status=TaskStatus.PENDING,
            created_at=now
        )
        
        with self._lock:
            self._tasks[task_id] = task
        
        self._task_queue.put((priority, task_id))
        
        return task_id
    
    def _scheduler_loop(self):
        while self._running:
            try:
                priority, task_id = self._task_queue.get(timeout=1.0)
                
                with self._lock:
                    if task_id not in self._tasks:
                        continue
                    task = self._tasks[task_id]
                    
                    if task.status != TaskStatus.PENDING:
                        continue
                    
                    worker_id = self._find_best_worker(task)
                    
                    if worker_id:
                        self._assign_task(task_id, worker_id)
                    else:
                        self._task_queue.put((priority, task_id))
                
            except queue.Empty:
                continue
            except:
                pass
            
            time.sleep(0.1)
    
    def _find_best_worker(self, task: Task) -> Optional[str]:
        candidates = []
        
        if task.required_role:
            pool = self._worker_pools.get(task.required_role, set())
            for wid in pool:
                worker = self._workers.get(wid)
                if worker and worker.state == WorkerState.IDLE:
                    score = worker.performance_score
                    if all(cap in worker.capabilities for cap in task.required_capabilities):
                        score += 1.0
                    candidates.append((wid, score))
        else:
            for wid, worker in self._workers.items():
                if worker.state == WorkerState.IDLE:
                    score = worker.performance_score
                    matching_caps = sum(1 for cap in task.required_capabilities if cap in worker.capabilities)
                    score += matching_caps * 0.5
                    candidates.append((wid, score))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: -x[1])
        return candidates[0][0]
    
    def _assign_task(self, task_id: str, worker_id: str):
        task = self._tasks[task_id]
        worker = self._workers[worker_id]
        
        task.status = TaskStatus.ASSIGNED
        task.assigned_worker = worker_id
        task.started_at = datetime.utcnow().isoformat()
        
        worker.state = WorkerState.BUSY
        worker.current_task = task_id
        
        thread = threading.Thread(
            target=self._execute_task,
            args=(task_id, worker_id),
            daemon=True
        )
        self._worker_threads[task_id] = thread
        thread.start()
    
    def _execute_task(self, task_id: str, worker_id: str):
        task = self._tasks[task_id]
        worker = self._workers[worker_id]
        
        try:
            task.status = TaskStatus.RUNNING
            
            handler = self._task_handlers.get(task.task_type)
            
            if handler:
                result = handler(task.payload)
                task.result = result
                task.status = TaskStatus.COMPLETED
                worker.performance_score = min(2.0, worker.performance_score + 0.1)
            else:
                task.error = f"No handler for task type: {task.task_type}"
                task.status = TaskStatus.FAILED
                worker.performance_score = max(0.1, worker.performance_score - 0.1)
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            worker.performance_score = max(0.1, worker.performance_score - 0.1)
        
        finally:
            task.completed_at = datetime.utcnow().isoformat()
            worker.state = WorkerState.IDLE
            worker.current_task = None
            worker.completed_tasks.append(task_id)
    
    def register_task_handler(self, task_type: str, 
                              handler: Callable[[Dict], Any]):
        self._task_handlers[task_type] = handler
    
    def get_task_status(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)
    
    def get_worker_status(self, worker_id: str) -> Optional[Worker]:
        return self._workers.get(worker_id)
    
    def get_all_workers(self) -> List[Worker]:
        return list(self._workers.values())
    
    def get_active_tasks(self) -> List[Task]:
        return [
            t for t in self._tasks.values()
            if t.status in [TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.RUNNING]
        ]
    
    def cancel_task(self, task_id: str) -> bool:
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return False
            
            task.status = TaskStatus.CANCELLED
            
            if task.assigned_worker:
                worker = self._workers.get(task.assigned_worker)
                if worker:
                    worker.state = WorkerState.IDLE
                    worker.current_task = None
            
            return True
    
    def get_stats(self) -> Dict:
        with self._lock:
            total_tasks = len(self._tasks)
            completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
            failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)
            pending = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
            running = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
            
            idle_workers = sum(1 for w in self._workers.values() if w.state == WorkerState.IDLE)
            busy_workers = sum(1 for w in self._workers.values() if w.state == WorkerState.BUSY)
            
            return {
                "total_tasks": total_tasks,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "running": running,
                "total_workers": len(self._workers),
                "idle_workers": idle_workers,
                "busy_workers": busy_workers,
                "avg_performance": sum(w.performance_score for w in self._workers.values()) / len(self._workers) if self._workers else 0
            }
