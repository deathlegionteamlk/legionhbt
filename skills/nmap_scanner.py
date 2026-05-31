import subprocess
import json
from typing import Dict, Any

def execute(config: Dict[str, Any]) -> Dict[str, Any]:
    target = config.get("target", "")
    ports = config.get("ports", "1-65535")
    scan_type = config.get("scan_type", "syn")
    
    if not target:
        return {"error": "Target is required"}
    
    scan_flags = {
        "syn": "-sS",
        "connect": "-sT",
        "udp": "-sU"
    }
    
    flag = scan_flags.get(scan_type, "-sS")
    
    try:
        cmd = f"nmap {flag} -p {ports} -sV -oX - {target}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        return {
            "skill_id": "nmap_scanner",
            "status": "completed" if result.returncode == 0 else "failed",
            "target": target,
            "ports": ports,
            "scan_type": scan_type,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {"error": "Scan timed out"}
    except Exception as e:
        return {"error": str(e)}
