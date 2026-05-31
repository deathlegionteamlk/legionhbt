from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import json


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    NETWORK = "network"
    SYSTEM = "system"


@dataclass
class RiskAssessment:
    action_id: str
    action_type: ActionType
    risk_level: RiskLevel
    risk_score: float
    factors: Dict[str, float]
    requires_approval: bool
    approvers_needed: int
    mitigation: List[str]


class C3RiskLayer:
    def __init__(self, high_threshold: float = 0.8, medium_threshold: float = 0.5):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold
        self._action_registry: Dict[str, Dict[str, Any]] = {}
        self._risk_handlers: Dict[ActionType, List[Callable]] = {
            ActionType.READ: [],
            ActionType.WRITE: [],
            ActionType.EXECUTE: [],
            ActionType.DELETE: [],
            ActionType.NETWORK: [],
            ActionType.SYSTEM: []
        }
        self._approval_callbacks: List[Callable[[RiskAssessment], bool]] = []
    
    def register_action(self, action_id: str, action_type: ActionType,
                        base_risk: float = 0.0, metadata: Optional[Dict] = None):
        self._action_registry[action_id] = {
            "type": action_type,
            "base_risk": base_risk,
            "metadata": metadata or {},
            "executed": False,
            "approved": False
        }
    
    def assess_risk(self, action_id: str, context: Optional[Dict] = None) -> RiskAssessment:
        if action_id not in self._action_registry:
            return RiskAssessment(
                action_id=action_id,
                action_type=ActionType.READ,
                risk_level=RiskLevel.HIGH,
                risk_score=1.0,
                factors={"unknown_action": 1.0},
                requires_approval=True,
                approvers_needed=2,
                mitigation=["Register action before execution"]
            )
        
        action = self._action_registry[action_id]
        action_type = action["type"]
        base_risk = action["base_risk"]
        ctx = context or {}
        
        factors = {}
        
        factors["base"] = base_risk
        
        if action_type == ActionType.EXECUTE:
            factors["execution"] = 0.3
        elif action_type == ActionType.DELETE:
            factors["deletion"] = 0.4
        elif action_type == ActionType.SYSTEM:
            factors["system"] = 0.5
        elif action_type == ActionType.NETWORK:
            factors["network"] = 0.25
        elif action_type == ActionType.WRITE:
            factors["write"] = 0.15
        else:
            factors["read"] = 0.05
        
        if ctx.get("target_critical", False):
            factors["critical_target"] = 0.3
        
        if ctx.get("irreversible", False):
            factors["irreversible"] = 0.2
        
        if ctx.get("data_sensitive", False):
            factors["sensitive_data"] = 0.25
        
        if ctx.get("scope_wide", False):
            factors["wide_scope"] = 0.15
        
        for handler in self._risk_handlers.get(action_type, []):
            handler_factors = handler(action_id, ctx)
            if handler_factors:
                factors.update(handler_factors)
        
        risk_score = min(1.0, sum(factors.values()))
        
        if risk_score >= self.high_threshold:
            risk_level = RiskLevel.HIGH
        elif risk_score >= self.medium_threshold:
            risk_level = RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.LOW
        
        requires_approval = risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        approvers_needed = 2 if risk_level == RiskLevel.CRITICAL else (1 if risk_level == RiskLevel.HIGH else 0)
        
        mitigation = self._generate_mitigation(action_type, factors, ctx)
        
        return RiskAssessment(
            action_id=action_id,
            action_type=action_type,
            risk_level=risk_level,
            risk_score=risk_score,
            factors=factors,
            requires_approval=requires_approval,
            approvers_needed=approvers_needed,
            mitigation=mitigation
        )
    
    def _generate_mitigation(self, action_type: ActionType, 
                             factors: Dict[str, float], 
                             context: Dict) -> List[str]:
        mitigation = []
        
        if "execution" in factors:
            mitigation.append("Execute in sandboxed environment")
            mitigation.append("Validate inputs before execution")
        
        if "deletion" in factors:
            mitigation.append("Create backup before deletion")
            mitigation.append("Require explicit confirmation")
        
        if "system" in factors:
            mitigation.append("Limit system privileges")
            mitigation.append("Audit all system calls")
        
        if "network" in factors:
            mitigation.append("Validate all outbound connections")
            mitigation.append("Use encrypted channels")
        
        if "sensitive_data" in factors:
            mitigation.append("Apply data encryption")
            mitigation.append("Minimize data exposure")
        
        if "irreversible" in factors:
            mitigation.append("Implement undo mechanism where possible")
            mitigation.append("Require multi-step confirmation")
        
        if not mitigation:
            mitigation.append("Standard safety protocols apply")
        
        return mitigation
    
    def request_approval(self, assessment: RiskAssessment) -> bool:
        if not assessment.requires_approval:
            return True
        
        approvals = 0
        for callback in self._approval_callbacks:
            if callback(assessment):
                approvals += 1
                if approvals >= assessment.approvers_needed:
                    return True
        
        return False
    
    def execute_with_risk_check(self, action_id: str, 
                                callback: Callable, 
                                context: Optional[Dict] = None) -> Any:
        assessment = self.assess_risk(action_id, context)
        
        if assessment.requires_approval:
            if not self.request_approval(assessment):
                raise PermissionError(f"Action {action_id} denied: insufficient approvals")
        
        self._action_registry[action_id]["approved"] = True
        
        try:
            result = callback()
            self._action_registry[action_id]["executed"] = True
            return result
        except Exception as e:
            self._action_registry[action_id]["error"] = str(e)
            raise
    
    def add_risk_handler(self, action_type: ActionType, 
                         handler: Callable[[str, Dict], Dict[str, float]]):
        self._risk_handlers[action_type].append(handler)
    
    def add_approval_callback(self, callback: Callable[[RiskAssessment], bool]):
        self._approval_callbacks.append(callback)
    
    def get_action_history(self) -> List[Dict]:
        return [
            {"action_id": k, **v} 
            for k, v in self._action_registry.items()
        ]
    
    def classify_action(self, action_type: str, target: str, 
                        scope: str) -> RiskLevel:
        ctx = {
            "target_critical": "system" in target.lower() or "prod" in target.lower(),
            "scope_wide": "all" in scope.lower() or "global" in scope.lower(),
            "irreversible": "delete" in action_type.lower() or "drop" in action_type.lower()
        }
        
        action_enum = ActionType.READ
        for at in ActionType:
            if at.value in action_type.lower():
                action_enum = at
                break
        
        temp_id = f"temp_{action_type}_{target}"
        self.register_action(temp_id, action_enum)
        assessment = self.assess_risk(temp_id, ctx)
        
        return assessment.risk_level
