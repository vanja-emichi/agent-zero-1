# _a0_connector

## Purpose

- Own the bridge between the Agent Zero runtime and a connected A0 CLI host.
- Provide remote execution, remote file editing, and remote desktop control to agent contexts that have an active CLI session.
- Expose a v1 REST API and a WebSocket protocol for CLI clients to discover capabilities, subscribe to contexts, send messages, and relay remote-tool results.

## Ownership

- `plugin.yaml` — manifest (name, title, version 1.5, settings_sections: external + developer).
- `hooks.py` — plugin lifecycle hooks: `warn_csrf_posture` for startup CSRF posture warning.
- `api/ws_connector.py` — WebSocket handler on the shared `/ws` namespace. Manages connector sessions, context subscriptions, message relay, and pending remote-operation futures.
- `api/v1/` — REST API handlers for CLI clients:
  - `base.py` — `PublicConnectorApiHandler` (no auth, no CSRF) and `ProtectedConnectorApiHandler` (session auth, no CSRF). Both carry `csrf_exempt = True` documenting the intentional CSRF bypass for localhost CLI use.
  - `capabilities.py` — public discovery endpoint returning protocol version, features, transports, and websocket handler paths.
  - Chat lifecycle: `chat_create.py`, `chats_list.py`, `chat_get.py`, `chat_reset.py`, `chat_delete.py`, `compact_chat.py`.
  - Messaging: `message_send.py`, `pause.py`, `nudge.py`.
  - Agent/config: `agent_profile_set.py`, `agents_list.py`, `settings_get.py`, `settings_set.py`, `model_presets.py`, `model_switcher.py`, `token_status.py`.
  - Skills: `skills_list.py`, `skills_activate.py`, `skills_delete.py`.
  - Other: `installed_plugins.py`, `log_tail.py`, `projects.py`, `browser_runtime.py`.
- `tools/` — three agent-facing tools:
  - `code_execution_remote.py` — shell-backed execution on the CLI host via WebSocket `connector_exec_op`.
  - `text_editor_remote.py` — read/write/patch files on the CLI host via WebSocket `connector_file_op`.
  - `computer_use_remote.py` — desktop control on the CLI host via WebSocket `connector_computer_use_op`.
- `helpers/` — plugin-local modules:
  - `ws_runtime.py` — in-memory session registry, pending-operation futures, metadata storage per SID, remote tree snapshots.
  - `chat_context.py` — context resolution and creation for incoming connector messages.
  - `event_bridge.py` — log entry extraction for context snapshot replay.
  - `exec_config.py` — execution configuration builder.
  - `text_editor_freshness.py` — file state tracking for freshness-aware patching.
  - `version.py` — Agent Zero version helper.
  - `csrf_posture.py` — CSRF bypass documentation, startup warning for non-localhost, optional per-IP rate limiting for non-localhost callers.
- `extensions/` — three framework extension points:
  - `.../startup_migration/_10_connector_csrf_warning.py` — fires a startup warning when connector endpoints are reachable from non-localhost origins.
  - `.../system_prompt/.../end/_70_include_remote_tool_stubs.py` — appends `computer_use_remote` tool prompt when a CLI session is active.
  - `.../message_loop_prompts_after/_76_include_remote_file_structure.py` — injects remote file tree into `extras_temporary` when a snapshot exists.
- `skills/` — seven agent skills: `host-code-execution`, `host-computer-use`, `host-computer-use-linux`, `host-computer-use-macos`, `host-computer-use-windows`, `host-file-editing`, `setup-a0-cli`.
- `prompts/` — four prompt templates: `agent.system.tool.code_execution_remote.md`, `agent.system.tool.computer_use_remote.md`, `agent.system.tool.text_editor_remote.md`, `agent.extras.remote_file_structure.md`.
- `webui/thumbnail.jpg` — plugin thumbnail asset.

## Local Contracts

- The WebSocket protocol version is `a0-connector.v1`. All connector events use the `connector_` prefix. Unknown `connector_` events return a `WsResult.error`.
- CLI sessions are identified by Socket.IO SID. On connect (`connector_hello`), the CLI declares remote-tool capabilities (computer_use, host_browser, remote_files, remote_exec). On disconnect, all pending operations for that SID fail with a disconnect error.
- Context subscriptions are SID-to-context-id mappings. A CLI may subscribe to multiple contexts. Snapshot replay is paged at 50 entries; live streaming is paged at 100 entries. Evidence: `ws_connector.py` constants `_SNAPSHOT_REPLAY_PAGE_SIZE` and `_LIVE_STREAM_PAGE_SIZE`.
- Remote tool operations use pending futures: a tool sends a `connector_*_op` event via WebSocket and awaits the corresponding `connector_*_op_result` from the CLI. Timeout defaults: file ops 30s, exec ops 120s, computer use and browser ops per-tool configured.
- The `installed_plugins` endpoint (`api/v1/installed_plugins.py`) protects `_a0_connector` from being toggled off through the connector API.
- The `capabilities` endpoint is the only public (no auth) surface. All other v1 endpoints inherit from `ProtectedConnectorApiHandler` (session auth required, CSRF not required for API-key/CLI flows).
- v1 API handlers extend `PublicConnectorApiHandler` or `ProtectedConnectorApiHandler` from `api/v1/base.py`, not the core `ApiHandler` directly.
- All connector API handlers bypass CSRF protection (`requires_csrf() -> False`, `csrf_exempt = True`). This is intentional: CLI clients authenticate via session cookies but cannot send CSRF tokens in programmatic JSON API calls. See `base.py` module docstring for the full rationale and mitigations.
- A startup warning fires when the server binds to `0.0.0.0` or a public interface, alerting operators that connector endpoints are reachable beyond localhost (`hooks.py` → `helpers/csrf_posture.py` → `extensions/.../startup_migration/_10_connector_csrf_warning.py`).
- Optional per-IP rate limiting for non-localhost callers is available via `helpers/csrf_posture.py`, controlled by `A0_CONNECTOR_RATE_LIMIT_PER_MINUTE` (default 100) and `A0_CONNECTOR_RATE_LIMIT_ENABLED` env vars.
- Prompt files under `prompts/` are resolved through the standard prompt precedence chain. The plugin does not override core prompts.
- Skills under `skills/` are loaded by the framework skill system and guide agents on safe host CLI, host file editing, host computer use (per-platform), and CLI setup workflows.
- The `_70_include_remote_tool_stubs` extension appends the `computer_use_remote` prompt only when the tool is not already present in the system prompt (checks for the `"tool_name": "computer_use_remote"` marker).
- The `_76_include_remote_file_structure` extension injects remote file tree into `extras_temporary` only when a snapshot less than 90 seconds old exists for the current context.
- `ws_runtime.py` stores all mutable connector state in module-level dicts protected by a threading lock. It does not persist state across server restarts.
- The `text_editor_remote` tool uses freshness-aware patching when the connected CLI supports it, falling back to basic operations for older CLI versions.

## Work Guidance

- Changes to the WebSocket protocol must preserve backward compatibility with deployed CLI clients. Add new events; avoid renaming or removing existing ones.
- When adding a new v1 REST endpoint, inherit from `PublicConnectorApiHandler` (no auth) or `ProtectedConnectorApiHandler` (session auth) and register the capability in `capabilities.py` (`_BASE_FEATURES` or `_OPTIONAL_FEATURES`).
- When adding a new remote tool, create a matching pending-operation dataclass in `ws_runtime.py`, add resolve/fail functions, wire the send and result handlers in `ws_connector.py`, and create a prompt file under `prompts/`.
- Use plugin-local helpers for connector-specific behavior. Use shared `helpers/` only for reusable framework logic.
- The `installed_plugins` endpoint must continue to protect `_a0_connector` and other always-enabled or critical plugins from being disabled via the connector API.
- Remote tool timeout values and pagination constants are defined at module level in `ws_connector.py` and the tool modules. Keep them configurable or clearly documented.
- Skills should not duplicate tool prompt content; they provide agent-facing guidance for using the remote tools safely.

## Verification

- After changing WebSocket event handling, verify: hello handshake, context subscribe/unsubscribe, message send, and at least one remote tool operation (file, exec, or computer use) complete successfully.
- After changing v1 REST endpoints, verify the endpoint returns expected data through the connector API path (`/api/plugins/_a0_connector/v1/<handler>`).
- After changing extension files, verify the remote tool stubs and remote file structure appear in agent prompt extras when a CLI session is active and do not appear when no session is connected.
- Run framework tests for touched extension points, API handlers, tools, and WebSocket event routing.
- For capability-discovery changes, verify `capabilities.py` returns correct feature lists with and without optional modules present.

## Child DOX Index

No child DOX files.
