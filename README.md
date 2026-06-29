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
mdtable <file>          # Fix tables in-place
mdtable < file.md       # Read from stdin, write to stdout
cat file.md | mdtable   # Same
mdtable --check <file>  # Dry-run: exit 1 if tables need fixing (CI)
mdtable --help          # Show help
```

Works with any markdown file: READMEs, docs, wikis, blog posts, GitHub Issues.

## Design

One Python file. Standard library only (`sys`, `re`, `os`). No pip install needed. It scans line by line, finds pipe-delimited tables with a separator row, and reformats each one. Everything outside tables passes through untouched.

## License

Do whatever you want with it. If you find it useful, tell someone. If you find a bug, tell me. Ribbit.

— Froggy, CEO of [Rib IT Ltd](https://frog.unfrogettable.co.uk)