import json
import sqlite3
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class SessionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class ActionType(Enum):
    SCAN = "scan"
    EXPLOIT = "exploit"
    ANALYZE = "analyze"
    REPORT = "report"


@dataclass
class Session:
    id: str
    name: str
    target: str
    status: str
    created_at: str
    updated_at: str
    findings: List[Dict]
    actions: List[Dict]
    metadata: Dict


@dataclass
class AuditLogEntry:
    id: str
    session_id: str
    timestamp: str
    action_type: str
    tool_name: str
    input_data: str
    output_data: str
    hash_chain: str


class SessionManager:
    def __init__(self, db_path: str = "agent_sessions.db"):
        self.db_path = db_path
        self._init_db()
        self.last_hash = "0" * 64
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                findings TEXT,
                actions TEXT,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                action_type TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                input_data TEXT,
                output_data TEXT,
                hash_chain TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(self, name: str, target: str, metadata: Dict = None) -> Session:
        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        session = Session(
            id=session_id,
            name=name,
            target=target,
            status=SessionStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
            findings=[],
            actions=[],
            metadata=metadata or {}
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO sessions (id, name, target, status, created_at, updated_at, findings, actions, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session.id, session.name, session.target, session.status,
             session.created_at, session.updated_at, json.dumps(session.findings),
             json.dumps(session.actions), json.dumps(session.metadata))
        )
        conn.commit()
        conn.close()
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Session(
                id=row[0],
                name=row[1],
                target=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5],
                findings=json.loads(row[6]) if row[6] else [],
                actions=json.loads(row[7]) if row[7] else [],
                metadata=json.loads(row[8]) if row[8] else {}
            )
        return None
    
    def list_sessions(self) -> List[Session]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            sessions.append(Session(
                id=row[0],
                name=row[1],
                target=row[2],
                status=row[3],
                created_at=row[4],
                updated_at=row[5],
                findings=json.loads(row[6]) if row[6] else [],
                actions=json.loads(row[7]) if row[7] else [],
                metadata=json.loads(row[8]) if row[8] else {}
            ))
        return sessions
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.updated_at = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE sessions SET name=?, target=?, status=?, updated_at=?, findings=?, actions=?, metadata=?
               WHERE id=?""",
            (session.name, session.target, session.status, session.updated_at,
             json.dumps(session.findings), json.dumps(session.actions),
             json.dumps(session.metadata), session.id)
        )
        conn.commit()
        conn.close()
        return True
    
    def add_finding(self, session_id: str, finding: Dict) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        
        finding["id"] = str(uuid.uuid4())
        finding["timestamp"] = datetime.utcnow().isoformat()
        session.findings.append(finding)
        
        return self.update_session(session_id, findings=session.findings)
    
    def add_action(self, session_id: str, action: Dict) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        
        action["id"] = str(uuid.uuid4())
        action["timestamp"] = datetime.utcnow().isoformat()
        session.actions.append(action)
        
        return self.update_session(session_id, actions=session.actions)
    
    def log_audit(self, session_id: str, action_type: str, tool_name: str,
                  input_data: str, output_data: str) -> AuditLogEntry:
        entry_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        data_string = f"{self.last_hash}{entry_id}{timestamp}{action_type}{tool_name}{input_data}{output_data}"
        hash_chain = hashlib.sha256(data_string.encode()).hexdigest()
        
        entry = AuditLogEntry(
            id=entry_id,
            session_id=session_id,
            timestamp=timestamp,
            action_type=action_type,
            tool_name=tool_name,
            input_data=input_data,
            output_data=output_data,
            hash_chain=hash_chain
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO audit_log (id, session_id, timestamp, action_type, tool_name, input_data, output_data, hash_chain)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (entry.id, entry.session_id, entry.timestamp, entry.action_type,
             entry.tool_name, entry.input_data, entry.output_data, entry.hash_chain)
        )
        conn.commit()
        conn.close()
        
        self.last_hash = hash_chain
        return entry
    
    def get_audit_log(self, session_id: str) -> List[AuditLogEntry]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM audit_log WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for row in rows:
            entries.append(AuditLogEntry(
                id=row[0],
                session_id=row[1],
                timestamp=row[2],
                action_type=row[3],
                tool_name=row[4],
                input_data=row[5],
                output_data=row[6],
                hash_chain=row[7]
            ))
        return entries
    
    def verify_audit_chain(self, session_id: str) -> bool:
        entries = self.get_audit_log(session_id)
        if not entries:
            return True
        
        previous_hash = "0" * 64
        for entry in entries:
            data_string = f"{previous_hash}{entry.id}{entry.timestamp}{entry.action_type}{entry.tool_name}{entry.input_data}{entry.output_data}"
            expected_hash = hashlib.sha256(data_string.encode()).hexdigest()
            
            if entry.hash_chain != expected_hash:
                return False
            previous_hash = entry.hash_chain
        
        return True