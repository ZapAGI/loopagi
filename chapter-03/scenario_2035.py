"""
Chapter 3: A Morning in 2035

Interactive model of a day in 2035 where AGI systems are woven
into daily life. Extrapolation from current engineering, not science fiction.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Scenario:
    """A scene from the 2035 scenario."""

    time: str
    actor: str
    description: str
    agi_system: str
    technology: str


MORNING_2035: list[Scenario] = [
    Scenario(
        time="06:00",
        actor="Energy Grid",
        description="AGI optimizes regional power distribution based on weather forecasts, "
        "demand predictions, and renewable output. Solar farms in Arizona ramp up "
        "as wind farms in Texas scale down.",
        agi_system="Grid Orchestrator (multi-agent energy management)",
        technology="Real-time optimization, predictive modeling, sensor fusion",
    ),
    Scenario(
        time="06:30",
        actor="Maya (student, age 16)",
        description="Maya's personal AI tutor reviews her progress overnight and prepares "
        "a customized lesson plan. It noticed she struggled with quadratic equations "
        "yesterday and generated three new practice problems with visual explanations.",
        agi_system="Personal Tutor Agent (adaptive learning)",
        technology="Knowledge tracing, spaced repetition, personalized content generation",
    ),
    Scenario(
        time="07:00",
        actor="Dr. Chen (physician)",
        description="Dr. Chen's diagnostic assistant flagged three patients whose overnight "
        "vitals suggest early intervention. It prepared preliminary assessments and "
        "ordered non-invasive follow-up tests, pending Dr. Chen's approval.",
        agi_system="Medical Orchestrator (diagnostic + scheduling agents)",
        technology="Continuous monitoring, anomaly detection, careful mode approval",
    ),
    Scenario(
        time="07:30",
        actor="Jorge (farmer)",
        description="Jorge's agricultural AGI analyzed soil moisture, weather data, and crop "
        "growth patterns. It recommends delaying irrigation by 4 hours due to incoming "
        "rain, saving 12,000 gallons of water.",
        agi_system="Farm Optimization Agent (environmental + crop agents)",
        technology="Sensor fusion, weather API, optimization algorithms",
    ),
    Scenario(
        time="08:00",
        actor="Sofia (software engineer)",
        description="Sofia opens her terminal. Her coding assistant has already indexed the "
        "overnight PR reviews, summarized 3 failing CI tests, and proposed fixes for "
        "2 of them. She approves one fix and asks for a different approach on the other.",
        agi_system="LoopAGI (13-agent coding assistant)",
        technology="Multi-agent orchestration, git integration, quality pipeline",
    ),
    Scenario(
        time="08:30",
        actor="City Transit",
        description="The city transit AGI reroutes 40 buses based on real-time traffic, a "
        "construction closure on 5th Avenue, and surge demand from a concert venue. "
        "Average commute time decreased 11% compared to static schedules.",
        agi_system="Transit Orchestrator (routing + demand + vehicle agents)",
        technology="Real-time optimization, demand prediction, fleet management",
    ),
    Scenario(
        time="09:00",
        actor="Elderly Care",
        description="Mrs. Kowalski's home health agent detected she skipped her morning "
        "medication. It sent a gentle voice reminder. When she confirmed she took it, "
        "it logged the event and updated her care team.",
        agi_system="Home Health Agent (monitoring + voice + care coordination)",
        technology="Voice I/O, medication tracking, caregiver notification",
    ),
    Scenario(
        time="09:30",
        actor="Environmental Monitor",
        description="A network of environmental sensors detected elevated particulate matter "
        "in the industrial district. The air quality agent issued a localized advisory "
        "and recommended school recess be moved indoors for 3 schools.",
        agi_system="Environmental Mesh (distributed sensor agents)",
        technology="Sensor mesh, threshold alerting, public health integration",
    ),
]


def demo() -> None:
    """Walk through a morning in 2035."""
    print("Chapter 3: A Morning in 2035")
    print("=" * 60)
    print()
    print("Every scene below is extrapolated from technology that exists")
    print("today. The only difference is integration and orchestration.")
    print()

    for scenario in MORNING_2035:
        print(f"  [{scenario.time}] {scenario.actor}")
        print(f"  {scenario.description}")
        print(f"  System: {scenario.agi_system}")
        print(f"  Tech:   {scenario.technology}")
        print()

    # Summary statistics
    systems = set(s.agi_system.split("(")[0].strip() for s in MORNING_2035)
    actors = set(s.actor for s in MORNING_2035)

    print("-" * 60)
    print(f"Scenes: {len(MORNING_2035)}")
    print(f"Unique actors: {len(actors)}")
    print(f"AGI systems: {len(systems)}")
    print()
    print("Common thread: every system is local-first, human-approved,")
    print("and augments rather than replaces human judgment.")
    print("The human is always the god in the loop.")


if __name__ == "__main__":
    demo()
