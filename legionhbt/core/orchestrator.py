import os
import json
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from ..components.c1_engagement_graph import C1EngagementGraph, EngagementState, EngagementPriority
from ..components.c2_audit_log import C2AuditLog, AuditEventType
from ..components.c3_risk_layer import C3RiskLayer, RiskLevel, ActionType
from ..components.c4_self_monitor import C4SelfMonitor, GateDecision
from ..components.c5_ultraplan import C5ULTRAPLAN, PlanStatus
from ..components.c6_coordinator import C6Coordinator, WorkerRole, TaskStatus
from ..components.c7_corroboration import C7Corroboration, CorroborationStatus
from ..components.c8_poc_verification import C8PoCVerification, PoCStatus
from ..components.c9_variant_hunter import C9VariantHunter, VariantStatus
from ..components.c10_chain_builder import C10ChainBuilder, ChainStatus
from ..components.c11_fixer import C11Fixer, FixStatus, FixType
from ..components.c12_speculation import C12SpeculationLayer, SpeculationStatus
from ..utils.safetensor_utils import SafetensorManager
from .config import Config


class LegionHBTOrchestrator:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        
        self.c1_engagement = C1EngagementGraph(self.config.db_path)
        self.c2_audit = C2AuditLog(self.config.audit_log_path)
        self.c3_risk = C3RiskLayer(self.config.risk_high_threshold, self.config.risk_medium_threshold)
        self.c4_monitor = C4SelfMonitor()
        self.c5_ultraplan = C5ULTRAPLAN()
        self.c6_coordinator = C6Coordinator(self.config.max_workers)
        self.c7_corroboration = C7Corroboration(self.config.corroboration_threshold)
        self.c8_poc = C8PoCVerification()
        self.c9_variant = C9VariantHunter()
        self.c10_chain = C10ChainBuilder()
        self.c11_fixer = C11Fixer()
        self.c12_speculation = C12SpeculationLayer()
        self.safetensor = SafetensorManager(self.config.models_dir)
        
        self._running = False
        self._autonomous_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        self._setup_integrations()
    
    def _setup_integrations(self):
        self.c4_monitor.add_deliberation_hook(self._deliberation_callback)
        self.c6_coordinator.register_task_handler("process_node", self._process_node_task)
        self.c6_coordinator.register_task_handler("verify_poc", self._verify_poc_task)
        self.c6_coordinator.register_task_handler("corroborate", self._corroborate_task)
        self.c10_chain.register_link_handler("execute_action", self._chain_action_handler)
    
    def start(self):
        with self._lock:
            if self._running:
                return
            
            self._running = True
            self.c4_monitor.start_monitoring()
            self.c6_coordinator.start()
            
            self.c2_audit.log(
                AuditEventType.SYSTEM_START,
                "orchestrator",
                "system_start",
                payload={"timestamp": datetime.utcnow().isoformat()}
            )
            
            if self.config.enable_autonomous:
                self._autonomous_thread = threading.Thread(target=self._autonomous_loop, daemon=True)
                self._autonomous_thread.start()
    
    def stop(self):
        with self._lock:
            self._running = False
            
            self.c4_monitor.stop_monitoring()
            self.c6_coordinator.stop()
            
            self.c2_audit.log(
                AuditEventType.SYSTEM_STOP,
                "orchestrator",
                "system_stop",
                payload={"timestamp": datetime.utcnow().isoformat()}
            )
    
    def _autonomous_loop(self):
        import time
        while self._running:
            try:
                self._process_pending_engagements()
            except:
                pass
            time.sleep(1.0)
    
    def _process_pending_engagements(self):
        pending = self.c1_engagement.get_pending_engagements()
        
        for node in pending[:5]:
            gate_check = self.c4_monitor.deliberative_gate(node.node_id, {
                "risk_score": node.risk_score,
                "node_type": node.node_type
            })
            
            if gate_check.decision == GateDecision.BLOCK:
                self.c1_engagement.update_node_state(node.node_id, EngagementState.SUSPENDED, node.risk_score)
                continue
            
            self.c1_engagement.update_node_state(node.node_id, EngagementState.ACTIVE, node.risk_score)
            
            self.c6_coordinator.submit_task(
                "process_node",
                {"node_id": node.node_id, "gate_decision": gate_check.decision.value},
                priority=node.priority.value
            )
    
    def _deliberation_callback(self, node_id: str, context: Dict):
        risk_score = context.get("risk_score", 0.0)
        
        if risk_score > 0.8:
            variants = self.c9_variant.hunt_variants(node_id, context)
            if variants:
                return self.c4_monitor.deliberative_gate(node_id, {**context, "variants": variants})
        
        return None
    
    def _process_node_task(self, payload: Dict) -> Any:
        node_id = payload.get("node_id")
        node = self.c1_engagement.get_node(node_id)
        
        if not node:
            return {"error": "Node not found"}
        
        self.c2_audit.log(
            AuditEventType.NODE_UPDATED,
            "c6_coordinator",
            "process_node",
            node_id=node_id,
            payload={"status": "processing"}
        )
        
        self.c1_engagement.update_node_state(node_id, EngagementState.PROCESSING, node.risk_score)
        
        plan_id = self.c5_ultraplan.create_plan(
            f"Process {node.node_type}",
            f"Execute {node.node_type} node",
            self.c5_ultraplan.decompose_objective(node.node_type)
        )
        
        self.c5_ultraplan.optimize_plan(plan_id)
        
        result = {"node_id": node_id, "plan_id": plan_id, "status": "completed"}
        
        self.c1_engagement.update_node_state(node_id, EngagementState.COMPLETED, node.risk_score)
        
        self.c2_audit.log(
            AuditEventType.NODE_COMPLETED,
            "c6_coordinator",
            "process_node",
            node_id=node_id,
            payload={"plan_id": plan_id}
        )
        
        return result
    
    def _verify_poc_task(self, payload: Dict) -> Any:
        poc_id = payload.get("poc_id")
        result = self.c8_poc.verify_poc(poc_id)
        return {
            "poc_id": poc_id,
            "status": result.status.value,
            "verified": result.status == PoCStatus.VERIFIED
        }
    
    def _corroborate_task(self, payload: Dict) -> Any:
        query = payload.get("query", "")
        result = self.c7_corroboration.query_with_corroboration(query)
        return {
            "query_id": result.query_id,
            "consensus": result.status == CorroborationStatus.CONSENSUS,
            "answer": result.consensus_answer,
            "agreement": result.agreement_score
        }
    
    def _chain_action_handler(self, params: Dict, context: Dict) -> Any:
        action_type = params.get("action_type")
        
        if action_type == "create_node":
            node_id = self.c1_engagement.create_node(
                params.get("node_type", "generic"),
                params.get("payload", {}),
                EngagementPriority(params.get("priority", 2))
            )
            return {"node_id": node_id}
        
        elif action_type == "verify":
            poc_id = self.c8_poc.create_poc(
                params.get("name", "verification"),
                params.get("description", ""),
                self.c8_poc.poc_type.CODE_EXECUTION,
                params.get("code", "")
            )
            result = self.c8_poc.verify_poc(poc_id)
            return {"poc_id": poc_id, "verified": result.status == PoCStatus.VERIFIED}
        
        return {"status": "unknown_action"}
    
    def submit_engagement(self, node_type: str, payload: Dict,
                          priority: int = 2) -> str:
        node_id = self.c1_engagement.create_node(
            node_type,
            payload,
            EngagementPriority(priority)
        )
        
        self.c2_audit.log(
            AuditEventType.NODE_CREATED,
            "orchestrator",
            "submit_engagement",
            node_id=node_id,
            payload={"node_type": node_type, "priority": priority}
        )
        
        return node_id
    
    def get_system_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "monitor": self.c4_monitor.get_health_report(),
            "coordinator": self.c6_coordinator.get_stats(),
            "engagements": {
                "pending": len(self.c1_engagement.get_pending_engagements()),
                "active": len(self.c1_engagement.get_active_engagements())
            },
            "audit_integrity": self.c2_audit.verify_chain(),
            "speculation_layer": self.c12_speculation.get_active_layer()
        }
    
    def execute_chain(self, chain_id: str, context: Optional[Dict] = None) -> Dict:
        return self.c10_chain.execute_chain(chain_id, context)
    
    def create_fix(self, target_id: str, issue: str, 
                   fix_type: str, context: Dict) -> str:
        fix_type_enum = FixType(fix_type) if fix_type in [f.value for f in FixType] else FixType.CODE_PATCH
        return self.c11_fixer.identify_fix(target_id, issue, fix_type_enum, context)
    
    def apply_fix(self, fix_id: str) -> bool:
        return self.c11_fixer.apply_fix(fix_id)
    
    def create_speculation(self, name: str) -> str:
        return self.c12_speculation.create_layer(name)
    
    def commit_speculation(self, layer_id: str) -> bool:
        return self.c12_speculation.commit_layer(layer_id)
    
    def get_engagement(self, node_id: str) -> Optional[Dict]:
        node = self.c1_engagement.get_node(node_id)
        if not node:
            return None
        return {
            "node_id": node.node_id,
            "type": node.node_type,
            "state": node.state.value,
            "priority": node.priority.value,
            "risk_score": node.risk_score,
            "created_at": node.created_at,
            "updated_at": node.updated_at
        }
    
    def list_engagements(self, state: Optional[str] = None) -> List[Dict]:
        if state:
            nodes = self.c1_engagement.get_nodes_by_state(EngagementState(state))
        else:
            nodes = []
            for s in EngagementState:
                nodes.extend(self.c1_engagement.get_nodes_by_state(s))
        
        return [
            {
                "node_id": n.node_id,
                "type": n.node_type,
                "state": n.state.value,
                "priority": n.priority.value,
                "risk_score": n.risk_score
            }
            for n in nodes
        ]
