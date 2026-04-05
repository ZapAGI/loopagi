"""
Chapter 19: Docker Agent Patterns

58 Docker containers on a single machine. Why dedicated tool agents
(Docker, Security, Database) elevate the whole system.

What does it mean for an agent to have a body? When it can start
containers, query databases, and scan networks, has it crossed
a threshold from digital to physical?

NOTE: This is a pattern demonstration. Docker is optional.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DockerService:
    """A Docker service managed by the agent."""

    name: str
    image: str
    port: int
    domain: str
    description: str


# The 58+ services that ZAP AGI manages
SERVICE_CATALOG: list[DockerService] = [
    # Databases
    DockerService("postgres", "postgres:17", 5432, "database", "Primary relational database"),
    DockerService("redis", "redis:8", 6379, "database", "Cache and session store"),
    DockerService("qdrant", "qdrant/qdrant:latest", 6333, "database", "Vector database for RAG"),

    # Monitoring
    DockerService("prometheus", "prom/prometheus:latest", 9090, "monitoring", "Metrics collection"),
    DockerService("grafana", "grafana/grafana:latest", 3000, "monitoring", "Metrics dashboards"),
    DockerService("loki", "grafana/loki:latest", 3100, "monitoring", "Log aggregation"),

    # Security
    DockerService("vault", "hashicorp/vault:latest", 8200, "security", "Secret management"),
    DockerService(
        "trivy", "aquasec/trivy:latest", 0, "security",
        "Container vulnerability scanner",
    ),

    # Development
    DockerService("gitea", "gitea/gitea:latest", 3001, "development", "Self-hosted git"),
    DockerService("registry", "registry:2", 5000, "development", "Container registry"),

    # AI/ML
    DockerService("ollama", "ollama/ollama:latest", 11434, "ai", "Local LLM inference"),
    DockerService("jupyter", "jupyter/scipy-notebook:latest", 8888, "ai", "Notebook server"),

    # Infrastructure
    DockerService("traefik", "traefik:latest", 80, "infrastructure", "Reverse proxy"),
    DockerService("minio", "minio/minio:latest", 9000, "infrastructure", "Object storage"),
    DockerService("rabbitmq", "rabbitmq:management", 5672, "infrastructure", "Message queue"),
]


def demo() -> None:
    """Demonstrate Docker agent service management patterns."""
    print("Chapter 19: Docker Agent - Service Orchestration")
    print("=" * 60)

    # Organize by domain
    domains: dict[str, list[DockerService]] = {}
    for svc in SERVICE_CATALOG:
        domains.setdefault(svc.domain, []).append(svc)

    print(f"\nService Catalog ({len(SERVICE_CATALOG)} services across {len(domains)} domains):")
    print("-" * 60)

    for domain, services in sorted(domains.items()):
        print(f"\n  {domain.upper()} ({len(services)} services):")
        for svc in services:
            port = f":{svc.port}" if svc.port else ""
            print(f"    - {svc.name:<15} {svc.image:<35} {port}")
            print(f"      {svc.description}")

    # Agent capabilities
    print("\n\nDocker Agent Capabilities:")
    print("-" * 50)
    capabilities = [
        "Start/stop/restart containers",
        "Build images from Dockerfile",
        "Read container logs",
        "Monitor resource usage (CPU, memory, network)",
        "Execute commands inside containers",
        "Manage volumes and networks",
        "Health checks and auto-restart",
        "Scale services up/down",
        "Pull updated images",
        "Security scan with Trivy",
    ]
    for cap in capabilities:
        print(f"  - {cap}")

    # The embodiment thesis
    print("\n\nThe Embodiment Thesis:")
    print("-" * 50)
    print("  When an agent can:")
    print("    - Start a PostgreSQL container")
    print("    - Create tables and run migrations")
    print("    - Deploy application containers")
    print("    - Monitor health and auto-heal")
    print("    - Scan for vulnerabilities")
    print()
    print("  ...it has crossed the threshold from digital to physical.")
    print("  Embodiment is not about having a body.")
    print("  It is about having consequences in the physical world.")


if __name__ == "__main__":
    demo()
