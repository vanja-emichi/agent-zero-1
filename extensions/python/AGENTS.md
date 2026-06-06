# Python Extensions DOX

## Purpose

- Own built-in backend lifecycle extensions under `extensions/python/`.
- Keep Python hook behavior compatible with `helpers.extension.call_extensions_async` and `call_extensions_sync`.

## Ownership

- Each direct subdirectory is one named extension point.
- Python files inside an extension point are loaded in deterministic filename order.
- Implicit `@extensible` hook implementations use `_functions/<module>/<qualname>/<start|end>/` layout when present.

## Local Contracts

- Extension functions must match the arguments supplied by their hook point.
- Preserve numeric prefixes when ordering affects prompt construction, stream masking, persistence, or cleanup.
- Use `AgentContext` from `agent` when context access is needed.
- Do not log unmasked secrets, raw hidden prompt sections, or private user data.
- `tool_execute_before/_10_unmask_secrets` resolves secret placeholders only in args whose names match `SECRET_ARG_NAMES` (e.g., `token`, `api_key`, `password`). Content-bearing args (`content`, `text`, `code`, etc.) and unrecognized args are skipped with a warning log. Add new arg names to the appropriate frozenset when extending tool interfaces.

## Work Guidance

- Keep extension modules import-light; many hooks run during hot paths.
- Use mutable `ctx` or `data` dictionaries according to the hook contract when rewriting content.
- Add or update tests when a hook changes prompt content, message history, tool output, streaming, or persistence behavior.

## Verification

- Run targeted tests for the affected lifecycle area.
- Run a startup smoke check for `agent_init`, `startup_migration`, or `system_prompt` changes when practical.

## Child DOX Index

No child DOX files.
