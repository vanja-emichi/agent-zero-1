# PromptInclude Helpers DOX

## Purpose

File scanning logic that discovers and reads `*.promptinclude.md` files from the working directory tree. Enforces token budgets, file-count limits, and gitignore-style exclusion patterns to inject user-defined prompt content into agent contexts safely.

## Ownership

- `__init__.py` — Empty; the directory is a Python package.
- `scanner.py` — Core scanner: `scan_promptinclude_files()` walks the directory tree, matches files by glob pattern, enforces byte-size limits before reading (per-file `max_file_size` and total `max_total_size`), enforces per-file and total token budgets, crops or skips files that exceed limits, logs warnings for size-skipped files, and returns typed `ScanResult`.

## Local Contracts

- `scan_promptinclude_files()` accepts `root`, `name_pattern` (default `*.promptinclude.md`), `max_depth`, `max_file_tokens` (2000), `max_file_count` (50), `max_total_tokens` (8000), optional `gitignore` string, `max_file_size` (10240 bytes), and `max_total_size` (51200 bytes).
- Returns `ScanResult(files=list[FileEntry], skipped_count=int)` where each `FileEntry` has `path`, `content`, `token_count`, and `status` (ok/cropped/skipped).
- Token counting uses `helpers.tokens.count_tokens()`.
- Cropping trims from the start of the file to fit within budget.
- Gitignore patterns are parsed via `pathspec.PathSpec` with `gitwildmatch` syntax.
- Directory traversal uses `os.walk` with in-place `dirnames` filtering for ignore patterns.
- No agent or tool dependencies; pure filesystem + token counting.

## Work Guidance

- Changes to token budgets or file limits should preserve backward compatibility with existing promptinclude files.
- New ignore patterns must follow gitwildmatch syntax.
- Cropping direction is currently start-only; adding end-cropping requires a new parameter.
- Keep this module free of imports from `agent/` or tool modules.

## Verification

- `scan_promptinclude_files()` on an empty directory returns zero files.
- Files exceeding `max_file_size` are skipped with a `logging.warning()` and status counted in `skipped_count`.
- Files exceeding `max_total_size` are skipped with a `logging.warning()` and budget is marked exhausted.
- Files exceeding `max_file_tokens` are cropped with status `cropped`.
- Total token budget is respected; excess files get status `skipped`.
- Gitignore patterns correctly exclude matched paths and directories.
- Token counts in `FileEntry` match `helpers.tokens.count_tokens(content)`.

## Child DOX Index

No child DOX files.
