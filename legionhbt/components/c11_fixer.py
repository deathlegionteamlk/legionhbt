import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re


class FixStatus(Enum):
    IDENTIFIED = "identified"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    TESTING = "testing"
    APPLIED = "applied"
    VERIFIED = "verified"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class FixType(Enum):
    CODE_PATCH = "code_patch"
    CONFIG_UPDATE = "config_update"
    DEPENDENCY_FIX = "dependency_fix"
    LOGIC_CORRECTION = "logic_correction"
    SECURITY_PATCH = "security_patch"
    PERFORMANCE_FIX = "performance_fix"


@dataclass
class FixProposal:
    fix_id: str
    target_id: str
    fix_type: FixType
    description: str
    changes: List[Dict[str, Any]]
    validation_tests: List[str]
    rollback_plan: List[Dict[str, Any]]
    status: FixStatus
    created_at: str
    applied_at: Optional[str] = None
    verified_at: Optional[str] = None


@dataclass
class ChainSeveranceProof:
    proof_id: str
    chain_id: str
    severed_at_link: str
    reason: str
    snapshot_before: Dict[str, Any]
    snapshot_after: Dict[str, Any]
    timestamp: str
    verification_hash: str


class C11Fixer:
    def __init__(self):
        self._fixes: Dict[str, FixProposal] = {}
        self._severance_proofs: Dict[str, ChainSeveranceProof] = {}
        self._fix_handlers: Dict[FixType, Callable[[FixProposal], bool]] = {}
        self._validation_hooks: List[Callable[[FixProposal], bool]] = []
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        self._fix_handlers[FixType.CODE_PATCH] = self._apply_code_patch
        self._fix_handlers[FixType.CONFIG_UPDATE] = self._apply_config_update
    
    def identify_fix(self, target_id: str, issue_description: str,
                     fix_type: FixType, context: Dict[str, Any]) -> str:
        fix_id = hashlib.sha256(f"{target_id}:{issue_description}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        changes = self._generate_changes(fix_type, context)
        tests = self._generate_validation_tests(fix_type, context)
        rollback = self._generate_rollback_plan(fix_type, changes)
        
        fix = FixProposal(
            fix_id=fix_id,
            target_id=target_id,
            fix_type=fix_type,
            description=issue_description,
            changes=changes,
            validation_tests=tests,
            rollback_plan=rollback,
            status=FixStatus.IDENTIFIED,
            created_at=datetime.utcnow().isoformat()
        )
        
        self._fixes[fix_id] = fix
        return fix_id
    
    def _generate_changes(self, fix_type: FixType, context: Dict) -> List[Dict]:
        changes = []
        
        if fix_type == FixType.CODE_PATCH:
            if "file_path" in context and "patch" in context:
                changes.append({
                    "type": "file_modify",
                    "path": context["file_path"],
                    "patch": context["patch"],
                    "backup": True
                })
        
        elif fix_type == FixType.CONFIG_UPDATE:
            if "config_path" in context and "updates" in context:
                changes.append({
                    "type": "config_update",
                    "path": context["config_path"],
                    "updates": context["updates"],
                    "backup": True
                })
        
        elif fix_type == FixType.DEPENDENCY_FIX:
            if "dependencies" in context:
                changes.append({
                    "type": "dependency_update",
                    "add": context["dependencies"].get("add", []),
                    "remove": context["dependencies"].get("remove", []),
                    "update": context["dependencies"].get("update", [])
                })
        
        return changes
    
    def _generate_validation_tests(self, fix_type: FixType, context: Dict) -> List[str]:
        tests = []
        
        if fix_type == FixType.CODE_PATCH:
            tests.append("Syntax validation")
            tests.append("Unit test execution")
            tests.append("Integration test")
        
        elif fix_type == FixType.CONFIG_UPDATE:
            tests.append("Config schema validation")
            tests.append("Config load test")
        
        elif fix_type == FixType.DEPENDENCY_FIX:
            tests.append("Dependency resolution")
            tests.append("Import test")
        
        return tests
    
    def _generate_rollback_plan(self, fix_type: FixType, changes: List[Dict]) -> List[Dict]:
        rollback = []
        
        for change in changes:
            if change.get("backup"):
                rollback.append({
                    "type": "restore_backup",
                    "path": change["path"],
                    "backup_path": f"{change['path']}.backup"
                })
            elif change["type"] == "dependency_update":
                rollback.append({
                    "type": "dependency_rollback",
                    "restore_previous": True
                })
        
        return rollback
    
    def apply_fix(self, fix_id: str) -> bool:
        if fix_id not in self._fixes:
            return False
        
        fix = self._fixes[fix_id]
        fix.status = FixStatus.ANALYZING
        
        for hook in self._validation_hooks:
            if not hook(fix):
                fix.status = FixStatus.FAILED
                return False
        
        fix.status = FixStatus.GENERATING
        
        handler = self._fix_handlers.get(fix.fix_type)
        if not handler:
            fix.status = FixStatus.FAILED
            return False
        
        fix.status = FixStatus.TESTING
        
        try:
            success = handler(fix)
            if success:
                fix.status = FixStatus.APPLIED
                fix.applied_at = datetime.utcnow().isoformat()
            else:
                fix.status = FixStatus.FAILED
            return success
        except Exception as e:
            fix.status = FixStatus.FAILED
            return False
    
    def _apply_code_patch(self, fix: FixProposal) -> bool:
        for change in fix.changes:
            if change["type"] == "file_modify":
                try:
                    import shutil
                    shutil.copy2(change["path"], change["path"] + ".backup")
                    
                    with open(change["path"], 'r') as f:
                        content = f.read()
                    
                    patch = change["patch"]
                    if "search" in patch and "replace" in patch:
                        content = content.replace(patch["search"], patch["replace"])
                    
                    with open(change["path"], 'w') as f:
                        f.write(content)
                    
                except:
                    return False
        
        return True
    
    def _apply_config_update(self, fix: FixProposal) -> bool:
        for change in fix.changes:
            if change["type"] == "config_update":
                try:
                    import shutil
                    shutil.copy2(change["path"], change["path"] + ".backup")
                    
                    with open(change["path"], 'r') as f:
                        config = json.load(f)
                    
                    config.update(change["updates"])
                    
                    with open(change["path"], 'w') as f:
                        json.dump(config, f, indent=2)
                    
                except:
                    return False
        
        return True
    
    def verify_fix(self, fix_id: str) -> bool:
        if fix_id not in self._fixes:
            return False
        
        fix = self._fixes[fix_id]
        
        if fix.status != FixStatus.APPLIED:
            return False
        
        fix.status = FixStatus.VERIFIED
        fix.verified_at = datetime.utcnow().isoformat()
        return True
    
    def rollback_fix(self, fix_id: str) -> bool:
        if fix_id not in self._fixes:
            return False
        
        fix = self._fixes[fix_id]
        
        for rollback_step in fix.rollback_plan:
            try:
                if rollback_step["type"] == "restore_backup":
                    import shutil
                    shutil.copy2(rollback_step["backup_path"], rollback_step["path"])
            except:
                return False
        
        fix.status = FixStatus.ROLLED_BACK
        return True
    
    def sever_chain_with_proof(self, chain_id: str, link_id: str, 
                               reason: str, snapshot_before: Dict) -> str:
        proof_id = hashlib.sha256(f"{chain_id}:{link_id}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        snapshot_after = {
            "chain_id": chain_id,
            "severed_link": link_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "severed"
        }
        
        proof_data = f"{chain_id}:{link_id}:{reason}:{json.dumps(snapshot_before, sort_keys=True)}"
        verification_hash = hashlib.sha256(proof_data.encode()).hexdigest()
        
        proof = ChainSeveranceProof(
            proof_id=proof_id,
            chain_id=chain_id,
            severed_at_link=link_id,
            reason=reason,
            snapshot_before=snapshot_before,
            snapshot_after=snapshot_after,
            timestamp=datetime.utcnow().isoformat(),
            verification_hash=verification_hash
        )
        
        self._severance_proofs[proof_id] = proof
        return proof_id
    
    def verify_severance_proof(self, proof_id: str) -> bool:
        proof = self._severance_proofs.get(proof_id)
        if not proof:
            return False
        
        proof_data = f"{proof.chain_id}:{proof.severed_at_link}:{proof.reason}:{json.dumps(proof.snapshot_before, sort_keys=True)}"
        expected_hash = hashlib.sha256(proof_data.encode()).hexdigest()
        
        return proof.verification_hash == expected_hash
    
    def add_fix_handler(self, fix_type: FixType, handler: Callable[[FixProposal], bool]):
        self._fix_handlers[fix_type] = handler
    
    def add_validation_hook(self, hook: Callable[[FixProposal], bool]):
        self._validation_hooks.append(hook)
    
    def get_fix(self, fix_id: str) -> Optional[FixProposal]:
        return self._fixes.get(fix_id)
    
    def get_fixes_for_target(self, target_id: str) -> List[FixProposal]:
        return [f for f in self._fixes.values() if f.target_id == target_id]
    
    def get_severance_proof(self, proof_id: str) -> Optional[ChainSeveranceProof]:
        return self._severance_proofs.get(proof_id)
    
    def create_ci_workflow(self, fix_id: str) -> Dict:
        fix = self._fixes.get(fix_id)
        if not fix:
            return {}
        
        return {
            "name": f"Fix Validation - {fix_id}",
            "on": ["push", "pull_request"],
            "jobs": {
                "validate": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {"uses": "actions/checkout@v3"},
                        {"name": "Setup Python", "uses": "actions/setup-python@v4", "with": {"python-version": "3.11"}},
                        {"name": "Install dependencies", "run": "pip install -r requirements.txt"},
                        {"name": "Run validation tests", "run": f"python -m pytest tests/ -k {fix_id}"},
                        {"name": "Verify fix", "run": f"python -c \"from legionhbt import verify_fix; verify_fix('{fix_id}')\""}
                    ]
                }
            }
        }
