"""ARC-AGI grid visualizer.

Renders ARC grids as colored ASCII art in the terminal using Rich,
and optionally as matplotlib plots for notebooks and file export.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    Console = Panel = Table = Text = None  # type: ignore[assignment,misc]

if TYPE_CHECKING:
    from loopagi.arc.arc_loader import ArcTask, Grid

logger = logging.getLogger(__name__)

# ARC color palette: maps cell values 0-9 to (display_char, rich_color)
ARC_COLORS: dict[int, tuple[str, str]] = {
    0: (".", "bright_black"),      # Black (background)
    1: ("#", "blue"),              # Blue
    2: ("#", "red"),               # Red
    3: ("#", "green"),             # Green
    4: ("#", "yellow"),            # Yellow
    5: ("#", "bright_white"),      # Gray/White
    6: ("#", "magenta"),           # Magenta
    7: ("#", "rgb(255,165,0)"),    # Orange
    8: ("#", "cyan"),              # Cyan/Light Blue
    9: ("#", "dark_red"),          # Maroon/Brown
}

# Matplotlib color map for ARC values 0-9
ARC_MATPLOTLIB_COLORS: list[str] = [
    "#000000",  # 0: Black
    "#0074D9",  # 1: Blue
    "#FF4136",  # 2: Red
    "#2ECC40",  # 3: Green
    "#FFDC00",  # 4: Yellow
    "#AAAAAA",  # 5: Gray
    "#F012BE",  # 6: Magenta
    "#FF851B",  # 7: Orange
    "#7FDBFF",  # 8: Light Blue
    "#870C25",  # 9: Maroon
]


def grid_to_rich_text(grid: Grid, cell_width: int = 2) -> Text:
    """Convert a grid to a Rich Text object with colored cells.

    Args:
        grid: 2D list of ints 0-9.
        cell_width: Character width per cell.

    Returns:
        Rich Text object with colored grid representation.
    """
    text = Text()
    for row in grid:
        for j, val in enumerate(row):
            char, color = ARC_COLORS.get(val, ("?", "white"))
            display = (char * cell_width) if cell_width > 1 else char
            text.append(display, style=f"bold {color} on {color}")
            if j < len(row) - 1:
                text.append(" ")
        text.append("\n")
    return text


def grid_to_ascii(grid: Grid) -> str:
    """Convert a grid to a plain ASCII string (no color).

    Each cell is represented by its integer value.

    Args:
        grid: 2D list of ints 0-9.

    Returns:
        Multi-line string representation.
    """
    lines: list[str] = []
    for row in grid:
        lines.append(" ".join(str(v) for v in row))
    return "\n".join(lines)


def print_grid(
    grid: Grid,
    title: str = "",
    console: Console | None = None,
    cell_width: int = 2,
) -> None:
    """Print a single grid to the terminal with colors.

    Args:
        grid: 2D list of ints 0-9.
        title: Optional title for the panel.
        console: Rich Console instance (creates one if not provided).
        cell_width: Character width per cell.
    """
    if console is None:
        console = Console()

    text = grid_to_rich_text(grid, cell_width=cell_width)
    rows, cols = len(grid), len(grid[0]) if grid else 0
    subtitle = f"{rows}x{cols}"

    panel = Panel(text, title=title, subtitle=subtitle, expand=False)
    console.print(panel)


def print_grid_pair(
    input_grid: Grid,
    output_grid: Grid,
    pair_label: str = "",
    console: Console | None = None,
    cell_width: int = 2,
) -> None:
    """Print an input/output grid pair side by side.

    Args:
        input_grid: Input grid.
        output_grid: Output grid.
        pair_label: Label for the pair (e.g., "Train 1").
        console: Rich Console instance.
        cell_width: Character width per cell.
    """
    if console is None:
        console = Console()

    table = Table(title=pair_label, show_header=True, expand=False)
    table.add_column("Input", justify="center")
    table.add_column("Output", justify="center")

    input_text = grid_to_rich_text(input_grid, cell_width=cell_width)
    output_text = grid_to_rich_text(output_grid, cell_width=cell_width)

    table.add_row(input_text, output_text)
    console.print(table)


def print_task(
    task: ArcTask,
    console: Console | None = None,
    cell_width: int = 2,
    show_test_output: bool = False,
) -> None:
    """Print a complete ARC task: all training pairs and test inputs.

    Args:
        task: The ARC task to display.
        console: Rich Console instance.
        cell_width: Character width per cell.
        show_test_output: Whether to show test outputs (if available).
    """
    if console is None:
        console = Console()

    console.print(f"\n[bold cyan]Task: {task.task_id}[/bold cyan]")
    console.print(f"Training pairs: {task.num_train}, Test inputs: {task.num_test}\n")

    # Print training pairs
    for i, pair in enumerate(task.train):
        print_grid_pair(
            pair.input,
            pair.output,
            pair_label=f"Train {i + 1}",
            console=console,
            cell_width=cell_width,
        )

    # Print test inputs
    for i, test in enumerate(task.test):
        if show_test_output and test.output is not None:
            print_grid_pair(
                test.input,
                test.output,
                pair_label=f"Test {i + 1}",
                console=console,
                cell_width=cell_width,
            )
        else:
            print_grid(
                test.input,
                title=f"Test {i + 1} Input",
                console=console,
                cell_width=cell_width,
            )


def plot_grid(grid: Grid, ax: object | None = None, title: str = "") -> object:
    """Plot a grid using matplotlib.

    Args:
        grid: 2D list of ints 0-9.
        ax: Matplotlib axes object (creates new figure if None).
        title: Plot title.

    Returns:
        The matplotlib axes object.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import ListedColormap

    arr = np.array(grid)
    cmap = ListedColormap(ARC_MATPLOTLIB_COLORS)

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(max(3, arr.shape[1] * 0.5), max(3, arr.shape[0] * 0.5)))

    ax.imshow(arr, cmap=cmap, vmin=0, vmax=9, interpolation="nearest")
    ax.set_title(title)
    ax.set_xticks(range(arr.shape[1]))
    ax.set_yticks(range(arr.shape[0]))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.grid(True, linewidth=0.5, color="gray", alpha=0.5)

    return ax


def plot_task(
    task: ArcTask,
    show_test_output: bool = False,
    save_path: str | None = None,
) -> None:
    """Plot a complete ARC task using matplotlib.

    Args:
        task: The ARC task to plot.
        show_test_output: Whether to show test outputs (if available).
        save_path: If provided, save the figure to this path instead of showing.
    """
    import matplotlib.pyplot as plt

    num_pairs = task.num_train + task.num_test
    fig, axes = plt.subplots(num_pairs, 2, figsize=(8, 3 * num_pairs))

    if num_pairs == 1:
        axes = [axes]

    # Training pairs
    for i, pair in enumerate(task.train):
        plot_grid(pair.input, ax=axes[i][0], title=f"Train {i + 1} Input")
        plot_grid(pair.output, ax=axes[i][1], title=f"Train {i + 1} Output")

    # Test inputs
    for i, test in enumerate(task.test):
        row_idx = task.num_train + i
        plot_grid(test.input, ax=axes[row_idx][0], title=f"Test {i + 1} Input")
        if show_test_output and test.output is not None:
            plot_grid(test.output, ax=axes[row_idx][1], title=f"Test {i + 1} Output")
        else:
            axes[row_idx][1].set_visible(False)

    fig.suptitle(f"Task: {task.task_id}", fontsize=14, fontweight="bold")
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        logger.info(f"Saved task plot to {save_path}")
        plt.close(fig)
    else:
        plt.show()
