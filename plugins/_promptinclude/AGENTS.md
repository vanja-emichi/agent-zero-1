# _promptinclude

## Purpose

- Own the promptinclude system: discover `*.promptinclude.md` files in the agent workdir (or project directory) and inject their content into the agent system prompt.
- Provide gitignore-aware recursive scanning with token-budgeted inclusion, per-file cropping, and file-count limits.
- Inject base behavioral guidance into every system prompt regardless of whether files are found, instructing agents how to use promptinclude files, `behaviour_adjustment`, and memory tools.

## Ownership

- `plugin.yaml` — manifest (name `_promptinclude`, version 1.0.0, settings section `agent`, per-project and per-agent config enabled).
- `default_config.yaml` — scanning defaults: `name_pattern` (`*.promptinclude.md`), `max_depth` (10), `max_file_tokens` (2000), `max_file_count` (50), `max_total_tokens` (8000), `max_file_size` (10240 bytes), `max_total_size` (51200 bytes), `gitignore` patterns.
- `helpers/scanner.py` — core scanner: recursive file discovery with `fnmatch` glob, `pathspec` gitignore filtering, token budgeting via `helpers.tokens`, byte-size validation (`os.path.getsize` before read), per-file cropping (`direction="start"`), and structured `ScanResult` output. Logs warnings via `logging.warning()` for files skipped due to size limits.
- `helpers/__init__.py` — empty package marker.
- `extensions/python/system_prompt/_16_promptinclude.py` — framework extension hooking into the `system_prompt` point at priority `_16`. Resolves the scan path (project folder or fallback workdir), calls the scanner, formats results, and appends the promptinclude block to `system_prompt`.
- `prompts/agent.system.promptinclude.md` — system prompt template wrapping discovered includes. Always injected; conditional `{{includes}}` section renders only when files are found. Carries behavioral instructions for agents on when to use promptinclude files vs. memory tools vs. `behaviour_adjustment`.
- `prompts/fw.promptinclude.includes.md` — per-file include template: `{{path}}{{suffix}}` header followed by fenced content block.
- `webui/config.html` — settings UI exposing all six config fields (name pattern, max depth, max file tokens, max file count, max total tokens, gitignore patterns). Binds to `config.*` via `$store.pluginSettingsPrototype`.
- `webui/thumbnail.jpg` — plugin thumbnail asset.
- `README.md` — user-facing plugin documentation.

## Local Contracts

- The extension `_16_promptinclude.py` runs during every `system_prompt` extension pass. It always appends the `agent.system.promptinclude.md` prompt, even when no files are discovered, so agents always receive the behavioral guidance about promptinclude file usage.
- Scan path resolution order: active project folder (via `projects.get_context_project_name`) → `settings["workdir_path"]` fallback. When running in development mode, the project folder path is normalized through `files.normalize_a0_path`.
- `scan_promptinclude_files` returns a `ScanResult` with `files` (list of `FileEntry`) and `skipped_count`. Each `FileEntry` has `path`, `content`, `token_count`, and `status` (`ok`, `cropped`, or `skipped`).
- Files are sorted alphabetically by full path before processing, producing deterministic ordering across scans.
- Token budgeting is enforced in three dimensions: per-file cap (`max_file_tokens`), file count cap (`max_file_count`), and total token cap (`max_total_tokens`). Oversized files are cropped from the start (`direction="start"`) when they partially fit the remaining budget.
- Byte-size validation is enforced in two dimensions: per-file size cap (`max_file_size`, default 10240 bytes) and total size cap (`max_total_size`, default 51200 bytes). Files exceeding the per-file limit are skipped with a `logging.warning()` message. When the total budget would be exceeded, remaining files are skipped with a warning and the budget is marked exhausted. Size checks use `os.path.getsize()` before reading file contents.
- Content delimiters: each file's injected block is wrapped in `<!-- promptinclude: {path} -->` and `<!-- /promptinclude: {path} -->` HTML comment delimiters for traceability and parsing.
- Gitignore patterns use `pathspec.PathSpec` with `gitwildmatch` semantics. Both files and directories are checked; directories are filtered in-place during `os.walk` to prune entire subtrees.
- The per-file template (`fw.promptinclude.includes.md`) appends a ` !!! cropped to fit` suffix when a file was trimmed, and the aggregate includes block appends a `!!! N more files skipped to fit` trailer when files were skipped.
- Configuration resolution follows the standard plugin config cascade: project/profile → project → agent/profile → user plugin config → bundled `default_config.yaml`.
- The `name_pattern` field uses `fnmatch` glob semantics, not regex. The default `*.promptinclude.md` matches files ending with `.promptinclude.md` at any depth.
- **Content boundary**: user-authored `*.promptinclude.md` files are injected verbatim into the system prompt without sanitization. This is intentional — promptinclude files are a high-trust channel equivalent to direct prompt editing. The token budgeting and file-count limits prevent runaway context inflation, but they do not filter content.
- No API surface, no tools, no `hooks.py`, no skills. The plugin operates entirely through the `system_prompt` extension point and the WebUI config page.

## Work Guidance

- Changes to `agent.system.promptinclude.md` affect every agent turn for every user. Treat it as a high-impact prompt surface and keep the behavioral instructions concise and unambiguous.
- When modifying scanner budgeting logic, verify that the three-dimension token budget (per-file, count, total) still respects `max_total_tokens` as the hard ceiling, including path overhead tokens (5 per file), and that the two-dimension byte-size budget (`max_file_size`, `max_total_size`) is enforced before file reads.
- The scanner runs inside `runtime.call_development_function`, so any scanner changes must remain compatible with the async runtime wrapper.
- When adding new config fields, update `default_config.yaml`, `webui/config.html`, and the `.get()` calls in `_16_promptinclude.py` together.
- Keep gitignore default patterns aligned with common noise directories (venv, node_modules, .git, build artifacts) to avoid scanning irrelevant subtrees.
- The `_16` priority in the extension filename determines ordering relative to other system prompt extensions. Check `/a0/extensions/python/system_prompt/` for the full extension sequence before changing priority.
- Do not add sanitization or content filtering to the scanner without explicit architectural approval — the promptinclude system is designed for verbatim user-authored injection.

## Verification

- After changing scanner logic, verify: files are discovered recursively within `max_depth`, gitignore patterns prune matching directories, token budgeting respects all three caps, byte-size validation respects both size caps, cropped files retain leading content, `skipped_count` is accurate, and `logging.warning()` fires for size-skipped files.
- After changing `_16_promptinclude.py`, verify: the promptinclude block appears in the agent system prompt with and without discovered files, the base behavioral guidance is always present, and project folder resolution works for both project and non-project contexts.
- After changing `agent.system.promptinclude.md`, verify the template renders correctly with `{{includes}}` populated and with `includes` empty.
- After changing `webui/config.html`, verify all eight config fields bind to `config.*` and persist through the settings modal.
- Run framework tests for the `system_prompt` extension point after any change to the extension file.

## Child DOX Index

No child DOX files.
