import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque
import numpy as np
from datetime import datetime, timedelta
import hashlib


@dataclass
class MemoryEntry:
    content: str
    timestamp: float
    memory_type: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    importance: float = 1.0
    access_count: int = 0
    last_accessed: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        if self.embedding is not None:
            result['embedding'] = self.embedding.tolist()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        if 'embedding' in data and data['embedding'] is not None:
            data['embedding'] = np.array(data['embedding'])
        return cls(**data)


class EpisodicMemory:
    def __init__(self, max_size: int = 10000, retention_days: int = 30):
        self.memories: List[MemoryEntry] = []
        self.max_size = max_size
        self.retention_days = retention_days
        self.index: Dict[str, int] = {}

    def store(self, content: str, metadata: Dict[str, Any] = None, 
              embedding: Optional[np.ndarray] = None, importance: float = 1.0) -> str:
        entry = MemoryEntry(
            content=content,
            timestamp=time.time(),
            memory_type="episodic",
            metadata=metadata or {},
            embedding=embedding,
            importance=importance,
            last_accessed=time.time()
        )
        memory_id = hashlib.md5(f"{content}{entry.timestamp}".encode()).hexdigest()[:16]
        self.index[memory_id] = len(self.memories)
        self.memories.append(entry)

        if len(self.memories) > self.max_size:
            self._prune_old_memories()

        return memory_id

    def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        if memory_id in self.index:
            idx = self.index[memory_id]
            entry = self.memories[idx]
            entry.access_count += 1
            entry.last_accessed = time.time()
            return entry
        return None

    def search_by_time(self, start_time: float, end_time: float) -> List[MemoryEntry]:
        return [m for m in self.memories if start_time <= m.timestamp <= end_time]

    def search_by_content(self, keyword: str) -> List[MemoryEntry]:
        return [m for m in self.memories if keyword.lower() in m.content.lower()]

    def get_recent(self, n: int = 10) -> List[MemoryEntry]:
        return sorted(self.memories, key=lambda x: x.timestamp, reverse=True)[:n]

    def _prune_old_memories(self):
        cutoff = time.time() - (self.retention_days * 86400)
        self.memories = [m for m in self.memories if m.timestamp > cutoff or m.importance > 0.8]
        self._rebuild_index()

    def _rebuild_index(self):
        self.index = {}
        for i, memory in enumerate(self.memories):
            memory_id = hashlib.md5(f"{memory.content}{memory.timestamp}".encode()).hexdigest()[:16]
            self.index[memory_id] = i

    def clear(self):
        self.memories.clear()
        self.index.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memories": [m.to_dict() for m in self.memories],
            "max_size": self.max_size,
            "retention_days": self.retention_days
        }

    def from_dict(self, data: Dict[str, Any]):
        self.memories = [MemoryEntry.from_dict(m) for m in data.get("memories", [])]
        self.max_size = data.get("max_size", 10000)
        self.retention_days = data.get("retention_days", 30)
        self._rebuild_index()


class SemanticMemory:
    def __init__(self, embedding_dim: int = 384):
        self.knowledge: Dict[str, MemoryEntry] = {}
        self.embedding_dim = embedding_dim
        self.category_index: Dict[str, List[str]] = {}

    def store(self, key: str, content: str, category: str = "general",
              embedding: Optional[np.ndarray] = None, metadata: Dict[str, Any] = None) -> str:
        entry = MemoryEntry(
            content=content,
            timestamp=time.time(),
            memory_type="semantic",
            metadata={"category": category, **(metadata or {})},
            embedding=embedding,
            importance=1.0
        )
        self.knowledge[key] = entry

        if category not in self.category_index:
            self.category_index[category] = []
        self.category_index[category].append(key)

        return key

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        if key in self.knowledge:
            entry = self.knowledge[key]
            entry.access_count += 1
            entry.last_accessed = time.time()
            return entry
        return None

    def search_by_category(self, category: str) -> List[Tuple[str, MemoryEntry]]:
        keys = self.category_index.get(category, [])
        return [(k, self.knowledge[k]) for k in keys if k in self.knowledge]

    def search_by_similarity(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[str, float, MemoryEntry]]:
        results = []
        for key, entry in self.knowledge.items():
            if entry.embedding is not None:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                results.append((key, similarity, entry))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

    def update(self, key: str, content: str, metadata: Dict[str, Any] = None):
        if key in self.knowledge:
            self.knowledge[key].content = content
            if metadata:
                self.knowledge[key].metadata.update(metadata)
            self.knowledge[key].timestamp = time.time()

    def delete(self, key: str) -> bool:
        if key in self.knowledge:
            entry = self.knowledge[key]
            category = entry.metadata.get("category", "general")
            if category in self.category_index and key in self.category_index[category]:
                self.category_index[category].remove(key)
            del self.knowledge[key]
            return True
        return False

    def get_all_keys(self) -> List[str]:
        return list(self.knowledge.keys())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "knowledge": {k: v.to_dict() for k, v in self.knowledge.items()},
            "embedding_dim": self.embedding_dim,
            "category_index": self.category_index
        }

    def from_dict(self, data: Dict[str, Any]):
        self.knowledge = {k: MemoryEntry.from_dict(v) for k, v in data.get("knowledge", {}).items()}
        self.embedding_dim = data.get("embedding_dim", 384)
        self.category_index = data.get("category_index", {})


class WorkingMemory:
    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.items: deque = deque(maxlen=capacity)
        self.context: Dict[str, Any] = {}
        self.focus: Optional[str] = None

    def add(self, item: str, priority: float = 1.0) -> bool:
        entry = {
            "content": item,
            "timestamp": time.time(),
            "priority": priority,
            "access_count": 0
        }
        self.items.append(entry)
        return True

    def get_current(self) -> List[Dict[str, Any]]:
        return list(self.items)

    def get_focus(self) -> Optional[str]:
        return self.focus

    def set_focus(self, item: str):
        self.focus = item
        for entry in self.items:
            if entry["content"] == item:
                entry["access_count"] += 1

    def clear_focus(self):
        self.focus = None

    def update_context(self, key: str, value: Any):
        self.context[key] = value

    def get_context(self, key: str) -> Optional[Any]:
        return self.context.get(key)

    def clear_context(self):
        self.context.clear()

    def get_all_context(self) -> Dict[str, Any]:
        return self.context.copy()

    def clear(self):
        self.items.clear()
        self.context.clear()
        self.focus = None

    def is_full(self) -> bool:
        return len(self.items) >= self.capacity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": list(self.items),
            "context": self.context,
            "focus": self.focus,
            "capacity": self.capacity
        }

    def from_dict(self, data: Dict[str, Any]):
        self.items = deque(data.get("items", []), maxlen=self.capacity)
        self.context = data.get("context", {})
        self.focus = data.get("focus")
        self.capacity = data.get("capacity", 7)


class MemoryManager:
    def __init__(self, storage_path: Optional[str] = None):
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.working = WorkingMemory()
        self.storage_path = storage_path

    def store_interaction(self, user_input: str, agent_response: str, 
                         embedding: Optional[np.ndarray] = None, metadata: Dict[str, Any] = None):
        content = f"User: {user_input}\nAgent: {agent_response}"
        memory_id = self.episodic.store(content, metadata, embedding)
        self.working.add(f"Interaction: {user_input[:50]}...")
        return memory_id

    def store_knowledge(self, key: str, content: str, category: str = "general",
                       embedding: Optional[np.ndarray] = None, metadata: Dict[str, Any] = None):
        return self.semantic.store(key, content, category, embedding, metadata)

    def retrieve_relevant(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        episodic_results = []
        for entry in self.episodic.memories[-100:]:
            if entry.embedding is not None:
                sim = self._cosine_similarity(query_embedding, entry.embedding)
                episodic_results.append({"type": "episodic", "similarity": sim, "entry": entry})

        semantic_results = self.semantic.search_by_similarity(query_embedding, top_k)

        all_results = episodic_results + [
            {"type": "semantic", "similarity": sim, "entry": entry, "key": key}
            for key, sim, entry in semantic_results
        ]

        all_results.sort(key=lambda x: x["similarity"], reverse=True)
        return all_results[:top_k]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

    def get_working_memory(self) -> List[Dict[str, Any]]:
        return self.working.get_current()

    def update_context(self, key: str, value: Any):
        self.working.update_context(key, value)

    def get_context(self, key: str) -> Optional[Any]:
        return self.working.get_context(key)

    def save(self, path: Optional[str] = None):
        save_path = path or self.storage_path
        if save_path:
            data = {
                "episodic": self.episodic.to_dict(),
                "semantic": self.semantic.to_dict(),
                "working": self.working.to_dict()
            }
            with open(save_path, 'w') as f:
                json.dump(data, f, default=str)

    def load(self, path: Optional[str] = None):
        load_path = path or self.storage_path
        if load_path:
            try:
                with open(load_path, 'r') as f:
                    data = json.load(f)
                self.episodic.from_dict(data.get("episodic", {}))
                self.semantic.from_dict(data.get("semantic", {}))
                self.working.from_dict(data.get("working", {}))
            except FileNotFoundError:
                pass

    def clear_all(self):
        self.episodic.clear()
        self.semantic = SemanticMemory()
        self.working.clear()
