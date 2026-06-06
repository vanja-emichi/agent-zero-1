"""Base classes for A0 Connector v1 API handlers.

CSRF posture:
    Both PublicConnectorApiHandler and ProtectedConnectorApiHandler bypass CSRF
    protection (requires_csrf() returns False). This is intentional: connector
    endpoints are designed for CLI localhost clients that authenticate via session
    cookies but cannot easily provide a CSRF token (programmatic API consumers).

    The csrf_exempt = True class attribute documents this exemption explicitly
    so that security audits and future contributors can see the decision at a
    glance without tracing through the requires_csrf() override chain.

    Mitigations in place:
    - Session authentication is required on all protected endpoints.
    - Startup warning fires when connector endpoints are reachable from
      non-localhost origins (see hooks.py).
    - Per-IP rate limiting for non-localhost callers enforced on every
      protected request (see helpers.csrf_posture).
"""
from __future__ import annotations

from flask import Request, Response

from helpers.api import ApiHandler


class PublicConnectorApiHandler(ApiHandler):
    # CSRF exempt: public discovery endpoint, no state mutation.
    # Only used by Capabilities handler to advertise features to connecting CLIs.
    csrf_exempt: bool = True

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False


class ProtectedConnectorApiHandler(ApiHandler):
    # CSRF exempt: these endpoints serve the A0 CLI running on localhost.
    # CLI clients authenticate via session but cannot send CSRF tokens in
    # programmatic JSON API calls. All endpoints are POST-based and require
    # an authenticated session. When the server is exposed beyond localhost,
    # startup warnings and per-IP rate limiting apply.
    csrf_exempt: bool = True

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    async def handle_request(self, request: Request) -> Response:
        """Enforce per-IP rate limiting before processing protected requests."""
        from plugins._a0_connector.helpers.csrf_posture import check_rate_limit

        remote_ip = str(request.remote_addr or "")
        if not check_rate_limit(remote_ip):
            return Response(
                response='{"error": "Rate limit exceeded"}',
                status=429,
                mimetype="application/json",
            )
        return await super().handle_request(request)
