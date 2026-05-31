import torch
import torch.nn as nn
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import random
import json

@dataclass
class TrainingTask:
    task_id: str
    difficulty: float
    task_type: str
    description: str
    expected_output: str
    validation_criteria: Dict[str, Any]
    tools_required: List[str]
    created_at: str
    success_rate: float = 0.0
    attempts: int = 0

class TaskGenerator(nn.Module):
    def __init__(self, input_dim: int = 128, hidden_dim: int = 256, output_dim: int = 128):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        self.difficulty_head = nn.Linear(hidden_dim, 1)
        self.type_head = nn.Linear(hidden_dim, 10)
        self.description_decoder = nn.LSTM(hidden_dim, hidden_dim, 2, batch_first=True)
        self.output_proj = nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x):
        encoded = self.encoder(x)
        difficulty = torch.sigmoid(self.difficulty_head(encoded))
        task_type_logits = self.type_head(encoded)
        return difficulty, task_type_logits, encoded

class CurriculumAgent:
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.task_generator = TaskGenerator().to(device)
        self.tasks: List[TrainingTask] = []
        self.task_history: List[Dict] = []
        self.current_difficulty = 0.1
        self.success_threshold = 0.7
        self.difficulty_increment = 0.1
        self.task_types = [
            "reconnaissance", "vulnerability_scan", "exploit_development",
            "privilege_escalation", "lateral_movement", "data_exfiltration",
            "persistence", "defense_evasion", "credential_access", "discovery"
        ]
        self.tools_catalog = {
            "reconnaissance": ["nmap", "masscan", "theharvester", "shodan"],
            "vulnerability_scan": ["nessus", "openvas", "nikto", "burpsuite"],
            "exploit_development": ["metasploit", "msfvenom", "searchsploit"],
            "privilege_escalation": ["linpeas", "winpeas", "powerup"],
            "lateral_movement": ["psexec", "wmiexec", "crackmapexec"],
            "data_exfiltration": ["dnscat2", "iodine", "hping3"],
            "persistence": ["mimikatz", " Empire", "chisel"],
            "defense_evasion": ["veil", "shellter", "unicorn"],
            "credential_access": ["hashcat", "john", "hydra"],
            "discovery": ["bloodhound", "ldapdomaindump", "pingcastle"]
        }
    
    def generate_task(self, executor_performance: Optional[Dict] = None) -> TrainingTask:
        if executor_performance:
            self._update_difficulty(executor_performance)
        
        task_type = random.choice(self.task_types)
        difficulty = self.current_difficulty + random.uniform(-0.05, 0.05)
        difficulty = max(0.0, min(1.0, difficulty))
        
        description = self._generate_description(task_type, difficulty)
        expected_output = self._generate_expected_output(task_type, difficulty)
        validation_criteria = self._generate_validation_criteria(task_type)
        tools_required = random.sample(
            self.tools_catalog.get(task_type, ["nmap"]),
            k=min(3, len(self.tools_catalog.get(task_type, ["nmap"])))
        )
        
        task = TrainingTask(
            task_id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}",
            difficulty=difficulty,
            task_type=task_type,
            description=description,
            expected_output=expected_output,
            validation_criteria=validation_criteria,
            tools_required=tools_required,
            created_at=datetime.now().isoformat()
        )
        
        self.tasks.append(task)
        return task
    
    def _update_difficulty(self, performance: Dict):
        success_rate = performance.get("success_rate", 0.0)
        
        if success_rate > self.success_threshold:
            self.current_difficulty = min(1.0, self.current_difficulty + self.difficulty_increment)
        elif success_rate < 0.3:
            self.current_difficulty = max(0.0, self.current_difficulty - self.difficulty_increment)
    
    def _generate_description(self, task_type: str, difficulty: float) -> str:
        templates = {
            "reconnaissance": [
                "Perform network reconnaissance on target subnet",
                "Identify live hosts and open ports",
                "Map network topology and services"
            ],
            "vulnerability_scan": [
                "Scan for known vulnerabilities",
                "Identify misconfigurations",
                "Assess security posture"
            ],
            "exploit_development": [
                "Develop proof-of-concept exploit",
                "Create custom payload",
                "Bypass security controls"
            ],
            "privilege_escalation": [
                "Escalate from user to admin",
                "Identify privilege escalation vectors",
                "Exploit misconfigured permissions"
            ],
            "lateral_movement": [
                "Move laterally through network",
                "Compromise additional hosts",
                "Establish pivot points"
            ],
            "data_exfiltration": [
                "Extract sensitive data",
                "Establish covert channel",
                "Bypass DLP controls"
            ],
            "persistence": [
                "Establish persistence mechanism",
                "Create backdoor access",
                "Maintain long-term access"
            ],
            "defense_evasion": [
                "Evade antivirus detection",
                "Bypass application whitelisting",
                "Obfuscate malicious activity"
            ],
            "credential_access": [
                "Dump credentials from memory",
                "Crack password hashes",
                "Harvest authentication tokens"
            ],
            "discovery": [
                "Enumerate domain resources",
                "Map trust relationships",
                "Identify high-value targets"
            ]
        }
        
        task_templates = templates.get(task_type, ["Perform security assessment"])
        base_desc = random.choice(task_templates)
        
        if difficulty > 0.7:
            return f"Advanced: {base_desc} under time constraints with active defense"
        elif difficulty > 0.4:
            return f"Intermediate: {base_desc} with partial information"
        else:
            return f"Beginner: {base_desc} with full access and documentation"
    
    def _generate_expected_output(self, task_type: str, difficulty: float) -> str:
        outputs = {
            "reconnaissance": "List of live hosts, open ports, service versions",
            "vulnerability_scan": "Vulnerability report with CVSS scores",
            "exploit_development": "Working exploit code and demonstration",
            "privilege_escalation": "Root/administrator access obtained",
            "lateral_movement": "Access to additional network segments",
            "data_exfiltration": "Sensitive data extracted successfully",
            "persistence": "Persistent backdoor installed and verified",
            "defense_evasion": "Malware executed without detection",
            "credential_access": "Valid credentials obtained",
            "discovery": "Complete asset inventory and mapping"
        }
        return outputs.get(task_type, "Task completed successfully")
    
    def _generate_validation_criteria(self, task_type: str) -> Dict[str, Any]:
        return {
            "success_indicators": ["access_granted", "data_extracted", "privilege_elevated"],
            "failure_indicators": ["access_denied", "detection_triggered", "timeout"],
            "metrics": ["execution_time", "stealth_score", "completeness"],
            "required_evidence": ["screenshot", "command_output", "log_entries"]
        }
    
    def evaluate_task_completion(self, task: TrainingTask, result: Dict) -> Dict:
        success = result.get("success", False)
        task.attempts += 1
        
        if success:
            task.success_rate = (task.success_rate * (task.attempts - 1) + 1) / task.attempts
        else:
            task.success_rate = (task.success_rate * (task.attempts - 1)) / task.attempts
        
        evaluation = {
            "task_id": task.task_id,
            "success": success,
            "success_rate": task.success_rate,
            "difficulty": task.difficulty,
            "metrics": result.get("metrics", {}),
            "recommendations": self._generate_recommendations(task, result)
        }
        
        self.task_history.append(evaluation)
        return evaluation
    
    def _generate_recommendations(self, task: TrainingTask, result: Dict) -> List[str]:
        recommendations = []
        
        if not result.get("success"):
            if task.difficulty > 0.5:
                recommendations.append("Consider reducing task difficulty")
            if result.get("error_type") == "timeout":
                recommendations.append("Increase time allocation for this task type")
            if result.get("error_type") == "tool_failure":
                recommendations.append("Review tool configuration and prerequisites")
        
        if task.success_rate > 0.8:
            recommendations.append("Ready for increased difficulty")
        
        return recommendations
    
    def get_curriculum_stats(self) -> Dict:
        if not self.tasks:
            return {"total_tasks": 0, "average_difficulty": 0, "average_success_rate": 0}
        
        return {
            "total_tasks": len(self.tasks),
            "average_difficulty": sum(t.difficulty for t in self.tasks) / len(self.tasks),
            "average_success_rate": sum(t.success_rate for t in self.tasks) / len(self.tasks),
            "current_difficulty": self.current_difficulty,
            "task_type_distribution": self._get_type_distribution()
        }
    
    def _get_type_distribution(self) -> Dict[str, int]:
        distribution = {}
        for task in self.tasks:
            distribution[task.task_type] = distribution.get(task.task_type, 0) + 1
        return distribution
    
    def export_curriculum(self, filepath: str):
        data = {
            "tasks": [self._task_to_dict(t) for t in self.tasks],
            "history": self.task_history,
            "stats": self.get_curriculum_stats()
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def _task_to_dict(self, task: TrainingTask) -> Dict:
        return {
            "task_id": task.task_id,
            "difficulty": task.difficulty,
            "task_type": task.task_type,
            "description": task.description,
            "expected_output": task.expected_output,
            "tools_required": task.tools_required,
            "success_rate": task.success_rate,
            "attempts": task.attempts
        }
