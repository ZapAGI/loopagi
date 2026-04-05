"""
Chapter 20: Agent Kernel - OS Abstractions for Artificial Minds

What happens when the AI is not an app on your desktop, but IS
your desktop? The agent kernel provides OS-level primitives for
managing agent lifecycles, resources, and communication.

The future operating system does not run apps. It runs agents.
And the user is the god in the loop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentState(str, Enum):
    """Agent lifecycle states (analogous to process states in an OS)."""

    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


@dataclass
class AgentProcess:
    """
    An agent process in the agent kernel.

    Analogous to a process in a traditional OS, but designed
    for AI agent lifecycles. Each agent has a PID, state,
    resource allocation, and communication channels.
    """

    pid: int
    name: str
    agent_type: str
    state: AgentState = AgentState.CREATED
    priority: int = 5  # 1 (highest) to 10 (lowest)
    memory_mb: int = 0
    vram_mb: int = 0
    model: str = ""
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentKernel:
    """
    The Agent Kernel: OS abstractions for artificial minds.

    Provides:
    - Agent lifecycle management (create, start, suspend, terminate)
    - Resource allocation (memory, VRAM, model slots)
    - Inter-agent communication (message passing)
    - Scheduling (priority-based agent execution)
    - Health monitoring
    """

    def __init__(self, total_vram_mb: int = 16384, max_agents: int = 50) -> None:
        self._processes: dict[int, AgentProcess] = {}
        self._next_pid = 1
        self._total_vram = total_vram_mb
        self._max_agents = max_agents
        self._message_queue: list[dict] = []

    def spawn(self, name: str, agent_type: str, model: str = "llama3.2", **kwargs) -> AgentProcess:
        """Spawn a new agent process."""
        if len(self._processes) >= self._max_agents:
            raise RuntimeError(f"Maximum agent limit ({self._max_agents}) reached")

        pid = self._next_pid
        self._next_pid += 1

        process = AgentProcess(
            pid=pid,
            name=name,
            agent_type=agent_type,
            model=model,
            state=AgentState.READY,
            **kwargs,
        )
        self._processes[pid] = process
        return process

    def start(self, pid: int) -> None:
        """Start an agent process."""
        proc = self._get_process(pid)
        if proc.state not in (AgentState.READY, AgentState.SUSPENDED):
            raise RuntimeError(f"Cannot start agent in state {proc.state}")
        proc.state = AgentState.RUNNING

    def suspend(self, pid: int) -> None:
        """Suspend a running agent."""
        proc = self._get_process(pid)
        proc.state = AgentState.SUSPENDED

    def terminate(self, pid: int) -> None:
        """Terminate an agent process."""
        proc = self._get_process(pid)
        proc.state = AgentState.TERMINATED

    def send_message(self, from_pid: int, to_pid: int, content: str) -> None:
        """Send a message between agents."""
        self._message_queue.append({
            "from": from_pid,
            "to": to_pid,
            "content": content,
            "timestamp": time.time(),
        })

    def list_processes(self) -> list[AgentProcess]:
        """List all agent processes."""
        return list(self._processes.values())

    @property
    def used_vram(self) -> int:
        return sum(p.vram_mb for p in self._processes.values() if p.state == AgentState.RUNNING)

    @property
    def available_vram(self) -> int:
        return self._total_vram - self.used_vram

    def _get_process(self, pid: int) -> AgentProcess:
        proc = self._processes.get(pid)
        if not proc:
            raise ValueError(f"No agent process with PID {pid}")
        return proc


def demo() -> None:
    """Demonstrate the agent kernel."""
    print("Chapter 20: ZAPIX Agent Kernel")
    print("=" * 60)

    kernel = AgentKernel(total_vram_mb=16384, max_agents=20)

    # Spawn agent processes
    agents_to_spawn = [
        ("master", "orchestrator", "llama3.2", 4096),
        ("coder:0", "specialist", "qwen2.5-coder:14b", 3072),
        ("coder:1", "specialist", "qwen2.5-coder:14b", 3072),
        ("tester", "specialist", "llama3.2", 2048),
        ("reviewer", "specialist", "llama3.2", 2048),
        ("researcher", "specialist", "llama3.2", 2048),
        ("security_scanner", "background", "llama3.2", 0),
        ("health_monitor", "background", "llama3.2", 0),
    ]

    print("\nSpawning agent processes:")
    for name, atype, model, vram in agents_to_spawn:
        proc = kernel.spawn(name, atype, model=model, vram_mb=vram)
        kernel.start(proc.pid)
        print(f"  PID {proc.pid:3d} | {name:<20} | {atype:<14} | {model:<20} | {vram}MB VRAM")

    # Show process table
    print("\nAgent Process Table:")
    print("-" * 70)
    print(f"{'PID':<6} {'Name':<20} {'Type':<14} {'State':<12} {'VRAM'}")
    print("-" * 70)
    for proc in kernel.list_processes():
        print(
            f"{proc.pid:<6} {proc.name:<20} {proc.agent_type:<14}"
            f" {proc.state.value:<12} {proc.vram_mb}MB"
        )

    print(
        f"\nVRAM: {kernel.used_vram}/{kernel._total_vram}MB used"
        f" ({kernel.available_vram}MB available)"
    )

    # Simulate inter-agent communication
    print("\nInter-Agent Messages:")
    kernel.send_message(1, 2, "Handle coding task: implement fibonacci")
    kernel.send_message(2, 4, "Code complete, please run tests")
    kernel.send_message(4, 5, "Tests pass, please review")
    for msg in kernel._message_queue:
        print(f"  PID {msg['from']} -> PID {msg['to']}: {msg['content']}")

    # Boot sequence
    print("\nZAPIX Boot Sequence:")
    print("-" * 50)
    boot_steps = [
        "UEFI firmware initialization",
        "Linux kernel boot (6.13)",
        "Systemd service startup",
        "ZAPIX agent kernel initialization",
        "Biometric authentication (face + voice + YubiKey)",
        "Master orchestrator spawned (PID 1)",
        "Specialist agents spawned (PID 2-6)",
        "Background agents spawned (PID 7-8)",
        "Context engine loaded (.looprules, memories)",
        "'How can I help?' displayed",
    ]
    for i, step in enumerate(boot_steps, 1):
        print(f"  [{i:2d}] {step}")

    print()
    print("When you boot your machine and the first thing it says is")
    print("'How can I help?', you will understand why this chapter exists.")


if __name__ == "__main__":
    demo()
