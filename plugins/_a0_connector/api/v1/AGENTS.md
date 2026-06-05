# A0 Connector API v1 — DOX

## Purpose

Version 1 REST API endpoints exposed by the A0 Connector plugin for CLI and external clients. Each module is a single `POST /api/plugins/_a0_connector/v1/<endpoint>` handler class that delegates to core runtime helpers.

## Ownership

| File | Role |
|------|------|
| `base.py` | `PublicConnectorApiHandler` (no auth) and `ProtectedConnectorApiHandler` (auth required) base classes. Both carry `csrf_exempt = True` documenting the intentional CSRF bypass for localhost CLI use. See module docstring for rationale. |
| `chat_create.py` | Create new chat contexts with optional project/agent profile |
| `chat_get.py` | Retrieve chat message history and project metadata |
| `chat_delete.py` | Delete a chat context by ID |
| `chat_reset.py` | Reset a chat context to initial state |
| `chats_list.py` | List all active chat contexts |
| `compact_chat.py` | Compact/summarize chat history to reduce token usage |
| `message_send.py` | Send a user message into a chat context, with optional base64 attachments |
| `pause.py` | Pause or resume agent processing on a context |
| `nudge.py` | Nudge a paused agent to continue processing |
| `log_tail.py` | Stream recent log entries for a context via event bridge |
| `token_status.py` | Return token usage and budget status for a context |
| `capabilities.py` | Report feature flags and version info to connecting CLI clients |
| `settings_get.py` | Read current Agent Zero settings |
| `settings_set.py` | Update Agent Zero settings |
| `agent_profile_set.py` | Switch the agent profile for a context |
| `agents_list.py` | List available agent profiles |
| `model_presets.py` | Get/set model configuration presets (global and project-scoped) |
| `model_switcher.py` | Switch active model provider and track override revision |
| `projects.py` | CRUD for project definitions |
| `skills_list.py` | List skills available to a context or project |
| `skills_activate.py` | Activate a skill for a context |
| `skills_delete.py` | Delete a user-created skill |
| `installed_plugins.py` | List installed plugins with metadata |
| `browser_runtime.py` | Query and configure browser backend (container vs host) |
| `__init__.py` | Package marker (empty) |

## Local Contracts

- All handlers inherit from `base.PublicConnectorApiHandler` or `base.ProtectedConnectorApiHandler`.
- Both base classes carry `csrf_exempt = True` and return `requires_csrf() -> False`, intentionally bypassing CSRF for localhost CLI clients that cannot send CSRF tokens in programmatic JSON API calls.
- A startup warning fires when the server binds to `0.0.0.0` or a public interface (`hooks.py` → `helpers/csrf_posture.py`).
- Optional per-IP rate limiting for non-localhost callers via `helpers/csrf_posture.py` (env: `A0_CONNECTOR_RATE_LIMIT_PER_MINUTE`, `A0_CONNECTOR_RATE_LIMIT_ENABLED`).
- Protected endpoints require an authenticated CLI session via the connector WS channel.
- Each handler receives `input: dict` and `request: Request`, returns `dict | Response`.
- Handlers lazy-import core modules to avoid circular imports at plugin load.
- Error responses use `Response(status=400, mimetype="application/json")` with JSON error bodies.
- New endpoints must follow the `"""POST /api/plugins/_a0_connector/v1/<name>."""` docstring convention.

## Work Guidance

- Add new endpoints as single-file modules named after the route.
- Import from `plugins._a0_connector.helpers.*` for shared logic, not from other API handlers.
- Use `connector_base.ProtectedConnectorApiHandler` unless the endpoint is intentionally public.
- Keep input validation at the top of `process()`, return early with 400 on missing/invalid params.

## Verification

- Confirm the new handler class name matches the file name (PascalCase of snake_case file).
- Test via CLI: `a0 api plugins/_a0_connector/v1/<endpoint>` or direct POST.
- Verify auth requirement: protected endpoints should reject unauthenticated requests.

## Child DOX Index

No child DOX files.
