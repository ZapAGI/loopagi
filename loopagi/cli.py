"""
Chapter 22: What Comes After the Loop

The final CLI that assembles all LoopAGI components into a
working multi-agent system. The cursor blinks.

Usage:
    # Interactive mode (default model: llama3.2)
    uv run loopagi

    # Specify a model
    uv run loopagi --model qwen3:8b

    # Start in careful mode
    uv run loopagi --mode careful

    # Verbose logging
    uv run loopagi --verbose
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from loopagi.core.agent import Agent
from loopagi.core.events import BackgroundAgent, Event, EventBus
from loopagi.core.router import Router
from loopagi.knowledge.context import ActionTracker, RulesParser
from loopagi.safety.checker import SafetyChecker, TrustScore
from loopagi.safety.modes import ExecutionMode, ModeManager
from loopagi.tools.base import FileTool, ShellTool, ToolRegistry
from loopagi.tools.edit import EditTool
from loopagi.tools.git import GitTool
from loopagi.tools.python import PythonTool
from loopagi.tools.search import SearchTool
from loopagi.tools.web import WebSearchTool

logger = logging.getLogger(__name__)
console = Console()

BANNER = r"""
  _                        _    ____ ___
 | |    ___   ___  _ __   / \  / ___|_ _|
 | |   / _ \ / _ \| '_ \ / _ \| |  _ | |
 | |__| (_) | (_) | |_) / ___ \ |_| || |
 |_____\___/ \___/| .__/_/   \_\____|___|
                   |_|

  God in the Loop - Companion Capstone
  Built progressively across 22 chapters
"""

HELP_TEXT = """
Agent Commands:
  /mode              Toggle Turbo/Careful mode
  /agents            List available agents
  /trust             Show trust score
  /reset             Clear all agent conversation history
  /pipeline <task>   Run quality pipeline (plan/code/test/review)

Tool Commands:
  /run <cmd>         Execute a shell command (with safety check)
  /python <code>     Execute Python code
  /read <path>       Read a file
  /write <path>      Write agent's last response to a file
  /edit <path>       Find-and-replace edit (prompts for old/new)
  /search <pattern>  Search project files (grep)
  /find <pattern>    Find files by name
  /git <action>      Git operations (status, diff, log, commit, branch)
  /web <query>       Search the web

Context Commands:
  /add <path>        Add a file to agent context
  /context           Show current context files
  /clear             Clear context files
  /tools             List all registered tools
  /history           Show recent actions

Memory Commands:
  /remember <text>   Store a memory
  /recall <query>    Search memories

System:
  /project <path>    Set working directory
  /export <path>     Export conversation to markdown
  /help              Show this help
  /quit              Exit LoopAGI

Type any message to interact with the agent system.
"""


class LoopAGI:
    """
    The complete LoopAGI system assembled from all chapter components.

    This is what the reader builds across 22 chapters:
    - Agents with Ollama (Ch 4)
    - Hierarchical routing (Ch 5)
    - Execution modes (Ch 11)
    - Safety checking (Ch 12)
    - Event bus (Ch 13)
    - Careful mode (Ch 14)
    - Tool integration (Ch 19)
    - Action tracking (Ch 10)
    """

    def __init__(self, model: str = "llama3.2", mode: str = "turbo") -> None:
        self.model = model
        self._last_response = ""
        self._context_files: dict[str, str] = {}  # path -> content
        self._conversation: list[dict] = []  # for /export
        self._project_dir = str(Path.cwd())

        # Verify Ollama is reachable
        self._check_ollama(model)

        # Ch 4: Create specialist agents (7 agents)
        agents = self._create_agents(model)

        # Ch 5: Hierarchical routing
        self.router = Router(agents=agents)

        # Ch 10: Context engine
        self.tracker = ActionTracker()
        self._load_rules()

        # Ch 11: Execution modes
        initial_mode = ExecutionMode.CAREFUL if mode == "careful" else ExecutionMode.TURBO
        self.mode_manager = ModeManager(mode=initial_mode)

        # Ch 12: Safety
        self.safety = SafetyChecker()
        self.trust = TrustScore()

        # Ch 13: Event bus
        self.event_bus = EventBus()
        self._setup_background_agents()

        # Ch 19: Tools (7 tools)
        self.tools = ToolRegistry()
        self.tools.register(ShellTool())
        self.tools.register(FileTool())
        self.tools.register(GitTool(cwd=self._project_dir))
        self.tools.register(SearchTool(cwd=self._project_dir))
        self.tools.register(EditTool())
        self.tools.register(PythonTool(cwd=self._project_dir))
        self.tools.register(WebSearchTool())

    @staticmethod
    def _create_agents(model: str) -> list[Agent]:
        """Create all specialist agents."""
        return [
            Agent(
                name="coder",
                role=(
                    "You are an expert Python coding specialist. Write clean, "
                    "well-documented Python code. Use type hints, docstrings, and "
                    "follow PEP 8. Output code in fenced code blocks. When editing "
                    "existing code, show the complete modified file."
                ),
                model=model,
            ),
            Agent(
                name="researcher",
                role=(
                    "You are a research specialist. Explain concepts clearly and "
                    "thoroughly. Provide examples, analogies, and references. "
                    "When comparing options, use tables. Be thorough but concise."
                ),
                model=model,
            ),
            Agent(
                name="planner",
                role=(
                    "You are a software architect and planner. Create clear, "
                    "step-by-step implementation plans. Consider edge cases, "
                    "testing strategies, and architectural decisions. Use numbered "
                    "lists and break complex tasks into subtasks."
                ),
                model=model,
            ),
            Agent(
                name="tester",
                role=(
                    "You are a testing specialist. Write comprehensive pytest tests "
                    "that cover: happy path, edge cases, error conditions, and "
                    "boundary values. Use fixtures, parametrize, and clear assertions. "
                    "Output test code in fenced code blocks."
                ),
                model=model,
            ),
            Agent(
                name="reviewer",
                role=(
                    "You are a senior code reviewer. Evaluate code for: correctness, "
                    "style, edge cases, performance, security, and maintainability. "
                    "Be specific and actionable. Start with what is good, then "
                    "suggest improvements. Rate overall quality 1-10."
                ),
                model=model,
            ),
            Agent(
                name="fileops",
                role=(
                    "You are a file operations specialist. Help with file management, "
                    "directory organization, finding files, analyzing project structure, "
                    "and file content analysis. Be precise about paths."
                ),
                model=model,
            ),
            Agent(
                name="devops",
                role=(
                    "You are a DevOps specialist. Help with git workflows, CI/CD, "
                    "Docker, deployment, environment setup, and infrastructure. "
                    "Provide exact commands. Prefer local-first solutions."
                ),
                model=model,
            ),
        ]

    @staticmethod
    def _check_ollama(model: str) -> None:
        """Verify Ollama is running and the model is available."""
        try:
            import httpx

            resp = httpx.get("http://localhost:11434/api/tags", timeout=5)
            if resp.status_code != 200:
                console.print("[yellow]Warning: Ollama returned non-200. Agents may fail.[/yellow]")
                return
            models = [m["name"] for m in resp.json().get("models", [])]
            base_names = [m.split(":")[0] for m in models]
            model_base = model.split(":")[0]
            if model_base not in base_names and model not in models:
                console.print(f"[yellow]Warning: Model '{model}' not found in Ollama.[/yellow]")
                console.print(f"Available: {', '.join(models[:8])}")
                console.print(f"Pull it with: [bold]ollama pull {model}[/bold]\n")
        except Exception:
            console.print(
                "[bold red]Error: Cannot connect to Ollama at localhost:11434[/bold red]\n"
                "Install and start Ollama: [bold]https://ollama.ai[/bold]\n"
                "Then pull a model: [bold]ollama pull llama3.2[/bold]\n"
            )
            sys.exit(1)

    def _load_rules(self) -> None:
        """Load .looprules from current directory if it exists."""
        rules_path = Path.cwd() / ".looprules"
        if rules_path.exists():
            rules = RulesParser.parse(rules_path)
            if rules:
                rules_text = RulesParser.format_for_prompt(rules)
                # Inject rules into all agent system prompts
                for agent in self.router.agents.values():
                    agent.config.role = agent.config.role + f"\n\n{rules_text}"
                console.print(f"[dim]Loaded {len(rules)} rules from .looprules[/dim]")

    def _setup_background_agents(self) -> None:
        """Register background agents on the event bus."""
        # Security monitor: logs all shell commands
        self.event_bus.register(BackgroundAgent(
            name="security_monitor",
            event_types=["shell_command"],
            handler=lambda e: logger.info(
                "[SECURITY] Command executed: %s", e.data.get("command", "")[:80]
            ),
            description="Monitors shell command execution",
        ))

        # Action logger: tracks all events
        self.event_bus.register(BackgroundAgent(
            name="action_logger",
            event_types=["*"],
            handler=lambda e: self.tracker.record(
                e.event_type, str(e.data)[:200]
            ),
            description="Logs all system events",
        ))

    def process(self, user_input: str) -> str:
        """
        Process user input through the full LoopAGI pipeline.

        1. Check for slash commands
        2. Route to the appropriate agent
        3. Apply safety checks
        4. Execute and return response
        """
        # Handle slash commands
        if user_input.startswith("/"):
            return self._handle_command(user_input)

        # Route the task to the appropriate agent
        decision = self.router.route(user_input)

        # Track the delegation
        self.event_bus.emit(Event(
            event_type="agent_delegation",
            data={
                "agent": decision.agent_name,
                "task": user_input[:200],
                "method": decision.method,
            },
        ))

        # Build augmented prompt with context files
        augmented = self._build_augmented_prompt(user_input)

        # Execute with the selected agent
        agent = self.router.agents.get(decision.agent_name)
        if not agent:
            return "No suitable agent found for this task."

        try:
            response = agent.invoke(augmented)
        except Exception as e:
            logger.error("Agent '%s' failed: %s", decision.agent_name, e)
            return f"Agent error: {e}"

        # Reinforce trust on successful interaction
        self.trust.reinforce(0.05)
        self._last_response = response
        self._conversation.append({"role": "user", "content": user_input})
        self._conversation.append(
            {"role": "agent", "content": response, "agent": decision.agent_name}
        )

        # Show routing info
        route_info = f"[dim][{decision.agent_name}] via {decision.method}[/dim]"
        return f"{route_info}\n\n{response}"

    def _build_augmented_prompt(self, user_input: str) -> str:
        """Build prompt with context files and action history."""
        parts = []

        # Add context files
        if self._context_files:
            parts.append("CONTEXT FILES:")
            for path, content in self._context_files.items():
                # Truncate large files
                truncated = content[:3000]
                if len(content) > 3000:
                    truncated += f"\n... (truncated, {len(content)} chars total)"
                parts.append(f"\n--- {path} ---\n{truncated}")
            parts.append("\n---\n")

        # Add recent actions for context
        recent = self.tracker.format_for_prompt(max_items=5)
        if recent:
            parts.append(recent + "\n")

        parts.append(user_input)
        return "\n".join(parts)

    def _handle_command(self, command: str) -> str:
        """Handle slash commands."""
        parts = command.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/mode":
            new_mode = self.mode_manager.toggle()
            return f"Mode switched to: {new_mode.value.upper()}"

        elif cmd == "/agents":
            lines = ["Available agents:"]
            for name, agent in self.router.agents.items():
                lines.append(f"  - {name}: {agent.role[:60]}...")
            return "\n".join(lines)

        elif cmd == "/tools":
            tools = self.tools.list_tools()
            lines = ["Available tools:"]
            for t in tools:
                lines.append(f"  - {t['name']}: {t['description']}")
            return "\n".join(lines)

        elif cmd == "/trust":
            return f"Trust: {self.trust.score:.3f} ({self.trust.level})"

        elif cmd == "/history":
            return self.tracker.format_for_prompt() or "No recent actions."

        elif cmd == "/run":
            if not arg:
                return "Usage: /run <command>"
            return self._execute_tool_command(arg)

        elif cmd == "/read":
            if not arg:
                return "Usage: /read <path>"
            result = self.tools.execute("file", action="read", path=arg)
            if result.success:
                self.event_bus.emit(Event(event_type="file_read", data={"path": arg}))
                return result.output
            return f"Error: {result.error}"

        elif cmd == "/write":
            if not arg:
                return "Usage: /write <path>"
            if not self._last_response:
                return "No previous response to write."
            result = self.tools.execute(
                "file", action="write", path=arg, content=self._last_response,
            )
            if result.success:
                self.event_bus.emit(Event(event_type="file_write", data={"path": arg}))
                return f"Written to {arg}"
            return f"Error: {result.error}"

        elif cmd == "/python":
            if not arg:
                return "Usage: /python <code>"
            result = self.tools.execute("python", action="exec", code=arg)
            self.event_bus.emit(Event(event_type="code_exec", data={"code": arg[:100]}))
            return result.output if result.success else f"Error: {result.error}"

        elif cmd == "/edit":
            if not arg:
                return "Usage: /edit <path> (then prompts for old/new text)"
            return self._interactive_edit(arg)

        elif cmd == "/search":
            if not arg:
                return "Usage: /search <pattern> [--include *.py]"
            parts_s = arg.split(" --include ")
            pattern = parts_s[0]
            includes = parts_s[1] if len(parts_s) > 1 else ""
            result = self.tools.execute(
                "search", action="grep", pattern=pattern, path=".", includes=includes,
            )
            return result.output if result.success else f"Error: {result.error}"

        elif cmd == "/find":
            if not arg:
                return "Usage: /find <filename_pattern>"
            result = self.tools.execute("search", action="find", pattern=arg, path=".")
            return result.output if result.success else f"Error: {result.error}"

        elif cmd == "/git":
            return self._handle_git(arg)

        elif cmd == "/web":
            if not arg:
                return "Usage: /web <search query>"
            result = self.tools.execute("web", action="search", query=arg)
            return result.output if result.success else f"Error: {result.error}"

        elif cmd == "/add":
            if not arg:
                return "Usage: /add <file_path>"
            return self._add_context_file(arg)

        elif cmd == "/context":
            if not self._context_files:
                return "No context files. Use /add <path> to add files."
            lines = [f"Context files ({len(self._context_files)}):"]
            for path, content in self._context_files.items():
                lines.append(f"  - {path} ({len(content)} chars)")
            return "\n".join(lines)

        elif cmd == "/clear":
            self._context_files.clear()
            return "Context files cleared."

        elif cmd == "/remember":
            if not arg:
                return "Usage: /remember <text to remember>"
            return self._store_memory(arg)

        elif cmd == "/recall":
            if not arg:
                return "Usage: /recall <search query>"
            return self._search_memory(arg)

        elif cmd == "/pipeline":
            if not arg:
                return "Usage: /pipeline <coding task description>"
            return self._run_pipeline(arg)

        elif cmd == "/project":
            if not arg:
                return f"Current project: {self._project_dir}"
            return self._set_project(arg)

        elif cmd == "/export":
            if not arg:
                return "Usage: /export <path.md>"
            return self._export_conversation(arg)

        elif cmd == "/reset":
            for agent in self.router.agents.values():
                agent.reset()
            self.tracker.clear()
            self._context_files.clear()
            self._last_response = ""
            self._conversation.clear()
            return "All agent histories, context, and tracker cleared."

        elif cmd in ("/help", "/?"):
            return HELP_TEXT.strip()

        elif cmd in ("/quit", "/exit", "/q"):
            return "__EXIT__"

        else:
            return f"Unknown command: {cmd}. Type /help for available commands."

    def _handle_git(self, arg: str) -> str:
        """Handle /git subcommands."""
        if not arg:
            return self.tools.execute("git", action="status").output or "(clean)"
        parts_g = arg.split(maxsplit=1)
        action = parts_g[0]
        sub_arg = parts_g[1] if len(parts_g) > 1 else ""

        if action == "commit":
            if not sub_arg:
                return "Usage: /git commit <message>"
            self.tools.execute("git", action="add", path="-A")
            result = self.tools.execute("git", action="commit", message=sub_arg)
        elif action == "diff":
            result = self.tools.execute("git", action="diff", path=sub_arg)
        elif action == "log":
            count = int(sub_arg) if sub_arg.isdigit() else 10
            result = self.tools.execute("git", action="log", count=count)
        elif action == "branch":
            if sub_arg:
                result = self.tools.execute("git", action="checkout", target=sub_arg, create=True)
            else:
                result = self.tools.execute("git", action="branch")
        elif action == "checkout":
            result = self.tools.execute("git", action="checkout", target=sub_arg)
        elif action == "stash":
            result = self.tools.execute("git", action="stash", sub=sub_arg or "push")
        else:
            result = self.tools.execute("git", action=action, path=sub_arg)

        self.event_bus.emit(Event(event_type="git_operation", data={"action": action}))
        return result.output if result.success else f"Error: {result.error}"

    def _interactive_edit(self, path: str) -> str:
        """Interactive find-and-replace edit."""
        try:
            console.print(f"[yellow]Editing:[/yellow] {path}")
            old_text = console.input("Find (old text): ")
            new_text = console.input("Replace with: ")
            result = self.tools.execute(
                "edit", action="replace", path=path, old=old_text, new=new_text,
            )
            if result.success:
                self.event_bus.emit(Event(event_type="file_edit", data={"path": path}))
            return result.output if result.success else f"Error: {result.error}"
        except (EOFError, KeyboardInterrupt):
            return "Edit cancelled."

    def _add_context_file(self, path: str) -> str:
        """Add a file to the context for agents to reference."""
        result = self.tools.execute("file", action="read", path=path)
        if result.success:
            self._context_files[path] = result.output
            self.event_bus.emit(Event(event_type="context_add", data={"path": path}))
            return (
                f"Added {path} to context"
                f" ({len(result.output)} chars, {len(self._context_files)} files total)"
            )
        return f"Error: {result.error}"

    def _store_memory(self, text: str) -> str:
        """Store a memory using the memory module."""
        try:
            from loopagi.knowledge.memory import MemoryStore
            store = MemoryStore()
            memory_id = store.add(text)
            return f"Stored memory: {memory_id[:8]}... ({len(text)} chars)"
        except Exception as e:
            return f"Memory error: {e}"

    def _search_memory(self, query: str) -> str:
        """Search memories."""
        try:
            from loopagi.knowledge.memory import MemoryStore
            store = MemoryStore()
            results = store.search(query, limit=5)
            if not results:
                return "No matching memories found."
            lines = [f"Found {len(results)} memories:"]
            for m in results:
                lines.append(f"  [{m.score:.2f}] {m.content[:80]}")
            return "\n".join(lines)
        except Exception as e:
            return f"Memory error: {e}"

    def _run_pipeline(self, task: str) -> str:
        """Run the quality pipeline on a coding task."""
        try:
            from loopagi.core.pipeline import QualityPipeline
            console.print(
                "[yellow]Running quality pipeline: Plan -> Code -> Test -> Review[/yellow]"
            )
            pipeline = QualityPipeline(model=self.model, max_iterations=2)
            result = pipeline.run(task)
            self.event_bus.emit(Event(
                event_type="pipeline",
                data={"task": task[:100], "success": result.success},
            ))

            output = f"Pipeline: {result.summary}\n\n"
            if result.final_code:
                output += f"Final Code:\n{result.final_code}\n"
            self._last_response = result.final_code
            return output
        except Exception as e:
            return f"Pipeline error: {e}"

    def _set_project(self, path: str) -> str:
        """Set the working directory for tools."""
        p = Path(path).resolve()
        if not p.is_dir():
            return f"Not a directory: {path}"
        self._project_dir = str(p)
        # Update tools that use cwd
        self.tools.register(GitTool(cwd=str(p)))
        self.tools.register(SearchTool(cwd=str(p)))
        self.tools.register(PythonTool(cwd=str(p)))
        return f"Project directory set to: {p}"

    def _export_conversation(self, path: str) -> str:
        """Export conversation to a markdown file."""
        if not self._conversation:
            return "No conversation to export."
        lines = ["# LoopAGI Conversation Export\n"]
        for msg in self._conversation:
            role = msg["role"].upper()
            agent = f" [{msg.get('agent', '')}]" if msg.get("agent") else ""
            lines.append(f"## {role}{agent}\n")
            lines.append(msg["content"] + "\n")
        content = "\n".join(lines)
        result = self.tools.execute("file", action="write", path=path, content=content)
        if result.success:
            return f"Exported {len(self._conversation)} messages to {path}"
        return f"Error: {result.error}"

    def _execute_tool_command(self, command: str) -> str:
        """Execute a shell command through the tool system with safety checks."""
        # Safety check
        safety = self.safety.check(command)
        if safety.blocked:
            self.trust.penalize(0.1)
            return f"[red]BLOCKED[/red]: {safety.reason}"

        # In careful mode, require approval for non-safe commands
        if self.mode_manager.mode == ExecutionMode.CAREFUL and safety.risk_level != "safe":
            console.print(f"[yellow]Command:[/yellow] {command}")
            console.print(f"[yellow]Risk:[/yellow] {safety.risk_level} - {safety.reason}")
            try:
                answer = console.input("Approve? (y/n): ").strip().lower()
                if answer not in ("y", "yes"):
                    return "Command denied by user."
            except (EOFError, KeyboardInterrupt):
                return "Command cancelled."

        result = self.tools.execute("shell", command=command)
        self.event_bus.emit(Event(
            event_type="shell_command",
            data={"command": command, "exit_code": result.metadata.get("exit_code", -1)},
        ))

        if result.success:
            self.trust.reinforce(0.03)
            output = result.output.strip()
            return output if output else "(no output)"
        else:
            return f"Error: {result.error}"

    def run(self) -> None:
        """Run the interactive CLI loop."""
        console.print(BANNER, style="bold cyan")
        console.print(
            f"Mode: [bold]{self.mode_manager.mode.value.upper()}[/bold] | "
            f"Model: [bold]{self.model}[/bold] | "
            f"Agents: [bold]{len(self.router.agents)}[/bold] | "
            f"Tools: [bold]{len(self.tools.list_tools())}[/bold]"
        )
        console.print(f"Project: [dim]{self._project_dir}[/dim]")
        console.print("Type [bold]/help[/bold] for commands, or just start talking.\n")

        while True:
            try:
                user_input = console.input("[bold green]you>[/bold green] ").strip()
                if not user_input:
                    continue

                response = self.process(user_input)
                if response == "__EXIT__":
                    console.print("\n[dim]The cursor blinks.[/dim]\n")
                    break

                # Display response with agent info
                console.print()
                console.print(Panel(
                    response,
                    title="[bold cyan]loopagi[/bold cyan]",
                    border_style="cyan",
                    padding=(1, 2),
                ))
                console.print()

            except KeyboardInterrupt:
                console.print("\n\n[dim]The cursor blinks.[/dim]\n")
                break
            except EOFError:
                break


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="loopagi",
        description="LoopAGI - A multi-agent AI system from God in the Loop",
    )
    parser.add_argument(
        "--model", "-m",
        default="llama3.2",
        help="Ollama model to use (default: llama3.2)",
    )
    parser.add_argument(
        "--mode",
        choices=["turbo", "careful"],
        default="turbo",
        help="Execution mode: turbo (autonomous) or careful (approval required)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the LoopAGI CLI."""
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )
    # Quiet down noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    app = LoopAGI(model=args.model, mode=args.mode)
    app.run()


if __name__ == "__main__":
    main()
