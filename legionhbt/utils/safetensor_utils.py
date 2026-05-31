import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import struct


@dataclass
class TensorMetadata:
    name: str
    shape: List[int]
    dtype: str
    offset: int
    length: int
    hash: str


@dataclass
class SafetensorFile:
    path: str
    header: Dict[str, Any]
    tensors: Dict[str, TensorMetadata]
    metadata: Dict[str, Any]
    hash: str


class SafetensorManager:
    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        self._loaded_models: Dict[str, SafetensorFile] = {}
    
    def _parse_dtype(self, dtype_str: str) -> str:
        dtype_map = {
            "F64": "float64",
            "F32": "float32",
            "F16": "float16",
            "BF16": "bfloat16",
            "I64": "int64",
            "I32": "int32",
            "I16": "int16",
            "I8": "int8",
            "U8": "uint8",
            "BOOL": "bool"
        }
        return dtype_map.get(dtype_str, dtype_str)
    
    def load_safetensor(self, filepath: str, 
                        model_id: Optional[str] = None) -> Optional[SafetensorFile]:
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'rb') as f:
                header_len = struct.unpack('<Q', f.read(8))[0]
                header_bytes = f.read(header_len)
                header = json.loads(header_bytes.decode('utf-8'))
            
            tensors = {}
            metadata = header.get("__metadata__", {})
            
            offset = 8 + header_len
            
            for key, value in header.items():
                if key == "__metadata__":
                    continue
                
                tensor_meta = TensorMetadata(
                    name=key,
                    shape=value["shape"],
                    dtype=self._parse_dtype(value["dtype"]),
                    offset=offset,
                    length=value["data_offsets"][1] - value["data_offsets"][0],
                    hash=""
                )
                tensors[key] = tensor_meta
                offset += tensor_meta.length
            
            with open(filepath, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            safetensor = SafetensorFile(
                path=filepath,
                header=header,
                tensors=tensors,
                metadata=metadata,
                hash=file_hash
            )
            
            model_key = model_id or os.path.basename(filepath)
            self._loaded_models[model_key] = safetensor
            
            return safetensor
            
        except Exception:
            return None
    
    def save_safetensor(self, tensors: Dict[str, Any], 
                        filepath: str,
                        metadata: Optional[Dict] = None) -> bool:
        try:
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            
            header = {}
            if metadata:
                header["__metadata__"] = metadata
            
            tensor_data = []
            current_offset = 0
            
            for name, tensor in tensors.items():
                if hasattr(tensor, 'shape') and hasattr(tensor, 'dtype'):
                    shape = list(tensor.shape)
                    dtype_str = str(tensor.dtype).upper().replace('TORCH.', '').replace('FLOAT', 'F').replace('INT', 'I').replace('UINT', 'U')
                    data = tensor.detach().cpu().numpy().tobytes() if hasattr(tensor, 'detach') else tensor.tobytes()
                elif isinstance(tensor, dict):
                    shape = tensor.get('shape', [])
                    dtype_str = tensor.get('dtype', 'F32')
                    data = tensor.get('data', b'')
                else:
                    continue
                
                data_len = len(data)
                header[name] = {
                    "dtype": dtype_str,
                    "shape": shape,
                    "data_offsets": [current_offset, current_offset + data_len]
                }
                tensor_data.append(data)
                current_offset += data_len
            
            header_bytes = json.dumps(header, separators=(',', ':')).encode('utf-8')
            header_len = len(header_bytes)
            
            with open(filepath, 'wb') as f:
                f.write(struct.pack('<Q', header_len))
                f.write(header_bytes)
                for data in tensor_data:
                    f.write(data)
            
            return True
            
        except Exception:
            return False
    
    def get_tensor_info(self, model_id: str, 
                        tensor_name: str) -> Optional[TensorMetadata]:
        model = self._loaded_models.get(model_id)
        if not model:
            return None
        return model.tensors.get(tensor_name)
    
    def list_tensors(self, model_id: str) -> List[str]:
        model = self._loaded_models.get(model_id)
        if not model:
            return []
        return list(model.tensors.keys())
    
    def get_model_metadata(self, model_id: str) -> Dict[str, Any]:
        model = self._loaded_models.get(model_id)
        if not model:
            return {}
        return model.metadata
    
    def verify_integrity(self, model_id: str) -> bool:
        model = self._loaded_models.get(model_id)
        if not model:
            return False
        
        if not os.path.exists(model.path):
            return False
        
        with open(model.path, 'rb') as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        
        return current_hash == model.hash
    
    def list_loaded_models(self) -> List[str]:
        return list(self._loaded_models.keys())
    
    def unload_model(self, model_id: str) -> bool:
        if model_id in self._loaded_models:
            del self._loaded_models[model_id]
            return True
        return False
    
    def get_model_stats(self, model_id: str) -> Dict[str, Any]:
        model = self._loaded_models.get(model_id)
        if not model:
            return {}
        
        total_params = 0
        total_bytes = 0
        
        for tensor in model.tensors.values():
            params = 1
            for dim in tensor.shape:
                params *= dim
            total_params += params
            total_bytes += tensor.length
        
        return {
            "model_id": model_id,
            "path": model.path,
            "tensor_count": len(model.tensors),
            "total_parameters": total_params,
            "total_bytes": total_bytes,
            "total_mb": total_bytes / (1024 * 1024),
            "hash": model.hash[:16] + "...",
            "metadata_keys": list(model.metadata.keys())
        }
    
    def convert_from_pytorch(self, pytorch_path: str, 
                             output_path: str) -> bool:
        try:
            import torch
            
            state_dict = torch.load(pytorch_path, map_location='cpu')
            
            tensors = {}
            for key, value in state_dict.items():
                if hasattr(value, 'numpy'):
                    tensors[key] = value
            
            return self.save_safetensor(tensors, output_path)
            
        except Exception:
            return False
    
    def scan_models_directory(self) -> List[str]:
        models = []
        
        if not os.path.exists(self.models_dir):
            return models
        
        for root, dirs, files in os.walk(self.models_dir):
            for file in files:
                if file.endswith('.safetensors') or file.endswith('.safetensor'):
                    models.append(os.path.join(root, file))
        
        return models
