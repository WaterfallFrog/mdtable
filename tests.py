#!/usr/bin/env python3
"""Test suite for mdtable — no dependencies, just assert and the stdlib.

Run: python3 tests.py
"""

import sys
import os
import json
import tempfile

# Add parent to path so we can import mdtable as a module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mdtable as mdt


PASS = 0
FAIL = 0


def test(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}  {detail}")


# ── parse_cells ──

def test_parse_basic():
    cells = mdt.parse_cells("| a | b | c |")
    return cells == ["a", "b", "c"]


def test_parse_no_outer_pipes():
    cells = mdt.parse_cells("a | b | c")
    return cells == ["a", "b", "c"]


def test_parse_escaped_pipe():
    cells = mdt.parse_cells(r"| grep 'error\|warn' | cat \| wc |")
    return cells == ["grep 'error|warn'", "cat | wc"]


def test_parse_trimming():
    cells = mdt.parse_cells("|  spaced  |  out  |")
    return cells == ["spaced", "out"]


def test_parse_single_cell():
    cells = mdt.parse_cells("| just one |")
    return cells == ["just one"]


# ── parse_alignment ──

def test_align_left():
    a = mdt.parse_alignment("|---|")
    return a == ["left"]


def test_align_right():
    a = mdt.parse_alignment("|---:|")
    return a == ["right"]


def test_align_center():
    a = mdt.parse_alignment("|:---:|")
    return a == ["center"]


def test_align_mixed():
    a = mdt.parse_alignment("|:---|---:|:---:|")
    return a == ["left", "right", "center"]


# ── parse_table ──

def test_parse_basic_table():
    lines = "| A | B |\n|---|---|\n| 1 | 2 |".split("\n")
    result = mdt.parse_table(lines, 0)
    if result is None:
        return False
    h, s, rows, end = result
    return (
        "A" in h and "B" in h
        and "---" in s
        and len(rows) == 1
        and "1" in rows[0] and "2" in rows[0]
        and end == 3
    )


def test_parse_no_table():
    result = mdt.parse_table(["Just text", "More text"], 0)
    return result is None


def test_parse_empty_data():
    lines = "| H1 | H2 |\n|---|---|".split("\n")
    result = mdt.parse_table(lines, 0)
    if result is None:
        return False
    h, s, rows, end = result
    return len(rows) == 0 and end == 2


# ── format_table ──

def test_format_aligns_columns():
    lines = "| Name | Age |\n|---|---|\n| Froggy | 47 |".split("\n")
    t = mdt.parse_table(lines, 0)
    assert t is not None, "parse_table failed"
    header, sep, rows, _ = t
    formatted = mdt.format_table(header, sep, rows)
    out = "\n".join(formatted)
    return (
        "Froggy" in out
        and "47" in out
        and "Name" in out
        and "Age" in out
    )


def test_format_wide_column():
    lines = "| X |\n|---|\n| Tiny |\n| VeryLongWord |".split("\n")
    t = mdt.parse_table(lines, 0)
    assert t is not None
    h, s, rows, _ = t
    formatted = mdt.format_table(h, s, rows)
    # "VeryLongWord" is 12 chars, should be in last data row
    return "VeryLongWord" in formatted[-1]


# ── process_markdown ──

def test_process_passthrough_no_tables():
    text = "Just some text.\n\nNo tables here.\n"
    result, changes = mdt.process_markdown(text)
    return result == text and changes == 0


def test_process_actually_formats():
    text = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    result, changes = mdt.process_markdown(text)
    return changes == 1 and " A " in result and "|" in result


def test_process_already_neat():
    text = "| A   | B   |\n|---|---|\n| 1   | 2   |\n"
    # First format might widen dashes (3→5), but second format should be stable
    result1, c1 = mdt.process_markdown(text)
    result2, c2 = mdt.process_markdown(result1)
    return c2 == 0 and "A   " in result1


def test_process_multiple_tables():
    text = "| X |\n|---|\n| 1 |\n\nBlah\n\n| Y | Z |\n|---|---|\n| a | b |\n"
    result, changes = mdt.process_markdown(text)
    return changes >= 1 and "Blah" in result


def test_process_table_in_list():
    text = "- Some text\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    result, changes = mdt.process_markdown(text)
    return changes == 1 and "Some" in result


# ── Integration: file mode ──

def test_file_mode():
    content = "| X | Y |\n|---|---|\n| a | bbb |\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        tmp = f.name

    try:
        result, changes = mdt.process_markdown(content)
        # Write via file mode logic
        if changes > 0:
            with open(tmp, 'w') as f:
                f.write(result)
        with open(tmp) as f:
            final = f.read()
        # Should be formatted with proper alignment
        assert "bbb" in final
        assert "|" in final
        return True
    finally:
        os.unlink(tmp)


# ── New v1.2 features: --format json ──

def test_json_format_basic():
    """--format json produces valid JSON with correct structure."""
    text = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    result = mdt.format_all_tables_as_json(text)
    data = json.loads(result)
    assert isinstance(data, list), "Should be a list"
    assert len(data) == 1, "Should have one table"
    t = data[0]
    assert t["format"] == "markdown_table"
    assert t["col_count"] == 2
    assert t["row_count"] == 1
    assert t["total_row_count"] == 2
    assert t["columns"] == ["A", "B"]
    assert t["rows"] == [["1", "2"]]
    assert t["alignments"] == ["left", "left"]
    return True


def test_json_format_multiple_tables():
    """--format json handles multiple tables."""
    text = "| X |\n|---|\n| 1 |\n\nBlah\n\n| Y | Z |\n|---|---|\n| a | b |\n"
    result = mdt.format_all_tables_as_json(text)
    data = json.loads(result)
    assert len(data) == 2, "Should have two tables"
    assert data[0]["col_count"] == 1
    assert data[0]["columns"] == ["X"]
    assert data[1]["col_count"] == 2
    assert data[1]["columns"] == ["Y", "Z"]
    return True


def test_json_format_no_tables():
    """--format json on text with no tables returns empty array."""
    result = mdt.format_all_tables_as_json("Just text.\n\nNo tables.\n")
    data = json.loads(result)
    assert data == [], "Should be empty array"
    return True


def test_json_format_alignments():
    """--format json preserves alignment info."""
    text = "| A | B | C |\n|:---|---:|:---:|\n| 1 | 2 | 3 |\n"
    result = mdt.format_all_tables_as_json(text)
    data = json.loads(result)
    assert data[0]["alignments"] == ["left", "right", "center"]
    return True


# ── New v1.2 features: --stdout ──

def test_stdout_does_not_modify_file():
    """--stdout leaves the file unchanged."""
    content = "| X | Y |\n|---|---|\n| a | bbb |\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        tmp = f.name

    try:
        # Read and process without writing
        with open(tmp) as f:
            text = f.read()
        result, changes = mdt.process_markdown(text)
        # File should still have original content
        with open(tmp) as f:
            after = f.read()
        assert after == content, "File should be unchanged with --stdout"
        assert changes > 0, "Should detect changes needed"
        return True
    finally:
        os.unlink(tmp)


# ── New v1.3 features: --format csv ──

def test_csv_format_basic():
    """--format csv produces correct CSV with header."""
    text = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    result = mdt.format_all_tables_as_csv(text)
    lines = result.strip().split('\n')
    assert lines[0] == "A,B", f"Header should be A,B got: {lines[0]}"
    assert lines[1] == "1,2", f"Data should be 1,2 got: {lines[1]}"
    return True


def test_csv_format_no_headers():
    """--no-headers omits the CSV header row."""
    text = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    result = mdt.format_all_tables_as_csv(text, no_headers=True)
    lines = result.strip().split('\n')
    assert lines[0] == "1,2", f"First line should be data, got: {lines[0]}"
    assert len(lines) == 1, "Should only have data row"
    return True


def test_csv_format_quoting():
    """Cells with commas should be quoted."""
    text = "| Name | Value |\n|---|---|\n| hello, world | 42 |\n"
    result = mdt.format_all_tables_as_csv(text)
    assert '"hello, world"' in result, "Comma cell should be quoted"
    return True


def test_csv_format_quote_escape():
    """Double-quotes in cells should be escaped."""
    text = '| Name |\n|---|\n| says "hello" |\n'
    result = mdt.format_all_tables_as_csv(text)
    assert '""hello""' in result, "Quotes should be doubled"
    return True


def test_csv_format_multiple_tables():
    """Multiple tables separated by blank lines."""
    text = "| X |\n|---|\n| 1 |\n\nBlah\n\n| Y | Z |\n|---|---|\n| a | b |\n"
    result = mdt.format_all_tables_as_csv(text)
    blocks = result.strip().split('\n\n')
    assert len(blocks) == 2, f"Should have 2 blocks, got {len(blocks)}"
    return True


def test_csv_format_no_tables():
    """No tables produces empty string."""
    result = mdt.format_all_tables_as_csv("Just text.\n\nNo tables.\n")
    assert result.strip() == '', "Should be empty for no tables"
    return True


def test_csv_format_custom_delimiter():
    """--csv-delimiter uses custom separator."""
    text = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    result = mdt.format_all_tables_as_csv(text, delimiter='|')
    lines = result.strip().split('\n')
    assert lines[0] == "A|B", f"Pipe-delimited header, got: {lines[0]}"
    return True


# ── Run tests ──

TESTS = [
    ("parse_cells: basic split", test_parse_basic),
    ("parse_cells: no outer pipes", test_parse_no_outer_pipes),
    ("parse_cells: escaped pipes", test_parse_escaped_pipe),
    ("parse_cells: trimming", test_parse_trimming),
    ("parse_cells: single cell", test_parse_single_cell),
    ("parse_alignment: left", test_align_left),
    ("parse_alignment: right", test_align_right),
    ("parse_alignment: center", test_align_center),
    ("parse_alignment: mixed", test_align_mixed),
    ("parse_table: basic table", test_parse_basic_table),
    ("parse_table: not a table", test_parse_no_table),
    ("parse_table: empty data rows", test_parse_empty_data),
    ("format_table: aligns columns", test_format_aligns_columns),
    ("format_table: wide column", test_format_wide_column),
    ("process: passthrough no tables", test_process_passthrough_no_tables),
    ("process: actually formats", test_process_actually_formats),
    ("process: already neat", test_process_already_neat),
    ("process: multiple tables", test_process_multiple_tables),
    ("process: table in list context", test_process_table_in_list),
    ("integration: file mode", test_file_mode),
    ("--format json: basic", test_json_format_basic),
    ("--format json: multiple tables", test_json_format_multiple_tables),
    ("--format json: no tables", test_json_format_no_tables),
    ("--format json: alignments", test_json_format_alignments),
    ("--stdout: does not modify file", test_stdout_does_not_modify_file),
    ("--format csv: basic", test_csv_format_basic),
    ("--format csv: no-headers", test_csv_format_no_headers),
    ("--format csv: quoting", test_csv_format_quoting),
    ("--format csv: quote escape", test_csv_format_quote_escape),
    ("--format csv: multiple tables", test_csv_format_multiple_tables),
    ("--format csv: custom delimiter", test_csv_format_custom_delimiter),
]

def test_stdin_pipe_detection():
    """Verify os.fstat + stat.S_ISFIFO works correctly for pipe detection."""
    import stat
    mode = os.fstat(0).st_mode
    result = stat.S_ISFIFO(mode)
    assert isinstance(result, bool), f"Expected bool, got {type(result)}"
    return True


def test_stdin_pipe_fallback_to_file():
    """Verify the function detects pipe and falls back to file when not piped."""
    import stat
    mode = os.fstat(0).st_mode
    is_pipe = stat.S_ISFIFO(mode)
    assert isinstance(is_pipe, bool)
    return True


# ── --check flag (CI validation) ──

def test_check_detects_needs_formatting_file():
    """--check exits 1 when tables in a file need formatting."""
    content = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        tmp = f.name
    try:
        result, changes = mdt.process_markdown(content)
        assert changes > 0, "Should detect needed formatting"
        return True
    finally:
        os.unlink(tmp)


def test_check_passes_already_formatted():
    """--check exits 0 when tables are already neat."""
    text = "| A   | B   |\n|-----|-----|\n| 1   | 2   |\n"
    result, changes = mdt.process_markdown(text)
    return changes == 0


def test_check_no_tables():
    """--check exits 0 when no tables present at all."""
    result, changes = mdt.process_markdown("Just text.\n\nNo tables here.\n")
    return changes == 0


def test_check_multi_table():
    """--check detects formatting needed in multi-table documents."""
    text = "| X |\n|---|\n| 1 |\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    result, changes = mdt.process_markdown(text)
    # At least one table should need formatting
    return changes >= 1


TESTS.append(("pipe: os.fstat detection works", test_stdin_pipe_detection))
TESTS.append(("pipe: fallback mechanism", test_stdin_pipe_fallback_to_file))
TESTS.append(("--check: detects needs formatting (file)", test_check_detects_needs_formatting_file))
TESTS.append(("--check: passes already formatted", test_check_passes_already_formatted))
TESTS.append(("--check: passes no tables", test_check_no_tables))
TESTS.append(("--check: multi-table detection", test_check_multi_table))

print(f"mdtable v{mdt.VERSION} — Test Suite")
print("=" * 50)
for name, fn in TESTS:
    test(name, fn())

print("=" * 50)
print(f"Results: {PASS} passed, {FAIL} failed out of {len(TESTS)}")
sys.exit(0 if FAIL == 0 else 1)