"""Remove credentials from URLs and messages before they are stored, served or logged.

Request URLs are kept as provenance (and exported in reports), so a connector that ever puts a key
in the query string (e.g. a future authenticated FRED/ALFRED client) must not leak it through the
database, the API or a downloaded report.
"""

from __future__ import annotations

import re

_SECRET_PARAM = re.compile(
    r"(?i)(?P<lead>[?&;]|\b)(?P<name>api_key|apikey|api-key|access_token|token|key|password|secret)"
    r"=(?P<value>[^&#\s'\"]+)"
)
_URL_USERINFO = re.compile(r"(?i)\b(?P<scheme>[a-z][a-z0-9+.-]*://)(?P<user>[^:/@\s]+):[^@/\s]+@")
REDACTED = "REDACTED"


def redact_secrets(text: str | None) -> str | None:
    """Mask secret query parameters and URL passwords.

    `...&api_key=abc123` -> `...&api_key=REDACTED`; `scheme://user:pw@host` -> `user:REDACTED@`.
    """
    if text is None:
        return None
    text = _SECRET_PARAM.sub(lambda m: f"{m['lead']}{m['name']}={REDACTED}", text)
    return _URL_USERINFO.sub(lambda m: f"{m['scheme']}{m['user']}:{REDACTED}@", text)
