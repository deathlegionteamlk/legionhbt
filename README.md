<div align="center">

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDRkbWg5aXo5dW82dDljMWhuNHYxdm43bTcwNnJ0MGZqcWc3NnlkNyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/RDZo7znAdn2u7sAcWH/giphy.gif" width="100%"/>

# ⚡ LEGIONHBT

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=28&duration=3000&pause=500&color=00FF41&center=true&vCenter=true&width=800&lines=Autonomous+AI+Pentesting+Ecosystem;Agent+%7C+Model+%7C+RAG+%7C+Orchestrator;Built+by+death+legion;Coded+by+Demo+X+Hexa;Zero+Hand-Holding.+Full+Autonomy.)](https://git.io/typing-svg)

<img src="https://img.shields.io/badge/STATUS-ACTIVE-00FF41?style=for-the-badge&logo=statuspage&logoColor=black"/>
<img src="https://img.shields.io/badge/PYTHON-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/AI-AUTONOMOUS-FF0000?style=for-the-badge&logo=openai&logoColor=white"/>
<img src="https://img.shields.io/badge/LICENSE-MIT-yellow?style=for-the-badge"/>
<img src="https://img.shields.io/badge/BUILT_BY-death_legion-8A2BE2?style=for-the-badge"/>

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZjRhMW9tOHkyN2p2YXZhdW1zYzFiNGxhZ2xkcGp5bTV2dDU2aW5hZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/077i6AULCXc0FKTj9s/giphy.gif" width="80%"/>

</div>

---

<div align="center">

## 🌐 What Is This

</div>

Three systems. One ecosystem. Zero hand-holding.

LEGIONHBT is a fully autonomous AI pentesting suite — agent, model, and knowledge base working together. Open source, modular, built for people who know what they're doing.

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcW83bHgxY2szYzZ4NHZ5NTFpNGI4aG1iNGF6NTNicGpldWp4MHVtZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26tn33aiTi1jkl6H6/giphy.gif" width="70%"/>
</div>

---

<div align="center">

## 🗺️ Architecture

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN25uaWR5Zjd4MnFkdGdrZ3d0YXRtZDZzd3N3ZTFwcGdzeGxrcHFtaiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l46Cy1rHbQ92uuLXa/giphy.gif" width="60%"/>

</div>

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
│                    │  • Health Monitoring          │                         │
│                    │  • Query Routing              │                         │
│                    │  • Unified API                │                         │
│                    │  • Live Dashboard             │                         │
│                    └──────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMW1vaWZlajA0YzVjcDd3em9ia2syOThwa3d6OTA5YmRtbno5MTFxdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPEqDGUULpEU0aQ/giphy.gif" width="55%"/>
</div>

---

<div align="center">

## ⚙️ System Overview

| System | Port | Role |
|:---:|:---:|:---|
| 🤖 **LEGIONHBT-AGENT** | `8080` | Autonomous recon + exploitation |
| 🧠 **LEGIONHBT-MODEL** | `8081` | Fine-tuned CVE/exploit brain |
| 📚 **LEGIONHBT-RAG** | `8082` | Vector-powered security knowledge |
| 🎛️ **Orchestrator** | `8083` | Routes everything, watches everything |

</div>

---

<div align="center">

## 🤖 System 1 — LEGIONHBT-AGENT

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExZjRhMW9tOHkyN2p2YXZhdW1zYzFiNGxhZ2xkcGp5bTV2dDU2aW5hZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/077i6AULCXc0FKTj9s/giphy.gif" width="65%"/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=2000&pause=300&color=00FF41&center=true&vCenter=true&width=700&lines=Connecting+to+GPT-4...+%E2%9C%93;Running+nmap+scan...+%E2%9C%93;Metasploit+module+loaded...+%E2=9C%93;ReAct+loop+active...+%E2%9C%93;Audit+log+hash-chained...+%E2%9C%93)](https://git.io/typing-svg)

</div>

The actual agent. Hooks into GPT-4, Claude, or DeepSeek. Runs a ReAct loop, calls real tools (nmap, metasploit, SSH brute, web scanners), and logs every action into a hash-chained audit trail you can't quietly edit later.

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExb3BsaWFtazIxdXVjYzN3c3QwMmJ6ZG5lazZ2MXQ3aGV0a2ZsdzB3aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ZvLUtG6BZkBi0/giphy.gif" width="60%"/>
</div>

**Install & run:**

```bash
cd legionhbt-agent
pip install -e .
python -m agent.main
```

**API keys:**

```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export DEEPSEEK_API_KEY="your-key"
```

**Endpoints:**

```
GET  /api/tools        → list available tools
POST /api/sessions     → new pentest session
GET  /api/sessions     → list active sessions
POST /api/chat         → WebSocket chat
```

---

<div align="center">

## 🧠 System 2 — LEGIONHBT-MODEL

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNnhkcGgxOW9yMnZodXk3cjF6OWt5bjg2aXA1eW4wY2Z4OWN0c28xdyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9IgzoKnwFNmISR8I/giphy.gif" width="65%"/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=2000&pause=300&color=FF6B35&center=true&vCenter=true&width=700&lines=Loading+Qwen+2.5+7B...;Applying+LoRA+weights...;CVE+database+indexed...;Exploit+generation+ready...;Vulnerability+scanner+online...)](https://git.io/typing-svg)

</div>

Qwen 2.5 7B, LoRA fine-tuned on security datasets. Runs local. Knows CVEs, generates exploit stubs, and flags vulnerable code patterns if you feed it source.

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcW83bHgxY2szYzZ4NHZ5NTFpNGI4aG1iNGF6NTNicGpldWp4MHVtZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26tn33aiTi1jkl6H6/giphy.gif" width="55%"/>
</div>

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

**Endpoints:**

```
POST /generate              → security generation
POST /analyze/cve           → CVE breakdown
POST /generate/exploit      → exploit scaffolding
POST /detect/vulnerability  → code vuln scan
GET  /health                → ping
```

---

<div align="center">

## 📚 System 3 — LEGIONHBT-RAG

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN25uaWR5Zjd4MnFkdGdrZ3d0YXRtZDZzd3N3ZTFwcGdzeGxrcHFtaiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l46Cy1rHbQ92uuLXa/giphy.gif" width="65%"/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=2000&pause=300&color=00D4FF&center=true&vCenter=true&width=700&lines=Initializing+Qdrant...;Ingesting+CVE+database...;ExploitDB+synced...;Vector+embeddings+built...;RAG+pipeline+ready...)](https://git.io/typing-svg)

</div>

Qdrant vector database pre-loaded with CVEs, ExploitDB entries, security papers, and vuln writeups. Ask it anything in plain text and it pulls the right context before answering through a frontier LLM.

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMW1vaWZlajA0YzVjcDd3em9ia2syOThwa3d6OTA5YmRtbno1MTFxdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPEqDGUULpEU0aQ/giphy.gif" width="55%"/>
</div>

**Install & run:**

```bash
cd legionhbt-rag
pip install -e .
python -m rag.main
```

**Endpoints:**

```
GET  /api/stats   → vector store stats
POST /api/search  → semantic search
POST /api/chat    → RAG-powered Q&A
```

---

<div align="center">

## 🎛️ System 4 — Orchestrator

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOWwwMG9kY254aHNuYXlkOGdhemc4NzBlOTc3aDJudnJ3Y3I5YXhncCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l1J9GIXk9w7OYsd5S/giphy.gif" width="65%"/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=2000&pause=300&color=FF00FF&center=true&vCenter=true&width=700&lines=Orchestrator+online...;Monitoring+AGENT+%3A+%E2%9C%93+healthy;Monitoring+MODEL+%3A+%E2%9C%93+healthy;Monitoring+RAG+%3A+%E2%9C%93+healthy;All+systems+go.)](https://git.io/typing-svg)

</div>

Ties the other three together. Watches their health, routes queries to the right subsystem, and gives you one dashboard instead of four browser tabs.

**Install & run:**

```bash
cd orchestrator
pip install -r requirements.txt
python main.py
```

**Endpoints:**

```
GET  /api/health          → full system status
GET  /api/systems         → registered systems
POST /api/query           → auto-route any query
GET  /api/agent/sessions  → proxy → agent
POST /api/model/generate  → proxy → model
POST /api/rag/query       → proxy → RAG
```

---

<div align="center">

## 🚀 Quick Start

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExb3BsaWFtazIxdXVjYzN3c3QwMmJ6ZG5lazZ2MXQ3aGV0a2ZsdzB3aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ZvLUtG6BZkBi0/giphy.gif" width="60%"/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=20&duration=1500&pause=200&color=00FF41&center=true&vCenter=true&width=700&lines=%24+pip+install+-e+.;%24+python+-m+agent.main;%24+python+-m+model.server;%24+python+-m+rag.main;%24+python+main.py;All+systems+online+%F0%9F%9F%A2)](https://git.io/typing-svg)

</div>

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

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN2Q2NHd4Y3ZrcjYwYm44ejUxejh0cGI4YzR2d2ZrczBrNzA5MGF6ZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l3q2K5jinAlChoCLS/giphy.gif" width="55%"/>
</div>

---

<div align="center">

## 🔧 Usage Examples

</div>

### 🕵️ Start a Pentest Session

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcDRkbWg5aXo5dW82dDljMWhuNHYxdm43bTcwNnJ0MGZqcWc3NnlkNyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/RDZo7znAdn2u7sAcWH/giphy.gif" width="50%"/>
</div>

```bash
curl -X POST http://localhost:8080/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "target_scan", "target": "192.168.1.1"}'
```

---

### 🔍 Analyze a CVE

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNnhkcGgxOW9yMnZodXk3cjF6OWt5bjg2aXA1eW4wY2Z4OWN0c28xdyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xT9IgzoKnwFNmISR8I/giphy.gif" width="50%"/>
</div>

```bash
curl -X POST http://localhost:8081/analyze/cve \
  -H "Content-Type: application/json" \
  -d '{
    "cve_id": "CVE-2021-44228",
    "description": "Log4j RCE vulnerability"
  }'
```

---

### 💬 Query the Knowledge Base

<div align="center">
<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN25uaWR5Zjd4MnFkdGdrZ3d0YXRtZDZzd3N3ZTFwcGdzeGxrcHFtaiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l46Cy1rHbQ92uuLXa/giphy.gif" width="50%"/>
</div>

```bash
curl -X POST http://localhost:8082/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is SQL injection and how do I prevent it?"}'
```

---

### 🧩 Route Through Orchestrator

```bash
curl -X POST http://localhost:8083/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Scan target for vulnerabilities", "type": "auto"}'
```

---

<div align="center">

## 💻 System Requirements

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcW83bHgxY2szYzZ4NHZ5NTFpNGI4aG1iNGF6NTNicGpldWp4MHVtZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26tn33aiTi1jkl6H6/giphy.gif" width="55%"/>

</div>

| Requirement | Minimum |
|:---|:---|
| Python | 3.11+ |
| RAM | 16 GB |
| GPU | Optional (CUDA, speeds up inference) |
| OS | Linux / macOS / Windows (WSL) |

**Core deps:**

```
PyTorch 2.3+          transformers 4.41+
FastAPI               Flask
qdrant-client         sentence-transformers
```

**LLM API keys** (at least one needed for the agent):

```bash
OPENAI_API_KEY
ANTHROPIC_API_KEY
DEEPSEEK_API_KEY
```

---

<div align="center">

## ⚠️ Security Notice

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOWwwMG9kY254aHNuYXlkOGdhemc4NzBlOTc3aDJudnJ3Y3I5YXhncCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l1J9GIXk9w7OYsd5S/giphy.gif" width="55%"/>

> **Authorized testing only.**
> Don't scan systems you don't own or have written permission to test.
> That's not a disclaimer — it's just obvious.

---

## 📜 License

MIT — see `LICENSE` for details.

---

## 🏴 Credits

**Created by `death legion`**
**Coded by `Demo X Hexa`**

*Inspired by Claude Mythos architecture from Anthropic.*

---

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMW1vaWZlajA0YzVjcDd3em9ia2syOThwa3d6OTA5YmRtbno1MTFxdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oKIPEqDGUULpEU0aQ/giphy.gif" width="70%"/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=4000&pause=1000&color=00FF41&center=true&vCenter=true&width=800&lines=LEGIONHBT+%E2%80%94+because+doing+it+manually+stopped+being+interesting.)](https://git.io/typing-svg)

<img src="https://komarev.com/ghpvc/?username=legionhbt&label=README+VIEWS&color=00ff41&style=for-the-badge"/>

</div>
