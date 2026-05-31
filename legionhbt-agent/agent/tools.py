import json
import subprocess
import socket
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import nmap
import paramiko
import pexpect


@dataclass
class ToolResult:
    success: bool
    output: str
    error: Optional[str] = None
    data: Optional[Dict] = None


class NmapTool:
    def __init__(self):
        self.name = "nmap_scan"
        self.description = "Perform network port scanning using nmap"
        self.risk_level = "MEDIUM"
    
    def execute(self, target: str, ports: str = "1-1000", scan_type: str = "syn") -> ToolResult:
        try:
            nm = nmap.PortScanner()
            arguments = "-sS" if scan_type == "syn" else "-sT"
            arguments += " -T4 --open"
            
            nm.scan(target, ports, arguments=arguments)
            
            results = {
                "target": target,
                "command": f"nmap {arguments} -p {ports} {target}",
                "hosts": []
            }
            
            for host in nm.all_hosts():
                host_info = {
                    "host": host,
                    "state": nm[host].state(),
                    "protocols": {}
                }
                for proto in nm[host].all_protocols():
                    ports_info = {}
                    for port in nm[host][proto].keys():
                        port_data = nm[host][proto][port]
                        ports_info[port] = {
                            "state": port_data["state"],
                            "service": port_data.get("name", "unknown"),
                            "version": port_data.get("version", ""),
                            "product": port_data.get("product", "")
                        }
                    host_info["protocols"][proto] = ports_info
                results["hosts"].append(host_info)
            
            return ToolResult(
                success=True,
                output=json.dumps(results, indent=2),
                data=results
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class MetasploitTool:
    def __init__(self):
        self.name = "metasploit"
        self.description = "Execute Metasploit framework commands and modules"
        self.risk_level = "HIGH"
    
    def execute(self, module: str, options: Dict[str, str] = None, action: str = "check") -> ToolResult:
        try:
            if action == "check":
                cmd = f"msfconsole -q -x 'use {module}; show options; exit'"
            elif action == "run":
                opts = "; ".join([f"set {k} {v}" for k, v in (options or {}).items()])
                cmd = f"msfconsole -q -x 'use {module}; {opts}; run; exit'"
            else:
                cmd = f"msfconsole -q -x 'search {module}; exit'"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            return ToolResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None,
                data={"command": cmd, "returncode": result.returncode}
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error="Metasploit command timed out"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class SSHBruteTool:
    def __init__(self):
        self.name = "ssh_brute"
        self.description = "SSH brute force and connection testing"
        self.risk_level = "HIGH"
    
    def execute(self, target: str, port: int = 22, username: str = None, password: str = None, 
                userlist: str = None, passlist: str = None) -> ToolResult:
        try:
            if username and password:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(target, port=port, username=username, password=password, timeout=10)
                stdin, stdout, stderr = client.exec_command("whoami")
                result = stdout.read().decode().strip()
                client.close()
                
                return ToolResult(
                    success=True,
                    output=f"Successfully connected as: {result}",
                    data={"username": username, "authenticated": True}
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error="Username and password required for SSH connection"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class WebScannerTool:
    def __init__(self):
        self.name = "web_scan"
        self.description = "Web application vulnerability scanning"
        self.risk_level = "MEDIUM"
    
    def execute(self, url: str, scan_type: str = "headers") -> ToolResult:
        try:
            import requests
            from urllib.parse import urlparse
            
            results = {"url": url, "findings": []}
            
            if scan_type in ["headers", "full"]:
                response = requests.get(url, timeout=30, verify=False)
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
            
            if scan_type in ["dirs", "full"]:
                common_paths = ["/admin", "/login", "/api", "/config", "/.env", "/robots.txt"]
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
            
            return ToolResult(
                success=True,
                output=json.dumps(results, indent=2),
                data=results
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class ExploitTool:
    def __init__(self):
        self.name = "custom_exploit"
        self.description = "Execute custom exploit scripts"
        self.risk_level = "HIGH"
    
    def execute(self, exploit_code: str, target: str, language: str = "python") -> ToolResult:
        try:
            if language == "python":
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(exploit_code)
                    temp_file = f.name
                
                result = subprocess.run(
                    ['python3', temp_file, target],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                os.unlink(temp_file)
                
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr if result.stderr else None,
                    data={"returncode": result.returncode}
                )
            elif language == "bash":
                result = subprocess.run(
                    exploit_code,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                return ToolResult(
                    success=result.returncode == 0,
                    output=result.stdout,
                    error=result.stderr if result.stderr else None
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unsupported language: {language}"
                )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error="Exploit execution timed out"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )


class ToolRegistry:
    def __init__(self):
        self.tools = {
            "nmap_scan": NmapTool(),
            "metasploit": MetasploitTool(),
            "ssh_brute": SSHBruteTool(),
            "web_scan": WebScannerTool(),
            "custom_exploit": ExploitTool()
        }
    
    def get_tool(self, name: str) -> Optional[Any]:
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "risk_level": tool.risk_level
            }
            for tool in self.tools.values()
        ]
    
    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{tool_name}' not found"
            )
        return tool.execute(**kwargs)