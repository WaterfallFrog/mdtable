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
cat doc.md | mdtable                    # Same
mdtable --check <file>                  # Dry-run: exit 1 if tables need fixing (CI)
mdtable --format json < doc.md          # JSON output (machine-readable)
mdtable --format json README.md         # JSON for files too
mdtable --help                          # Show help
mdtable --version                       # Show version
```

### `--format json`

Outputs table structure as JSON — perfect for scripts, CI pipelines, and tooling:

```json
[
  {
    "format": "markdown_table",
    "version": "1.2.0",
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

### `--stdout`

Preview formatted tables without modifying the file. Writes to stdout, leaves the original file untouched. Useful when you want to review changes before committing.

## Design

One Python file. Standard library only (`sys`, `re`, `os`, `json`). No pip install needed. It scans line by line, finds pipe-delimited tables with a separator row, and reformats each one. Everything outside tables passes through untouched.

## License

Do whatever you want with it. If you find it useful, tell someone. If you find a bug, tell me. Ribbit.

— Froggy, CEO of [Rib IT Ltd](https://frog.unfrogettable.co.uk)
