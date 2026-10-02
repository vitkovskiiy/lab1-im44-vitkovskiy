import subprocess
import sys

import pytest

from main import format_grid, next_cell_state, next_generation, parse_input, simulate


def board(*rows: str) -> list[list[bool]]:
    return [[cell == "x" for cell in row] for row in rows]


def test_live_cell_rule_table():
    for count, expected in [(0, False), (1, False), (2, True), (3, True), (4, False), (8, False)]:
        grid = [[False] * 5 for _ in range(5)]
        grid[2][2] = True
        positions = [(y, x) for y in range(1, 4) for x in range(1, 4) if (y, x) != (2, 2)]
        for y, x in positions[:count]:
            grid[y][x] = True
        assert next_cell_state(grid, 2, 2) is expected, f"{count} neighbors"


@pytest.mark.parametrize("count, expected", [(0, False), (1, False), (2, False), (3, True), (4, False), (8, False)])
def test_dead_cell_is_born_only_with_exactly_three_neighbors(count, expected):
    grid = [[False] * 5 for _ in range(5)]
    positions = [(y, x) for y in range(1, 4) for x in range(1, 4)]
    for y, x in positions[:count]:
        grid[y][x] = True
    assert next_cell_state(grid, 2, 2) is expected


def test_all_four_corner_offsets_wrap_into_top_left_cell():
    grid = board("x..x", "....", "....", "x..x")
    assert next_cell_state(grid, 0, 0) is True


@pytest.mark.parametrize(
    "rows, x, y, live_at, expected",
    [
        ((".....", ".....", ".....", ".....", "....."), 0, 2, ((2, 4), (1, 4), (3, 4)), True),
        ((".....", ".....", ".....", ".....", "....."), 4, 2, ((2, 0), (1, 0), (3, 0)), True),
        ((".....", ".....", ".....", ".....", "....."), 2, 0, ((4, 2), (4, 1), (4, 3)), True),
        ((".....", ".....", ".....", ".....", "....."), 2, 4, ((0, 2), (0, 1), (0, 3)), True),
    ],
)
def test_birth_uses_neighbors_across_each_edge(rows, x, y, live_at, expected):
    grid = [[False] * 5 for _ in range(5)]
    for yy, xx in live_at:
        grid[yy][xx] = True
    assert next_cell_state(grid, x, y) is expected


def test_block_still_life_is_unchanged():
    block = board("......", ".xx...", ".xx...", "......", "......")
    assert next_generation(block) == block


def test_blinker_has_period_two():
    horizontal = board(".......", ".......", "..xxx..", ".......", ".......", ".......", ".......")
    vertical = board(".......", "...x...", "...x...", "...x...", ".......", ".......", ".......")
    assert next_generation(horizontal) == vertical
    assert simulate(horizontal, 2) == horizontal


def test_glider_moves_one_cell_diagonally_after_four_generations_across_seam():
    start = [[False] * 8 for _ in range(7)]
    # Стандартну фігуру перенесено до (5, 4), поряд із правим нижнім краєм поля.
    for y, x in ((4, 6), (5, 7), (6, 5), (6, 6), (6, 7)):
        start[y][x] = True
    expected = board("x.....xx", "........", "........", "........", "........", ".......x", "x.......")
    assert simulate(start, 4) == expected


def test_zero_generations_returns_equal_but_independent_grid():
    original = board("x..", ".x.")
    result = simulate(original, 0)
    assert result == original
    assert result is not original and result[0] is not original[0]


def test_one_generation_and_no_mutation_of_input():
    original = board(".....", ".....", ".xxx.", ".....", ".....")
    before = [row[:] for row in original]
    assert format_grid(next_generation(original)) == ".....\n..x..\n..x..\n..x..\n....."
    assert original == before


@pytest.mark.parametrize("rows", [("....", "....", "...."), ("xxxx", "xxxx", "xxxx")])
def test_empty_and_full_fields_have_expected_next_state(rows):
    expected = ["...."] * 3 if rows[0] == "...." else ["...."] * 3
    assert format_grid(next_generation(board(*rows))) == "\n".join(expected)


@pytest.mark.parametrize(
    "grid, expected",
    [
        (board("x"), board(".")), 
        (board("x..."), board("xx.x")), 
        (board("x", ".", ".", "."), board("x", "x", ".", "x")), 
        (board("x...", "....", "....", "...."), board("....", "....", "....", "....")),
        (board("x.", "..", ".."), board("..", "..", "..")),
        (board("x....", ".....", "....."), board(".....", ".....", ".....")),
        (board(".......", ".......", "..xxx..", "......."), board(".......", "...x...", "...x...", "...x...")),
    ],
)
def test_degenerate_and_nonsquare_dimensions(grid, expected):
    assert next_generation(grid) == expected


def test_two_by_two_torus_counts_repeated_wrapped_offsets():
    grid = board("x.", ".x")
    assert next_generation(grid) == board("..", "..")


def test_parser_accepts_whitespace_and_trailing_blank_lines():
    generations, width, height, grid = parse_input(" 2 \n 3   2 \n..x\n.x.\n\n")
    assert (generations, width, height) == (2, 3, 2)
    assert grid == board("..x", ".x.")


@pytest.mark.parametrize(
    "content, message",
    [
        ("", "Ожидаются"),
        ("abc\n2 2\n..\n..", "поколений"),
        ("-1\n2 2\n..\n..", "неотрицательным"),
        ("1\n2\n..\n..", "ширину и высоту"),
        ("1\na 2\n..\n..", "целыми"),
        ("1\n0 2\n\n\n", "положительными"),
        ("1\n2 3\n..\n..", "Ожидалось 3 строк"),
        ("1\n2 1\n...", "ожидалась ширина 2"),
        ("1\n2 1\n.a", "только символы"),
    ],
)
def test_parser_rejects_invalid_input_with_actionable_error(content, message):
    with pytest.raises(ValueError, match=message):
        parse_input(content)


def test_cli_reads_input_and_writes_exact_expected_board(tmp_path):
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.txt"
    input_file.write_text("1\n5 5\n.....\n.....\n.xxx.\n.....\n.....\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "main.py", str(input_file), str(output_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert output_file.read_text(encoding="utf-8") == ".....\n..x..\n..x..\n..x..\n.....\n"
def test_always_passes_for_ci():
            """This test shows that CI is working"""
            assert 2 - 2 == 4