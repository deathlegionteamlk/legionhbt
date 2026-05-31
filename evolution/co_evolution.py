import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import random
from .curriculum_agent import CurriculumAgent, TrainingTask
from .executor_agent import ExecutorAgent, ExecutionResult

@dataclass
class EvolutionCycle:
    cycle_id: int
    tasks_generated: int
    tasks_completed: int
    success_rate: float
    avg_difficulty: float
    curriculum_improvement: float
    executor_improvement: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class CompetitionResult:
    winner: str
    loser: str
    margin: float
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class SymbioticCompetition:
    def __init__(self):
        self.competition_history: List[CompetitionResult] = []
        self.curriculum_score = 0.0
        self.executor_score = 0.0
        self.balance_factor = 0.5
    
    def evaluate_competition(self, task: TrainingTask, result: ExecutionResult) -> CompetitionResult:
        task_difficulty = task.difficulty
        success = result.success
        execution_time = result.execution_time
        self_repairs = result.self_repair_attempts
        
        curriculum_points = task_difficulty * 10
        if success:
            curriculum_points += 5
        
        executor_points = 0
        if success:
            executor_points += task_difficulty * 15
            executor_points += max(0, 10 - execution_time / 60)
            executor_points -= self_repairs * 2
        
        self.curriculum_score += curriculum_points
        self.executor_score += executor_points
        
        if curriculum_points > executor_points:
            winner = "curriculum"
            margin = curriculum_points - executor_points
            reason = "Generated challenging tasks that tested executor limits"
        else:
            winner = "executor"
            margin = executor_points - curriculum_points
            reason = "Successfully completed tasks with minimal repairs"
        
        result = CompetitionResult(
            winner=winner,
            loser="executor" if winner == "curriculum" else "curriculum",
            margin=margin,
            reason=reason
        )
        self.competition_history.append(result)
        return result
    
    def get_balance_adjustment(self) -> Dict[str, float]:
        total_competitions = len(self.competition_history)
        if total_competitions < 5:
            return {"curriculum": 1.0, "executor": 1.0}
        
        curriculum_wins = sum(1 for c in self.competition_history if c.winner == "curriculum")
        executor_wins = total_competitions - curriculum_wins
        
        curriculum_ratio = curriculum_wins / total_competitions
        
        if curriculum_ratio > 0.6:
            return {"curriculum": 0.9, "executor": 1.1}
        elif curriculum_ratio < 0.4:
            return {"curriculum": 1.1, "executor": 0.9}
        return {"curriculum": 1.0, "executor": 1.0}

class CoEvolutionFramework:
    def __init__(self, device: str = "cpu"):
        self.curriculum_agent = CurriculumAgent(device)
        self.executor_agent = ExecutorAgent(device)
        self.competition = SymbioticCompetition()
        self.evolution_cycles: List[EvolutionCycle] = []
        self.current_cycle = 0
        self.running = False
        self.max_cycles = 1000
        self.target_success_rate = 0.75
        self.min_cycles = 10
    
    async def start_evolution(self, from_zero: bool = True):
        self.running = True
        
        if from_zero:
            self.curriculum_agent.current_difficulty = 0.1
            self.executor_agent.execution_history.clear()
        
        while self.running and self.current_cycle < self.max_cycles:
            await self._run_evolution_cycle()
            
            if self._should_stop():
                break
        
        return self.get_evolution_summary()
    
    async def _run_evolution_cycle(self):
        self.current_cycle += 1
        cycle_id = self.current_cycle
        
        executor_stats = self.executor_agent.get_performance_stats()
        
        tasks = []
        for _ in range(5):
            task = self.curriculum_agent.generate_task(executor_stats)
            tasks.append(task)
        
        completed = 0
        successful = 0
        
        for task in tasks:
            result = await self.executor_agent.execute_task(task)
            
            if result.success:
                successful += 1
                completed += 1
            else:
                completed += 1
            
            competition_result = self.competition.evaluate_competition(task, result)
            
            evaluation = self.curriculum_agent.evaluate_task_completion(task, {
                "success": result.success,
                "metrics": result.metrics
            })
        
        success_rate = successful / max(1, completed)
        avg_difficulty = sum(t.difficulty for t in tasks) / max(1, len(tasks))
        
        balance = self.competition.get_balance_adjustment()
        
        cycle = EvolutionCycle(
            cycle_id=cycle_id,
            tasks_generated=len(tasks),
            tasks_completed=completed,
            success_rate=success_rate,
            avg_difficulty=avg_difficulty,
            curriculum_improvement=balance["curriculum"],
            executor_improvement=balance["executor"]
        )
        
        self.evolution_cycles.append(cycle)
    
    def _should_stop(self) -> bool:
        if self.current_cycle < self.min_cycles:
            return False
        
        recent_cycles = self.evolution_cycles[-10:]
        if not recent_cycles:
            return False
        
        avg_success = sum(c.success_rate for c in recent_cycles) / len(recent_cycles)
        
        if avg_success >= self.target_success_rate:
            return True
        
        if self.current_cycle >= self.max_cycles:
            return True
        
        return False
    
    def stop_evolution(self):
        self.running = False
    
    def get_evolution_summary(self) -> Dict:
        if not self.evolution_cycles:
            return {"status": "not_started", "cycles": 0}
        
        recent = self.evolution_cycles[-10:] if len(self.evolution_cycles) >= 10 else self.evolution_cycles
        
        return {
            "status": "completed" if not self.running else "running",
            "total_cycles": self.current_cycle,
            "final_success_rate": self.evolution_cycles[-1].success_rate,
            "average_success_rate": sum(c.success_rate for c in self.evolution_cycles) / len(self.evolution_cycles),
            "current_difficulty": self.curriculum_agent.current_difficulty,
            "curriculum_stats": self.curriculum_agent.get_curriculum_stats(),
            "executor_stats": self.executor_agent.get_performance_stats(),
            "competition_balance": self.competition.get_balance_adjustment(),
            "recent_cycles": [
                {
                    "cycle_id": c.cycle_id,
                    "success_rate": c.success_rate,
                    "avg_difficulty": c.avg_difficulty
                }
                for c in recent
            ]
        }
    
    def export_evolution_state(self, filepath: str):
        data = {
            "cycles": [
                {
                    "cycle_id": c.cycle_id,
                    "tasks_generated": c.tasks_generated,
                    "tasks_completed": c.tasks_completed,
                    "success_rate": c.success_rate,
                    "avg_difficulty": c.avg_difficulty,
                    "timestamp": c.timestamp
                }
                for c in self.evolution_cycles
            ],
            "curriculum": self.curriculum_agent.get_curriculum_stats(),
            "executor": self.executor_agent.get_performance_stats(),
            "competition": [
                {
                    "winner": c.winner,
                    "margin": c.margin,
                    "reason": c.reason
                }
                for c in self.competition.competition_history
            ],
            "summary": self.get_evolution_summary()
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_best_performing_tasks(self, n: int = 10) -> List[Dict]:
        successful_tasks = [
            {
                "task_id": result.task_id,
                "success": result.success,
                "execution_time": result.execution_time,
                "tools_used": result.tools_used,
                "metrics": result.metrics
            }
            for result in self.executor_agent.execution_history
            if result.success
        ]
        
        successful_tasks.sort(key=lambda x: x["metrics"].get("efficiency", 0), reverse=True)
        return successful_tasks[:n]
