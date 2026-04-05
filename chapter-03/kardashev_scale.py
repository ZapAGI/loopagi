"""
Chapter 3: Kardashev Scale and Civilization Progression

Humanity is at approximately 0.73 on the Kardashev Scale.
AGI may be the catalyst for advancing to Type I.

The five requirements for Type I:
1. Energy mastery
2. Information mastery (AGI)
3. Social unity
4. Environmental restoration
5. Digital sovereignty
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CivilizationMilestone:
    """A milestone on the path to Type I civilization."""

    name: str
    kardashev_level: float
    year_estimate: int
    description: str
    agi_contribution: str


MILESTONES: list[CivilizationMilestone] = [
    CivilizationMilestone(
        name="Industrial Revolution",
        kardashev_level=0.58,
        year_estimate=1800,
        description="Steam power, mechanized production",
        agi_contribution="N/A",
    ),
    CivilizationMilestone(
        name="Nuclear Age",
        kardashev_level=0.63,
        year_estimate=1945,
        description="Nuclear fission, early computing",
        agi_contribution="N/A",
    ),
    CivilizationMilestone(
        name="Internet Era",
        kardashev_level=0.72,
        year_estimate=1995,
        description="Global information network",
        agi_contribution="Foundation for distributed AI",
    ),
    CivilizationMilestone(
        name="Current (2026)",
        kardashev_level=0.73,
        year_estimate=2026,
        description="Large language models, multi-agent systems",
        agi_contribution="Local-first AGI on consumer hardware",
    ),
    CivilizationMilestone(
        name="AGI Threshold",
        kardashev_level=0.78,
        year_estimate=2030,
        description="Autonomous multi-agent orchestration",
        agi_contribution="Self-improving agent systems",
    ),
    CivilizationMilestone(
        name="Energy Optimization",
        kardashev_level=0.85,
        year_estimate=2035,
        description="AGI-managed energy grids, fusion progress",
        agi_contribution="Real-time optimization of power distribution",
    ),
    CivilizationMilestone(
        name="Digital Sovereignty",
        kardashev_level=0.90,
        year_estimate=2040,
        description="Decentralized identity, local AI for all",
        agi_contribution="Every person has a personal AGI agent",
    ),
    CivilizationMilestone(
        name="Type I Civilization",
        kardashev_level=1.00,
        year_estimate=2050,
        description="Full planetary energy and information mastery",
        agi_contribution="AGI as planetary coordination infrastructure",
    ),
]


def kardashev_power(level: float) -> float:
    """
    Calculate power consumption for a Kardashev level.

    K = log10(P) / 10, where P is power in watts.
    Therefore P = 10^(10*K)

    Type I = 10^16 W (total solar energy reaching Earth)
    Type II = 10^26 W (total stellar output)
    Type III = 10^36 W (total galactic output)
    """
    return 10 ** (10 * level)


def years_to_type_one(current_level: float, growth_rate: float = 0.003) -> float:
    """
    Estimate years to reach Type I at a given growth rate.

    Assumes exponential growth in energy utilization.
    Historical growth rate is approximately 0.3% per year.
    AGI could accelerate this to 0.5-1% per year.
    """
    remaining = 1.0 - current_level
    if growth_rate <= 0:
        return float("inf")
    return remaining / growth_rate


def demo() -> None:
    """Display the Kardashev scale progression with AGI milestones."""
    print("Kardashev Scale: Humanity's Path to Type I")
    print("=" * 70)
    print()

    # Visual scale
    print("Scale: 0.0 -------- 0.5 -------- 1.0 (Type I)")
    print()

    for m in MILESTONES:
        bar_pos = int(m.kardashev_level * 50)
        bar = "." * bar_pos + "█" + "." * (50 - bar_pos)
        print(f"  [{bar}] {m.kardashev_level:.2f}")
        print(f"  {m.name} ({m.year_estimate})")
        print(f"  {m.description}")
        if m.agi_contribution != "N/A":
            print(f"  AGI role: {m.agi_contribution}")
        print()

    # Projections
    current = 0.73
    print("Projections to Type I:")
    print("-" * 50)
    projections = [
        (0.003, "Historical (0.3%/yr)"),
        (0.005, "With AGI (0.5%/yr)"),
        (0.01, "Accelerated (1%/yr)"),
    ]
    for rate, label in projections:
        years = years_to_type_one(current, rate)
        target_year = 2026 + int(years)
        print(f"  {label}: ~{int(years)} years (by {target_year})")

    print()
    print("Power at current level (0.73): {:.2e} watts".format(kardashev_power(0.73)))
    print("Power at Type I (1.00):        {:.2e} watts".format(kardashev_power(1.0)))
    print()
    print("AGI is the catalyst for items 2-5 of the Type I requirements:")
    print("  2. Information mastery")
    print("  3. Social unity (shared digital infrastructure)")
    print("  4. Environmental restoration (optimization at scale)")
    print("  5. Digital sovereignty (personal AI for every human)")


if __name__ == "__main__":
    demo()
