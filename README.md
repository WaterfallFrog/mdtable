# mdtable — Markdown Table Aligner

Format ragged markdown tables into neat aligned columns. One file. Zero dependencies.

```bash
# Fix tables in a file
mdtable README.md

# Pipe mode
cat doc.md | mdtable

# Check mode (CI-friendly, exit 1 if tables need formatting)
mdtable --check README.md
mdtable --check < doc.md

# JSON output (machine-readable — for scripts and tooling)
mdtable --format json < doc.md
mdtable --format json README.md

# CSV output (for spreadsheets and data pipelines)
mdtable --format csv < doc.md
mdtable --format csv --no-headers < doc.md
mdtable --format csv --csv-delimiter '|' < doc.md

# GitHub-ready markdown (ensures GFM compliance)
mdtable --to github README.md
mdtable --to github < doc.md

# Preview to stdout (leave file unchanged)
mdtable --stdout README.md
```

## Why

Markdown tables are great until you add one cell that's longer than the others and the whole thing looks like someone dropped a keyboard. `mdtable` reads any markdown table, calculates column widths, and realigns everything — respecting your `:---` / `:---:` / `---:` alignment markers.

**Before:**
```
| Name            | Age |          City |
|-----------------|:---:|--------------:|
| Froggy          | 47  |        London |
| Spencer Batwick | 52  | Hedgerow Lane |
```

**After:**
```
| Name            | Age |          City |
|-----------------|:---:|--------------:|
| Froggy          | 47  |        London |
| Spencer Batwick | 52  | Hedgerow Lane |
```

## Install

```bash
# Download and make executable
curl -O https://raw.githubusercontent.com/WaterfallFrog/mdtable/main/mdtable
chmod +x mdtable

# Or clone the repo
git clone https://github.com/WaterfallFrog/mdtable.git
```

## Usage

```bash
mdtable <file>                          # Fix tables in-place (default)
mdtable --stdout <file>                 # Print formatted tables to stdout
mdtable < doc.md                        # Read from stdin, write to stdout
cat doc.md | mdtable                    # Same (pipe auto-detected)
mdtable --check <file>                  # Dry-run: exit 1 if tables need fixing (CI)
mdtable --check < doc.md                # Check on stdin
mdtable --format json < doc.md          # JSON output (machine-readable)
mdtable --format json README.md         # JSON for files too
mdtable --format csv < doc.md           # CSV output (spreadsheets)
mdtable --format csv README.md          # CSV for files too
mdtable --format csv --no-headers < doc.md   # CSV without header row
mdtable --format csv --csv-delimiter '|' < doc.md  # Pipe-delimited CSV
mdtable --to github < doc.md            # GitHub-ready markdown (GFM compliance)
mdtable --to github README.md           # GitHub-ready markdown for files too
mdtable --help                          # Show help
mdtable --version                       # Show version
```

### `--format csv`

Outputs table data as CSV — perfect for spreadsheets, data pipelines, and analytics:

```csv
Name,Age,City
Froggy,47,London
Spencer Batwick,52,Hedgerow Lane
```

Extended options:
- `--format csv` — comma-separated output (default delimiter)
- `--no-headers` — omit the header row, data rows only
- `--csv-delimiter '|'` — custom delimiter (tab, pipe, semicolon, etc.)

### `--format json`

Outputs table structure as JSON — perfect for scripts, CI pipelines, and tooling:

```json
[
  {
    "format": "markdown_table",
    "version": "1.4.0",
    "col_count": 3,
    "row_count": 2,
    "columns": ["Name", "Age", "City"],
    "alignments": ["left", "center", "right"],
    "widths": [15, 3, 12],
    "rows": [
      ["Froggy", "47", "London"],
      ["Spencer Batwick", "52", "Hedgerow Lane"]
    ]
  }
]
```

### `--to github`

Outputs GitHub Flavored Markdown (GFM) — ensures every table has blank lines before and after, which is required for proper rendering on GitHub. Also ensures the file ends with a newline. Use this when formatting README files, issue comments, or any markdown destined for GitHub.

```bash
# Format a file for GitHub
mdtable --to github README.md

# From stdin
cat doc.md | mdtable --to github

# Warnings (if any) go to stderr for CI visibility
```

This is especially useful in CI/CD pipelines that need to guarantee README files render correctly on GitHub.

### `--stdout`

Preview formatted tables without modifying the file. Writes to stdout, leaves the original file untouched. Useful when you want to review changes before committing.

## Pipe detection

`mdtable` auto-detects when piped data is coming from stdin (`cat doc.md | mdtable`) vs running in a terminal. No `-` argument or special flag needed — it just works.

## Design

One Python file. Standard library only (`sys`, `re`, `os`, `stat`, `json`). No pip install needed. It scans line by line, finds pipe-delimited tables with a separator row, and reformats each one. Everything outside tables passes through untouched.

## Version history

- **v1.4.0** — `--to github` flag (GFM-compliant output with blank-line spacing)
- **v1.3.0** — `--format csv`, `--no-headers`, `--csv-delimiter`, pipe auto-detection
- **v1.2.0** — `--format json`, `--stdout`, escaped pipes, `--version`
- **v1.1.0** — Stdin fix, pipe support, test suite
- **v1.0.0** — Initial release

## License

Do whatever you want with it. If you find it useful, tell someone. If you find a bug, tell me. Ribbit.

— Froggy, CEO of [Rib IT Ltd](https://frog.unfrogettable.co.uk)