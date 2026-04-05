# Reference System Specification

**Machine:** Alienware Aurora R6 (upgraded)  
**Owner:** Alexandros Karales  
**Purpose:** Development, LLM inference, model fine-tuning, book companion code  
**Last Updated:** 2026-03-19

---

## Hardware Summary

| Component | Specification |
|---|---|
| **System** | Alienware Aurora R6 (Dell 07HV66 motherboard) |
| **CPU** | Intel Core i7-7700 @ 3.60GHz (4C/8T, boost to 4.2GHz) |
| **RAM** | 64GB DDR4-2133 (4 × 16GB, non-ECC) |
| **GPU** | **NVIDIA GeForce RTX 5080 16GB GDDR7** |
| **Storage** | Lexar XG7000 2TB NVMe (PCIe Gen4 x4, 977GB free) |
| **Display** | 4K (3840×2160) via DisplayPort |
| **TDP (GPU)** | 360W |
| **PSU** | Alienware Aurora R6 stock (likely 460W — see note below) |

### GPU Details

| Spec | Value |
|---|---|
| **Model** | NVIDIA GeForce RTX 5080 |
| **Architecture** | Blackwell (GB203) |
| **VRAM** | 16GB GDDR7 |
| **Compute Capability** | 12.0 |
| **Max Core Clock** | 3090 MHz |
| **Max Memory Clock** | 15001 MHz |
| **Driver** | 590.48.01 |
| **CUDA** | 13.1 |
| **PCIe Link** | **Gen 3 x8** (see bandwidth note) |

### PCIe Bandwidth Note

The RTX 5080 supports PCIe Gen 5 x16 (~63 GB/s), but the i7-7700's
chipset only provides PCIe Gen 3. The card is running at **Gen 3 x8**,
which provides ~7.9 GB/s — roughly **8x less bandwidth** than the card's
maximum capability.

**Impact on LLM inference:** Minimal. LLM inference is compute-bound
(matrix multiplication on the GPU), not bandwidth-bound. Model weights
are loaded once into VRAM and stay there. The PCIe bottleneck only matters
during:
- Initial model loading (~2-5s for a 5GB model vs ~0.5s on Gen 5)
- Model swapping (loading a new model while unloading another)

**Impact on fine-tuning:** Moderate. Gradient synchronization between CPU
and GPU uses PCIe bandwidth. For LoRA fine-tuning of small models (1-3B),
the impact is negligible. For full fine-tuning of larger models, throughput
may be reduced by 10-20%.

**Recommendation:** This setup is excellent for inference workloads. For
heavy fine-tuning, consider a newer platform (13th+ gen Intel or AM5) with
PCIe Gen 4/5 support. However, for the LoRA-based fine-tuning strategy
outlined in `ZAPAGI_FINETUNING_STRATEGY.md`, the current system is
sufficient.

---

## Software Stack

### Operating System

| Component | Version |
|---|---|
| **OS** | Ubuntu 25.10 (Questing Quokka) |
| **Kernel** | 6.17.0-14-generic |

### AI / ML Stack

| Component | Version | Purpose |
|---|---|---|
| **Ollama** | 0.17.7 | Local LLM inference server |
| **CUDA Toolkit** | 13.1 | GPU compute |
| **NVIDIA Driver** | 590.48.01 | GPU driver |
| **Python** | 3.13.7 | Primary language |
| **uv** | 0.10.9 | Python package manager (replaces pip) |

### Ollama Configuration

```ini
# /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_NUM_PARALLEL=2"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
```

- **Flash Attention:** Enabled — reduces VRAM usage, improves throughput
- **Parallel Requests:** 2 — allows concurrent inference for multi-model routing
- **Max Loaded Models:** 2 — keeps two models hot in VRAM simultaneously

**With 16GB VRAM, optimal model combinations:**

| Combo | Model A | Model B | Total VRAM | Use Case |
|---|---|---|---|---|
| **Recommended** | qwen3:8b (5.2GB) | qwen2.5-coder:7b (4.7GB) | ~10GB | Reasoning + coding |
| Heavy | qwen3:14b (9.3GB) | — | ~10GB | Single large model |
| Light fleet | phi4-mini (2.5GB) | nemotron-mini (2.7GB) | ~5GB | Fast inference |
| Fine-tune ready | qwen3:8b (5.2GB) | — | ~6GB | Leaves 10GB for training |

### Development Tools

| Tool | Version | Purpose |
|---|---|---|
| **Git** | 2.51.0 | Version control |
| **Rust** | 1.94.0 | Systems language (ZapAGI kernel) |
| **Node.js** | 24.14.0 | Frontend tooling |
| **pnpm** | 10.30.3 | Node package manager |

---

## Installed Ollama Models

Total disk usage: **68GB** in `/usr/share/ollama/.ollama/models`

| Model | Size | Primary Role |
|---|---|---|
| `qwen3:8b` | 5.2GB | **Primary:** Perception, hypothesis, refinement |
| `qwen2.5-coder:7b` | 4.7GB | **Primary:** Code synthesis |
| `qwen3:14b` | 9.3GB | Heavy reasoning (complex tasks) |
| `qwen2.5-coder:14b` | 9.0GB | Heavy code generation |
| `deepseek-r1:14b` | 9.0GB | Chain-of-thought reasoning |
| `mistral-small:latest` | 14.3GB | General purpose (22B params) |
| `gpt-oss:20b` | 13.8GB | Large general model |
| `phi4-mini:latest` | 2.5GB | Fast lightweight reasoning |
| `nemotron-mini:latest` | 2.7GB | Fastest inference (4B params) |
| `llama3.2:latest` | 2.0GB | General chat |
| `nomic-embed-text:latest` | 0.3GB | Embedding model (RAG, similarity) |

### ARC Benchmark Results by Model

From Phase D benchmarking (5 tasks each):

| Model | Accuracy | Avg Latency | Best For |
|---|---|---|---|
| **qwen3:8b** | 79.4% | 1.8s/call | Best overall quality |
| qwen2.5-coder:7b | 68.1% | 2.1s/call | Code synthesis |
| phi4-mini | 51.2% | 0.8s/call | Fast + decent quality |
| nemotron-mini | 45.2% | 1.0s/call | Fastest inference |
| mistral-small | 42.0% | 3.5s/call | Not recommended for ARC |

---

## VRAM Budget Guide

The RTX 5080 has 16GB GDDR7. Here's how to budget it:

### Inference Only (Default)

```
Total VRAM:           16,303 MB
─────────────────────────────
System/driver:        ~500 MB
Model A (primary):    ~5,200 MB  (qwen3:8b)
Model B (secondary):  ~4,700 MB  (qwen2.5-coder:7b)
KV cache (2 models):  ~2,000 MB
─────────────────────────────
Available:            ~3,900 MB  (headroom for larger context)
```

### Inference + Fine-Tuning

```
Total VRAM:           16,303 MB
─────────────────────────────
System/driver:        ~500 MB
Model (inference):    ~5,200 MB  (qwen3:8b)
Training model:       ~1,200 MB  (Qwen2.5-1.5B base)
LoRA adapters:        ~200 MB
Optimizer states:     ~400 MB
Gradients:            ~400 MB
─────────────────────────────
Available:            ~8,400 MB  (comfortable margin)
```

**Key takeaway:** This system can simultaneously run inference on one 8B
model AND fine-tune a 1.5B model. This enables the self-improving data
flywheel described in `ZAPAGI_FINETUNING_STRATEGY.md`.

---

## Performance Benchmarks

### LLM Inference (qwen3:8b, think=False)

| Metric | Value |
|---|---|
| Single call latency | ~1.8s |
| Tokens/second (generation) | ~40-60 tok/s |
| ARC task solve time | ~100-180s |
| ARC transduction time | ~1-3s |
| Memory (RSS) during ARC eval | ~160-175MB (Python process) |

### ARC Evaluation Performance

| Pipeline | Solve Rate | Avg Similarity | Time/Task |
|---|---|---|---|
| Phase E baseline | 0/120 (0%) | 67.0% | 110s |
| **Improved (Phases F-L)** | **≥2/120** (in progress) | **73%+** | 122s |

---

## System Limitations & Upgrade Path

### Current Bottlenecks

| Bottleneck | Impact | Upgrade |
|---|---|---|
| **PCIe Gen 3 x8** | Slower model loading/swapping | New platform (AM5 or LGA1700+) |
| **DDR4-2133** | Slower CPU-side processing | DDR5 platform |
| **4C/8T CPU** | Limited parallelism for data prep | Modern 8C+ CPU |
| **No Docker** | Cannot test container workflows | Install Docker |

### What Works Excellently

| Capability | Why |
|---|---|
| **LLM inference** | 16GB VRAM handles 2× 7B models simultaneously |
| **LoRA fine-tuning** | Enough VRAM for 1.5-3B training while running inference |
| **ARC evaluation** | Full 120-task eval runs in ~3.5 hours |
| **Development** | 64GB RAM, 2TB NVMe, 4K display — no constraints |
| **Model storage** | 977GB free → room for 100+ more models |

### Recommended Upgrades (Priority Order)

1. **Install Docker** — Required for Chapter 19 (Docker agent) and ZapAGI deployment testing
2. **Upgrade platform** — AM5 (Ryzen 9) or LGA1851 (Core Ultra) for PCIe Gen 5, DDR5
3. **Add second GPU** — The Aurora R6 case supports dual GPUs. A second RTX 5080 = 32GB total VRAM, enabling 14B model fine-tuning

---

## For Book Readers

This reference system represents a **realistic developer workstation**
for running all code examples in both *God in the Loop* (Volume 1) and
*LoopAGI: The Engineering Manual* (Volume 2).

### Minimum Requirements (Volume 1)

| Component | Minimum | Recommended |
|---|---|---|
| **GPU VRAM** | 6GB (single 7B model) | 12GB+ (multi-model) |
| **RAM** | 16GB | 32GB+ |
| **Storage** | 50GB free | 200GB+ (for models) |
| **CPU** | 4 cores | 8+ cores |
| **OS** | Ubuntu 22.04+ / macOS 14+ | Ubuntu 24.04+ |

### Minimum Requirements (Volume 2 — Voice)

| Component | Additional Requirement |
|---|---|
| **GPU VRAM** | +2GB for faster-whisper STT model |
| **Microphone** | Any USB microphone |
| **Speakers** | Any audio output |
| **Storage** | +5GB for voice models |

### Minimum Requirements (Fine-Tuning)

| Component | Minimum |
|---|---|
| **GPU VRAM** | 8GB (LoRA on 1.5B) or 12GB (LoRA on 3B) |
| **RAM** | 32GB (dataset processing) |
| **Storage** | 100GB+ (datasets + checkpoints) |

---

*Reference System Specification — Copyright 2026 Alexandros Karales / ZapAGI.*
