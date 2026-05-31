# LEGIONHBT - Autonomous AI Pentesting Ecosystem

**Created by death legion | Coded by Demo X Hexa**

A complete open-source autonomous AI pentesting ecosystem with three integrated systems: autonomous pentesting agent, fine-tuned security model, and RAG security knowledge system.

## Overview

LEGIONHBT is an autonomous AI pentesting ecosystem inspired by Claude Mythos architecture. It combines three powerful systems to provide comprehensive security assessment capabilities:

1. **LEGIONHBT-AGENT**: Autonomous pentesting agent with LLM integration
2. **LEGIONHBT-MODEL**: Fine-tuned security model for CVE analysis and exploit generation
3. **LEGIONHBT-RAG**: RAG-based security knowledge system with vector database

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LEGIONHBT ECOSYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │   AGENT (8080)   │    │   MODEL (8081)   │    │    RAG (8082)    │      │
│  │                  │    │                  │    │                  │      │
│  │ • Autonomous     │    │ • Qwen 2.5 7B    │    │ • Qdrant Vector  │      │
│  │   Pentesting     │    │ • LoRA Fine-tuned│    │   DB             │      │
│  │ • LLM APIs       │    │ • CVE Analysis   │    │ • CVE/Exploit    │      │
│  │ • Tool Calling   │    │ • Exploit Gen    │    │   Ingestion      │      │
│  │ • Session Mgmt   │    │ • Vuln Detection │    │ • RAG Pipeline   │      │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘      │
│           │                       │                       │                │
│           └───────────────────────┼───────────────────────┘                │
│                                   │                                        │
│                    ┌──────────────┴──────────────┐                        │
│                    │      ORCHESTRATOR (8083)   │                        │
│                    │                             │                        │
│                    │  • Health Monitoring        │                        │
│                    │  • Query Routing            │                        │
│                    │  • Unified API              │                        │
│                    │  • Dashboard                │                        │
│                    └─────────────────────────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## System Components

### 1. LEGIONHBT-AGENT (Port 8080)

Autonomous AI pentesting agent with real LLM API integration.

**Features:**
- OpenAI GPT-4, Anthropic Claude, DeepSeek API integration
- Autonomous vulnerability discovery using ReAct pattern
- Tool calling for nmap, metasploit, SSH brute force, web scanning
- Session persistence with SQLite
- Hash-chained immutable audit log
- Professional web UI

**Installation:**
```bash
cd legionhbt-agent
pip install -e .
python -m agent.main
```

**Environment Variables:**
```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export DEEPSEEK_API_KEY="your-key"
```

**API Endpoints:**
- `GET /api/tools` - List available tools
- `POST /api/sessions` - Create new pentesting session
- `GET /api/sessions` - List active sessions
- `POST /api/chat` - WebSocket chat interface

### 2. LEGIONHBT-MODEL (Port 8081)

Fine-tuned security model based on Qwen 2.5 7B.

**Features:**
- Base: Qwen/Qwen2.5-7B from HuggingFace
- LoRA fine-tuning on security datasets
- CVE analysis endpoint
- Exploit generation endpoint
- Vulnerability detection endpoint
- Safetensors export format
- FastAPI inference server

**Installation:**
```bash
cd legionhbt-model
pip install -e .
python -m model.server
```

**Training:**
```bash
python -m model.train --base-model Qwen/Qwen2.5-7B --export-safetensors
```

**API Endpoints:**
- `POST /generate` - Generate security analysis
- `POST /analyze/cve` - Analyze CVE details
- `POST /generate/exploit` - Generate exploit code
- `POST /detect/vulnerability` - Detect vulnerabilities in code
- `GET /health` - Health check

### 3. LEGIONHBT-RAG (Port 8082)

RAG-based security knowledge system with Qdrant vector database.

**Features:**
- Qdrant vector database for semantic search
- CVE database ingestion
- ExploitDB integration
- Security paper ingestion
- Vulnerability writeup ingestion
- Real-time retrieval augmented generation
- Connected to frontier LLMs via API

**Installation:**
```bash
cd legionhbt-rag
pip install -e .
python -m rag.main
```

**API Endpoints:**
- `GET /api/stats` - Vector store statistics
- `POST /api/search` - Semantic search
- `POST /api/chat` - RAG-powered chat

### 4. Orchestrator (Port 8083)

Unified command center for managing all three systems.

**Features:**
- Health monitoring for all subsystems
- Intelligent query routing
- Unified API gateway
- Real-time dashboard
- WebSocket updates

**Installation:**
```bash
cd orchestrator
pip install -r requirements.txt
python main.py
```

**API Endpoints:**
- `GET /api/health` - System health status
- `GET /api/systems` - List all systems
- `POST /api/query` - Route query to appropriate system
- `GET /api/agent/sessions` - Proxy to agent sessions
- `POST /api/model/generate` - Proxy to model generation
- `POST /api/rag/query` - Proxy to RAG query

## Quick Start

1. **Install all systems:**
```bash
# Install AGENT
cd legionhbt-agent && pip install -e . && cd ..

# Install MODEL
cd legionhbt-model && pip install -e . && cd ..

# Install RAG
cd legionhbt-rag && pip install -e . && cd ..

# Install orchestrator dependencies
cd orchestrator && pip install -r requirements.txt && cd ..
```

2. **Start all services:**
```bash
# Terminal 1 - AGENT
cd legionhbt-agent && python -m agent.main

# Terminal 2 - MODEL
cd legionhbt-model && python -m model.server

# Terminal 3 - RAG
cd legionhbt-rag && python -m rag.main

# Terminal 4 - Orchestrator
cd orchestrator && python main.py
```

3. **Access the systems:**
- Orchestrator Dashboard: http://localhost:8083
- AGENT API: http://localhost:8080
- MODEL API: http://localhost:8081
- RAG API: http://localhost:8082

## Usage Examples

### Pentesting Session
```bash
curl -X POST http://localhost:8080/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "target_scan", "target": "192.168.1.1"}'
```

### CVE Analysis
```bash
curl -X POST http://localhost:8081/analyze/cve \
  -H "Content-Type: application/json" \
  -d '{"cve_id": "CVE-2021-44228", "description": "Log4j RCE vulnerability"}'
```

### RAG Query
```bash
curl -X POST http://localhost:8082/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is SQL injection and how to prevent it?"}'
```

### Orchestrator Query
```bash
curl -X POST http://localhost:8083/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Scan target for vulnerabilities", "type": "auto"}'
```

## System Requirements

- Python 3.11+
- 16GB+ RAM (for model inference)
- CUDA-capable GPU (optional, for faster inference)
- Linux/macOS/Windows with WSL

## Dependencies

### Core Dependencies
- PyTorch 2.3+
- Transformers 4.41+
- FastAPI
- Flask
- Qdrant-client
- Sentence-transformers

### LLM API Keys (Optional)
- OpenAI API key
- Anthropic API key
- DeepSeek API key

## Security Notice

This system is designed for authorized security testing only. Always ensure you have explicit permission before scanning or testing any systems you do not own.

## License

MIT License - See LICENSE file for details.

## Credits

**Created by death legion**
**Coded by Demo X Hexa**

Inspired by Claude Mythos architecture from Anthropic.
