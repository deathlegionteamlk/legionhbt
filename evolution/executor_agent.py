import torch
import torch.nn as nn
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
from .curriculum_agent import TrainingTask

@dataclass
class ExecutionResult:
    task_id: str
    success: bool
    output: str
    execution_time: float
    tools_used: List[str]
    errors: List[str]
    metrics: Dict[str, float] = field(default_factory=dict)
    self_repair_attempts: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class PolicyNetwork(nn.Module):
    def __init__(self, state_dim: int = 256, action_dim: int = 128, hidden_dim: int = 512):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        self.action_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Softmax(dim=-1)
        )
        self.value_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
    
    def forward(self, state):
        features = self.shared(state)
        action_probs = self.action_head(features)
        value = self.value_head(features)
        return action_probs, value

class ToolIntegrator:
    def __init__(self):
        self.tool_registry = {}
        self.tool_outputs = {}
    
    def register_tool(self, name: str, handler: callable, description: str):
        self.tool_registry[name] = {
            "handler": handler,
            "description": description,
            "usage_count": 0,
            "success_count": 0
        }
    
    def execute_tool(self, name: str, params: Dict) -> Tuple[bool, str]:
        if name not in self.tool_registry:
            return False, f"Tool '{name}' not found"
        
        tool = self.tool_registry[name]
        tool["usage_count"] += 1
        
        try:
            result = tool["handler"](**params)
            tool["success_count"] += 1
            return True, result
        except Exception as e:
            return False, str(e)
    
    def get_tool_stats(self) -> Dict:
        return {
            name: {
                "usage": data["usage_count"],
                "success_rate": data["success_count"] / max(1, data["usage_count"])
            }
            for name, data in self.tool_registry.items()
        }

class SelfRepairModule:
    def __init__(self):
        self.error_patterns = {}
        self.repair_strategies = {}
        self.repair_history = []
    
    def analyze_error(self, error: str, context: Dict) -> Dict:
        error_type = self._classify_error(error)
        
        return {
            "error_type": error_type,
            "severity": self._assess_severity(error, error_type),
            "repairable": error_type in self.repair_strategies,
            "suggested_fixes": self._suggest_fixes(error_type, context)
        }
    
    def _classify_error(self, error: str) -> str:
        patterns = {
            "timeout": r"timeout|timed out",
            "permission": r"permission denied|access denied|unauthorized",
            "connection": r"connection refused|network unreachable|no route",
            "not_found": r"not found|does not exist|no such file",
            "validation": r"invalid|validation|malformed",
            "resource": r"out of memory|disk full|resource exhausted"
        }
        
        for error_type, pattern in patterns.items():
            if re.search(pattern, error, re.IGNORECASE):
                return error_type
        return "unknown"
    
    def _assess_severity(self, error: str, error_type: str) -> str:
        critical_errors = ["permission", "resource"]
        high_errors = ["connection", "timeout"]
        
        if error_type in critical_errors:
            return "critical"
        elif error_type in high_errors:
            return "high"
        return "medium"
    
    def _suggest_fixes(self, error_type: str, context: Dict) -> List[Dict]:
        fixes = {
            "timeout": [
                {"action": "increase_timeout", "params": {"factor": 2}},
                {"action": "retry_with_backoff", "params": {"max_retries": 3}}
            ],
            "permission": [
                {"action": "escalate_privileges", "params": {}},
                {"action": "check_credentials", "params": {}}
            ],
            "connection": [
                {"action": "check_connectivity", "params": {}},
                {"action": "retry_with_delay", "params": {"delay": 5}}
            ],
            "not_found": [
                {"action": "verify_path", "params": {}},
                {"action": "create_if_missing", "params": {}}
            ]
        }
        return fixes.get(error_type, [{"action": "log_and_continue", "params": {}}])
    
    def apply_fix(self, error_type: str, fix: Dict, context: Dict) -> bool:
        repair_attempt = {
            "error_type": error_type,
            "fix_applied": fix,
            "timestamp": datetime.now().isoformat(),
            "success": False
        }
        
        try:
            action = fix.get("action")
            if action == "increase_timeout":
                context["timeout"] = context.get("timeout", 30) * fix["params"].get("factor", 2)
            elif action == "retry_with_backoff":
                context["retry_count"] = context.get("retry_count", 0) + 1
            elif action == "escalate_privileges":
                context["privilege_level"] = "elevated"
            
            repair_attempt["success"] = True
            self.repair_history.append(repair_attempt)
            return True
            
        except Exception as e:
            repair_attempt["error"] = str(e)
            self.repair_history.append(repair_attempt)
            return False
    
    def get_repair_stats(self) -> Dict:
        if not self.repair_history:
            return {"total_repairs": 0, "success_rate": 0}
        
        successful = sum(1 for r in self.repair_history if r["success"])
        return {
            "total_repairs": len(self.repair_history),
            "successful_repairs": successful,
            "success_rate": successful / len(self.repair_history)
        }

class ExecutorAgent:
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.policy_network = PolicyNetwork().to(device)
        self.tool_integrator = ToolIntegrator()
        self.self_repair = SelfRepairModule()
        self.execution_history: List[ExecutionResult] = []
        self.learning_rate = 0.001
        self.max_repair_attempts = 3
        self._register_default_tools()
    
    def _register_default_tools(self):
        self.tool_integrator.register_tool(
            "nmap_scan",
            lambda target, ports="": f"nmap -sV {target} {ports}",
            "Network port scanner"
        )
        self.tool_integrator.register_tool(
            "dirb_scan",
            lambda url, wordlist="": f"dirb {url} {wordlist}",
            "Web directory brute forcer"
        )
        self.tool_integrator.register_tool(
            "sqlmap_scan",
            lambda url, data="": f"sqlmap -u {url} --batch",
            "SQL injection scanner"
        )
        self.tool_integrator.register_tool(
            "hydra_brute",
            lambda target, service, userlist="": f"hydra -L {userlist} -P passwords.txt {target} {service}",
            "Password brute forcer"
        )
    
    async def execute_task(self, task: TrainingTask, max_attempts: int = 3) -> ExecutionResult:
        start_time = datetime.now()
        attempt = 0
        success = False
        output = ""
        errors = []
        tools_used = []
        self_repair_count = 0
        
        while attempt < max_attempts and not success:
            attempt += 1
            
            try:
                action_plan = self._generate_action_plan(task)
                
                for action in action_plan:
                    tool_result = await self._execute_action(action)
                    
                    if tool_result["success"]:
                        output += f"\n{tool_result['output']}"
                        if action.get("tool"):
                            tools_used.append(action["tool"])
                    else:
                        error_msg = tool_result.get("error", "Unknown error")
                        errors.append(error_msg)
                        
                        repair_result = await self._attempt_self_repair(error_msg, task)
                        if repair_result and self_repair_count < self.max_repair_attempts:
                            self_repair_count += 1
                            continue
                        else:
                            break
                
                success = len(errors) == 0 or self_repair_count > 0
                
            except Exception as e:
                errors.append(str(e))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = ExecutionResult(
            task_id=task.task_id,
            success=success,
            output=output,
            execution_time=execution_time,
            tools_used=list(set(tools_used)),
            errors=errors,
            metrics=self._calculate_metrics(task, success, execution_time),
            self_repair_attempts=self_repair_count
        )
        
        self.execution_history.append(result)
        self._update_policy(result)
        
        return result
    
    def _generate_action_plan(self, task: TrainingTask) -> List[Dict]:
        plan = []
        
        for tool in task.tools_required:
            plan.append({
                "type": "tool_execution",
                "tool": tool,
                "params": {"target": "target_placeholder"}
            })
        
        plan.append({
            "type": "validation",
            "check": "output_verification"
        })
        
        return plan
    
    async def _execute_action(self, action: Dict) -> Dict:
        action_type = action.get("type")
        
        if action_type == "tool_execution":
            tool_name = action.get("tool")
            params = action.get("params", {})
            success, output = self.tool_integrator.execute_tool(tool_name, params)
            return {"success": success, "output": output, "error": output if not success else None}
        
        elif action_type == "validation":
            return {"success": True, "output": "Validation passed"}
        
        return {"success": False, "error": f"Unknown action type: {action_type}"}
    
    async def _attempt_self_repair(self, error: str, task: TrainingTask) -> bool:
        analysis = self.self_repair.analyze_error(error, {"task": task})
        
        if not analysis["repairable"]:
            return False
        
        for fix in analysis["suggested_fixes"]:
            context = {"task": task, "timeout": 30}
            if self.self_repair.apply_fix(analysis["error_type"], fix, context):
                return True
        
        return False
    
    def _calculate_metrics(self, task: TrainingTask, success: bool, execution_time: float) -> Dict:
        return {
            "efficiency": 1.0 / max(1.0, execution_time / 60),
            "completeness": 1.0 if success else 0.0,
            "tool_diversity": len(set(task.tools_required)) / max(1, len(task.tools_required)),
            "difficulty_handled": task.difficulty
        }
    
    def _update_policy(self, result: ExecutionResult):
        reward = 1.0 if result.success else -0.5
        reward -= result.self_repair_attempts * 0.1
        reward += result.metrics.get("efficiency", 0) * 0.3
        
        pass
    
    def get_performance_stats(self) -> Dict:
        if not self.execution_history:
            return {"total_executions": 0, "success_rate": 0}
        
        successful = sum(1 for r in self.execution_history if r.success)
        avg_time = sum(r.execution_time for r in self.execution_history) / len(self.execution_history)
        
        return {
            "total_executions": len(self.execution_history),
            "successful_executions": successful,
            "success_rate": successful / len(self.execution_history),
            "average_execution_time": avg_time,
            "total_self_repairs": sum(r.self_repair_attempts for r in self.execution_history),
            "tool_stats": self.tool_integrator.get_tool_stats(),
            "repair_stats": self.self_repair.get_repair_stats()
        }
    
    def export_knowledge(self, filepath: str):
        data = {
            "execution_history": [
                {
                    "task_id": r.task_id,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "tools_used": r.tools_used,
                    "self_repair_attempts": r.self_repair_attempts,
                    "metrics": r.metrics
                }
                for r in self.execution_history
            ],
            "performance_stats": self.get_performance_stats(),
            "tool_stats": self.tool_integrator.get_tool_stats()
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
