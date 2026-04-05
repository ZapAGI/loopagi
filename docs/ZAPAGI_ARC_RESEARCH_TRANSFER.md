# ZapAGI Internal: How ARC Research Benefits ZapAGI

**Classification:** ZapAGI Internal Documentation  
**Author:** Alexandros Karales  
**Last Updated:** 2026-03-19  
**Status:** Living document — updated as ARC research progresses

---

## Executive Summary

The ARC-AGI challenge is not just a book chapter — it is a **research
accelerator** for ZapAGI's core product. Every technique developed for
solving abstract reasoning tasks maps directly to production capabilities
that make ZapAGI smarter, faster, and more reliable.

This document catalogs each transferable technique, explains the mapping,
and provides implementation guidance for the ZapAGI engineering team.

---

## The Core Insight

ARC forces us to solve the hardest problems in AGI engineering:
1. **Novel problem solving** — no memorization, pure reasoning
2. **Few-shot learning** — learn from 2-5 examples
3. **Multi-agent orchestration** — no single model can solve it alone
4. **Verification** — exact-match evaluation, no hand-waving
5. **Efficiency** — must solve within compute budget

These are exactly the problems ZapAGI faces in production:
1. Users bring novel tasks the system has never seen
2. Users show examples of what they want (few-shot)
3. Complex tasks require multiple specialist agents
4. Users expect correct, verifiable outputs
5. Running on consumer hardware demands efficiency

---

## Transfer Map: ARC Module → ZapAGI Capability

### 1. Transduction → "Predict Before Plan"

**ARC Module:** `transducer.py` (288 LOC)

**What it does in ARC:** Before running the expensive perceive → hypothesize
→ synthesize → verify pipeline, ask the LLM to directly predict the output
grid. Simple pattern tasks are solved in 1-3 seconds instead of 100+ seconds.

**ZapAGI Application:**

Before routing a user request through the full agent pipeline, try a "fast
path" — can the request be answered directly without planning, delegation,
or tool use?

```
User: "What's the Python syntax for list comprehension?"
→ Fast path: Direct answer (no agent routing needed)
→ Saves: 2-5 seconds of routing + agent warm-up

User: "Refactor this 500-line file into modules"
→ Fast path fails (too complex)
→ Falls through to full pipeline
```

**Implementation in ZapAGI:**

```python
class ZapAGI:
    def handle_request(self, request: str) -> Response:
        # Phase 0: Transduction (fast path)
        fast_result = self.transducer.try_direct(request)
        if fast_result.confident:
            return fast_result.response

        # Phase 1: Full pipeline
        return self.pipeline.execute(request)
```

**Estimated impact:** 30-50% of user requests are simple enough for direct
answers. Eliminating routing overhead for these saves ~2s per request and
reduces VRAM pressure from loading specialist agents.

---

### 2. Evolution → Automated Code Repair

**ARC Module:** `evolver.py` (279 LOC) + `mutator.py` (317 LOC)

**What it does in ARC:** When code synthesis produces a near-miss program
(90%+ correct), systematically mutate it — tweak constants, flip operators,
adjust loop bounds — and verify each mutation. Thousands of mutations per
second with no LLM calls.

**ZapAGI Application:**

When ZapAGI's coder agent generates code that almost works (tests pass
partially, linting finds minor issues), apply systematic mutations before
asking the LLM for a full rewrite.

```
Coder produces: for i in range(len(items) - 1)   # Off-by-one
Evolution tries: for i in range(len(items))       # Fixed!
                 for i in range(len(items) + 1)   # Also tried
                 for i in range(1, len(items))     # Also tried
```

**Why this matters for ZapAGI:**

1. **Speed:** Mutation + test is ~1ms. LLM rewrite is ~2-5 seconds.
2. **Cost:** No LLM calls for simple fixes.
3. **Reliability:** Mutations are syntactically valid by construction.
4. **Debugger agent:** Volume 2 Chapter 5 (Debugger) can use this as its
   primary repair strategy before escalating to the LLM.

**Mutation types that transfer directly:**

| ARC Mutation | ZapAGI Application |
|---|---|
| Integer constant sweep | Fix off-by-one errors, array indices |
| Comparison operator flip | Fix boundary conditions (< vs <=) |
| Boolean negation | Fix inverted conditions |
| Loop bound adjustment | Fix iteration counts |
| String constant swap | Fix hardcoded paths, keys, names |

---

### 3. Multi-Model Routing → Specialist Model Assignment

**ARC Module:** `llm_bridge.py` — `ModelConfig` + `call_as(role, prompt)`

**What it does in ARC:** Route different parts of the solve pipeline to
different models. Perception goes to a reasoning model (qwen3:8b).
Code synthesis goes to a coding model (qwen2.5-coder:7b). Each model
specializes in what it's best at.

**ZapAGI Application:**

Assign the right model to the right agent:

| ZapAGI Agent | Optimal Model Type | Why |
|---|---|---|
| Router | Small, fast (1-3B fine-tuned) | Classification only, needs speed |
| Coder | Code-specialized (coder:7b) | Code quality matters most |
| Debugger | Reasoning (qwen3:8b) | Needs to analyze error traces |
| Documenter | General (llama3.2) | Prose quality, not reasoning |
| Safety checker | Small fine-tuned (1B) | Binary classification, needs speed |
| Planner | Large reasoning (14b) | Complex planning benefits from scale |

**VRAM budget management:**

ARC research showed that two 7B models fit in 12GB VRAM (~5.5GB each).
For ZapAGI on consumer hardware (8-16GB VRAM):

```
Strategy A: Single 8B model for everything (simple, 5GB)
Strategy B: 3B router + 7B worker (8GB total, better quality)
Strategy C: 1B router + 3B safety + 7B coder (11GB, best quality)
```

ARC benchmarks provide the data to choose: model X gets Y% accuracy at
Z speed. This data transfers directly to ZapAGI agent model selection.

---

### 4. Task Similarity → Knowledge Retrieval

**ARC Module:** `task_similarity.py` (405 LOC)

**What it does in ARC:** Build a feature vector for each task (grid dims,
color distribution, symmetry, complexity). Use k-NN search to find the
most similar previously-solved tasks. Inject their solutions as few-shot
context.

**ZapAGI Application:**

Build a feature vector for each user request. Find the most similar
previously-completed tasks. Inject their solutions as context.

```
User: "Create a REST API with authentication"
→ Similarity search finds 3 past sessions where we built REST APIs
→ Extract the patterns: FastAPI template, JWT auth, Pydantic models
→ Inject as context: "In similar past tasks, we used this approach..."
```

**Key insight from ARC research:** Our evaluation showed that naively
injecting similar examples can **hurt** performance (+15.7% without
few-shot vs with). The lesson: **similarity must match on the
transformation, not just the surface features.**

For ZapAGI this means: match on what the user *did*, not what they
*asked about*. A request about "database migrations" should match past
sessions where we actually ran migrations, not sessions where we
discussed them theoretically.

---

### 5. Analytics Engine → Production Monitoring

**ARC Module:** `arc_analytics.py` (382 LOC) — Polars-powered

**What it does in ARC:** Track every candidate program, its similarity
score, which mutations improved it, which hypotheses led to solves.
Export to Parquet for offline analysis.

**ZapAGI Application:**

Track every agent interaction:

```python
analytics.add_event({
    "session_id": "abc123",
    "agent": "coder",
    "model": "qwen2.5-coder:7b",
    "task_type": "code_generation",
    "input_tokens": 1200,
    "output_tokens": 450,
    "latency_ms": 2100,
    "user_accepted": True,
    "edit_distance": 12,  # How much user modified output
})
```

**Insights this enables:**

1. **Model quality tracking:** Which model produces outputs users accept most?
2. **Agent effectiveness:** Which agents get used vs bypassed?
3. **Failure analysis:** What types of requests fail most often?
4. **Cost optimization:** Which agents consume most tokens per useful output?
5. **Regression detection:** Did a model update degrade quality?

Polars is critical here — it handles millions of events efficiently for
nightly analysis without needing a database.

---

### 6. Verification Pipeline → Output Validation

**ARC Module:** `verifier.py` (331 LOC)

**What it does in ARC:** Execute synthesized code on training examples,
compare outputs to expected results, compute cell-by-cell similarity,
detect shape mismatches.

**ZapAGI Application:**

Every agent output should be verifiable:

| Agent | Verification Method |
|---|---|
| Coder | Execute code, run tests, check syntax |
| Debugger | Verify fix resolves the original error |
| Documenter | Validate markdown syntax, check links |
| DevOps | Dry-run git commands, validate configs |
| Planner | Check plan is actionable (no vague steps) |

The ARC verification pattern generalizes: **never trust LLM output — always
verify against ground truth when possible.**

---

### 7. Object-Centric Description → Structured Context

**ARC Module:** `grid_describer.py` (346 LOC)

**What it does in ARC:** Convert raw integer grids into structured
descriptions: "A 3x3 blue square at position (2,1) adjacent to a red
L-shape at (5,3)." This gives the LLM much better context than raw numbers.

**ZapAGI Application:**

Convert raw code/files into structured descriptions before sending to agents:

```
Raw: 500 lines of Python code

Structured: "A FastAPI application with:
- 3 route handlers (GET /users, POST /users, DELETE /users/{id})
- SQLAlchemy ORM with User model (5 fields)
- JWT authentication middleware
- 2 Pydantic schemas (UserCreate, UserResponse)
- No tests present"
```

This is essentially a **code perceiver** — the same pattern as ARC's
grid perceiver, applied to source code instead of grids.

---

### 8. Improved Solver Pipeline → Orchestration Template

**ARC Module:** `solve_improved.py` (281 LOC)

**What it does in ARC:** Layers three enhancement strategies on top of
the base solver:
1. Fast path (transduction)
2. Main pipeline (multi-agent loop)
3. Post-processing (evolution)

**ZapAGI Application:**

This is the template for how ZapAGI handles any complex request:

```python
class TaskOrchestrator:
    def execute(self, task):
        # Layer 1: Can we answer this directly? (fast path)
        if result := self.try_direct(task):
            return result

        # Layer 2: Full agent pipeline
        result = self.run_pipeline(task)

        # Layer 3: Can we improve a near-miss? (post-processing)
        if result.quality < threshold:
            result = self.try_improve(result)

        return result
```

This pattern applies to every task type in ZapAGI, not just ARC grids.

---

## Implementation Roadmap

### Phase 1: Extract Patterns (Week 1-2)
- [ ] Create `zapagi/patterns/` package
- [ ] Port transduction pattern → `patterns/fast_path.py`
- [ ] Port evolution pattern → `patterns/auto_repair.py`
- [ ] Port analytics pattern → `patterns/tracking.py`
- [ ] Port verification pattern → `patterns/validation.py`

### Phase 2: Integration (Week 3-4)
- [ ] Wire fast path into main request handler
- [ ] Wire auto repair into debugger agent
- [ ] Wire analytics into session tracking
- [ ] Wire validation into agent output pipeline

### Phase 3: Evaluation (Week 5-6)
- [ ] Benchmark fast path hit rate on real user sessions
- [ ] Benchmark auto repair success rate vs LLM rewrite
- [ ] Compare analytics insights to manual debugging
- [ ] User acceptance testing

---

## Cost-Benefit Summary

| Transfer | Dev Effort | User Impact | VRAM Impact |
|---|---|---|---|
| Fast path (transduction) | Low | High (30-50% faster) | Neutral |
| Auto repair (evolution) | Medium | High (fewer LLM roundtrips) | Saves VRAM |
| Multi-model routing | Medium | Medium (better quality) | +2-3GB |
| Knowledge retrieval | Medium | High (learns from history) | +1GB (index) |
| Analytics | Low | Internal (better debugging) | Neutral |
| Verification | Low | High (fewer wrong answers) | Neutral |
| Structured description | Low | Medium (better context) | Neutral |
| Orchestration template | Low | High (consistent quality) | Neutral |

**Total estimated impact:** 40-60% reduction in average response time,
20-30% improvement in output quality, with minimal VRAM overhead.

---

*ZapAGI Internal — Confidential. Copyright 2026 ZapAGI. All Rights Reserved.*
