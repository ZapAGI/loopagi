"""
Chapter 1: Intelligence Definitions Analysis

The word "intelligence" has 74 competing definitions and counting.
This module catalogs representative definitions, classifies them,
and finds the common thread: adaptation and composition.

The builder's definition:
    "Intelligence is the ability to compose solutions from experience."
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntelligenceDefinition:
    """A definition of intelligence from the literature."""

    source: str
    year: int
    definition: str
    field: str
    emphasizes: str


# 15 representative definitions spanning multiple fields
DEFINITIONS: list[IntelligenceDefinition] = [
    IntelligenceDefinition(
        source="Alan Turing",
        year=1950,
        definition="A machine is intelligent if it can fool a human judge in conversation.",
        field="Computer Science",
        emphasizes="Behavioral mimicry",
    ),
    IntelligenceDefinition(
        source="John McCarthy",
        year=1956,
        definition="The science and engineering of making intelligent machines.",
        field="Computer Science",
        emphasizes="Engineering capability",
    ),
    IntelligenceDefinition(
        source="Marvin Minsky",
        year=1968,
        definition="Intelligence is the ability to solve hard problems.",
        field="Computer Science",
        emphasizes="Problem solving",
    ),
    IntelligenceDefinition(
        source="Howard Gardner",
        year=1983,
        definition=(
            "Multiple intelligences: linguistic, logical, spatial, musical,"
            " bodily, interpersonal, intrapersonal, naturalist."
        ),
        field="Psychology",
        emphasizes="Multiplicity of abilities",
    ),
    IntelligenceDefinition(
        source="Robert Sternberg",
        year=1985,
        definition=(
            "Intelligence is mental activity directed toward purposive"
            " adaptation to, selection of, and shaping of"
            " real-world environments."
        ),
        field="Psychology",
        emphasizes="Adaptation to environment",
    ),
    IntelligenceDefinition(
        source="Shane Legg & Marcus Hutter",
        year=2007,
        definition=(
            "Intelligence measures an agent's ability to achieve"
            " goals in a wide range of environments."
        ),
        field="AGI Research",
        emphasizes="Generalization across environments",
    ),
    IntelligenceDefinition(
        source="Francois Chollet",
        year=2019,
        definition=(
            "Intelligence is the rate at which a learner turns"
            " experience and priors into skill at new tasks."
        ),
        field="Machine Learning",
        emphasizes="Learning efficiency",
    ),
    IntelligenceDefinition(
        source="Charles Spearman",
        year=1904,
        definition="A general factor (g) underlying all cognitive abilities.",
        field="Psychology",
        emphasizes="General cognitive factor",
    ),
    IntelligenceDefinition(
        source="Jean Piaget",
        year=1952,
        definition="Intelligence is what you use when you don't know what to do.",
        field="Developmental Psychology",
        emphasizes="Novelty handling",
    ),
    IntelligenceDefinition(
        source="Jeff Hawkins",
        year=2004,
        definition=(
            "Intelligence is the ability to make predictions"
            " based on memory of past patterns."
        ),
        field="Neuroscience",
        emphasizes="Prediction from memory",
    ),
    IntelligenceDefinition(
        source="Max Tegmark",
        year=2017,
        definition="Intelligence is the ability to accomplish complex goals.",
        field="Physics / AGI",
        emphasizes="Goal achievement",
    ),
    IntelligenceDefinition(
        source="Integrated Information Theory",
        year=2004,
        definition=(
            "Consciousness (and intelligence) arise from"
            " integrated information (Phi) in a system."
        ),
        field="Neuroscience",
        emphasizes="Information integration",
    ),
    IntelligenceDefinition(
        source="Artificial General Intelligence (consensus)",
        year=2020,
        definition="A system that can perform any intellectual task that a human can.",
        field="AGI Research",
        emphasizes="Human-level generality",
    ),
    IntelligenceDefinition(
        source="Alexandros Karales",
        year=2026,
        definition="Intelligence is the ability to compose solutions from experience.",
        field="AGI Engineering",
        emphasizes="Composition and experience",
    ),
    IntelligenceDefinition(
        source="Hypothesis I1 (God in the Loop)",
        year=2026,
        definition=(
            "Intelligence is not a property of a single system"
            " but an emergent quality of orchestrated specialists."
        ),
        field="AGI Engineering",
        emphasizes="Emergence from orchestration",
    ),
]


def classify_definitions() -> dict[str, list[IntelligenceDefinition]]:
    """Group definitions by what they emphasize."""
    groups: dict[str, list[IntelligenceDefinition]] = {}
    for d in DEFINITIONS:
        groups.setdefault(d.emphasizes, []).append(d)
    return groups


def find_common_threads() -> list[str]:
    """Identify themes that appear across multiple definitions."""
    themes = {
        "Adaptation": ["adaptation", "environment", "goals", "new tasks"],
        "Composition": ["compose", "orchestrat", "integrat", "multiple"],
        "Learning": ["learn", "experience", "memory", "priors"],
        "Generalization": ["wide range", "general", "any", "new"],
        "Problem Solving": ["problem", "solve", "accomplish", "achieve"],
    }

    results = []
    for theme, keywords in themes.items():
        count = 0
        for d in DEFINITIONS:
            text = (d.definition + " " + d.emphasizes).lower()
            if any(kw in text for kw in keywords):
                count += 1
        if count >= 3:
            results.append(f"{theme} ({count}/{len(DEFINITIONS)} definitions)")

    return results


# --- Demonstration ---


def demo() -> None:
    """Display and analyze intelligence definitions."""
    print("Intelligence Definitions Analysis")
    print("=" * 70)
    print(f"\nTotal definitions cataloged: {len(DEFINITIONS)}")
    print()

    # Display table
    print(f"{'Source':<30} {'Year':<6} {'Field':<20} {'Emphasizes'}")
    print("-" * 90)
    for d in DEFINITIONS:
        print(f"{d.source:<30} {d.year:<6} {d.field:<20} {d.emphasizes}")

    # Classification
    print("\nClassification by Emphasis:")
    print("-" * 40)
    groups = classify_definitions()
    for emphasis, defs in groups.items():
        sources = ", ".join(d.source.split("(")[0].strip() for d in defs)
        print(f"  {emphasis}: {sources}")

    # Common threads
    print("\nCommon Threads Across Definitions:")
    print("-" * 40)
    threads = find_common_threads()
    for thread in threads:
        print(f"  - {thread}")

    # The builder's conclusion
    print("\n" + "=" * 70)
    print("THE BUILDER'S CONCLUSION:")
    print()
    print("  'Intelligence is not a destination. It is an architecture.'")
    print()
    print("  All definitions point to: the ability to COMPOSE new solutions")
    print("  from EXPERIENCE, across DIVERSE environments, through")
    print("  ORCHESTRATED SPECIALISTS that produce EMERGENT behavior.")
    print("=" * 70)


if __name__ == "__main__":
    demo()
