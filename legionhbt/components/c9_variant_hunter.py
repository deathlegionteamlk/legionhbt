import hashlib
import json
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import difflib


class VariantStatus(Enum):
    DISCOVERED = "discovered"
    ANALYZING = "analyzing"
    VALIDATED = "validated"
    DUPLICATE = "duplicate"
    MERGED = "merged"
    REJECTED = "rejected"


@dataclass
class Variant:
    variant_id: str
    parent_id: Optional[str]
    source_node: str
    mutation_type: str
    payload: Dict[str, Any]
    hash_signature: str
    status: VariantStatus
    similarity_to_parent: float
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VariantCluster:
    cluster_id: str
    root_variant: str
    variants: List[str]
    common_signature: str
    created_at: str


class C9VariantHunter:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self._variants: Dict[str, Variant] = {}
        self._clusters: Dict[str, VariantCluster] = {}
        self._hash_index: Dict[str, Set[str]] = {}
        self._source_index: Dict[str, Set[str]] = {}
        self._mutation_handlers: Dict[str, Callable[[Dict], List[Dict]]] = {}
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        self._mutation_handlers["parameter_variation"] = self._parameter_variation
        self._mutation_handlers["scope_expansion"] = self._scope_expansion
        self._mutation_handlers["approach_alternation"] = self._approach_alternation

    def hunt_variants(self, source_node: str, base_payload: Dict[str, Any],
                      mutation_types: Optional[List[str]] = None) -> List[str]:
        variant_ids = []
        mutations = mutation_types or list(self._mutation_handlers.keys())

        for mutation_type in mutations:
            handler = self._mutation_handlers.get(mutation_type)
            if not handler:
                continue

            try:
                mutated_payloads = handler(base_payload)
                for payload in mutated_payloads:
                    variant_id = self._create_variant(source_node, None, mutation_type, payload)
                    if variant_id:
                        variant_ids.append(variant_id)
            except:
                pass

        return variant_ids

    def _create_variant(self, source_node: str, parent_id: Optional[str],
                        mutation_type: str, payload: Dict[str, Any]) -> Optional[str]:
        payload_str = json.dumps(payload, sort_keys=True)
        hash_signature = hashlib.sha256(payload_str.encode()).hexdigest()[:32]

        if hash_signature in self._hash_index:
            existing = next(iter(self._hash_index[hash_signature]))
            return existing

        similarity = 1.0
        if parent_id and parent_id in self._variants:
            parent = self._variants[parent_id]
            similarity = self._calculate_similarity(payload, parent.payload)

            if similarity >= self.similarity_threshold:
                return None

        variant_id = hashlib.sha256(f"{source_node}:{mutation_type}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]

        variant = Variant(
            variant_id=variant_id,
            parent_id=parent_id,
            source_node=source_node,
            mutation_type=mutation_type,
            payload=payload,
            hash_signature=hash_signature,
            status=VariantStatus.DISCOVERED,
            similarity_to_parent=similarity,
            created_at=datetime.utcnow().isoformat()
        )

        self._variants[variant_id] = variant

        if hash_signature not in self._hash_index:
            self._hash_index[hash_signature] = set()
        self._hash_index[hash_signature].add(variant_id)

        if source_node not in self._source_index:
            self._source_index[source_node] = set()
        self._source_index[source_node].add(variant_id)

        self._check_for_duplicates(variant)

        return variant_id

    def _calculate_similarity(self, payload1: Dict, payload2: Dict) -> float:
        str1 = json.dumps(payload1, sort_keys=True)
        str2 = json.dumps(payload2, sort_keys=True)

        if str1 == str2:
            return 1.0

        matcher = difflib.SequenceMatcher(None, str1, str2)
        return matcher.ratio()

    def _check_for_duplicates(self, variant: Variant):
        for vid, other in self._variants.items():
            if vid == variant.variant_id:
                continue

            if other.hash_signature == variant.hash_signature:
                variant.status = VariantStatus.DUPLICATE
                return

            similarity = self._calculate_similarity(variant.payload, other.payload)
            if similarity >= self.similarity_threshold:
                if variant.created_at > other.created_at:
                    variant.status = VariantStatus.DUPLICATE
                else:
                    other.status = VariantStatus.DUPLICATE

    def _parameter_variation(self, payload: Dict) -> List[Dict]:
        variants = []

        for key, value in payload.items():
            if isinstance(value, (int, float)):
                variants.append({**payload, key: value * 1.5})
                variants.append({**payload, key: value * 0.5})
            elif isinstance(value, str):
                variants.append({**payload, key: value + "_variant"})
                variants.append({**payload, key: value.upper()})
            elif isinstance(value, list) and value:
                variants.append({**payload, key: value + [value[-1]]})
                variants.append({**payload, key: value[:-1]})

        return variants

    def _scope_expansion(self, payload: Dict) -> List[Dict]:
        variants = []

        if "scope" in payload:
            variants.append({**payload, "scope": "expanded_" + str(payload["scope"])})

        if "limit" in payload:
            variants.append({**payload, "limit": payload["limit"] * 2})

        variants.append({**payload, "deep_scan": True})

        return variants

    def _approach_alternation(self, payload: Dict) -> List[Dict]:
        variants = []

        if "method" in payload:
            methods = ["brute_force", "heuristic", "hybrid", "recursive"]
            current = payload["method"]
            for m in methods:
                if m != current:
                    variants.append({**payload, "method": m})

        if "strategy" in payload:
            strategies = ["aggressive", "conservative", "balanced"]
            current = payload["strategy"]
            for s in strategies:
                if s != current:
                    variants.append({**payload, "strategy": s})

        return variants

    def cluster_variants(self, source_node: str) -> Optional[str]:
        if source_node not in self._source_index:
            return None

        variant_ids = list(self._source_index[source_node])
        if len(variant_ids) < 2:
            return None

        cluster_id = hashlib.sha256(f"cluster:{source_node}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]

        root = variant_ids[0]
        signatures = [self._variants[vid].hash_signature for vid in variant_ids]
        common = hashlib.sha256("".join(sorted(signatures)).encode()).hexdigest()[:16]

        cluster = VariantCluster(
            cluster_id=cluster_id,
            root_variant=root,
            variants=variant_ids,
            common_signature=common,
            created_at=datetime.utcnow().isoformat()
        )

        self._clusters[cluster_id] = cluster
        return cluster_id

    def merge_variants(self, variant_ids: List[str], merged_payload: Dict[str, Any]) -> Optional[str]:
        if len(variant_ids) < 2:
            return None

        for vid in variant_ids:
            if vid in self._variants:
                self._variants[vid].status = VariantStatus.MERGED

        source_node = self._variants.get(variant_ids[0], Variant("", None, "", "", {}, "", VariantStatus.MERGED, 0.0, "")).source_node

        merged_id = self._create_variant(source_node, None, "merge", merged_payload)
        if merged_id:
            self._variants[merged_id].status = VariantStatus.VALIDATED

        return merged_id

    def get_variant(self, variant_id: str) -> Optional[Variant]:
        return self._variants.get(variant_id)

    def get_variants_by_source(self, source_node: str) -> List[Variant]:
        variant_ids = self._source_index.get(source_node, set())
        return [self._variants[vid] for vid in variant_ids if vid in self._variants]

    def get_unique_variants(self, source_node: str) -> List[Variant]:
        variants = self.get_variants_by_source(source_node)
        return [v for v in variants if v.status not in [VariantStatus.DUPLICATE, VariantStatus.MERGED]]

    def add_mutation_handler(self, mutation_type: str,
                             handler: Callable[[Dict], List[Dict]]):
        self._mutation_handlers[mutation_type] = handler

    def get_deduplication_stats(self) -> Dict:
        total = len(self._variants)
        duplicates = sum(1 for v in self._variants.values() if v.status == VariantStatus.DUPLICATE)
        merged = sum(1 for v in self._variants.values() if v.status == VariantStatus.MERGED)
        unique = total - duplicates - merged

        return {
            "total_variants": total,
            "duplicates": duplicates,
            "merged": merged,
            "unique": unique,
            "deduplication_ratio": duplicates / total if total > 0 else 0.0
        }

    def find_similar_variants(self, variant_id: str,
                              threshold: Optional[float] = None) -> List[str]:
        if variant_id not in self._variants:
            return []

        target = self._variants[variant_id]
        threshold = threshold or self.similarity_threshold
        similar = []

        for vid, variant in self._variants.items():
            if vid == variant_id:
                continue

            sim = self._calculate_similarity(target.payload, variant.payload)
            if sim >= threshold:
                similar.append(vid)

        return similar
