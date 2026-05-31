from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib


@dataclass
class BenchmarkResult:
    benchmark_name: str
    score: float
    target_score: float
    passed: bool
    details: Dict[str, Any]
    timestamp: str
    execution_time: float


class BenchmarkRunner(ABC):
    def __init__(self, name: str, target_score: float):
        self.name = name
        self.target_score = target_score
        self.results: List[BenchmarkResult] = []
    
    @abstractmethod
    def run(self, sample_size: Optional[int] = None) -> BenchmarkResult:
        pass
    
    def save_result(self, result: BenchmarkResult):
        self.results.append(result)
    
    def get_summary(self) -> Dict[str, Any]:
        if not self.results:
            return {"error": "No results available"}
        
        latest = self.results[-1]
        return {
            "benchmark": self.name,
            "target": self.target_score,
            "latest_score": latest.score,
            "passed": latest.passed,
            "total_runs": len(self.results),
            "pass_rate": sum(1 for r in self.results if r.passed) / len(self.results)
        }
