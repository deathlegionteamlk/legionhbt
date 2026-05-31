import subprocess
import json
from typing import Dict, Optional
from dataclasses import dataclass
import requests
from urllib.parse import urlparse


@dataclass
class ToolResult:
    success: bool
    output: str
    error: Optional[str] = None
    data: Optional[Dict] = None


class NmapTool:
    def __init__(self):
        self.name = "nmap_scan"
        self.description = "Network port scanning"
        self.risk_level = "MEDIUM"
    
    def execute(self, target: str, ports: str = "1-1000") -> ToolResult:
        try:
            import nmap
            nm = nmap.PortScanner()
            nm.scan(target, ports, arguments="-sS -T4 --open")
            
            results = {"target": target, "hosts": []}
            for host in nm.all_hosts():
                host_info = {"host": host, "state": nm[host].state(), "ports": []}
                for proto in nm[host].all_protocols():
                    for port in nm[host][proto].keys():
                        port_data = nm[host][proto][port]
                        host_info["ports"].append({
                            "port": port,
                            "state": port_data["state"],
                            "service": port_data.get("name", "unknown")
                        })
                results["hosts"].append(host_info)
            
            return ToolResult(success=True, output=json.dumps(results, indent=2), data=results)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class WebScannerTool:
    def __init__(self):
        self.name = "web_scan"
        self.description = "Web application security scanning"
        self.risk_level = "MEDIUM"
    
    def execute(self, url: str, scan_type: str = "headers") -> ToolResult:
        try:
            results = {"url": url, "findings": []}
            
            response = requests.get(url, timeout=30, verify=False, allow_redirects=True)
            headers = dict(response.headers)
            
            security_headers = ["X-Frame-Options", "X-XSS-Protection", "Content-Security-Policy",
                               "Strict-Transport-Security", "X-Content-Type-Options"]
            missing = [h for h in security_headers if h not in headers]
            
            results["findings"].append({
                "type": "security_headers",
                "missing": missing,
                "server": headers.get("Server", "Unknown"),
                "status_code": response.status_code
            })
            
            common_paths = ["/admin", "/login", "/api", "/config", "/.env", "/robots.txt", "/.git"]
            for path in common_paths:
                try:
                    full_url = url.rstrip("/") + path
                    resp = requests.get(full_url, timeout=10, verify=False, allow_redirects=False)
                    if resp.status_code in [200, 301, 302, 401, 403]:
                        results["findings"].append({
                            "type": "accessible_path",
                            "path": path,
                            "status": resp.status_code
                        })
                except:
                    pass
            
            return ToolResult(success=True, output=json.dumps(results, indent=2), data=results)
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


class BurpSuiteTool:
    def __init__(self):
        self.name = "burp_scan"
        self.description = "Burp Suite integration"
        self.risk_level = "MEDIUM"
    
    def execute(self, target: str, scan_config: Dict = None) -> ToolResult:
        return ToolResult(
            success=False,
            output="",
            error="Burp Suite requires Enterprise license. Use web_scan tool instead."
        )


class MetasploitTool:
    def __init__(self):
        self.name = "metasploit"
        self.description = "Metasploit framework integration"
        self.risk_level = "HIGH"
    
    def execute(self, module: str, options: Dict = None, action: str = "check") -> ToolResult:
        try:
            if action == "check":
                cmd = f"msfconsole -q -x 'use {module}; show options; exit' 2>/dev/null || echo 'Metasploit not installed'"
            else:
                opts = "; ".join([f"set {k} {v}" for k, v in (options or {}).items()])
                cmd = f"msfconsole -q -x 'use {module}; {opts}; run; exit' 2>/dev/null || echo 'Metasploit not installed'"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            return ToolResult(
                success="not installed" not in result.stdout.lower(),
                output=result.stdout,
                error=result.stderr if result.stderr else None
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Command timed out")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))