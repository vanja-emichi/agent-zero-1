"""CSRF posture helpers for the A0 Connector plugin.

Documents the connector's CSRF bypass and provides:
- Startup warning when connector endpoints are reachable from non-localhost.
- Optional per-IP rate limiting for non-localhost callers.

Rate limiting is controlled via environment variables:
    A0_CONNECTOR_RATE_LIMIT_PER_MINUTE  (default: 100)
    A0_CONNECTOR_RATE_LIMIT_ENABLED     (default: "true" when server binds to 0.0.0.0)
"""
from __future__ import annotations

import os
import time
import threading
from typing import Any

from helpers.print_style import PrintStyle


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_PLUGIN_NAME = "_a0_connector"

# Rate-limit defaults (requests per minute per non-localhost IP).
_DEFAULT_RATE_LIMIT_PER_MINUTE = 100
_RATE_WINDOW_SECONDS = 60.0


def rate_limit_per_minute() -> int:
    """Read the per-IP rate limit from env, clamped to [1, 10_000]."""
    raw = os.getenv(
        "A0_CONNECTOR_RATE_LIMIT_PER_MINUTE",
        str(_DEFAULT_RATE_LIMIT_PER_MINUTE),
    )
    try:
        value = max(1, min(10_000, int(raw)))
    except (TypeError, ValueError):
        value = _DEFAULT_RATE_LIMIT_PER_MINUTE
    return value


def rate_limiting_enabled() -> bool:
    """Check whether non-localhost rate limiting is active.

    Enabled by default when the server binds to a non-loopback address.
    Override with A0_CONNECTOR_RATE_LIMIT_ENABLED=true|false.
    """
    env = os.getenv("A0_CONNECTOR_RATE_LIMIT_ENABLED", "").strip().lower()
    if env in ("true", "1", "yes", "on"):
        return True
    if env in ("false", "0", "no", "off"):
        return False
    # Default: enabled if server is not loopback-only.
    return _server_binds_nonloopback()


# ---------------------------------------------------------------------------
# Non-loopback detection
# ---------------------------------------------------------------------------

def _server_binds_nonloopback() -> bool:
    """Return True if the server bind host suggests non-localhost access."""
    bind_host = os.getenv("A0_SERVER_HOST", "127.0.0.1").strip()
    return bind_host in ("0.0.0.0", "::", "[::]", "")


# ---------------------------------------------------------------------------
# Startup warning
# ---------------------------------------------------------------------------

_warned = False


def warn_if_nonloopback() -> dict[str, Any]:
    """Log a warning when connector endpoints may be reachable beyond localhost.

    Called once during startup via the startup_migration extension.
    Returns a summary dict for testability.
    """
    global _warned

    bind_host = os.getenv("A0_SERVER_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = os.getenv("A0_SERVER_PORT", "50001").strip() or "50001"
    non_loopback = _server_binds_nonloopback()

    result: dict[str, Any] = {
        "plugin": _PLUGIN_NAME,
        "bind_host": bind_host,
        "port": port,
        "non_loopback": non_loopback,
        "rate_limiting": rate_limiting_enabled(),
        "rate_limit_per_minute": rate_limit_per_minute(),
        "warned": False,
    }

    if non_loopback and not _warned:
        _warned = True
        result["warned"] = True
        PrintStyle.warning(
            f"Connector CSRF bypass: server binds to {bind_host}:{port}. "
            "Connector API endpoints do not enforce CSRF and will be "
            "accessible from non-localhost origins. Session auth still "
            "applies. Enable rate limiting or restrict network access "
            "if this is unintended. "
            f"(rate_limit={rate_limit_per_minute()}/min, "
            f"enabled={rate_limiting_enabled()})"
        )

    return result


# ---------------------------------------------------------------------------
# In-memory rate limiter (token bucket per IP)
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_buckets: dict[str, list[float]] = {}


def _prune_bucket(ip: str, now: float) -> list[float]:
    """Remove timestamps older than the rate-limit window."""
    cutoff = now - _RATE_WINDOW_SECONDS
    bucket = _buckets.get(ip, [])
    bucket = [ts for ts in bucket if ts > cutoff]
    if bucket:
        _buckets[ip] = bucket
    else:
        _buckets.pop(ip, None)
    return bucket


def check_rate_limit(remote_ip: str) -> bool:
    """Return True if the request is within rate limits.

    Loopback addresses are never rate-limited. For non-localhost IPs,
    uses a simple sliding-window counter.
    """
    from helpers.network import is_loopback_address

    if is_loopback_address(remote_ip):
        return True

    if not rate_limiting_enabled():
        return True

    now = time.monotonic()
    limit = rate_limit_per_minute()

    with _lock:
        bucket = _prune_bucket(remote_ip, now)
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        _buckets[remote_ip] = bucket
        return True


def reset_rate_limiter() -> None:
    """Clear all rate-limit state (for testing)."""
    with _lock:
        _buckets.clear()
