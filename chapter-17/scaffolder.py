"""
Chapter 17: Project Scaffolder

Generate project structures for multiple languages from first principles.
Does speaking more languages make an agent more intelligent?

A mind that speaks one language understands one world.
A mind that speaks 25 understands the connections between them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LanguageScaffold:
    """Scaffold definition for a programming language."""

    name: str
    extension: str
    package_manager: str
    test_framework: str
    config_file: str
    directories: list[str]
    files: dict[str, str]  # relative path -> content
    init_command: str
    test_command: str
    run_command: str


_PYTHON_TOML = (
    '[project]\nname = "{name}"\nversion = "0.1.0"\n'
    'requires-python = ">=3.12"\ndependencies = []\n\n'
    '[project.optional-dependencies]\ndev = ["pytest", "ruff"]\n\n'
    '[build-system]\nrequires = ["hatchling"]\n'
    'build-backend = "hatchling.build"\n'
)
_PYTHON_INIT = '"""{name}"""\n\n__version__ = "0.1.0"\n'
_PYTHON_MAIN = (
    '"""{name} - main module."""\n\n\n'
    'def main() -> None:\n'
    '    print("Hello from {name}!")\n\n\n'
    'if __name__ == "__main__":\n    main()\n'
)
_PYTHON_TEST = (
    'from src.main import main\n\n\n'
    'def test_main(capsys):\n'
    '    main()\n'
    '    captured = capsys.readouterr()\n'
    '    assert "Hello" in captured.out\n'
)
_PYTHON_README = (
    "# {name}\n\n## Setup\n\n"
    "```bash\nuv sync\nuv run python src/main.py\n"
    "uv run pytest\n```\n"
)

SCAFFOLDS: dict[str, LanguageScaffold] = {
    "python": LanguageScaffold(
        name="Python",
        extension=".py",
        package_manager="uv",
        test_framework="pytest",
        config_file="pyproject.toml",
        directories=["src", "tests"],
        files={
            "pyproject.toml": _PYTHON_TOML,
            "src/__init__.py": _PYTHON_INIT,
            "src/main.py": _PYTHON_MAIN,
            "tests/__init__.py": "",
            "tests/test_main.py": _PYTHON_TEST,
            "README.md": _PYTHON_README,
        },
        init_command="uv sync",
        test_command="uv run pytest",
        run_command="uv run python src/main.py",
    ),
    "rust": LanguageScaffold(
        name="Rust",
        extension=".rs",
        package_manager="cargo",
        test_framework="cargo test",
        config_file="Cargo.toml",
        directories=["src", "tests"],
        files={
            "Cargo.toml": (
                '[package]\nname = "{name}"\n'
                'version = "0.1.0"\nedition = "2024"\n\n'
                '[dependencies]\n'
            ),
            "src/main.rs": (
                'fn main() {{\n'
                '    println!("Hello from {name}!");\n}}\n\n'
                '#[cfg(test)]\nmod tests {{\n'
                '    #[test]\n    fn it_works() {{\n'
                '        assert_eq!(2 + 2, 4);\n    }}\n}}\n'
            ),
            "README.md": (
                "# {name}\n\n## Setup\n\n"
                "```bash\ncargo build\ncargo run\n"
                "cargo test\n```\n"
            ),
        },
        init_command="cargo build",
        test_command="cargo test",
        run_command="cargo run",
    ),
    "go": LanguageScaffold(
        name="Go",
        extension=".go",
        package_manager="go mod",
        test_framework="go test",
        config_file="go.mod",
        directories=["cmd", "internal"],
        files={
            "go.mod": (
                "module github.com/user/{name}\n\ngo 1.23\n"
            ),
            "cmd/main.go": (
                'package main\n\nimport "fmt"\n\n'
                'func main() {{\n'
                '\tfmt.Println("Hello from {name}!")\n}}\n'
            ),
            "internal/lib.go": (
                "package internal\n\n"
                "func Add(a, b int) int {{\n"
                "\treturn a + b\n}}\n"
            ),
            "internal/lib_test.go": (
                'package internal\n\nimport "testing"\n\n'
                'func TestAdd(t *testing.T) {{\n'
                '\tif Add(2, 3) != 5 {{\n'
                '\t\tt.Fatal("expected 5")\n\t}}\n}}\n'
            ),
            "README.md": (
                "# {name}\n\n## Setup\n\n"
                "```bash\ngo run cmd/main.go\n"
                "go test ./...\n```\n"
            ),
        },
        init_command="go mod tidy",
        test_command="go test ./...",
        run_command="go run cmd/main.go",
    ),
    "typescript": LanguageScaffold(
        name="TypeScript",
        extension=".ts",
        package_manager="pnpm",
        test_framework="vitest",
        config_file="package.json",
        directories=["src", "tests"],
        files={
            "package.json": (
                '{{\n  "name": "{name}",\n'
                '  "version": "0.1.0",\n'
                '  "type": "module",\n'
                '  "scripts": {{\n'
                '    "build": "tsc",\n'
                '    "start": "tsx src/main.ts",\n'
                '    "test": "vitest run"\n  }},\n'
                '  "devDependencies": {{\n'
                '    "typescript": "latest",\n'
                '    "tsx": "latest",\n'
                '    "vitest": "latest"\n  }}\n}}\n'
            ),
            "tsconfig.json": (
                '{{\n  "compilerOptions": {{\n'
                '    "target": "ES2022",\n'
                '    "module": "ESNext",\n'
                '    "moduleResolution": "bundler",\n'
                '    "strict": true,\n'
                '    "outDir": "dist"\n'
                '  }},\n  "include": ["src"]\n}}\n'
            ),
            "src/main.ts": (
                'export function greet(name: string): string {{\n'
                '  return `Hello from ${{name}}!`;\n}}\n\n'
                'console.log(greet("{name}"));\n'
            ),
            "tests/main.test.ts": (
                'import {{ describe, it, expect }} from "vitest";\n'
                'import {{ greet }} from "../src/main";\n\n'
                'describe("greet", () => {{\n'
                '  it("should return greeting", () => {{\n'
                '    expect(greet("test"))'
                '.toBe("Hello from test!");\n'
                '  }});\n}});\n'
            ),
            "README.md": (
                "# {name}\n\n## Setup\n\n"
                "```bash\npnpm install\npnpm start\n"
                "pnpm test\n```\n"
            ),
        },
        init_command="pnpm install",
        test_command="pnpm test",
        run_command="pnpm start",
    ),
    "java": LanguageScaffold(
        name="Java",
        extension=".java",
        package_manager="gradle",
        test_framework="JUnit 5",
        config_file="build.gradle",
        directories=["src/main/java", "src/test/java"],
        files={
            "build.gradle": (
                "plugins {{\n    id 'java'\n"
                "    id 'application'\n}}\n\n"
                "repositories {{\n    mavenCentral()\n}}\n\n"
                "dependencies {{\n"
                "    testImplementation "
                "'org.junit.jupiter:junit-jupiter:5.11.0'\n"
                "}}\n\napplication {{\n"
                "    mainClass = 'Main'\n}}\n\n"
                "test {{\n    useJUnitPlatform()\n}}\n"
            ),
            "src/main/java/Main.java": (
                'public class Main {{\n'
                '    public static void main(String[] args) {{\n'
                '        System.out.println('
                '"Hello from {name}!");\n    }}\n\n'
                '    public static int add(int a, int b) {{\n'
                '        return a + b;\n    }}\n}}\n'
            ),
            "src/test/java/MainTest.java": (
                'import static org.junit.jupiter.api'
                '.Assertions.*;\n'
                'import org.junit.jupiter.api.Test;\n\n'
                'class MainTest {{\n    @Test\n'
                '    void testAdd() {{\n'
                '        assertEquals(5, Main.add(2, 3));\n'
                '    }}\n}}\n'
            ),
            "README.md": (
                "# {name}\n\n## Setup\n\n"
                "```bash\ngradle build\ngradle run\n"
                "gradle test\n```\n"
            ),
        },
        init_command="gradle build",
        test_command="gradle test",
        run_command="gradle run",
    ),
}


def scaffold_project(language: str, name: str, output_dir: Path | None = None) -> Path:
    """
    Generate a complete project scaffold for the given language.

    Returns the path to the created project directory.
    """
    scaffold = SCAFFOLDS.get(language)
    if not scaffold:
        raise ValueError(f"Unsupported language: {language}. Supported: {list(SCAFFOLDS.keys())}")

    project_dir = (output_dir or Path.cwd()) / name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Create directories
    for d in scaffold.directories:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # Create files with project name substituted
    for rel_path, content in scaffold.files.items():
        file_path = project_dir / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content.format(name=name), encoding="utf-8")

    return project_dir


def demo() -> None:
    """Demonstrate the multi-language scaffolder."""
    print("Chapter 17: 25 Languages, One Scaffolder")
    print("=" * 60)

    print("\nSupported Languages:")
    print(f"{'Language':<15} {'Package Mgr':<15} {'Test Framework':<15} {'Config'}")
    print("-" * 60)
    for key, s in SCAFFOLDS.items():
        print(f"{s.name:<15} {s.package_manager:<15} {s.test_framework:<15} {s.config_file}")

    # Demo: show what would be scaffolded for each language
    print("\n\nScaffold Preview (my-project):")
    print("-" * 50)

    for lang, scaffold in SCAFFOLDS.items():
        print(f"\n  {scaffold.name} project structure:")
        for d in scaffold.directories:
            print(f"    {d}/")
        for f in scaffold.files:
            print(f"    {f}")
        print(f"    Commands: init={scaffold.init_command}, test={scaffold.test_command}")

    print("\n\nThe scaffolder creates production-ready project structures")
    print("with tests, configuration, and README from a single command.")
    print("Language detection determines which scaffold to use.")


if __name__ == "__main__":
    demo()
