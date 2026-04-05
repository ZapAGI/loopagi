"""
LoopAGI - A Mini Multi-Agent AGI System

Built progressively across the 22 chapters of
"God in the Loop" by Alexandros Karales.

Subpackage layout:
    loopagi/core/       - Agent infrastructure, routing, pools, pipelines, events
        agent.py        (Ch 4)  - Base Agent with Ollama LLM
        router.py       (Ch 5)  - Hierarchical routing
        pool.py         (Ch 6)  - Agent pools for parallel execution
        pipeline.py     (Ch 7)  - Quality pipeline (plan/code/test/review)
        events.py       (Ch 13) - Event bus and background agents
        session.py      (Ch 18) - Session-as-git provenance
        ollama_utils.py          - Ollama helpers and mock agents

    loopagi/knowledge/  - Memory, RAG, and context management
        memory.py       (Ch 8)  - Persistent vector memory
        rag.py          (Ch 9)  - RAG-powered knowledge retrieval
        context.py      (Ch 10) - Context engine (rules, actions, repo map)

    loopagi/safety/     - Command safety, execution modes, careful mode
        modes.py        (Ch 11) - Execution modes (Zap/Careful)
        checker.py      (Ch 12) - Command safety checker
        careful.py      (Ch 14) - Careful mode approval workflows

    loopagi/tools/      - Shell, file, code, search, and web tools
        base.py         (Ch 19) - Base tools (shell, file, registry)
        edit.py                  - File editing tool
        git.py                   - Git operations tool
        python.py                - Python execution tool
        search.py                - Code search tool
        web.py                   - Web search tool

    loopagi/arc/        - ARC-AGI challenge modules

    cli.py              (Ch 22) - Final CLI assembly
"""

__version__ = "1.0.0"
__author__ = "Alexandros Karales"
