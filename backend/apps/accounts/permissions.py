"""Authorisation primitives.

Controllers declare permissions; view bodies do not make authorisation
decisions. The default across the API is deny, and anything public says so
explicitly with AllowAny.

`IsInternalService` is the Phase 0 stand-in for real, revocable API keys owned
by this app's `ApiKey` model in Phase 2. It is deliberately narrow: a shared
secret compared in constant time, and nothing else.
"""

from __future__ import annotations

import hmac

from django.conf import settings
from ninja_extra.permissions import BasePermission

INTERNAL_KEY_HEADER = "X-Internal-Key"


class IsInternalService(BasePermission):
    """Allows requests carrying a configured internal service key."""

    message = "A valid X-Internal-Key header is required for this endpoint."

    def has_permission(self, request, controller) -> bool:
        presented = request.headers.get(INTERNAL_KEY_HEADER, "")
        if not presented:
            return False
        configured = getattr(settings, "INTERNAL_API_KEYS", []) or []
        # compare_digest against every configured key: constant time per key,
        # and no early exit that would leak which key matched.
        return any(hmac.compare_digest(presented, key) for key in configured)
