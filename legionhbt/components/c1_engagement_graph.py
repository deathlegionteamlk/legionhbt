import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class EngagementState(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"


class EngagementPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class EngagementNode:
    node_id: str
    node_type: str
    state: EngagementState
    priority: EngagementPriority
    payload: Dict[str, Any]
    created_at: str
    updated_at: str
    parent_id: Optional[str] = None
    risk_score: float = 0.0
    hash_chain: str = ""


class C1EngagementGraph:
    def __init__(self, db_path: str = "legionhbt.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement_nodes (
                node_id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                state TEXT NOT NULL,
                priority INTEGER NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                parent_id TEXT,
                risk_score REAL DEFAULT 0.0,
                hash_chain TEXT DEFAULT '',
                FOREIGN KEY (parent_id) REFERENCES engagement_nodes(node_id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement_edges (
                edge_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES engagement_nodes(node_id),
                FOREIGN KEY (target_id) REFERENCES engagement_nodes(node_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_state ON engagement_nodes(state)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_priority ON engagement_nodes(priority)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_source ON engagement_edges(source_id)
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_hash(self, node: EngagementNode, prev_hash: str = "") -> str:
        data = f"{node.node_id}:{node.node_type}:{node.state.value}:{node.updated_at}:{prev_hash}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def create_node(self, node_type: str, payload: Dict[str, Any], 
                    priority: EngagementPriority = EngagementPriority.MEDIUM,
                    parent_id: Optional[str] = None) -> str:
        node_id = hashlib.sha256(f"{node_type}:{datetime.utcnow().isoformat()}:{id(payload)}".encode()).hexdigest()[:16]
        now = datetime.utcnow().isoformat()
        
        node = EngagementNode(
            node_id=node_id,
            node_type=node_type,
            state=EngagementState.PENDING,
            priority=priority,
            payload=payload,
            created_at=now,
            updated_at=now,
            parent_id=parent_id,
            hash_chain=""
        )
        
        prev_hash = ""
        if parent_id:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT hash_chain FROM engagement_nodes WHERE node_id = ?", (parent_id,))
            result = cursor.fetchone()
            conn.close()
            if result:
                prev_hash = result[0]
        
        node.hash_chain = self._generate_hash(node, prev_hash)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO engagement_nodes 
            (node_id, node_type, state, priority, payload, created_at, updated_at, parent_id, risk_score, hash_chain)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            node.node_id, node.node_type, node.state.value, node.priority.value,
            json.dumps(node.payload), node.created_at, node.updated_at,
            node.parent_id, node.risk_score, node.hash_chain
        ))
        conn.commit()
        conn.close()
        
        return node_id
    
    def update_node_state(self, node_id: str, new_state: EngagementState, 
                          risk_score: Optional[float] = None) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT hash_chain FROM engagement_nodes WHERE node_id = ?", (node_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        now = datetime.utcnow().isoformat()
        new_hash = hashlib.sha256(f"{node_id}:{new_state.value}:{now}:{result[0]}".encode()).hexdigest()
        
        if risk_score is not None:
            cursor.execute("""
                UPDATE engagement_nodes 
                SET state = ?, updated_at = ?, risk_score = ?, hash_chain = ?
                WHERE node_id = ?
            """, (new_state.value, now, risk_score, new_hash, node_id))
        else:
            cursor.execute("""
                UPDATE engagement_nodes 
                SET state = ?, updated_at = ?, hash_chain = ?
                WHERE node_id = ?
            """, (new_state.value, now, new_hash, node_id))
        
        conn.commit()
        conn.close()
        return True
    
    def get_node(self, node_id: str) -> Optional[EngagementNode]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT node_id, node_type, state, priority, payload, created_at, updated_at, parent_id, risk_score, hash_chain
            FROM engagement_nodes WHERE node_id = ?
        """, (node_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        return EngagementNode(
            node_id=result[0],
            node_type=result[1],
            state=EngagementState(result[2]),
            priority=EngagementPriority(result[3]),
            payload=json.loads(result[4]),
            created_at=result[5],
            updated_at=result[6],
            parent_id=result[7],
            risk_score=result[8],
            hash_chain=result[9]
        )
    
    def get_nodes_by_state(self, state: EngagementState) -> List[EngagementNode]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT node_id, node_type, state, priority, payload, created_at, updated_at, parent_id, risk_score, hash_chain
            FROM engagement_nodes WHERE state = ? ORDER BY priority ASC, created_at ASC
        """, (state.value,))
        results = cursor.fetchall()
        conn.close()
        
        return [
            EngagementNode(
                node_id=r[0], node_type=r[1], state=EngagementState(r[2]),
                priority=EngagementPriority(r[3]), payload=json.loads(r[4]),
                created_at=r[5], updated_at=r[6], parent_id=r[7],
                risk_score=r[8], hash_chain=r[9]
            ) for r in results
        ]
    
    def create_edge(self, source_id: str, target_id: str, 
                    edge_type: str, weight: float = 1.0) -> str:
        edge_id = hashlib.sha256(f"{source_id}:{target_id}:{edge_type}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        now = datetime.utcnow().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO engagement_edges (edge_id, source_id, target_id, edge_type, weight, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (edge_id, source_id, target_id, edge_type, weight, now))
        conn.commit()
        conn.close()
        
        return edge_id
    
    def get_children(self, node_id: str) -> List[EngagementNode]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT n.node_id, n.node_type, n.state, n.priority, n.payload, 
                   n.created_at, n.updated_at, n.parent_id, n.risk_score, n.hash_chain
            FROM engagement_nodes n
            JOIN engagement_edges e ON n.node_id = e.target_id
            WHERE e.source_id = ?
            ORDER BY n.priority ASC
        """, (node_id,))
        results = cursor.fetchall()
        conn.close()
        
        return [
            EngagementNode(
                node_id=r[0], node_type=r[1], state=EngagementState(r[2]),
                priority=EngagementPriority(r[3]), payload=json.loads(r[4]),
                created_at=r[5], updated_at=r[6], parent_id=r[7],
                risk_score=r[8], hash_chain=r[9]
            ) for r in results
        ]
    
    def verify_chain_integrity(self, node_id: str) -> bool:
        node = self.get_node(node_id)
        if not node:
            return False
        
        if not node.parent_id:
            expected_hash = self._generate_hash(node, "")
            return node.hash_chain == expected_hash
        
        parent = self.get_node(node.parent_id)
        if not parent:
            return False
        
        expected_hash = self._generate_hash(node, parent.hash_chain)
        if node.hash_chain != expected_hash:
            return False
        
        return self.verify_chain_integrity(node.parent_id)
    
    def get_active_engagements(self) -> List[EngagementNode]:
        return self.get_nodes_by_state(EngagementState.ACTIVE)
    
    def get_pending_engagements(self) -> List[EngagementNode]:
        return self.get_nodes_by_state(EngagementState.PENDING)
