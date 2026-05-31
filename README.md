# LEGIONHBT — Autonomous AI Pentesting Ecosystem

> **Built by death legion · Coded by Demo X Hexa**

![Hacking Animation](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDRkbWg5aXo5dW82dDljMWhuNHYxdm43bTcwNnJ0MGZqcWc3NnlkNyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/RDZo7znAdn2u7sAcWH/giphy.gif)

Three systems. One ecosystem. Zero hand-holding.

LEGIONHBT is a fully autonomous AI pentesting suite — agent, model, and knowledge base working together. It's open source, modular, and built for people who know what they're doing.

---

## What's Inside

![System Overview](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcW83bHgxY2szYzZ4NHZ5NTFpNGI4aG1iNGF6NTNicGpldWp4MHVtZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26tn33aiTi1jkl6H6/giphy.gif)

| System | Port | What it does |
|---|---|---|
| **LEGIONHBT-AGENT** | `8080` | Autonomous recon + exploitation |
| **LEGIONHBT-MODEL** | `8081` | Fine-tuned CVE/exploit brain |
| **LEGIONHBT-RAG** | `8082` | Vector-powered security knowledge |
| **Orchestrator** | `8083` | Routes everything, watches everything |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LEGIONHBT ECOSYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │   AGENT :8080    │    │   MODEL :8081    │    │    RAG :8082     │       │
│  │                  │    │                  │    │                  │       │
│  │ • Autonomous     │    │ • Qwen 2.5 7B    │    │ • Qdrant Vector  │       │
│  │   Pentesting     │    │ • LoRA Fine-tune │    │   DB             │       │
│  │ • GPT-4/Claude   │    │ • CVE Analysis   │    │ • CVE Ingestion  │       │
│  │ • Tool Calling   │    │ • Exploit Gen    │    │ • ExploitDB sync │       │
│  │ • Session Mgmt   │    │ • Vuln Detection │    │ • RAG Pipeline   │       │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘       │
│           │                       │                       │                 │
│           └───────────────────────┼───────────────────────┘                 │
│                                   ▼                                         │
│                    ┌──────────────────────────────┐                         │
│                    │     ORCHESTRATOR :8083        │                         │
│                    │                              │                         │
│                    │  • Health Monitoring         │                         │
│                    │  • Query Routing             │                         │
│                    │  • Unified API               │                         │
│                    │  • Live Dashboard            │                         │
│                    └──────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## System 1 — LEGIONHBT-AGENT

![Agent Running](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZjRhMW9tOHkyN2p2YXZhdW1zYzFiNGxhZ2xkcGp5bTV2dDU2aW5hZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/077i6AULCXc0FKTj9s/giphy.gif)

The actual agent. Hooks into GPT-4, Claude, or DeepSeek — whichever key you drop in. It runs a ReAct loop, calls real tools (nmap, metasploit, SSH brute, web scanners), and logs every action into a hash-chained audit trail you can't quietly edit later.

**Install & run:**

```bash
cd legionhbt-agent
pip install -e .
python -m agent.main
```

**Set your keys:**

```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export DEEPSEEK_API_KEY="your-key"
```

**API surface:**

```
GET  /api/tools           → list available tools
POST /api/sessions        → create a new pentest session
GET  /api/sessions        → list active sessions
POST /api/chat            → WebSocket chat interface
```

---

## System 2 — LEGIONHBT-MODEL

![Neural Network](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNnhkcGgxOW9yMnZodXk3cjF6OWt5bjg2aXA1eW4wY2Z4OWN0c28xdyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9IgzoKnwFNmISR8I/giphy.gif)

Qwen 2.5 7B, LoRA fine-tuned on security datasets. Runs local. Knows CVEs, can generate exploit stubs, and will flag vulnerable code patterns if you feed it source.

**Install & run:**

```bash
cd legionhbt-model
pip install -e .
python -m model.server
```

**Train your own weights:**

```bash
python -m model.train \
  --base-model Qwen/Qwen2.5-7B \
  --export-safetensors
```

**API surface:**

```
POST /generate              → general security generation
POST /analyze/cve           → break down a CVE
POST /generate/exploit      → generate exploit scaffolding
POST /detect/vulnerability  → scan code for vulns
GET  /health                → ping
```

---

## System 3 — LEGIONHBT-RAG

![Data Flow](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN25uaWR5Zjd4MnFkdGdrZ3d0YXRtZDZzd3N3ZTFwcGdzeGxrcHFtaiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l46Cy1rHbQ92uuLXa/giphy.gif)

Qdrant vector database, pre-loaded with CVEs, ExploitDB entries, security papers, and vuln writeups. Ask it anything in plain text and it pulls the right context before answering through a frontier LLM.

**Install & run:**

```bash
cd legionhbt-rag
pip install -e .
python -m rag.main
```

**API surface:**

```
GET  /api/stats   → vector store stats
POST /api/search  → semantic search
POST /api/chat    → RAG-powered Q&A
```

---

## System 4 — Orchestrator

![Control Panel](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMW1vaWZlajA0YzVjcDd3em9ia2syOThwa3d6OTA5YmRtbno5MTFxdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPEqDGUULpEU0aQ/giphy.gif)

Ties the other three together. Watches their health, routes queries to the right subsystem, and gives you a single dashboard instead of four browser tabs.

**Install & run:**

```bash
cd orchestrator
pip install -r requirements.txt
python main.py
```

**API surface:**

```
GET  /api/health          → full system status
GET  /api/systems         → list registered systems
POST /api/query           → auto-route any query
GET  /api/agent/sessions  → proxy → agent
POST /api/model/generate  → proxy → model
POST /api/rag/query       → proxy → RAG
```

---

## Quick Start

![Terminal](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExb3BsaWFtazIxdXVjYzN3c3QwMmJ6ZG5lazZ2MXQ3aGV0a2ZsdzB3aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ZvLUtG6BZkBi0/giphy.gif)

**Step 1 — install everything:**

```bash
cd legionhbt-agent && pip install -e . && cd ..
cd legionhbt-model && pip install -e . && cd ..
cd legionhbt-rag   && pip install -e . && cd ..
cd orchestrator    && pip install -r requirements.txt && cd ..
```

**Step 2 — spin up four terminals:**

```bash
# Terminal 1
cd legionhbt-agent && python -m agent.main

# Terminal 2
cd legionhbt-model && python -m model.server

# Terminal 3
cd legionhbt-rag && python -m rag.main

# Terminal 4
cd orchestrator && python main.py
```

**Step 3 — open your browser:**

```
http://localhost:8083   ← Orchestrator dashboard
http://localhost:8080   ← Agent API
http://localhost:8081   ← Model API
http://localhost:8082   ← RAG API
```

---

## Usage Examples

### Start a pentest session

```bash
curl -X POST http://localhost:8080/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "target_scan", "target": "192.168.1.1"}'
```

### Analyze a CVE

```bash
curl -X POST http://localhost:8081/analyze/cve \
  -H "Content-Type: application/json" \
  -d '{
    "cve_id": "CVE-2021-44228",
    "description": "Log4j RCE vulnerability"
  }'
```

### Query the RAG knowledge base

```bash
curl -X POST http://localhost:8082/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is SQL injection and how do I prevent it?"}'
```

### Route through the orchestrator

```bash
curl -X POST http://localhost:8083/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Scan target for vulnerabilities", "type": "auto"}'
```

---

## System Requirements

![Requirements Check](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN2Q2NHd4Y3ZrcjYwYm44ejUxejh0cGI4YzR2d2ZrczBrNzA5MGF6ZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l3q2K5jinAlChoCLS/giphy.gif)

- Python 3.11+
- 16 GB RAM minimum (model inference is hungry)
- CUDA GPU optional but makes inference much faster
- Linux, macOS, or Windows via WSL

**Core deps:**

```
PyTorch 2.3+
Transformers 4.41+
FastAPI
Flask
Qdrant-client
Sentence-transformers
```

**LLM API keys** (at least one required for the agent):

```
OPENAI_API_KEY
ANTHROPIC_API_KEY
DEEPSEEK_API_KEY
```

---

## Security Notice

![Warning](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOWwwMG9kY254aHNuYXlkOGdhemc4NzBlOTc3aDJudnJ3Y3I5YXhncCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l1J9GIXk9w7OYsd5S/giphy.gif)

This tool is for authorized testing only. Don't scan systems you don't own or have written permission to test. That's not a disclaimer — it's just obvious.

---

## License

MIT — see `LICENSE` for details.

---

## Credits

**Created by death legion**  
**Coded by Demo X Hexa**

Inspired by Claude Mythos architecture from Anthropic.

---

*LEGIONHBT — because doing it manually stopped being interesting.*
