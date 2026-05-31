import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class MonitorState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    RECOVERING = "recovering"


class GateDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    DELIBERATE = "deliberate"
    ESCALATE = "escalate"


@dataclass
class SystemMetric:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    active_nodes: int
    pending_nodes: int
    error_rate: float
    throughput: float


@dataclass
class GateCheck:
    check_id: str
    timestamp: str
    node_id: str
    decision: GateDecision
    confidence: float
    reasoning: List[str]
    overrides: Dict[str, Any]


class C4SelfMonitor:
    def __init__(self, check_interval: float = 5.0):
        self.check_interval = check_interval
        self._state = MonitorState.HEALTHY
        self._metrics_history: List[SystemMetric] = []
        self._gate_history: List[GateCheck] = []
        self._thresholds = {
            "cpu_critical": 90.0,
            "cpu_warning": 70.0,
            "memory_critical": 90.0,
            "memory_warning": 75.0,
            "error_rate_critical": 0.1,
            "error_rate_warning": 0.05,
            "max_pending": 100
        }
        self._gate_rules: List[Callable[[str, Dict], GateDecision]] = []
        self._deliberation_hooks: List[Callable[[str, Dict], GateCheck]] = []
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._error_count = 0
        self._total_operations = 0
    
    def start_monitoring(self):
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)
    
    def _monitor_loop(self):
        while self._running:
            try:
                self._collect_metrics()
                self._evaluate_health()
            except:
                pass
            time.sleep(self.check_interval)
    
    def _collect_metrics(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent
        except:
            cpu = 0.0
            memory = 0.0
        
        metric = SystemMetric(
            timestamp=datetime.utcnow().isoformat(),
            cpu_percent=cpu,
            memory_percent=memory,
            active_nodes=0,
            pending_nodes=0,
            error_rate=self._calculate_error_rate(),
            throughput=self._calculate_throughput()
        )
        
        with self._lock:
            self._metrics_history.append(metric)
            if len(self._metrics_history) > 1000:
                self._metrics_history = self._metrics_history[-1000:]
    
    def _calculate_error_rate(self) -> float:
        if self._total_operations == 0:
            return 0.0
        return self._error_count / self._total_operations
    
    def _calculate_throughput(self) -> float:
        return 0.0
    
    def _evaluate_health(self):
        with self._lock:
            if not self._metrics_history:
                return
            
            latest = self._metrics_history[-1]
            
            if (latest.cpu_percent > self._thresholds["cpu_critical"] or
                latest.memory_percent > self._thresholds["memory_critical"] or
                latest.error_rate > self._thresholds["error_rate_critical"]):
                self._state = MonitorState.CRITICAL
            elif (latest.cpu_percent > self._thresholds["cpu_warning"] or
                  latest.memory_percent > self._thresholds["memory_warning"] or
                  latest.error_rate > self._thresholds["error_rate_warning"]):
                self._state = MonitorState.DEGRADED
            elif self._state == MonitorState.CRITICAL or self._state == MonitorState.DEGRADED:
                self._state = MonitorState.RECOVERING
            else:
                self._state = MonitorState.HEALTHY
    
    def get_state(self) -> MonitorState:
        return self._state
    
    def get_metrics(self, count: int = 100) -> List[SystemMetric]:
        with self._lock:
            return self._metrics_history[-count:]
    
    def record_operation(self, success: bool = True):
        with self._lock:
            self._total_operations += 1
            if not success:
                self._error_count += 1
    
    def deliberative_gate(self, node_id: str, context: Dict[str, Any]) -> GateCheck:
        check_id = f"gate_{node_id}_{int(time.time() * 1000)}"
        
        for rule in self._gate_rules:
            decision = rule(node_id, context)
            if decision == GateDecision.BLOCK:
                return GateCheck(
                    check_id=check_id,
                    timestamp=datetime.utcnow().isoformat(),
                    node_id=node_id,
                    decision=GateDecision.BLOCK,
                    confidence=1.0,
                    reasoning=["Blocked by rule"],
                    overrides={}
                )
        
        if self._state == MonitorState.CRITICAL:
            return GateCheck(
                check_id=check_id,
                timestamp=datetime.utcnow().isoformat(),
                node_id=node_id,
                decision=GateDecision.BLOCK,
                confidence=0.95,
                reasoning=["System in critical state"],
                overrides={}
            )
        
        risk_score = context.get("risk_score", 0.0)
        
        if risk_score > 0.8:
            decision = GateDecision.DELIBERATE
        elif risk_score > 0.5:
            decision = GateDecision.ESCALATE
        else:
            decision = GateDecision.ALLOW
        
        reasoning = []
        if risk_score > 0.5:
            reasoning.append(f"Elevated risk score: {risk_score}")
        if self._state == MonitorState.DEGRADED:
            reasoning.append("System degraded, extra caution")
        if context.get("requires_verification"):
            reasoning.append("Verification required by context")
        
        if not reasoning:
            reasoning.append("Standard operation")
        
        check = GateCheck(
            check_id=check_id,
            timestamp=datetime.utcnow().isoformat(),
            node_id=node_id,
            decision=decision,
            confidence=1.0 - (risk_score * 0.5),
            reasoning=reasoning,
            overrides=context.get("overrides", {})
        )
        
        if decision == GateDecision.DELIBERATE and self._deliberation_hooks:
            for hook in self._deliberation_hooks:
                hook_result = hook(node_id, context)
                if hook_result:
                    check = hook_result
                    break
        
        with self._lock:
            self._gate_history.append(check)
            if len(self._gate_history) > 1000:
                self._gate_history = self._gate_history[-1000:]
        
        return check
    
    def add_gate_rule(self, rule: Callable[[str, Dict], GateDecision]):
        self._gate_rules.append(rule)
    
    def add_deliberation_hook(self, hook: Callable[[str, Dict], Optional[GateCheck]]):
        self._deliberation_hooks.append(hook)
    
    def get_gate_history(self, count: int = 100) -> List[GateCheck]:
        with self._lock:
            return self._gate_history[-count:]
    
    def set_threshold(self, key: str, value: float):
        self._thresholds[key] = value
    
    def get_health_report(self) -> Dict:
        with self._lock:
            if not self._metrics_history:
                return {"state": self._state.value, "metrics": None}
            
            latest = self._metrics_history[-1]
            return {
                "state": self._state.value,
                "metrics": {
                    "cpu_percent": latest.cpu_percent,
                    "memory_percent": latest.memory_percent,
                    "error_rate": latest.error_rate,
                    "active_nodes": latest.active_nodes,
                    "pending_nodes": latest.pending_nodes
                },
                "thresholds": self._thresholds,
                "total_operations": self._total_operations,
                "error_count": self._error_count
            }
