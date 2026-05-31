import json
import requests
from typing import List, Dict
from datetime import datetime
import os


class CVEIngester:
    def __init__(self):
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    def fetch_recent_cves(self, results_per_page: int = 100) -> List[Dict]:
        try:
            url = f"{self.base_url}?resultsPerPage={results_per_page}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            documents = []
            for item in data.get("vulnerabilities", []):
                cve = item.get("cve", {})
                cve_id = cve.get("id", "")
                description = cve.get("descriptions", [{}])[0].get("value", "")
                
                if cve_id and description:
                    documents.append({
                        "text": f"{cve_id}: {description}",
                        "source": "NVD",
                        "category": "CVE",
                        "metadata": {
                            "cve_id": cve_id,
                            "published": cve.get("published", ""),
                            "severity": self._extract_severity(cve)
                        }
                    })
            
            return documents
        except Exception as e:
            print(f"Error fetching CVEs: {e}")
            return []
    
    def _extract_severity(self, cve: Dict) -> str:
        metrics = cve.get("metrics", {})
        cvss = metrics.get("cvssMetricV31", [{}])[0]
        return cvss.get("cvssData", {}).get("baseSeverity", "UNKNOWN")


class ExploitDBIngester:
    def __init__(self):
        self.base_url = "https://raw.githubusercontent.com/offensive-security/exploitdb/master/files_exploits.csv"
    
    def fetch_exploits(self, limit: int = 100) -> List[Dict]:
        sample_exploits = [
            {
                "id": "12345",
                "title": "Apache Struts2 Remote Code Execution",
                "type": "remote",
                "platform": "linux",
                "description": "Apache Struts2 vulnerability allows remote code execution via crafted OGNL expressions"
            },
            {
                "id": "12346",
                "title": "WordPress Plugin SQL Injection",
                "type": "webapps",
                "platform": "php",
                "description": "WordPress plugin vulnerable to SQL injection in user input parameters"
            },
            {
                "id": "12347",
                "title": "Windows SMB Remote Code Execution",
                "type": "remote",
                "platform": "windows",
                "description": "SMB protocol vulnerability allows remote code execution"
            },
            {
                "id": "12348",
                "title": "Linux Kernel Privilege Escalation",
                "type": "local",
                "platform": "linux",
                "description": "Kernel vulnerability allows local privilege escalation via race condition"
            },
            {
                "id": "12349",
                "title": "Jenkins Script Console RCE",
                "type": "webapps",
                "platform": "java",
                "description": "Jenkins script console allows arbitrary code execution"
            }
        ]
        
        documents = []
        for exploit in sample_exploits[:limit]:
            documents.append({
                "text": f"{exploit['title']} ({exploit['id']}): {exploit['description']}",
                "source": "ExploitDB",
                "category": "EXPLOIT",
                "metadata": {
                    "exploit_id": exploit["id"],
                    "type": exploit["type"],
                    "platform": exploit["platform"]
                }
            })
        
        return documents


class SecurityPapersIngester:
    def ingest_sample_papers(self) -> List[Dict]:
        papers = [
            {
                "title": "Return-Oriented Programming: Systems, Languages, and Applications",
                "content": "Return-oriented programming (ROP) is a system security exploit technique that allows an attacker to execute code in the presence of security defenses such as executable space protection and code signing. ROP uses control of the call stack to indirectly execute cherry-picked machine instructions immediately prior to the return instruction in subroutines within the existing program code.",
                "author": "Security Research Team"
            },
            {
                "title": "Memory Safety in Systems Programming",
                "content": "Memory safety vulnerabilities, including buffer overflows, use-after-free, and double-free errors, remain a significant source of security vulnerabilities in systems software. Modern mitigations include Address Space Layout Randomization (ASLR), stack canaries, and hardware-based memory tagging.",
                "author": "Cybersecurity Institute"
            },
            {
                "title": "Web Application Security: OWASP Top 10",
                "content": "The OWASP Top 10 is a standard awareness document for developers and web application security. It represents a broad consensus about the most critical security risks to web applications. Categories include Injection, Broken Authentication, Sensitive Data Exposure, XML External Entities (XXE), Broken Access Control, Security Misconfiguration, Cross-Site Scripting (XSS), Insecure Deserialization, Using Components with Known Vulnerabilities, and Insufficient Logging and Monitoring.",
                "author": "OWASP Foundation"
            },
            {
                "title": "Advanced Persistent Threats: Detection and Response",
                "content": "Advanced Persistent Threats (APTs) are sophisticated, long-term cyber attacks where intruders establish a long-term presence in a network to steal sensitive data. APTs typically follow a lifecycle: initial reconnaissance, initial compromise, establishing foothold, escalating privileges, internal reconnaissance, lateral movement, maintaining presence, and exfiltration.",
                "author": "Threat Intelligence Group"
            },
            {
                "title": "Zero Trust Architecture Principles",
                "content": "Zero Trust is a security framework requiring all users, whether in or outside the organization's network, to be authenticated, authorized, and continuously validated for security configuration and posture before being granted or keeping access to applications and data. Core principles include: never trust, always verify; assume breach; verify explicitly; use least privilege access.",
                "author": "NIST Cybersecurity Center"
            }
        ]
        
        documents = []
        for paper in papers:
            documents.append({
                "text": f"{paper['title']}\n\n{paper['content']}",
                "source": "Security Papers",
                "category": "RESEARCH",
                "metadata": {
                    "author": paper["author"],
                    "published": datetime.now().isoformat()
                }
            })
        
        return documents


class VulnerabilityWriteupsIngester:
    def ingest_sample_writeups(self) -> List[Dict]:
        writeups = [
            {
                "title": "CVE-2021-44228 Log4Shell Analysis",
                "content": "Log4Shell (CVE-2021-44228) is a remote code execution vulnerability in Apache Log4j 2. The vulnerability allows attackers to execute arbitrary code on affected systems by injecting specially crafted strings into log messages. The attack vector exploits JNDI lookup features in Log4j. Mitigation involves upgrading to Log4j 2.17.0 or later, or removing JNDI lookup class from classpath.",
                "severity": "Critical"
            },
            {
                "title": "Heartbleed Vulnerability (CVE-2014-0160)",
                "content": "Heartbleed is a security bug in the OpenSSL cryptography library. The vulnerability is in the implementation of the TLS heartbeat extension. It allows stealing information protected under normal conditions by the SSL/TLS encryption. The bug allows anyone on the Internet to read the memory of systems protected by vulnerable versions of OpenSSL.",
                "severity": "Critical"
            },
            {
                "title": "Shellshock Bash Vulnerability (CVE-2014-6271)",
                "content": "Shellshock is a family of security bugs in the Unix Bash shell. It allows attackers to execute arbitrary commands on vulnerable systems. The vulnerability occurs because Bash processes trailing strings after function definitions in environment variables. This allows remote attackers to execute arbitrary code through crafted environment variables.",
                "severity": "Critical"
            },
            {
                "title": "Spectre and Meltdown CPU Vulnerabilities",
                "content": "Spectre and Meltdown are side-channel attacks that exploit critical vulnerabilities in modern processors. These hardware bugs allow programs to steal data processed on the computer. Meltdown breaks the most fundamental isolation between user applications and the operating system. Spectre breaks the isolation between different applications.",
                "severity": "High"
            },
            {
                "title": "EternalBlue SMB Exploit (MS17-010)",
                "content": "EternalBlue exploits a vulnerability in Microsoft's implementation of the SMB protocol. It allows remote code execution on vulnerable systems. The vulnerability was used in the WannaCry ransomware attack. The exploit targets Windows systems that haven't applied the MS17-010 security update.",
                "severity": "Critical"
            }
        ]
        
        documents = []
        for writeup in writeups:
            documents.append({
                "text": f"{writeup['title']}\n\n{writeup['content']}",
                "source": "Vulnerability Writeups",
                "category": "WRITEUP",
                "metadata": {
                    "severity": writeup["severity"],
                    "published": datetime.now().isoformat()
                }
            })
        
        return documents


def ingest_all_data(vector_store):
    print("Starting data ingestion...")
    
    cve_ingester = CVEIngester()
    cve_docs = cve_ingester.fetch_recent_cves(results_per_page=50)
    if cve_docs:
        ids = vector_store.add_documents(cve_docs)
        print(f"Ingested {len(ids)} CVE documents")
    
    exploit_ingester = ExploitDBIngester()
    exploit_docs = exploit_ingester.fetch_exploits(limit=100)
    if exploit_docs:
        ids = vector_store.add_documents(exploit_docs)
        print(f"Ingested {len(ids)} ExploitDB documents")
    
    papers_ingester = SecurityPapersIngester()
    papers_docs = papers_ingester.ingest_sample_papers()
    if papers_docs:
        ids = vector_store.add_documents(papers_docs)
        print(f"Ingested {len(ids)} security papers")
    
    writeups_ingester = VulnerabilityWriteupsIngester()
    writeup_docs = writeups_ingester.ingest_sample_writeups()
    if writeup_docs:
        ids = vector_store.add_documents(writeup_docs)
        print(f"Ingested {len(ids)} vulnerability writeups")
    
    stats = vector_store.get_stats()
    print(f"Total documents in vector store: {stats['total_documents']}")
    return stats

def main():
    from rag.vector_store import SecurityVectorStore
    
    store = SecurityVectorStore()
    stats = ingest_all_data(store)
    print(f"Ingestion complete. {stats}")

if __name__ == "__main__":
    main()