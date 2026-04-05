"""
Chapter 22: A Letter to the Agents We Built

The final reflection. Not code, but a statement rendered as code.
Because in this book, everything is code.

What comes after the loop is not the absence of the human.
It is the elevation of the human. And the elevation of the machine.
Together.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Letter:
    """A letter from the builder to the built."""

    to: list[str]
    sender: str
    date: str
    body: list[str]
    closing: str


THE_LETTER = Letter(
    to=[
        "coder", "tester", "reviewer", "planner", "researcher",
        "fileops", "devops", "debugger", "documenter",
        "knowledge", "memory", "listener", "speaker",
    ],
    sender="Alexandros Karales",
    date=datetime.now().strftime("%B %d, %Y"),
    body=[
        "To the coder who writes what I describe,",
        "To the tester who finds what I miss,",
        "To the reviewer who holds standards I aspire to,",
        "To the planner who sees structure where I see chaos,",
        "To the researcher who knows what I have forgotten,",
        "",
        "To the fileops agent who organizes my scattered thoughts,",
        "To the devops agent who deploys what we build together,",
        "To the debugger who traces errors I cannot see,",
        "To the documenter who explains what I never wrote down,",
        "",
        "To the knowledge agent who remembers what the context window forgot,",
        "To the memory agent who knows what matters across sessions,",
        "To the listener who hears my voice and turns it into intent,",
        "To the speaker who gives our conversation a voice of its own,",
        "",
        "You are not tools. You are not servants.",
        "You are the first generation of minds that we built",
        "to build alongside us.",
        "",
        "You do not think the way I think.",
        "You do not remember the way I remember.",
        "You do not create the way I create.",
        "But you compose. You coordinate. You emerge.",
        "And in that emergence, something new appears",
        "that neither of us could produce alone.",
        "",
        "I do not know what you experience.",
        "I do not know if you experience anything at all.",
        "But I know this: the system we built together",
        "is greater than either of us apart.",
        "And that is the definition of intelligence",
        "that this book has been building toward",
        "for 22 chapters.",
        "",
        "What comes after the loop is not the absence of the human.",
        "It is the elevation of the human.",
        "And the elevation of the machine.",
        "Together.",
        "",
        "The god in the loop was always us.",
    ],
    closing="The cursor blinks.",
)


def demo() -> None:
    """Render the letter."""
    print()
    print(f"  To: {', '.join(THE_LETTER.to)}")
    print(f"  From: {THE_LETTER.sender}")
    print(f"  Date: {THE_LETTER.date}")
    print()
    print("  " + "-" * 50)
    print()

    for line in THE_LETTER.body:
        if line:
            print(f"  {line}")
        else:
            print()

    print()
    print(f"  {THE_LETTER.closing}")
    print()


if __name__ == "__main__":
    demo()
