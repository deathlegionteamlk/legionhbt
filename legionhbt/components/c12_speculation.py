import copy
import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading


class SpeculationStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    VALIDATING = "validating"
    COMMITTED = "committed"
    DISCARDED = "discarded"
    MERGED = "merged"


@dataclass
class SpeculationLayer:
    layer_id: str
    parent_layer: Optional[str]
    name: str
    state_overlay: Dict[str, Any]
    changes: List[Dict[str, Any]]
    status: SpeculationStatus
    created_at: str
    committed_at: Optional[str] = None
    validation_results: Dict[str, Any] = field(default_factory=dict)


class C12SpeculationLayer:
    def __init__(self):
        self._layers: Dict[str, SpeculationLayer] = {}
        self._base_state: Dict[str, Any] = {}
        self._active_layer: Optional[str] = None
        self._layer_stack: List[str] = []
        self._lock = threading.Lock()
        self._validation_hooks: List[Callable[[SpeculationLayer], bool]] = []
        self._commit_hooks: List[Callable[[SpeculationLayer], None]] = []
    
    def create_layer(self, name: str, 
                     parent_layer: Optional[str] = None) -> str:
        layer_id = hashlib.sha256(f"{name}:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        if parent_layer and parent_layer not in self._layers:
            parent_layer = None
        
        layer = SpeculationLayer(
            layer_id=layer_id,
            parent_layer=parent_layer or self._active_layer,
            name=name,
            state_overlay={},
            changes=[],
            status=SpeculationStatus.DRAFT,
            created_at=datetime.utcnow().isoformat()
        )
        
        with self._lock:
            self._layers[layer_id] = layer
            self._active_layer = layer_id
            self._layer_stack.append(layer_id)
        
        return layer_id
    
    def get_state(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if self._active_layer:
                layer = self._layers[self._active_layer]
                if key in layer.state_overlay:
                    return layer.state_overlay[key]
                
                parent = layer.parent_layer
                while parent:
                    parent_layer = self._layers.get(parent)
                    if parent_layer and key in parent_layer.state_overlay:
                        return parent_layer.state_overlay[key]
                    parent = parent_layer.parent_layer if parent_layer else None
            
            return self._base_state.get(key, default)
    
    def set_state(self, key: str, value: Any):
        with self._lock:
            if not self._active_layer:
                self._base_state[key] = value
                return
            
            layer = self._layers[self._active_layer]
            old_value = layer.state_overlay.get(key)
            layer.state_overlay[key] = copy.deepcopy(value)
            
            layer.changes.append({
                "type": "set",
                "key": key,
                "old_value": old_value,
                "new_value": value,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def delete_state(self, key: str):
        with self._lock:
            if not self._active_layer:
                if key in self._base_state:
                    del self._base_state[key]
                return
            
            layer = self._layers[self._active_layer]
            old_value = layer.state_overlay.get(key)
            
            if key in layer.state_overlay:
                del layer.state_overlay[key]
            
            layer.changes.append({
                "type": "delete",
                "key": key,
                "old_value": old_value,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    def get_full_state(self) -> Dict[str, Any]:
        with self._lock:
            state = copy.deepcopy(self._base_state)
            
            for layer_id in self._layer_stack:
                layer = self._layers.get(layer_id)
                if layer:
                    state.update(layer.state_overlay)
            
            return state
    
    def switch_layer(self, layer_id: str) -> bool:
        with self._lock:
            if layer_id not in self._layers:
                return False
            
            self._active_layer = layer_id
            
            if layer_id in self._layer_stack:
                idx = self._layer_stack.index(layer_id)
                self._layer_stack = self._layer_stack[:idx + 1]
            else:
                self._layer_stack.append(layer_id)
            
            return True
    
    def commit_layer(self, layer_id: str) -> bool:
        with self._lock:
            if layer_id not in self._layers:
                return False
            
            layer = self._layers[layer_id]
            
            for hook in self._validation_hooks:
                if not hook(layer):
                    layer.status = SpeculationStatus.DISCARDED
                    return False
            
            if layer.parent_layer:
                parent = self._layers.get(layer.parent_layer)
                if parent:
                    parent.state_overlay.update(layer.state_overlay)
                    parent.changes.extend(layer.changes)
            else:
                self._base_state.update(layer.state_overlay)
            
            layer.status = SpeculationStatus.COMMITTED
            layer.committed_at = datetime.utcnow().isoformat()
            
            for hook in self._commit_hooks:
                hook(layer)
            
            return True
    
    def discard_layer(self, layer_id: str) -> bool:
        with self._lock:
            if layer_id not in self._layers:
                return False
            
            layer = self._layers[layer_id]
            layer.status = SpeculationStatus.DISCARDED
            
            if self._active_layer == layer_id:
                if layer.parent_layer:
                    self._active_layer = layer.parent_layer
                else:
                    self._active_layer = None
            
            if layer_id in self._layer_stack:
                self._layer_stack.remove(layer_id)
            
            return True
    
    def merge_layers(self, source_layer_id: str, 
                     target_layer_id: str) -> bool:
        with self._lock:
            if source_layer_id not in self._layers or target_layer_id not in self._layers:
                return False
            
            source = self._layers[source_layer_id]
            target = self._layers[target_layer_id]
            
            target.state_overlay.update(source.state_overlay)
            target.changes.extend(source.changes)
            
            source.status = SpeculationStatus.MERGED
            
            return True
    
    def get_layer_state_diff(self, layer_id: str) -> List[Dict]:
        if layer_id not in self._layers:
            return []
        
        layer = self._layers[layer_id]
        return layer.changes
    
    def compare_layers(self, layer_id1: str, 
                       layer_id2: str) -> Dict[str, Any]:
        if layer_id1 not in self._layers or layer_id2 not in self._layers:
            return {}
        
        layer1 = self._layers[layer_id1]
        layer2 = self._layers[layer_id2]
        
        keys1 = set(layer1.state_overlay.keys())
        keys2 = set(layer2.state_overlay.keys())
        
        common = keys1 & keys2
        only_in_1 = keys1 - keys2
        only_in_2 = keys2 - keys1
        
        differences = {}
        for key in common:
            if layer1.state_overlay[key] != layer2.state_overlay[key]:
                differences[key] = {
                    "layer1": layer1.state_overlay[key],
                    "layer2": layer2.state_overlay[key]
                }
        
        return {
            "common_keys": list(common),
            "only_in_layer1": list(only_in_1),
            "only_in_layer2": list(only_in_2),
            "differences": differences
        }
    
    def add_validation_hook(self, hook: Callable[[SpeculationLayer], bool]):
        self._validation_hooks.append(hook)
    
    def add_commit_hook(self, hook: Callable[[SpeculationLayer], None]):
        self._commit_hooks.append(hook)
    
    def get_active_layer(self) -> Optional[str]:
        return self._active_layer
    
    def get_layer(self, layer_id: str) -> Optional[SpeculationLayer]:
        return self._layers.get(layer_id)
    
    def list_layers(self) -> List[str]:
        return list(self._layers.keys())
    
    def get_layer_stack(self) -> List[str]:
        return self._layer_stack.copy()
    
    def export_layer(self, layer_id: str) -> Optional[Dict]:
        layer = self._layers.get(layer_id)
        if not layer:
            return None
        
        return {
            "layer_id": layer.layer_id,
            "name": layer.name,
            "parent_layer": layer.parent_layer,
            "state_overlay": layer.state_overlay,
            "changes": layer.changes,
            "status": layer.status.value,
            "created_at": layer.created_at,
            "committed_at": layer.committed_at,
            "validation_results": layer.validation_results
        }
    
    def import_layer(self, data: Dict) -> Optional[str]:
        layer_id = data.get("layer_id")
        if not layer_id or layer_id in self._layers:
            layer_id = hashlib.sha256(f"imported:{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]
        
        layer = SpeculationLayer(
            layer_id=layer_id,
            parent_layer=data.get("parent_layer"),
            name=data.get("name", "imported"),
            state_overlay=data.get("state_overlay", {}),
            changes=data.get("changes", []),
            status=SpeculationStatus(data.get("status", "draft")),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            committed_at=data.get("committed_at"),
            validation_results=data.get("validation_results", {})
        )
        
        self._layers[layer_id] = layer
        return layer_id
