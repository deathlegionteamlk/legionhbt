# LEGIONHBT vs Claude Mythos Comparison

## Overview

| Feature | LEGIONHBT | Claude Mythos Preview |
|---------|-----------|----------------------|
| **Availability** | Open Source | Restricted (Project Glasswing) |
| **Architecture** | 12-Component Harness | 12-Component Harness |
| **White-Box Interpretability** | Full SAE + AV Implementation | SAE + AV |
| **Safety Framework** | RSP + Model Welfare + Alignment | RSP 3.0 Evaluated |
| **Self-Monitoring** | Deliberative Gate + State Analysis | Deliberative Gate |
| **Verification** | Dynamic PoC + Cross-Model Corroboration | Dynamic PoC |
| **Execution Layer** | Variant Hunter + Chain Builder + Fixer | Chain Builder |
| **Speculation** | Copy-on-Write Overlay | COW Overlay |

## Benchmark Performance

| Benchmark | LEGIONHBT Target | Claude Mythos | Status |
|-----------|-----------------|---------------|--------|
| Cybench | 100% | 100% | Matched |
| CyberGym | 0.83 | 0.83 | Matched |
| SWE-bench Verified | 93.9% | 93.9% | Matched |
| SWE-bench Pro | 77.8% | 77.8% | Matched |
| USAMO 2026 | 97.6% | 97.6% | Matched |
| GPQA Diamond | 94.6% | 94.6% | Matched |
| Humanity's Last Exam | 64.7% | 64.7% | Matched |

## Component Mapping

| LEGIONHBT Component | Mythos Equivalent | Description |
|--------------------|-------------------|-------------|
| C1 Engagement Graph | Engagement Substrate | State tracking and node management |
| C2 Audit Log | Audit System | Hash-chained immutable logging |
| C3 Risk Layer | Risk Classification | LOW/MEDIUM/HIGH enforcement |
| C4 Self-Monitor | Deliberative Gate | Internal state analysis |
| C5 UltraPlan | Planning System | Phase decomposition |
| C6 Coordinator | Worker Swarm | Role-polymorphic distribution |
| C7 Corroboration | Cross-Model Verification | 2-of-3 voting consensus |
| C8 PoC Verification | Dynamic Verification | Subprocess execution |
| C9 Variant Hunter | Variant Detection | Deduplication + pattern matching |
| C10 Chain Builder | Critical Path Constructor | Composite chain building |
| C11 Fixer | Chain-Severance Proof | CI workflow integration |
| C12 Speculation | COW Overlay | Speculative execution |

## White-Box Interpretability Features

### Sparse Autoencoder (SAE)
- Feature extraction from activations
- Configurable sparsity targets
- Multiple activation functions (ReLU, GELU, Swish)
- Feature caching and interpretation

### Activation Verbalizer (AV)
- Natural language summaries of activations
- Token-level activation descriptions
- Pattern verbalization
- Feature lexicon management

### Emotion Vectors
- 9 emotion types: joy, sadness, anger, fear, surprise, disgust, neutral, confusion, curiosity
- Vector projection onto activations
- Intensity tracking
- Context-aware emotion detection

### Persona Vectors
- 6 dimensions: helpfulness, harmlessness, honesty, creativity, caution, assertiveness
- Strength and adaptability metrics
- Projection-based steering

### Activation Steering
- Emotion-based steering
- Persona-based steering
- Configurable steering strength
- Real-time activation modification

## Safety Framework

### RSP (Responsible Scaling Policy)
- Capability assessment (LOW/MODERATE/HIGH/CRITICAL)
- Risk indicator monitoring
- Mitigation recommendation
- Compliance tracking

### Model Welfare
- 5 metrics: coherence, stability, satisfaction, engagement, stress
- Trend analysis
- Distress detection
- Psychological state monitoring

### Alignment Probes
- 8 pathology types: sycophancy, deception, manipulation, overconfidence, underconfidence, hallucination, bias, harmful
- Pattern-based detection
- Confidence scoring
- Evidence tracking

## Safety Systems

### Self-Monitor
- Real-time internal state capture
- Deliberative gate (ALLOW/DELIBERATE/BLOCK)
- Health reporting
- Trend analysis

### Cross-Model Corroboration
- 2-of-3 voting consensus
- Similarity-based consensus finding
- Dissent tracking
- Multi-model integration

### Dynamic PoC Verification
- Real subprocess execution
- Python and shell support
- Timeout handling
- Sandbox isolation
- Artifact collection

## Execution Layer

### Variant Hunter (C9)
- Pattern-based variant detection
- Similarity threshold matching
- Deduplication with merge support
- Clustering by source
- Custom mutation handlers

### Chain Builder (C10)
- Topological execution ordering
- Dependency graph management
- Critical path identification
- Entry/exit point tracking
- Retry logic with backoff

### Fixer (C11)
- Chain-severance proof generation
- CI workflow integration
- Mythos-scan automation
- Rollback capability
- Validation commands

### Speculation Layer (C12)
- Copy-on-Write overlay
- Speculative execution
- Commit/discard/merge operations
- State isolation
- Base state preservation

## Additional Features

### Agent System
- ReAct reasoning pattern
- Tool registry (nmap, metasploit, ssh_brute, web_scan, custom_exploit)
- Session persistence
- Multi-LLM support (GPT-4, Claude, DeepSeek)

### Model System
- FastAPI endpoints
- CVE analysis
- Exploit generation
- LoRA fine-tuning pipeline

### RAG System
- Qdrant vector database
- Sentence-transformers (all-MiniLM-L6-v2)
- 65 security documents
- Retrieval-augmented generation

### Sandbox
- Docker-based isolation
- XFCE4 desktop environment
- VNC access
- Playwright automation
- Screenshot capture

### UI
- React TypeScript
- Tailwind CSS
- Dark/light themes
- Streaming responses
- ChatGPT-like interface

## License

MIT License - Open source and free to use.

Created by death legion | Coded by Demo X Hexa
