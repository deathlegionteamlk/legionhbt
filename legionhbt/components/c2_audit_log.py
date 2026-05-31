import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import threading


class AuditEventType(Enum):
    NODE_CREATED = "node_created"
    NODE_UPDATED = "node_updated"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    RISK_ASSESSED = "risk_assessed"
    ACTION_EXECUTED = "action_executed"
    ACTION_BLOCKED = "action_blocked"
    CORROBORATION_INIT = "corroboration_init"
    CORROBORATION_COMPLETE = "corroboration_complete"
    POC_VERIFIED = "poc_verified"
    POC_FAILED = "poc_failed"
    CHAIN_BUILT = "chain_built"
    FIX_APPLIED = "fix_applied"
    SPECULATION_CREATED = "speculation_created"
    SPECULATION_MERGED = "speculation_merged"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"


@dataclass
class AuditEntry:
    entry_id: str
    timestamp: str
    event_type: AuditEventType
    node_id: Optional[str]
    component: str
    action: str
    payload: Dict[str, Any]
    previous_hash: str
    entry_hash: str
    signature: str


class C2AuditLog:
    def __init__(self, log_path: str = "audit_chain.log"):
        self.log_path = log_path
        self._lock = threading.Lock()
        self._last_hash = self._get_last_hash()
    
    def _get_last_hash(self) -> str:
        if not os.path.exists(self.log_path):
            return "0" * 64
        
        try:
            with open(self.log_path, 'r') as f:
                lines = f.readlines()
                if not lines:
                    return "0" * 64
                last_line = lines[-1].strip()
                entry = json.loads(last_line)
                return entry.get("entry_hash", "0" * 64)
        except:
            return "0" * 64
    
    def _generate_entry_hash(self, entry: AuditEntry) -> str:
        data = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp,
            "event_type": entry.event_type.value,
            "node_id": entry.node_id,
            "component": entry.component,
            "action": entry.action,
            "payload": entry.payload,
            "previous_hash": entry.previous_hash
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _generate_signature(self, entry_hash: str) -> str:
        sig_data = f"LEGIONHBT:{entry_hash}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(sig_data.encode()).hexdigest()[:32]
    
    def log(self, event_type: AuditEventType, component: str, action: str,
            node_id: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> str:
        with self._lock:
            entry_id = hashlib.sha256(f"{datetime.utcnow().isoformat()}:{component}:{action}".encode()).hexdigest()[:16]
            
            entry = AuditEntry(
                entry_id=entry_id,
                timestamp=datetime.utcnow().isoformat(),
                event_type=event_type,
                node_id=node_id,
                component=component,
                action=action,
                payload=payload or {},
                previous_hash=self._last_hash,
                entry_hash="",
                signature=""
            )
            
            entry.entry_hash = self._generate_entry_hash(entry)
            entry.signature = self._generate_signature(entry.entry_hash)
            
            self._last_hash = entry.entry_hash
            
            entry_dict = {
                "entry_id": entry.entry_id,
                "timestamp": entry.timestamp,
                "event_type": entry.event_type.value,
                "node_id": entry.node_id,
                "component": entry.component,
                "action": entry.action,
                "payload": entry.payload,
                "previous_hash": entry.previous_hash,
                "entry_hash": entry.entry_hash,
                "signature": entry.signature
            }
            
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(entry_dict) + "\n")
            
            return entry_id
    
    def verify_chain(self) -> bool:
        if not os.path.exists(self.log_path):
            return True
        
        with open(self.log_path, 'r') as f:
            lines = f.readlines()
        
        if not lines:
            return True
        
        previous_hash = "0" * 64
        
        for line in lines:
            try:
                entry_data = json.loads(line.strip())
                
                if entry_data.get("previous_hash") != previous_hash:
                    return False
                
                entry = AuditEntry(
                    entry_id=entry_data["entry_id"],
                    timestamp=entry_data["timestamp"],
                    event_type=AuditEventType(entry_data["event_type"]),
                    node_id=entry_data.get("node_id"),
                    component=entry_data["component"],
                    action=entry_data["action"],
                    payload=entry_data["payload"],
                    previous_hash=entry_data["previous_hash"],
                    entry_hash="",
                    signature=""
                )
                
                computed_hash = self._generate_entry_hash(entry)
                if computed_hash != entry_data["entry_hash"]:
                    return False
                
                previous_hash = entry_data["entry_hash"]
            except:
                return False
        
        return True
    
    def get_entries_for_node(self, node_id: str) -> List[AuditEntry]:
        entries = []
        
        if not os.path.exists(self.log_path):
            return entries
        
        with open(self.log_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get("node_id") == node_id:
                        entries.append(AuditEntry(
                            entry_id=data["entry_id"],
                            timestamp=data["timestamp"],
                            event_type=AuditEventType(data["event_type"]),
                            node_id=data.get("node_id"),
                            component=data["component"],
                            action=data["action"],
                            payload=data["payload"],
                            previous_hash=data["previous_hash"],
                            entry_hash=data["entry_hash"],
                            signature=data["signature"]
                        ))
                except:
                    continue
        
        return entries
    
    def get_recent_entries(self, count: int = 100) -> List[AuditEntry]:
        entries = []
        
        if not os.path.exists(self.log_path):
            return entries
        
        with open(self.log_path, 'r') as f:
            lines = f.readlines()
        
        for line in lines[-count:]:
            try:
                data = json.loads(line.strip())
                entries.append(AuditEntry(
                    entry_id=data["entry_id"],
                    timestamp=data["timestamp"],
                    event_type=AuditEventType(data["event_type"]),
                    node_id=data.get("node_id"),
                    component=data["component"],
                    action=data["action"],
                    payload=data["payload"],
                    previous_hash=data["previous_hash"],
                    entry_hash=data["entry_hash"],
                    signature=data["signature"]
                ))
            except:
                continue
        
        return entries
    
    def export_to_file(self, filepath: str) -> bool:
        if not os.path.exists(self.log_path):
            return False
        
        with open(self.log_path, 'r') as f:
            content = f.read()
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        return True
