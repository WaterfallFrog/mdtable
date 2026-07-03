#!/usr/bin/env python3
"""mdtable — Format ragged markdown tables into neat aligned columns.

Usage:
    mdtable README.md                    # Fix tables in-place (default)
    mdtable --stdout README.md           # Print formatted tables to stdout
    cat doc.md | mdtable                 # Pipe mode — auto-detected
    mdtable < README.md                  # Stdin redirect — also auto-detected
    mdtable --format json < table.md     # JSON as output (machine-readable)
    mdtable --format csv < table.md      # CSV output (machine-readable)
    mdtable --format json README.md      # JSON for files too
    mdtable --format csv README.md       # CSV for files too
    mdtable --format csv --no-headers < t  # CSV without header row
    mdtable --format csv --csv-delimiter '|' < t  # Pipe-delimited output
    mdtable --to github < file.md        # GitHub-ready markdown (GFM compliance)
    mdtable --to github README.md        # GitHub-ready markdown for files too
    mdtable --check <file>               # Dry-run: exit 1 if tables need formatting
    mdtable --check < doc.md             # Check on stdin
    mdtable --version                    # Show version
    mdtable --help                       # Show this message
"""

import sys
import re
import os
import stat
import json

VERSION = "1.4.0"


def parse_cells(row):
    """Split a table row into individual cells, handling escaped pipes."""
    content = row.strip()
    if content.startswith('|'):
        content = content[1:]
    if content.endswith('|'):
        content = content[:-1]

    # Protect escaped pipes (\| → placeholder) before splitting on real pipes
    PLACEHOLDER = '\x00'
    escaped = content.replace('\\|', PLACEHOLDER)

    cells = []
    current = ''
    for char in escaped:
        if char == '|':
            cells.append(current.strip().replace(PLACEHOLDER, '|'))
            current = ''
        else:
            current += char
    cells.append(current.strip().replace(PLACEHOLDER, '|'))
    return cells


def parse_alignment(sep):
    """Parse alignment from separator row. Returns list of alignments."""
    cells = parse_cells(sep)
    alignments = []
    for cell in cells:
        cell = cell.strip()
        if cell.startswith(':') and cell.endswith(':'):
            alignments.append('center')
        elif cell.endswith(':'):
            alignments.append('right')
        else:
            alignments.append('left')
    return alignments


def parse_table(lines, start):
    """Parse a markdown table starting at `start` in `lines`.

    Returns (header, separator, rows, end_index) or None.
    Handles tables without a separator row (returns header only).
    Handles tables with only header + separator, no data rows.
    """
    if not lines[start].strip().startswith('|'):
        return None

    header = lines[start].rstrip()
    if start + 1 >= len(lines):
        return None

    sep = lines[start + 1].rstrip()
    # The separator row must contain only |, -, :, and spaces
    sep_content = sep.strip().strip('|').strip()
    if not re.match(r'^[\s\-:|]+$', sep_content):
        return None

    rows = []
    end = start + 2
    while end < len(lines):
        line = lines[end].rstrip()
        if not line.strip().startswith('|'):
            break
        rows.append(line)
        end += 1

    return (header, sep, rows, end)


def format_separator(widths, alignments):
    """Build a formatted separator row."""
    parts = []
    for w, a in zip(widths, alignments):
        # width + 2 accounts for mandatory space padding in data rows
        dashes = '-' * max(3, w + 2)
        if a == 'center':
            parts.append(f':{dashes[1:-1]}:')
        elif a == 'right':
            parts.append(f'{dashes[:-1]}:')
        else:
            parts.append(dashes)
    return '|' + '|'.join(parts) + '|'


def format_row(cells, widths, alignments):
    """Format a data row with proper padding."""
    parts = []
    for cell, w, a in zip(cells, widths, alignments):
        if a == 'right':
            parts.append(cell.rjust(w))
        elif a == 'center':
            left = (w - len(cell)) // 2
            right = w - len(cell) - left
            parts.append(' ' * left + cell + ' ' * right)
        else:
            parts.append(cell.ljust(w))
    return '| ' + ' | '.join(parts) + ' |'


# ── JSON output ──


def format_table_json(header, sep, rows):
    """Format table as JSON — machine-readable output.

    Returns a dict with: columns, rows, alignments, col_count, row_count, widths.
    """
    header_cells = parse_cells(header)
    alignments = parse_alignment(sep)
    all_rows = [header_cells]
    for row in rows:
        all_rows.append(parse_cells(row))

    ncols = max(len(r) for r in all_rows)
    if len(alignments) < ncols:
        alignments = alignments + ['left'] * (ncols - len(alignments))
    else:
        alignments = alignments[:ncols]

    widths = [0] * ncols
    for row in all_rows:
        for i, cell in enumerate(row):
            if i < ncols:
                widths[i] = max(widths[i], len(cell))
    widths = [max(w, 3) for w in widths]

    return {
        "format": "markdown_table",
        "version": VERSION,
        "col_count": ncols,
        "row_count": len(rows),  # data rows only
        "total_row_count": len(all_rows),  # header + data
        "columns": header_cells,
        "alignments": alignments,
        "widths": widths,
        "rows": [parse_cells(row) for row in rows],
    }


def format_all_tables_as_json(text):
    """Parse all tables in markdown text and return them as a JSON array."""
    lines = text.split('\n')
    tables = []
    i = 0
    while i < len(lines):
        table = parse_table(lines, i)
        if table:
            header, sep, rows, end = table
            tables.append(format_table_json(header, sep, rows))
            i = end
        else:
            i += 1
    return json.dumps(tables, indent=2)


# ── CSV output ──


def format_table_csv(header, sep, rows, delimiter=',', no_headers=False):
    """Format a table as CSV lines.

    Returns a list of CSV-formatted strings (header + data rows).
    Cells with commas, quotes, or newlines are properly quoted.
    """
    def escape_cell(cell):
        if delimiter in cell or '"' in cell or '\n' in cell or '\r' in cell:
            return '"' + cell.replace('"', '""') + '"'
        return cell

    header_cells = parse_cells(header)
    lines_out = []
    if not no_headers:
        lines_out.append(delimiter.join(escape_cell(c) for c in header_cells))
    for row in rows:
        cells = parse_cells(row)
        while len(cells) < len(header_cells):
            cells.append('')
        cells = cells[:len(header_cells)]
        lines_out.append(delimiter.join(escape_cell(c) for c in cells))
    return lines_out


def format_all_tables_as_csv(text, delimiter=',', no_headers=False):
    """Parse all tables in markdown text and return them as CSV blocks.

    Each table becomes a block of CSV lines, separated by a blank line.
    Returns a string.
    """
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        table = parse_table(lines, i)
        if table:
            header, sep, rows, end = table
            blocks.append('\n'.join(format_table_csv(header, sep, rows, delimiter, no_headers)))
            i = end
        else:
            i += 1
    return '\n\n'.join(blocks) + '\n'


# ── Markdown table formatting ──


def format_table(header, sep, rows):
    """Reformat an entire markdown table."""
    header_cells = parse_cells(header)
    alignments = parse_alignment(sep)

    all_rows = [header_cells]
    for row in rows:
        all_rows.append(parse_cells(row))

    # Calculate max widths
    ncols = max(len(r) for r in all_rows)
    widths = [0] * ncols
    if len(alignments) < ncols:
        alignments = alignments + ['left'] * (ncols - len(alignments))
    else:
        alignments = alignments[:ncols]

    for row in all_rows:
        for i, cell in enumerate(row):
            if i < ncols:
                widths[i] = max(widths[i], len(cell))

    # Ensure min width for separator readability
    widths = [max(w, 3) for w in widths]

    # Build output
    out = [format_row(header_cells, widths, alignments)]
    out.append(format_separator(widths, alignments))
    for row in rows:
        cells = parse_cells(row)
        cells = cells[:ncols] + [''] * (ncols - len(cells))
        out.append(format_row(cells, widths, alignments))

    return out


def process_markdown(text):
    """Process markdown text, formatting all tables.

    Returns (result_text, change_count).
    """
    lines = text.split('\n')
    result = []
    i = 0
    changes = 0

    while i < len(lines):
        table = parse_table(lines, i)
        if table:
            header, sep, rows, end = table
            original_block = '\n'.join([header, sep] + rows)
            formatted = format_table(header, sep, rows)
            if '\n'.join(formatted) != original_block:
                changes += 1
            result.extend(formatted)
            i = end
        else:
            result.append(lines[i])
            i += 1

    return '\n'.join(result), changes


# ── GitHub Flavored Markdown output ──


def format_all_tables_as_github(text):
    """Format tables specifically for GitHub Flavored Markdown rendering.

    GitHub requires blank lines before and after every table block
    to render correctly. This function formats tables and ensures
    proper GFM spacing.

    Returns (result_text, changes, warnings) where:
      - result_text: formatted text with GitHub-safe table spacing
      - changes: number of formatting changes + blank-line insertions
      - warnings: always empty (reserved for future GFM checks)
    """
    # First, format all tables as normal
    formatted, fmt_changes = process_markdown(text)
    fmt_lines = formatted.split('\n')
    warnings = []
    total_adjustments = fmt_changes

    # Detect which line ranges are tables in the already-formatted output
    table_ranges = []  # list of (start_idx, end_idx_exclusive)
    i = 0
    while i < len(fmt_lines):
        line = fmt_lines[i]
        if line.strip().startswith('|') and i + 1 < len(fmt_lines):
            sep = fmt_lines[i + 1]
            sep_content = sep.strip().strip('|').strip()
            if re.match(r'^[\s\-:|]+$', sep_content):
                start = i
                i += 2
                while i < len(fmt_lines) and fmt_lines[i].strip().startswith('|'):
                    i += 1
                table_ranges.append((start, i))
                total_adjustments += 1
                continue
        i += 1

    # Build output with blank lines around tables
    out_lines = []
    prev_end = 0
    for tbl_start, tbl_end in table_ranges:
        # Copy lines before this table
        for idx in range(prev_end, tbl_start):
            out_lines.append(fmt_lines[idx])

        # Ensure blank line before table (unless at start of file or already blank)
        if out_lines and out_lines[-1] != '':
            out_lines.append('')

        # Copy table lines
        for idx in range(tbl_start, tbl_end):
            out_lines.append(fmt_lines[idx])

        # Ensure blank line after table (unless last thing in file)
        if tbl_end < len(fmt_lines) and fmt_lines[tbl_end] != '':
            out_lines.append('')

        prev_end = tbl_end

    # Copy remaining lines after last table
    for idx in range(prev_end, len(fmt_lines)):
        out_lines.append(fmt_lines[idx])

    result = '\n'.join(out_lines)

    # Ensure file ends with newline
    if not result.endswith('\n'):
        result += '\n'
        total_adjustments += 1

    return result, total_adjustments, warnings


# ── Entry point ──


def main():
    args = sys.argv[1:]

    # Help: explicit --help or -h
    if args and args[0] in ('-h', '--help'):
        print((__doc__ or "").strip())
        return

    # Version
    if args and args[0] == '--version':
        print(f"mdtable v{VERSION}")
        return

    # Parse flags
    csv_mode = False
    json_mode = False
    github_mode = False
    stdout_mode = False
    no_headers = False
    csv_delimiter = ','
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '--format' and i + 1 < len(args):
            fmt = args[i + 1]
            if fmt == 'json':
                json_mode = True
            elif fmt == 'csv':
                csv_mode = True
            else:
                print(f"mdtable: unknown format '{fmt}' (use 'json' or 'csv')", file=sys.stderr)
                sys.exit(1)
            i += 2
            continue
        elif args[i] == '--stdout':
            stdout_mode = True
            i += 1
            continue
        elif args[i] == '--no-headers':
            no_headers = True
            i += 1
            continue
        elif args[i] == '--csv-delimiter' and i + 1 < len(args):
            csv_delimiter = args[i + 1]
            i += 2
            continue
        elif args[i] == '--to' and i + 1 < len(args):
            target = args[i + 1]
            if target == 'github':
                github_mode = True
            else:
                print(f"mdtable: unknown target '{target}' (use 'github')", file=sys.stderr)
                sys.exit(1)
            i += 2
            continue
        else:
            filtered.append(args[i])
            i += 1
    args = filtered

    # Parse --check flag
    if args and args[0] == '--check':
        check_mode = True
        files = args[1:]
    else:
        check_mode = False
        files = args

    # Detect pipe mode: stdin connected to a pipe (not a terminal)
    stdin_pipe = False
    try:
        stdin_pipe = stat.S_ISFIFO(os.fstat(0).st_mode)
    except (OSError, AttributeError):
        pass

    if stdin_pipe:
        # Pipe mode — read from stdin even if file arguments given
        text = sys.stdin.read()

        if files:
            print(f"stdin: reading from pipe (ignoring {len(files)} file argument(s))",
                  file=sys.stderr)

        if json_mode:
            print(format_all_tables_as_json(text))
            return

        if csv_mode:
            print(format_all_tables_as_csv(text, delimiter=csv_delimiter, no_headers=no_headers), end='')
            return

        if github_mode:
            result, changes, warnings = format_all_tables_as_github(text)
            sys.stdout.write(result)
            if changes > 0:
                print(f"# {changes} change(s) applied", file=sys.stderr)
            for w in warnings:
                print(f"# WARNING: {w}", file=sys.stderr)
            return

        result, changes = process_markdown(text)
        if check_mode:
            if changes > 0:
                print(f"stdin: {changes} table(s) need formatting", file=sys.stderr)
            sys.exit(0 if changes == 0 else 1)
        sys.stdout.write(result)
        return

    # No pipe — fall back to file mode
    if not files:
        print("mdtable: no input — pipe data or provide a filename", file=sys.stderr)
        sys.exit(1)

    # File mode
    exit_code = 0
    for path in files:
        if not os.path.exists(path):
            print(f"mdtable: file not found: {path}", file=sys.stderr)
            sys.exit(1)

        with open(path, 'r') as f:
            text = f.read()

        if json_mode:
            print(format_all_tables_as_json(text))
            continue

        if csv_mode:
            print(format_all_tables_as_csv(text, delimiter=csv_delimiter, no_headers=no_headers), end='')
            continue

        if github_mode:
            result, changes, warnings = format_all_tables_as_github(text)
            sys.stdout.write(result)
            if changes > 0:
                print(f"# {path}: {changes} change(s) applied", file=sys.stderr)
            else:
                print(f"# {path}: no changes needed", file=sys.stderr)
            for w in warnings:
                print(f"# WARNING ({path}): {w}", file=sys.stderr)
            continue

        result, changes = process_markdown(text)

        if check_mode:
            if changes > 0:
                print(f"{path}: {changes} table(s) need formatting")
                exit_code = 1
        elif stdout_mode:
            sys.stdout.write(result)
            if changes > 0:
                print(f"# Written to stdout ({path}: {changes} table(s) formatted)", file=sys.stderr)
            else:
                print(f"# Written to stdout ({path}: no tables to format)", file=sys.stderr)
        else:
            if changes > 0:
                with open(path, 'w') as f:
                    f.write(result)
                print(f"{path}: {changes} table(s) formatted")
            else:
                print(f"{path}: no tables to format")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()