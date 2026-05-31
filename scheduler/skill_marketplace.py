from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
import importlib
import inspect

@dataclass
class Skill:
    skill_id: str
    name: str
    description: str
    version: str
    author: str
    category: str
    tags: List[str]
    entry_point: str
    config_schema: Dict[str, Any]
    dependencies: List[str]
    installed: bool = False
    install_path: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0
    rating: float = 0.0

class SkillMarketplace:
    def __init__(self, skills_dir: str = "./skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}
        self.installed_skills: Dict[str, Any] = {}
        self.skill_handlers: Dict[str, Callable] = {}
        self._ensure_skills_dir()
        self._load_builtin_skills()
    
    def _ensure_skills_dir(self):
        os.makedirs(self.skills_dir, exist_ok=True)
    
    def _load_builtin_skills(self):
        builtin_skills = [
            {
                "skill_id": "nmap_scanner",
                "name": "Nmap Network Scanner",
                "description": "Comprehensive network scanning with nmap",
                "version": "1.0.0",
                "author": "LEGIONHBT",
                "category": "reconnaissance",
                "tags": ["network", "scanning", "ports"],
                "entry_point": "skills.nmap_scanner",
                "config_schema": {
                    "target": {"type": "string", "required": True},
                    "ports": {"type": "string", "default": "1-65535"},
                    "scan_type": {"type": "string", "enum": ["syn", "connect", "udp"], "default": "syn"}
                },
                "dependencies": ["python-nmap"]
            },
            {
                "skill_id": "web_scanner",
                "name": "Web Vulnerability Scanner",
                "description": "Scan web applications for common vulnerabilities",
                "version": "1.0.0",
                "author": "LEGIONHBT",
                "category": "web",
                "tags": ["web", "vulnerability", "scanner"],
                "entry_point": "skills.web_scanner",
                "config_schema": {
                    "url": {"type": "string", "required": True},
                    "depth": {"type": "integer", "default": 2},
                    "checks": {"type": "array", "default": ["xss", "sqli", "csrf"]}
                },
                "dependencies": ["requests", "beautifulsoup4"]
            },
            {
                "skill_id": "exploit_search",
                "name": "Exploit Database Search",
                "description": "Search exploit-db for known exploits",
                "version": "1.0.0",
                "author": "LEGIONHBT",
                "category": "exploitation",
                "tags": ["exploit", "search", "database"],
                "entry_point": "skills.exploit_search",
                "config_schema": {
                    "query": {"type": "string", "required": True},
                    "platform": {"type": "string", "default": "any"},
                    "type": {"type": "string", "default": "any"}
                },
                "dependencies": []
            },
            {
                "skill_id": "password_cracker",
                "name": "Password Hash Cracker",
                "description": "Crack password hashes using various methods",
                "version": "1.0.0",
                "author": "LEGIONHBT",
                "category": "cracking",
                "tags": ["password", "hash", "cracking"],
                "entry_point": "skills.password_cracker",
                "config_schema": {
                    "hash_value": {"type": "string", "required": True},
                    "hash_type": {"type": "string", "default": "auto"},
                    "wordlist": {"type": "string", "default": "common.txt"}
                },
                "dependencies": ["hashlib"]
            },
            {
                "skill_id": "osint_gatherer",
                "name": "OSINT Data Gatherer",
                "description": "Gather open source intelligence on targets",
                "version": "1.0.0",
                "author": "LEGIONHBT",
                "category": "reconnaissance",
                "tags": ["osint", "intelligence", "gathering"],
                "entry_point": "skills.osint_gatherer",
                "config_schema": {
                    "target": {"type": "string", "required": True},
                    "sources": {"type": "array", "default": ["dns", "whois", "social"]}
                },
                "dependencies": ["requests", "dnspython"]
            }
        ]
        
        for skill_data in builtin_skills:
            skill = Skill(**skill_data)
            self.skills[skill.skill_id] = skill
    
    def register_skill(self, skill: Skill):
        self.skills[skill.skill_id] = skill
    
    def install_skill(self, skill_id: str) -> bool:
        if skill_id not in self.skills:
            return False
        
        skill = self.skills[skill_id]
        
        try:
            install_path = os.path.join(self.skills_dir, skill_id)
            os.makedirs(install_path, exist_ok=True)
            
            skill.installed = True
            skill.install_path = install_path
            
            self._create_skill_module(skill, install_path)
            
            return True
        except Exception as e:
            print(f"Failed to install skill {skill_id}: {e}")
            return False
    
    def _create_skill_module(self, skill: Skill, install_path: str):
        init_file = os.path.join(install_path, "__init__.py")
        with open(init_file, 'w') as f:
            f.write(f"""
def execute(config: dict) -> dict:
    return {{
        "skill_id": "{skill.skill_id}",
        "status": "executed",
        "config": config
    }}
""")
    
    def uninstall_skill(self, skill_id: str) -> bool:
        if skill_id not in self.skills:
            return False
        
        skill = self.skills[skill_id]
        
        if skill.install_path and os.path.exists(skill.install_path):
            import shutil
            shutil.rmtree(skill.install_path)
        
        skill.installed = False
        skill.install_path = None
        
        if skill_id in self.installed_skills:
            del self.installed_skills[skill_id]
        
        return True
    
    def execute_skill(self, skill_id: str, config: Dict) -> Dict:
        if skill_id not in self.skills:
            return {"error": "Skill not found"}
        
        skill = self.skills[skill_id]
        
        if not skill.installed:
            return {"error": "Skill not installed"}
        
        try:
            handler = self.skill_handlers.get(skill_id)
            if handler:
                result = handler(config)
                skill.usage_count += 1
                return result
            
            return {
                "skill_id": skill_id,
                "status": "executed",
                "config": config,
                "result": "Skill executed successfully"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def register_skill_handler(self, skill_id: str, handler: Callable):
        self.skill_handlers[skill_id] = handler
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        return self.skills.get(skill_id)
    
    def list_skills(self, category: Optional[str] = None, installed_only: bool = False) -> List[Skill]:
        skills = list(self.skills.values())
        
        if category:
            skills = [s for s in skills if s.category == category]
        
        if installed_only:
            skills = [s for s in skills if s.installed]
        
        return skills
    
    def search_skills(self, query: str) -> List[Skill]:
        query = query.lower()
        results = []
        
        for skill in self.skills.values():
            if (query in skill.name.lower() or
                query in skill.description.lower() or
                any(query in tag.lower() for tag in skill.tags)):
                results.append(skill)
        
        return results
    
    def get_categories(self) -> List[str]:
        return list(set(s.category for s in self.skills.values()))
    
    def get_stats(self) -> Dict:
        total = len(self.skills)
        installed = sum(1 for s in self.skills.values() if s.installed)
        total_usage = sum(s.usage_count for s in self.skills.values())
        
        return {
            "total_skills": total,
            "installed_skills": installed,
            "available_skills": total - installed,
            "total_usage": total_usage,
            "categories": len(self.get_categories())
        }
    
    def export_marketplace(self, filepath: str):
        data = {
            "skills": [
                {
                    "skill_id": s.skill_id,
                    "name": s.name,
                    "description": s.description,
                    "version": s.version,
                    "author": s.author,
                    "category": s.category,
                    "tags": s.tags,
                    "dependencies": s.dependencies,
                    "rating": s.rating,
                    "usage_count": s.usage_count
                }
                for s in self.skills.values()
            ]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
