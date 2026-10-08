from __future__ import annotations

import sys
from pathlib import Path

Grid = list[list[bool]]


def parse_input(content: str) -> tuple[int, int, int, Grid]:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("Очікуються кількість поколінь і розміри поля.")
    try:
        generations = int(lines[0])
    except ValueError as exc:
        raise ValueError("Кількість поколінь має бути цілим невід’ємним числом.") from exc
    if generations < 0:
        raise ValueError("Кількість поколінь має бути невід’ємною.")
    dimensions = lines[1].split()
    if len(dimensions) != 2:
        raise ValueError("Розміри мають містити ширину та висоту.")
    try:
        width, height = map(int, dimensions)
    except ValueError as exc:
        raise ValueError("Ширина та висота мають бути цілими числами.") from exc
    if width <= 0 or height <= 0:
        raise ValueError("Ширина та висота мають бути додатними.")
    rows = lines[2:]
    if len(rows) != height:
        raise ValueError(f"Очікувалася кількість рядків поля: {height}, отримано: {len(rows)}.")
    grid: Grid = []
    for index, row in enumerate(rows, start=1):
        if len(row) != width:
            raise ValueError(f"Рядок {index}: очікувана ширина {width}, отримано {len(row)}.")
        if any(cell not in ".x" for cell in row):
            raise ValueError(f"Рядок {index}: дозволені лише символи '.' та 'x'.")
        grid.append([cell == "x" for cell in row])
    return generations, width, height, grid


def next_cell_state(grid: Grid, x: int, y: int) -> bool:
    """Return one cell's next state, counting the eight wrapped offsets."""
    height, width = len(grid), len(grid[0])
    neighbors = sum(
        grid[(y + dy) % height][(x + dx) % width]
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if dx != 0 or dy != 0
    )
    return neighbors == 3 or (grid[y][x] and neighbors == 2)


def next_generation(grid: Grid) -> Grid:
    """Create a new generation without modifying the input grid."""
    return [[next_cell_state(grid, x, y) for x in range(len(grid[0]))]
            for y in range(len(grid))]


def simulate(grid: Grid, generations: int) -> Grid:
    """Return the grid after ``generations`` transitions."""
    current = [row[:] for row in grid]
    for _ in range(generations):
        current = next_generation(current)
    return current


def format_grid(grid: Grid) -> str:
    """Serialize a grid without adding a trailing newline."""
    return "\n".join("".join("x" if cell else "." for cell in row) for row in grid)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("Використання: python main.py <input> <output>", file=sys.stderr)
        return 2
    try:
        generations, _width, _height, grid = parse_input(Path(args[0]).read_text(encoding="utf-8"))
        Path(args[1]).write_text(format_grid(simulate(grid, generations)) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"Помилка: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
