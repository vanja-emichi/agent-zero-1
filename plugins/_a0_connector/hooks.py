"""Plugin hooks for _a0_connector.

Exposes named hooks that the framework calls at well-defined lifecycle points.
- warn_csrf_posture: called during startup_migration to log a warning when
  connector endpoints are reachable from non-localhost origins.
"""
from __future__ import annotations

from typing import Any


def warn_csrf_posture() -> dict[str, Any]:
    """Check and warn about connector CSRF posture on startup.

    Delegates to helpers.csrf_posture.warn_if_nonloopback().
    Returns a summary dict for callers and tests.
    """
    from plugins._a0_connector.helpers.csrf_posture import warn_if_nonloopback

    return warn_if_nonloopback()
