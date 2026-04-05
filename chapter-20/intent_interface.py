"""
Chapter 20: Intent-Based Interaction

What happens when the user describes what they want and the
OS figures out how? Intent replaces interface.

This demo shows how natural language intents can be parsed
into executable actions without traditional GUI elements.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Intent:
    """A parsed user intent."""

    action: str
    target: str
    parameters: dict = field(default_factory=dict)
    confidence: float = 0.0
    raw_input: str = ""


@dataclass
class IntentPattern:
    """A pattern for matching intents from natural language."""

    action: str
    patterns: list[str]
    parameter_extractors: dict[str, str] = field(default_factory=dict)


INTENT_PATTERNS: list[IntentPattern] = [
    IntentPattern(
        action="open_file",
        patterns=[
            r"open\s+(.+)",
            r"show\s+(?:me\s+)?(.+)",
            r"read\s+(.+)",
            r"display\s+(.+)",
        ],
        parameter_extractors={"path": r"(.+)"},
    ),
    IntentPattern(
        action="create_file",
        patterns=[
            r"create\s+(?:a\s+)?(?:new\s+)?(?:file\s+)?(.+)",
            r"make\s+(?:a\s+)?(?:new\s+)?(.+)",
            r"new\s+file\s+(.+)",
        ],
        parameter_extractors={"path": r"(.+)"},
    ),
    IntentPattern(
        action="search",
        patterns=[
            r"(?:search|find|look)\s+(?:for\s+)?(.+)",
            r"where\s+is\s+(.+)",
            r"grep\s+(.+)",
        ],
        parameter_extractors={"query": r"(.+)"},
    ),
    IntentPattern(
        action="run_command",
        patterns=[
            r"run\s+(.+)",
            r"execute\s+(.+)",
            r"start\s+(.+)",
        ],
        parameter_extractors={"command": r"(.+)"},
    ),
    IntentPattern(
        action="install",
        patterns=[
            r"install\s+(.+)",
            r"add\s+(?:package\s+)?(.+)",
            r"set\s*up\s+(.+)",
        ],
        parameter_extractors={"package": r"(.+)"},
    ),
    IntentPattern(
        action="explain",
        patterns=[
            r"(?:explain|what\s+is|describe|tell\s+me\s+about)\s+(.+)",
            r"how\s+does\s+(.+)\s+work",
            r"why\s+(.+)",
        ],
        parameter_extractors={"topic": r"(.+)"},
    ),
    IntentPattern(
        action="git_operation",
        patterns=[
            r"commit\s+(.+)",
            r"push\s*(?:to\s+)?(.+)?",
            r"(?:create|make)\s+(?:a\s+)?branch\s+(.+)",
            r"merge\s+(.+)",
        ],
        parameter_extractors={"target": r"(.+)"},
    ),
    IntentPattern(
        action="test",
        patterns=[
            r"(?:run\s+)?tests?\s*(?:for\s+)?(.+)?",
            r"check\s+(.+)",
            r"verify\s+(.+)",
        ],
        parameter_extractors={"target": r"(.*)"},
    ),
]


def parse_intent(user_input: str) -> Intent:
    """
    Parse natural language into a structured intent.

    This is the core of intent-based interaction:
    the user says what they want, the system determines how.
    """
    text = user_input.strip().lower()

    best_match: Intent | None = None
    best_confidence = 0.0

    for ip in INTENT_PATTERNS:
        for pattern in ip.patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                # Extract parameters
                params = {}
                captured = match.group(1) if match.lastindex else ""
                for param_name, extractor in ip.parameter_extractors.items():
                    param_match = re.match(extractor, captured)
                    if param_match:
                        params[param_name] = param_match.group(1).strip()

                confidence = len(match.group(0)) / len(text) if text else 0
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = Intent(
                        action=ip.action,
                        target=captured.strip(),
                        parameters=params,
                        confidence=confidence,
                        raw_input=user_input,
                    )

    if best_match:
        return best_match

    return Intent(
        action="unknown",
        target=text,
        confidence=0.0,
        raw_input=user_input,
    )


def intent_to_command(intent: Intent) -> str:
    """Convert a parsed intent into an executable command or action."""
    match intent.action:
        case "open_file":
            return f"/read {intent.parameters.get('path', intent.target)}"
        case "create_file":
            return f"/write {intent.parameters.get('path', intent.target)}"
        case "search":
            return f"/search {intent.parameters.get('query', intent.target)}"
        case "run_command":
            return f"/run {intent.parameters.get('command', intent.target)}"
        case "install":
            pkg = intent.parameters.get("package", intent.target)
            return f"/run uv add {pkg}"
        case "explain":
            return f"Explain {intent.parameters.get('topic', intent.target)}"
        case "git_operation":
            return f"/git {intent.target}"
        case "test":
            target = intent.parameters.get("target", "")
            return f"/run pytest {target}".strip()
        case _:
            return intent.raw_input


def demo() -> None:
    """Demonstrate intent-based interaction parsing."""
    print("Chapter 20: Intent-Based Interaction")
    print("=" * 60)
    print()
    print("The user describes WHAT they want. The system figures out HOW.")
    print()

    test_inputs = [
        "open main.py",
        "show me the README",
        "create a new file called utils.py",
        "search for authentication",
        "find the config file",
        "run the tests",
        "install requests",
        "explain how routing works",
        "commit the changes",
        "what is the Kardashev scale",
        "make a branch called feature/auth",
        "execute python main.py",
        "where is the database config",
        "check the API endpoints",
    ]

    print(f"{'User Input':<40} {'Intent':<15} {'Conf':<6} {'Command'}")
    print("-" * 90)

    for user_input in test_inputs:
        intent = parse_intent(user_input)
        command = intent_to_command(intent)
        print(
            f"  {user_input:<38} {intent.action:<15} {intent.confidence:<6.2f} {command}"
        )

    print()
    print("In an intent-based OS, the user never needs to know the exact")
    print("command syntax. They describe what they want in natural language.")
    print("The system translates intent into action.")
    print()
    print("This is ZAPIX: when you boot your machine and the first thing")
    print("it says is 'How can I help?'")


if __name__ == "__main__":
    demo()
