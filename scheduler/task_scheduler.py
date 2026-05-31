from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
import asyncio
import json
import uuid

@dataclass
class ScheduledTask:
    task_id: str
    name: str
    task_type: str
    schedule: str
    action: Dict[str, Any]
    enabled: bool
    created_at: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

class TaskScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.running = False
    
    def start(self):
        if not self.running:
            self.scheduler.start()
            self.running = True
    
    def stop(self):
        if self.running:
            self.scheduler.shutdown()
            self.running = False
    
    def register_handler(self, task_type: str, handler: Callable):
        self.task_handlers[task_type] = handler
    
    def create_task(self, name: str, task_type: str, schedule: str, action: Dict, enabled: bool = True) -> str:
        task_id = str(uuid.uuid4())[:8]
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_type=task_type,
            schedule=schedule,
            action=action,
            enabled=enabled,
            created_at=datetime.now().isoformat()
        )
        
        self.tasks[task_id] = task
        
        if enabled:
            self._schedule_job(task)
        
        return task_id
    
    def _schedule_job(self, task: ScheduledTask):
        if task.schedule.startswith('cron:'):
            cron_expr = task.schedule[5:]
            parts = cron_expr.split()
            if len(parts) == 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
            else:
                trigger = IntervalTrigger(minutes=60)
        elif task.schedule.startswith('interval:'):
            interval = int(task.schedule[9:])
            trigger = IntervalTrigger(minutes=interval)
        else:
            trigger = IntervalTrigger(minutes=60)
        
        self.scheduler.add_job(
            self._execute_task,
            trigger=trigger,
            id=task.task_id,
            args=[task.task_id],
            replace_existing=True
        )
    
    async def _execute_task(self, task_id: str):
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.last_run = datetime.now().isoformat()
        task.run_count += 1
        
        handler = self.task_handlers.get(task.task_type)
        if not handler:
            task.failure_count += 1
            return
        
        try:
            await handler(task.action)
            task.success_count += 1
        except Exception as e:
            task.failure_count += 1
            task.metadata['last_error'] = str(e)
    
    def enable_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.enabled = True
        self._schedule_job(task)
        return True
    
    def disable_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.enabled = False
        
        try:
            self.scheduler.remove_job(task_id)
        except:
            pass
        
        return True
    
    def delete_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        
        self.disable_task(task_id)
        del self.tasks[task_id]
        return True
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[ScheduledTask]:
        return list(self.tasks.values())
    
    def get_stats(self) -> Dict[str, Any]:
        total = len(self.tasks)
        enabled = sum(1 for t in self.tasks.values() if t.enabled)
        total_runs = sum(t.run_count for t in self.tasks.values())
        total_success = sum(t.success_count for t in self.tasks.values())
        
        return {
            "total_tasks": total,
            "enabled_tasks": enabled,
            "disabled_tasks": total - enabled,
            "total_runs": total_runs,
            "total_success": total_success,
            "total_failures": sum(t.failure_count for t in self.tasks.values()),
            "success_rate": total_success / max(1, total_runs)
        }
    
    def export_tasks(self, filepath: str):
        data = {
            "tasks": [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "task_type": t.task_type,
                    "schedule": t.schedule,
                    "action": t.action,
                    "enabled": t.enabled,
                    "created_at": t.created_at,
                    "run_count": t.run_count,
                    "success_count": t.success_count,
                    "failure_count": t.failure_count
                }
                for t in self.tasks.values()
            ]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_tasks(self, filepath: str):
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        for task_data in data.get('tasks', []):
            self.create_task(
                name=task_data['name'],
                task_type=task_data['task_type'],
                schedule=task_data['schedule'],
                action=task_data['action'],
                enabled=task_data.get('enabled', True)
            )
