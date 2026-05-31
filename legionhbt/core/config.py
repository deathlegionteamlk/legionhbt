import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    db_path: str = "legionhbt.db"
    audit_log_path: str = "audit_chain.log"
    models_dir: str = "models"
    max_workers: int = 8
    corroboration_threshold: float = 0.67
    risk_high_threshold: float = 0.8
    risk_medium_threshold: float = 0.5
    speculation_depth: int = 3
    enable_autonomous: bool = True
    web_port: int = 8080
    web_host: str = "0.0.0.0"
    
    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            db_path=os.getenv("LEGIONHBT_DB", "legionhbt.db"),
            audit_log_path=os.getenv("LEGIONHBT_AUDIT", "audit_chain.log"),
            models_dir=os.getenv("LEGIONHBT_MODELS", "models"),
            max_workers=int(os.getenv("LEGIONHBT_WORKERS", "8")),
            corroboration_threshold=float(os.getenv("LEGIONHBT_CORROB", "0.67")),
            risk_high_threshold=float(os.getenv("LEGIONHBT_RISK_HIGH", "0.8")),
            risk_medium_threshold=float(os.getenv("LEGIONHBT_RISK_MED", "0.5")),
            speculation_depth=int(os.getenv("LEGIONHBT_SPEC_DEPTH", "3")),
            enable_autonomous=os.getenv("LEGIONHBT_AUTO", "true").lower() == "true",
            web_port=int(os.getenv("LEGIONHBT_PORT", "8080")),
            web_host=os.getenv("LEGIONHBT_HOST", "0.0.0.0"),
        )
