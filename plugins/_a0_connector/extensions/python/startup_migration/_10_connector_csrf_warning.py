"""Startup extension: warn when connector endpoints are reachable from non-localhost.

Fires during startup_migration to alert operators that connector API endpoints
bypass CSRF protection and may be accessible beyond localhost if the server
binds to 0.0.0.0 or a public interface.
"""
from __future__ import annotations

from helpers.extension import Extension
from helpers.plugins import call_plugin_hook


class ConnectorCsrfWarning(Extension):
    def execute(self, **kwargs):
        call_plugin_hook(
            "_a0_connector",
            "warn_csrf_posture",
            default={"warned": False},
        )
