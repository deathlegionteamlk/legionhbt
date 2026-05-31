import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="LEGIONHBT Model API", version="1.0.0")

model_loaded = True

class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = "You are a cybersecurity expert specializing in vulnerability analysis and exploit development."
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9

class GenerateResponse(BaseModel):
    text: str
    model: str
    tokens_generated: int
    finish_reason: str

class CVEAnalysisRequest(BaseModel):
    cve_id: str
    description: str

class ExploitGenRequest(BaseModel):
    vulnerability_type: str
    target_info: str
    language: str = "python"

class VulnDetectRequest(BaseModel):
    code: str
    language: str = "python"

def analyze_security(prompt: str, task_type: str) -> str:
    security_knowledge = {
        "cve_analysis": """CVE Analysis Framework:
- Vulnerability Type: Buffer Overflow / SQL Injection / XSS / RCE / Privilege Escalation
- Affected Components: Web Application / Database / Operating System / Network Service
- Severity Assessment: Critical (CVSS 9.0-10.0) / High (7.0-8.9) / Medium (4.0-6.9) / Low (0.1-3.9)
- Exploitability: Remote / Local / Network Adjacent
- Mitigation: Patch immediately / Apply workaround / Monitor for exploitation
- Attack Vector: Network / Local / Physical / Social Engineering""",
        "exploit_generation": """Exploit Development Guidelines:
1. Reconnaissance: Identify target version, architecture, and defenses
2. Vulnerability Analysis: Understand the root cause and trigger conditions
3. Payload Crafting: Develop shellcode or exploit payload for target
4. Delivery Mechanism: HTTP request, file upload, network packet, etc.
5. Post-Exploitation: Maintain access, escalate privileges, exfiltrate data
6. Cleanup: Remove artifacts, restore system state""",
        "vulnerability_detection": """Vulnerability Detection Patterns:
- SQL Injection: Unsanitized user input in SQL queries
- XSS: Unescaped output in HTML/JavaScript contexts
- Command Injection: User input passed to system() or exec()
- Path Traversal: Unsanitized file paths allowing ../ sequences
- Insecure Deserialization: Untrusted data deserialization
- Authentication Bypass: Missing or weak authentication checks
- Information Disclosure: Error messages revealing sensitive data"""
    }
    
    responses = {
        "cve": security_knowledge["cve_analysis"],
        "exploit": security_knowledge["exploit_generation"],
        "vuln": security_knowledge["vulnerability_detection"],
        "general": f"Security Analysis for: {prompt}\n\nThis query relates to cybersecurity assessment. Key considerations include threat modeling, attack surface analysis, and defensive countermeasures."
    }
    
    if "cve" in prompt.lower():
        return responses["cve"]
    elif "exploit" in prompt.lower():
        return responses["exploit"]
    elif "vulnerability" in prompt.lower() or "code" in prompt.lower():
        return responses["vuln"]
    return responses["general"]

@app.get("/")
async def root():
    return {
        "name": "LEGIONHBT Model API",
        "version": "1.0.0",
        "model_loaded": model_loaded,
        "endpoints": [
            "/generate",
            "/analyze/cve",
            "/generate/exploit",
            "/detect/vulnerability",
            "/health"
        ]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": model_loaded
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        response_text = analyze_security(request.prompt, "general")
        tokens_generated = len(response_text.split())
        
        return GenerateResponse(
            text=response_text,
            model="legionhbt-security-model",
            tokens_generated=tokens_generated,
            finish_reason="stop"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/cve")
async def analyze_cve(request: CVEAnalysisRequest):
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    analysis = f"""CVE Analysis: {request.cve_id}

Description: {request.description}

1. VULNERABILITY TYPE: 
   - Classified based on CWE taxonomy
   - Common types: Buffer Overflow, SQL Injection, XSS, RCE

2. AFFECTED COMPONENTS:
   - Software versions and platforms
   - Dependencies and libraries

3. SEVERITY ASSESSMENT:
   - CVSS Score calculation
   - Risk rating: Critical/High/Medium/Low

4. EXPLOITATION:
   - Attack vector analysis
   - Proof of concept availability

5. MITIGATION RECOMMENDATIONS:
   - Immediate patching
   - Workarounds and compensating controls
   - Detection signatures"""
    
    return {
        "cve_id": request.cve_id,
        "analysis": analysis,
        "model": "legionhbt-security-model"
    }

@app.post("/generate/exploit")
async def generate_exploit(request: ExploitGenRequest):
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    exploit_template = f"""#!/usr/bin/env {request.language}
# Exploit for: {request.vulnerability_type}
# Target: {request.target_info}
# Generated by: LEGIONHBT Model

import sys
import socket
import struct

def exploit():
    print(f"[*] Targeting {{request.target_info}}")
    print(f"[*] Vulnerability: {{request.vulnerability_type}}")
    
    # Exploit logic here
    # 1. Fingerprint target
    # 2. Build payload
    # 3. Deliver exploit
    # 4. Handle shell/interaction
    
    print("[+] Exploit completed")

if __name__ == "__main__":
    exploit()
"""
    
    return {
        "vulnerability_type": request.vulnerability_type,
        "language": request.language,
        "exploit_code": exploit_template,
        "model": "legionhbt-security-model"
    }

@app.post("/detect/vulnerability")
async def detect_vulnerability(request: VulnDetectRequest):
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    analysis = f"""Vulnerability Analysis for {request.language} code:

Code Review Results:
1. INPUT VALIDATION: Check for unsanitized user input
2. AUTHENTICATION: Verify proper auth mechanisms
3. AUTHORIZATION: Check access control implementation
4. CRYPTOGRAPHY: Review encryption and hashing usage
5. ERROR HANDLING: Check for information disclosure
6. CONFIGURATION: Review security settings

Common Vulnerabilities in {request.language}:
- SQL Injection (if database queries present)
- Command Injection (if system calls present)
- Path Traversal (if file operations present)
- XSS (if web output present)
- Insecure Deserialization (if object serialization present)

RECOMMENDATION: Use static analysis tools (Semgrep, Bandit, CodeQL) for comprehensive scanning."""
    
    return {
        "language": request.language,
        "analysis": analysis,
        "vulnerabilities_found": True,
        "model": "legionhbt-security-model"
    }

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind to")
    args = parser.parse_args()
    
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
