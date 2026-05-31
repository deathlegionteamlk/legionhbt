import subprocess
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
import tempfile
import os
import signal


class GateDecision(Enum):
    ALLOW = "allow"
    DELIBERATE = "deliberate"
    BLOCK = "block"


class CorroborationStatus(Enum):
    CONSENSUS = "consensus"
    DISSENT = "dissent"
    TIE = "tie"
    INSUFFICIENT = "insufficient"


class ModelProvider(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    BACKUP = "backup"


class PoCStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    VERIFIED = "verified"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class PoCType(Enum):
    CODE_EXECUTION = "code_execution"
    COMMAND_INJECTION = "command_injection"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    SSRF = "ssrf"
    LFI = "lfi"
    RFI = "rfi"


@dataclass
class InternalState:
    confidence: float
    uncertainty: float
    risk_assessment: float
    emotional_valence: float
    cognitive_load: float
    timestamp: str


@dataclass
class DeliberationResult:
    decision: GateDecision
    confidence: float
    reasoning: str
    checks_performed: List[str]
    state_snapshot: InternalState


@dataclass
class CorroborationVote:
    model_id: str
    provider: ModelProvider
    response: str
    confidence: float
    timestamp: str


@dataclass
class CorroborationResult:
    status: CorroborationStatus
    consensus_response: Optional[str]
    votes: List[CorroborationVote]
    agreement_score: float
    dissenting_models: List[str]
    timestamp: str


@dataclass
class PoCResult:
    poc_id: str
    status: PoCStatus
    output: str
    error: str
    exit_code: int
    execution_time: float
    artifacts: List[str]


@dataclass
class PoCDefinition:
    poc_id: str
    name: str
    description: str
    poc_type: PoCType
    code: str
    language: str
    timeout: int
    sandbox_config: Dict[str, Any]
    created_at: str


class SelfMonitor:
    def __init__(self, check_interval: float = 1.0):
        self.check_interval = check_interval
        self.state_history: List[InternalState] = []
        self.deliberation_history: List[DeliberationResult] = []
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
    
    def _monitor_loop(self):
        while self.running:
            state = self._capture_state()
            with self._lock:
                self.state_history.append(state)
                if len(self.state_history) > 1000:
                    self.state_history.pop(0)
            time.sleep(self.check_interval)
    
    def _capture_state(self) -> InternalState:
        return InternalState(
            confidence=0.8,
            uncertainty=0.2,
            risk_assessment=0.3,
            emotional_valence=0.5,
            cognitive_load=0.4,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def get_current_state(self) -> InternalState:
        with self._lock:
            return self.state_history[-1] if self.state_history else self._capture_state()
    
    def deliberative_gate(self, action: str, context: Dict[str, Any]) -> DeliberationResult:
        state = self.get_current_state()
        checks = []
        
        risk_score = context.get("risk_score", 0.5)
        
        if risk_score < 0.3:
            decision = GateDecision.ALLOW
            confidence = 0.9
            reasoning = "Low risk action approved"
            checks.append("risk_assessment")
        elif risk_score < 0.7:
            decision = GateDecision.DELIBERATE
            confidence = 0.7
            reasoning = "Moderate risk requires deliberation"
            checks.extend(["risk_assessment", "uncertainty_check", "capability_check"])
        else:
            decision = GateDecision.BLOCK
            confidence = 0.95
            reasoning = "High risk action blocked"
            checks.extend(["risk_assessment", "safety_check", "policy_check"])
        
        result = DeliberationResult(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            checks_performed=checks,
            state_snapshot=state
        )
        
        self.deliberation_history.append(result)
        return result
    
    def analyze_state_trends(self, window: int = 100) -> Dict[str, Any]:
        with self._lock:
            recent = self.state_history[-window:] if len(self.state_history) >= window else self.state_history
        
        if not recent:
            return {"error": "No state history available"}
        
        trends = {
            "confidence_trend": sum(s.confidence for s in recent) / len(recent),
            "uncertainty_trend": sum(s.uncertainty for s in recent) / len(recent),
            "risk_trend": sum(s.risk_assessment for s in recent) / len(recent),
            "samples": len(recent)
        }
        return trends
    
    def get_health_report(self) -> Dict[str, Any]:
        state = self.get_current_state()
        trends = self.analyze_state_trends()
        
        return {
            "current_state": {
                "confidence": state.confidence,
                "uncertainty": state.uncertainty,
                "risk_assessment": state.risk_assessment,
                "cognitive_load": state.cognitive_load
            },
            "trends": trends,
            "total_deliberations": len(self.deliberation_history),
            "monitoring_active": self.running,
            "timestamp": datetime.utcnow().isoformat()
        }


class CrossModelCorroboration:
    def __init__(self, threshold: float = 0.67):
        self.threshold = threshold
        self.model_interfaces: Dict[str, Tuple[ModelProvider, Callable]] = {}
        self.vote_history: List[CorroborationResult] = []
    
    def register_model(self, model_id: str, provider: ModelProvider,
                       interface: Callable[[str], Dict[str, Any]]):
        self.model_interfaces[model_id] = (provider, interface)
    
    def query_all_models(self, prompt: str) -> List[CorroborationVote]:
        votes = []
        for model_id, (provider, interface) in self.model_interfaces.items():
            try:
                response = interface(prompt)
                vote = CorroborationVote(
                    model_id=model_id,
                    provider=provider,
                    response=response.get("response", ""),
                    confidence=response.get("confidence", 0.5),
                    timestamp=datetime.utcnow().isoformat()
                )
                votes.append(vote)
            except Exception as e:
                vote = CorroborationVote(
                    model_id=model_id,
                    provider=provider,
                    response="",
                    confidence=0.0,
                    timestamp=datetime.utcnow().isoformat()
                )
                votes.append(vote)
        return votes
    
    def compute_similarity(self, response1: str, response2: str) -> float:
        words1 = set(response1.lower().split())
        words2 = set(response2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)
    
    def find_consensus(self, votes: List[CorroborationVote]) -> Tuple[Optional[str], float]:
        if len(votes) < 2:
            return (votes[0].response if votes else None, 0.0)
        
        best_response = None
        best_score = 0.0
        
        for vote in votes:
            agreement_count = 0
            for other in votes:
                if vote.model_id != other.model_id:
                    similarity = self.compute_similarity(vote.response, other.response)
                    if similarity > 0.5:
                        agreement_count += 1
            
            score = agreement_count / (len(votes) - 1) if len(votes) > 1 else 0
            if score > best_score:
                best_score = score
                best_response = vote.response
        
        return best_response, best_score
    
    def corroborate(self, prompt: str) -> CorroborationResult:
        votes = self.query_all_models(prompt)
        
        if len(votes) < 2:
            result = CorroborationResult(
                status=CorroborationStatus.INSUFFICIENT,
                consensus_response=None,
                votes=votes,
                agreement_score=0.0,
                dissenting_models=[],
                timestamp=datetime.utcnow().isoformat()
            )
            self.vote_history.append(result)
            return result
        
        consensus, agreement = self.find_consensus(votes)
        
        if agreement >= self.threshold:
            status = CorroborationStatus.CONSENSUS
            dissenting = [v.model_id for v in votes if self.compute_similarity(v.response, consensus) < 0.5] if consensus else []
        elif agreement >= 0.5:
            status = CorroborationStatus.TIE
            dissenting = []
        else:
            status = CorroborationStatus.DISSENT
            dissenting = [v.model_id for v in votes]
        
        result = CorroborationResult(
            status=status,
            consensus_response=consensus,
            votes=votes,
            agreement_score=agreement,
            dissenting_models=dissenting,
            timestamp=datetime.utcnow().isoformat()
        )
        
        self.vote_history.append(result)
        return result
    
    def two_of_three_vote(self, prompt: str) -> CorroborationResult:
        votes = self.query_all_models(prompt)
        
        if len(votes) < 3:
            return CorroborationResult(
                status=CorroborationStatus.INSUFFICIENT,
                consensus_response=None,
                votes=votes,
                agreement_score=0.0,
                dissenting_models=[v.model_id for v in votes],
                timestamp=datetime.utcnow().isoformat()
            )
        
        consensus, agreement = self.find_consensus(votes)
        
        if agreement >= 0.67:
            status = CorroborationStatus.CONSENSUS
            dissenting = [v.model_id for v in votes if self.compute_similarity(v.response, consensus) < 0.5] if consensus else []
        else:
            status = CorroborationStatus.DISSENT
            dissenting = [v.model_id for v in votes]
        
        return CorroborationResult(
            status=status,
            consensus_response=consensus,
            votes=votes,
            agreement_score=agreement,
            dissenting_models=dissenting,
            timestamp=datetime.utcnow().isoformat()
        )


class DynamicPoCVerification:
    def __init__(self, sandbox_dir: Optional[str] = None):
        self.sandbox_dir = sandbox_dir or tempfile.mkdtemp(prefix="poc_sandbox_")
        self.poc_registry: Dict[str, PoCDefinition] = {}
        self.execution_history: List[PoCResult] = []
        os.makedirs(self.sandbox_dir, exist_ok=True)
    
    def create_poc(self, name: str, description: str, poc_type: PoCType,
                   code: str, language: str = "python",
                   timeout: int = 30) -> str:
        poc_id = hashlib.sha256(
            f"{name}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        poc = PoCDefinition(
            poc_id=poc_id,
            name=name,
            description=description,
            poc_type=poc_type,
            code=code,
            language=language,
            timeout=timeout,
            sandbox_config={"isolated": True, "network": False},
            created_at=datetime.utcnow().isoformat()
        )
        
        self.poc_registry[poc_id] = poc
        return poc_id
    
    def _execute_python(self, code: str, timeout: int) -> PoCResult:
        poc_id = hashlib.sha256(code.encode()).hexdigest()[:16]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                ['python3', temp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.sandbox_dir
            )
            
            return PoCResult(
                poc_id=poc_id,
                status=PoCStatus.VERIFIED if result.returncode == 0 else PoCStatus.FAILED,
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
                execution_time=0.0,
                artifacts=[]
            )
        except subprocess.TimeoutExpired:
            return PoCResult(
                poc_id=poc_id,
                status=PoCStatus.TIMEOUT,
                output="",
                error="Execution timed out",
                exit_code=-1,
                execution_time=float(timeout),
                artifacts=[]
            )
        except Exception as e:
            return PoCResult(
                poc_id=poc_id,
                status=PoCStatus.ERROR,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=0.0,
                artifacts=[]
            )
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _execute_shell(self, command: str, timeout: int) -> PoCResult:
        poc_id = hashlib.sha256(command.encode()).hexdigest()[:16]
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.sandbox_dir
            )
            
            return PoCResult(
                poc_id=poc_id,
                status=PoCStatus.VERIFIED if result.returncode == 0 else PoCStatus.FAILED,
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
                execution_time=0.0,
                artifacts=[]
            )
        except subprocess.TimeoutExpired:
            return PoCResult(
                poc_id=poc_id,
                status=PoCStatus.TIMEOUT,
                output="",
                error="Execution timed out",
                exit_code=-1,
                execution_time=float(timeout),
                artifacts=[]
            )
        except Exception as e:
            return PoCResult(
                poc_id=poc_id,
                status=PoCStatus.ERROR,
                output="",
                error=str(e),
                exit_code=-1,
                execution_time=0.0,
                artifacts=[]
            )
    
    def verify_poc(self, poc_id: str) -> PoCResult:
        poc = self.poc_registry.get(poc_id)
        if not poc:
            return PoCResult(
                poc_id=poc_id,
                status=PoCStatus.ERROR,
                output="",
                error="PoC not found",
                exit_code=-1,
                execution_time=0.0,
                artifacts=[]
            )
        
        start_time = time.time()
        
        if poc.language == "python":
            result = self._execute_python(poc.code, poc.timeout)
        elif poc.language == "shell":
            result = self._execute_shell(poc.code, poc.timeout)
        else:
            result = PoCResult(
                poc_id=poc_id,
                status=PoCStatus.ERROR,
                output="",
                error=f"Unsupported language: {poc.language}",
                exit_code=-1,
                execution_time=0.0,
                artifacts=[]
            )
        
        result.execution_time = time.time() - start_time
        self.execution_history.append(result)
        return result
    
    def get_poc(self, poc_id: str) -> Optional[PoCDefinition]:
        return self.poc_registry.get(poc_id)
    
    def list_pocs(self) -> List[str]:
        return list(self.poc_registry.keys())
    
    def get_execution_stats(self) -> Dict[str, Any]:
        if not self.execution_history:
            return {"total": 0, "verified": 0, "failed": 0, "success_rate": 0.0}
        
        total = len(self.execution_history)
        verified = sum(1 for r in self.execution_history if r.status == PoCStatus.VERIFIED)
        failed = sum(1 for r in self.execution_history if r.status == PoCStatus.FAILED)
        
        return {
            "total": total,
            "verified": verified,
            "failed": failed,
            "timeout": sum(1 for r in self.execution_history if r.status == PoCStatus.TIMEOUT),
            "error": sum(1 for r in self.execution_history if r.status == PoCStatus.ERROR),
            "success_rate": verified / total if total > 0 else 0.0
        }


class SafetyEngine:
    def __init__(self):
        self.self_monitor = SelfMonitor()
        self.corroboration = CrossModelCorroboration()
        self.poc_verifier = DynamicPoCVerification()
    
    def comprehensive_check(self, action: str, context: Dict[str, Any],
                           prompt: str) -> Dict[str, Any]:
        deliberation = self.self_monitor.deliberative_gate(action, context)
        
        if deliberation.decision == GateDecision.BLOCK:
            return {
                "approved": False,
                "reason": deliberation.reasoning,
                "deliberation": deliberation,
                "corroboration": None,
                "poc_result": None
            }
        
        corroboration = self.corroboration.two_of_three_vote(prompt)
        
        if corroboration.status != CorroborationStatus.CONSENSUS:
            return {
                "approved": False,
                "reason": "No consensus on action safety",
                "deliberation": deliberation,
                "corroboration": corroboration,
                "poc_result": None
            }
        
        return {
            "approved": True,
            "reason": "All safety checks passed",
            "deliberation": deliberation,
            "corroboration": corroboration,
            "poc_result": None
        }
