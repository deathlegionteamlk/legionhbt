import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import statistics


class CorroborationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONSENSUS = "consensus"
    DISSENT = "dissent"
    INCONCLUSIVE = "inconclusive"


class ModelProvider(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


@dataclass
class ModelResponse:
    model_id: str
    provider: ModelProvider
    response: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    latency_ms: float = 0.0


@dataclass
class CorroborationResult:
    query_id: str
    status: CorroborationStatus
    responses: List[ModelResponse]
    consensus_answer: Optional[str]
    agreement_score: float
    dissenting_models: List[str]
    timestamp: str
    verification_method: str


class C7Corroboration:
    def __init__(self, threshold: float = 0.67, min_models: int = 2):
        self.threshold = threshold
        self.min_models = min_models
        self._model_interfaces: Dict[str, Callable[[str], Dict]] = {}
        self._history: List[CorroborationResult] = []
        self._verification_methods: Dict[str, Callable[[List[ModelResponse]], tuple]] = {}
        self._setup_default_methods()
    
    def _setup_default_methods(self):
        self._verification_methods["exact_match"] = self._exact_match_verification
        self._verification_methods["semantic_similarity"] = self._semantic_similarity_verification
        self._verification_methods["majority_vote"] = self._majority_vote_verification
    
    def register_model(self, model_id: str, provider: ModelProvider,
                       interface: Callable[[str], Dict]):
        self._model_interfaces[model_id] = {
            "provider": provider,
            "interface": interface
        }
    
    def query_with_corroboration(self, query: str, 
                                  method: str = "majority_vote",
                                  timeout_ms: float = 30000) -> CorroborationResult:
        query_id = hashlib.sha256(f"{query}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        responses = self._gather_responses(query, timeout_ms)
        
        if len(responses) < self.min_models:
            return CorroborationResult(
                query_id=query_id,
                status=CorroborationStatus.INCONCLUSIVE,
                responses=responses,
                consensus_answer=None,
                agreement_score=0.0,
                dissenting_models=[],
                timestamp=datetime.utcnow().isoformat(),
                verification_method=method
            )
        
        verification_fn = self._verification_methods.get(method, self._majority_vote_verification)
        consensus_answer, agreement_score, dissenting = verification_fn(responses)
        
        if agreement_score >= self.threshold:
            status = CorroborationStatus.CONSENSUS
        elif agreement_score >= 0.5:
            status = CorroborationStatus.DISSENT
        else:
            status = CorroborationStatus.INCONCLUSIVE
        
        result = CorroborationResult(
            query_id=query_id,
            status=status,
            responses=responses,
            consensus_answer=consensus_answer,
            agreement_score=agreement_score,
            dissenting_models=dissenting,
            timestamp=datetime.utcnow().isoformat(),
            verification_method=method
        )
        
        self._history.append(result)
        return result
    
    def _gather_responses(self, query: str, timeout_ms: float) -> List[ModelResponse]:
        import time
        responses = []
        
        for model_id, config in self._model_interfaces.items():
            try:
                start = time.time()
                result = config["interface"](query)
                latency = (time.time() - start) * 1000
                
                response = ModelResponse(
                    model_id=model_id,
                    provider=config["provider"],
                    response=result.get("response", ""),
                    confidence=result.get("confidence", 0.5),
                    metadata=result.get("metadata", {}),
                    timestamp=datetime.utcnow().isoformat(),
                    latency_ms=latency
                )
                responses.append(response)
            except:
                pass
        
        return responses
    
    def _exact_match_verification(self, responses: List[ModelResponse]) -> tuple:
        if not responses:
            return None, 0.0, []
        
        answer_counts = {}
        for r in responses:
            normalized = r.response.strip().lower()
            answer_counts[normalized] = answer_counts.get(normalized, 0) + 1
        
        if not answer_counts:
            return None, 0.0, []
        
        consensus = max(answer_counts.items(), key=lambda x: x[1])
        agreement = consensus[1] / len(responses)
        
        dissenting = [
            r.model_id for r in responses 
            if r.response.strip().lower() != consensus[0]
        ]
        
        return consensus[0], agreement, dissenting
    
    def _semantic_similarity_verification(self, responses: List[ModelResponse]) -> tuple:
        if len(responses) < 2:
            return responses[0].response if responses else None, 1.0, []
        
        base_response = responses[0].response
        similarities = []
        
        for r in responses[1:]:
            sim = self._calculate_similarity(base_response, r.response)
            similarities.append(sim)
        
        avg_similarity = statistics.mean(similarities) if similarities else 0.0
        
        dissenting = [
            r.model_id for i, r in enumerate(responses[1:])
            if similarities[i] < 0.7
        ]
        
        if avg_similarity >= self.threshold:
            return base_response, avg_similarity, dissenting
        
        return None, avg_similarity, [r.model_id for r in responses]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _majority_vote_verification(self, responses: List[ModelResponse]) -> tuple:
        if not responses:
            return None, 0.0, []
        
        answer_groups = {}
        for r in responses:
            normalized = self._normalize_answer(r.response)
            if normalized not in answer_groups:
                answer_groups[normalized] = []
            answer_groups[normalized].append(r)
        
        if not answer_groups:
            return None, 0.0, []
        
        majority_group = max(answer_groups.values(), key=len)
        agreement = len(majority_group) / len(responses)
        
        consensus_answer = majority_group[0].response
        
        dissenting = [
            r.model_id for r in responses
            if self._normalize_answer(r.response) != self._normalize_answer(consensus_answer)
        ]
        
        return consensus_answer, agreement, dissenting
    
    def _normalize_answer(self, answer: str) -> str:
        return answer.strip().lower().replace(".", "").replace("!", "").replace("?", "")
    
    def add_verification_method(self, name: str, 
                                method: Callable[[List[ModelResponse]], tuple]):
        self._verification_methods[name] = method
    
    def get_confidence_score(self, query_id: str) -> float:
        for result in self._history:
            if result.query_id == query_id:
                return result.agreement_score
        return 0.0
    
    def get_corroboration_history(self, count: int = 100) -> List[CorroborationResult]:
        return self._history[-count:]
    
    def requires_additional_verification(self, query_id: str) -> bool:
        for result in self._history:
            if result.query_id == query_id:
                return result.status != CorroborationStatus.CONSENSUS
        return True
