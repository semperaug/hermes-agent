"""Shared helpers for canonicalising WhatsApp sender identity.

The implementation moved to :mod:`session_rules.whatsapp_identity` so that the
neutral package's own session-key builder can canonicalise WhatsApp aliases
exactly the way the gateway does. A neutral module may not import the
application package, so the shared code had to live on the neutral side.

This module re-exports it; every existing caller keeps working unchanged.
"""

from __future__ import annotations

from session_rules.whatsapp_identity import (
    canonical_whatsapp_identifier,
    expand_whatsapp_aliases,
    normalize_whatsapp_identifier,
    normalize_whatsapp_mention_jid,
    to_whatsapp_jid,
)

__all__ = [
    "canonical_whatsapp_identifier",
    "expand_whatsapp_aliases",
    "normalize_whatsapp_identifier",
    "normalize_whatsapp_mention_jid",
    "to_whatsapp_jid",
]
