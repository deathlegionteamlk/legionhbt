import hashlib
import json
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import graphlib


class ChainStatus(Enum):
    DRAFT = "draft"
    BUILDING = "building"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BROKEN = "broken"


class LinkType(Enum):
    DEPENDENCY = "dependency"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"


@dataclass
class ChainLink:
    link_id: str
    name: str
    link_type: LinkType
    action: Dict[str, Any]
    dependencies: List[str]
    outputs: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class CriticalPathChain:
    chain_id: str
    name: str
    description: str
    links: Dict[str, ChainLink]
    execution_order: List[str]
    status: ChainStatus
    entry_points: List[str]
    exit_points: List[str]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class C10ChainBuilder:
    def __init__(self):
        self._chains: Dict[str, CriticalPathChain] = {}
        self._execution_history: List[Dict] = []
        self._link_handlers: Dict[str, Callable[[Dict], Any]] = {}

    def create_chain(self, name: str, description: str,
                     links_data: List[Dict],
                     metadata: Optional[Dict] = None) -> str:
        chain_id = hashlib.sha256(f"{name}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        now = datetime.utcnow().isoformat()

        links = {}
        for i, link_data in enumerate(links_data):
            link_id = f"{chain_id}_link_{i}"
            link = ChainLink(
                link_id=link_id,
                name=link_data.get("name", f"Link {i}"),
                link_type=LinkType(link_data.get("type", "sequential")),
                action=link_data.get("action", {}),
                dependencies=link_data.get("dependencies", []),
                max_retries=link_data.get("max_retries", 3)
            )
            links[link_id] = link

        execution_order = self._compute_execution_order(links)
        entry_points = self._find_entry_points(links)
        exit_points = self._find_exit_points(links)

        chain = CriticalPathChain(
            chain_id=chain_id,
            name=name,
            description=description,
            links=links,
            execution_order=execution_order,
            status=ChainStatus.DRAFT,
            entry_points=entry_points,
            exit_points=exit_points,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )

        self._chains[chain_id] = chain
        return chain_id

    def _compute_execution_order(self, links: Dict[str, ChainLink]) -> List[str]:
        graph = {link_id: set(link.dependencies) for link_id, link in links.items()}

        try:
            ts = graphlib.TopologicalSorter(graph)
            return list(ts.static_order())
        except:
            return list(links.keys())

    def _find_entry_points(self, links: Dict[str, ChainLink]) -> List[str]:
        all_deps = set()
        for link in links.values():
            all_deps.update(link.dependencies)

        return [link_id for link_id in links if link_id not in all_deps]

    def _find_exit_points(self, links: Dict[str, ChainLink]) -> List[str]:
        all_deps = set()
        for link in links.values():
            all_deps.update(link.dependencies)

        link_ids = set(links.keys())
        dependents = {link_id for link_id in link_ids if any(link_id in links[other].dependencies for other in link_ids)}

        return [link_id for link_id in link_ids if link_id not in dependents]

    def add_link(self, chain_id: str, link_data: Dict) -> Optional[str]:
        if chain_id not in self._chains:
            return None

        chain = self._chains[chain_id]
        link_id = f"{chain_id}_link_{len(chain.links)}"

        link = ChainLink(
            link_id=link_id,
            name=link_data.get("name", f"Link {len(chain.links)}"),
            link_type=LinkType(link_data.get("type", "sequential")),
            action=link_data.get("action", {}),
            dependencies=link_data.get("dependencies", []),
            max_retries=link_data.get("max_retries", 3)
        )

        chain.links[link_id] = link
        chain.execution_order = self._compute_execution_order(chain.links)
        chain.entry_points = self._find_entry_points(chain.links)
        chain.exit_points = self._find_exit_points(chain.links)
        chain.updated_at = datetime.utcnow().isoformat()

        return link_id

    def execute_chain(self, chain_id: str,
                      context: Optional[Dict] = None) -> Dict[str, Any]:
        if chain_id not in self._chains:
            return {"error": "Chain not found"}

        chain = self._chains[chain_id]
        chain.status = ChainStatus.EXECUTING

        ctx = context or {}
        results = {}
        failed_links = []

        for link_id in chain.execution_order:
            link = chain.links[link_id]

            deps_satisfied = all(
                chain.links.get(dep) and chain.links[dep].status == "completed"
                for dep in link.dependencies
            )

            if not deps_satisfied:
                failed_links.append(link_id)
                link.status = "skipped"
                continue

            success = self._execute_link(chain, link, ctx)

            if success:
                link.status = "completed"
                results[link_id] = link.outputs
            else:
                link.status = "failed"
                failed_links.append(link_id)
                if link.retry_count >= link.max_retries:
                    chain.status = ChainStatus.FAILED
                    break

        if not failed_links:
            chain.status = ChainStatus.COMPLETED
        elif chain.status != ChainStatus.FAILED:
            chain.status = ChainStatus.BROKEN

        self._execution_history.append({
            "chain_id": chain_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": chain.status.value,
            "results": results,
            "failed_links": failed_links
        })

        return {
            "chain_id": chain_id,
            "status": chain.status.value,
            "results": results,
            "failed_links": failed_links
        }

    def _execute_link(self, chain: CriticalPathChain,
                      link: ChainLink, context: Dict) -> bool:
        action_type = link.action.get("type")
        handler = self._link_handlers.get(action_type)

        if not handler:
            link.outputs = {"error": f"No handler for action type: {action_type}"}
            return False

        try:
            result = handler(link.action.get("params", {}), context)
            link.outputs = {"result": result}
            return True
        except Exception as e:
            link.retry_count += 1
            link.outputs = {"error": str(e)}
            return False

    def register_link_handler(self, action_type: str,
                              handler: Callable[[Dict, Dict], Any]):
        self._link_handlers[action_type] = handler

    def get_chain(self, chain_id: str) -> Optional[CriticalPathChain]:
        return self._chains.get(chain_id)

    def get_chain_status(self, chain_id: str) -> Dict:
        chain = self._chains.get(chain_id)
        if not chain:
            return {}

        total = len(chain.links)
        completed = sum(1 for l in chain.links.values() if l.status == "completed")
        failed = sum(1 for l in chain.links.values() if l.status == "failed")
        pending = sum(1 for l in chain.links.values() if l.status == "pending")

        return {
            "chain_id": chain_id,
            "name": chain.name,
            "status": chain.status.value,
            "progress": completed / total if total > 0 else 0,
            "total_links": total,
            "completed": completed,
            "failed": failed,
            "pending": pending
        }

    def validate_chain(self, chain_id: str) -> List[str]:
        chain = self._chains.get(chain_id)
        if not chain:
            return ["Chain not found"]

        errors = []

        for link_id, link in chain.links.items():
            for dep in link.dependencies:
                if dep not in chain.links:
                    errors.append(f"Link {link_id} has unknown dependency: {dep}")

        try:
            self._compute_execution_order(chain.links)
        except:
            errors.append("Circular dependency detected")

        if not chain.entry_points:
            errors.append("No entry points found")

        return errors

    def clone_chain(self, chain_id: str, new_name: Optional[str] = None) -> Optional[str]:
        chain = self._chains.get(chain_id)
        if not chain:
            return None

        links_data = [
            {
                "name": link.name,
                "type": link.link_type.value,
                "action": link.action,
                "dependencies": link.dependencies,
                "max_retries": link.max_retries
            }
            for link in chain.links.values()
        ]

        return self.create_chain(
            name=new_name or f"{chain.name}_copy",
            description=chain.description,
            links_data=links_data,
            metadata=chain.metadata.copy()
        )

    def get_critical_path(self, chain_id: str) -> List[str]:
        chain = self._chains.get(chain_id)
        if not chain:
            return []

        return chain.execution_order

    def list_chains(self) -> List[str]:
        return list(self._chains.keys())
