import os
import sys
import tempfile
import subprocess
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import shutil


class PoCStatus(Enum):
    PENDING = "pending"
    BUILDING = "building"
    RUNNING = "running"
    VERIFIED = "verified"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class PoCType(Enum):
    CODE_EXECUTION = "code_execution"
    API_CALL = "api_call"
    FILE_OPERATION = "file_operation"
    NETWORK_REQUEST = "network_request"
    DATA_PROCESSING = "data_processing"
    COMPOSITE = "composite"


@dataclass
class PoCResult:
    poc_id: str
    status: PoCStatus
    output: str
    error_output: str
    exit_code: int
    execution_time_ms: float
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class PoCTest:
    test_id: str
    name: str
    description: str
    poc_type: PoCType
    code: str
    language: str
    timeout_seconds: float = 30.0
    expected_output: Optional[str] = None
    expected_exit_code: int = 0
    dependencies: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)


class C8PoCVerification:
    def __init__(self, sandbox_dir: Optional[str] = None, 
                 max_concurrent: int = 4):
        self.sandbox_dir = sandbox_dir or tempfile.mkdtemp(prefix="legionhbt_poc_")
        self.max_concurrent = max_concurrent
        self._results: Dict[str, PoCResult] = {}
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(max_concurrent)
        self._language_runners = {
            "python": self._run_python,
            "bash": self._run_bash,
            "javascript": self._run_javascript,
            "sh": self._run_bash,
        }
    
    def create_poc(self, name: str, description: str, 
                   poc_type: PoCType, code: str,
                   language: str = "python",
                   timeout_seconds: float = 30.0,
                   expected_output: Optional[str] = None,
                   dependencies: Optional[List[str]] = None) -> str:
        poc_id = hashlib.sha256(f"{name}:{code[:100]}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        test = PoCTest(
            test_id=poc_id,
            name=name,
            description=description,
            poc_type=poc_type,
            code=code,
            language=language,
            timeout_seconds=timeout_seconds,
            expected_output=expected_output,
            dependencies=dependencies or []
        )
        
        os.makedirs(os.path.join(self.sandbox_dir, poc_id), exist_ok=True)
        
        with open(os.path.join(self.sandbox_dir, poc_id, "test.json"), 'w') as f:
            json.dump({
                "test_id": test.test_id,
                "name": test.name,
                "description": test.description,
                "poc_type": test.poc_type.value,
                "code": test.code,
                "language": test.language,
                "timeout_seconds": test.timeout_seconds,
                "expected_output": test.expected_output,
                "expected_exit_code": test.expected_exit_code,
                "dependencies": test.dependencies,
                "environment_vars": test.environment_vars
            }, f)
        
        return poc_id
    
    def verify_poc(self, poc_id: str) -> PoCResult:
        test_path = os.path.join(self.sandbox_dir, poc_id, "test.json")
        
        if not os.path.exists(test_path):
            return PoCResult(
                poc_id=poc_id,
                status=PoCStatus.ERROR,
                output="",
                error_output="PoC not found",
                exit_code=-1,
                execution_time_ms=0.0,
                timestamp=datetime.utcnow().isoformat()
            )
        
        with open(test_path, 'r') as f:
            test_data = json.load(f)
        
        test = PoCTest(
            test_id=test_data["test_id"],
            name=test_data["name"],
            description=test_data["description"],
            poc_type=PoCType(test_data["poc_type"]),
            code=test_data["code"],
            language=test_data["language"],
            timeout_seconds=test_data["timeout_seconds"],
            expected_output=test_data.get("expected_output"),
            expected_exit_code=test_data.get("expected_exit_code", 0),
            dependencies=test_data.get("dependencies", []),
            environment_vars=test_data.get("environment_vars", {})
        )
        
        with self._semaphore:
            result = self._execute_poc(test)
        
        with self._lock:
            self._results[poc_id] = result
        
        return result
    
    def _execute_poc(self, test: PoCTest) -> PoCResult:
        import time
        
        runner = self._language_runners.get(test.language, self._run_python)
        
        poc_dir = os.path.join(self.sandbox_dir, test.test_id)
        start_time = time.time()
        
        try:
            status, output, error, exit_code = runner(test, poc_dir)
        except Exception as e:
            status = PoCStatus.ERROR
            output = ""
            error = str(e)
            exit_code = -1
        
        execution_time = (time.time() - start_time) * 1000
        
        artifacts = []
        if os.path.exists(poc_dir):
            for f in os.listdir(poc_dir):
                if f not in ["test.json", "script.py", "script.sh", "script.js"]:
                    artifacts.append(os.path.join(poc_dir, f))
        
        return PoCResult(
            poc_id=test.test_id,
            status=status,
            output=output,
            error_output=error,
            exit_code=exit_code,
            execution_time_ms=execution_time,
            artifacts=artifacts,
            timestamp=datetime.utcnow().isoformat()
        )
    
    def _run_python(self, test: PoCTest, poc_dir: str) -> tuple:
        script_path = os.path.join(poc_dir, "script.py")
        with open(script_path, 'w') as f:
            f.write(test.code)
        
        env = os.environ.copy()
        env.update(test.environment_vars)
        
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=test.timeout_seconds,
                env=env,
                cwd=poc_dir
            )
            
            if result.returncode == test.expected_exit_code:
                if test.expected_output is None or test.expected_output in result.stdout:
                    return PoCStatus.VERIFIED, result.stdout, result.stderr, result.returncode
            
            return PoCStatus.FAILED, result.stdout, result.stderr, result.returncode
            
        except subprocess.TimeoutExpired:
            return PoCStatus.TIMEOUT, "", "Execution timed out", -1
    
    def _run_bash(self, test: PoCTest, poc_dir: str) -> tuple:
        script_path = os.path.join(poc_dir, "script.sh")
        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(test.code)
        
        os.chmod(script_path, 0o755)
        
        env = os.environ.copy()
        env.update(test.environment_vars)
        
        try:
            result = subprocess.run(
                ["/bin/bash", script_path],
                capture_output=True,
                text=True,
                timeout=test.timeout_seconds,
                env=env,
                cwd=poc_dir
            )
            
            if result.returncode == test.expected_exit_code:
                if test.expected_output is None or test.expected_output in result.stdout:
                    return PoCStatus.VERIFIED, result.stdout, result.stderr, result.returncode
            
            return PoCStatus.FAILED, result.stdout, result.stderr, result.returncode
            
        except subprocess.TimeoutExpired:
            return PoCStatus.TIMEOUT, "", "Execution timed out", -1
    
    def _run_javascript(self, test: PoCTest, poc_dir: str) -> tuple:
        script_path = os.path.join(poc_dir, "script.js")
        with open(script_path, 'w') as f:
            f.write(test.code)
        
        env = os.environ.copy()
        env.update(test.environment_vars)
        
        try:
            result = subprocess.run(
                ["node", script_path],
                capture_output=True,
                text=True,
                timeout=test.timeout_seconds,
                env=env,
                cwd=poc_dir
            )
            
            if result.returncode == test.expected_exit_code:
                if test.expected_output is None or test.expected_output in result.stdout:
                    return PoCStatus.VERIFIED, result.stdout, result.stderr, result.returncode
            
            return PoCStatus.FAILED, result.stdout, result.stderr, result.returncode
            
        except subprocess.TimeoutExpired:
            return PoCStatus.TIMEOUT, "", "Execution timed out", -1
        except FileNotFoundError:
            return PoCStatus.ERROR, "", "Node.js not available", -1
    
    def get_result(self, poc_id: str) -> Optional[PoCResult]:
        return self._results.get(poc_id)
    
    def is_verified(self, poc_id: str) -> bool:
        result = self._results.get(poc_id)
        return result is not None and result.status == PoCStatus.VERIFIED
    
    def get_all_results(self) -> Dict[str, PoCResult]:
        return self._results.copy()
    
    def cleanup_poc(self, poc_id: str) -> bool:
        poc_dir = os.path.join(self.sandbox_dir, poc_id)
        if os.path.exists(poc_dir):
            shutil.rmtree(poc_dir)
            return True
        return False
    
    def add_language_runner(self, language: str, 
                            runner: Callable[[PoCTest, str], tuple]):
        self._language_runners[language] = runner
    
    def get_verification_summary(self) -> Dict:
        with self._lock:
            total = len(self._results)
            verified = sum(1 for r in self._results.values() if r.status == PoCStatus.VERIFIED)
            failed = sum(1 for r in self._results.values() if r.status == PoCStatus.FAILED)
            errors = sum(1 for r in self._results.values() if r.status == PoCStatus.ERROR)
            timeouts = sum(1 for r in self._results.values() if r.status == PoCStatus.TIMEOUT)
            
            return {
                "total": total,
                "verified": verified,
                "failed": failed,
                "errors": errors,
                "timeouts": timeouts,
                "success_rate": verified / total if total > 0 else 0.0
            }
