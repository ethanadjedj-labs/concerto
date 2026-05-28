import os
import re

from concerto.transactional import get_client

_OPERATOR_EMAIL = os.getenv("OPERATOR_EMAIL", "adjedjethan@gmail.com")

# Smoke-test mode: when CONCERTO_SUPPRESS_EMAILS_TO is set (comma-separated
# email patterns), customer-facing emails to matching addresses are silently
# dropped. Used by automated smoke tests against operator emails to avoid
# spamming the operator inbox.
#
# When NOT set (production default), all emails go out normally. So when YOU
# test manually via concerto.run with your real email, you receive every email
# a real customer would.
_SUPPRESS_PATTERN = os.getenv("CONCERTO_SUPPRESS_EMAILS_TO", "").strip()
_SUPPRESS_RE = re.compile(_SUPPRESS_PATTERN, re.IGNORECASE) if _SUPPRESS_PATTERN else None


async def _send_via_client(to: str, subject: str, html: str, text: str | None = None, *, _bypass_suppress: bool = False) -> bool:
    if not to:
        return False
    try:
        await get_client().send_async(to, subject, html, text, _bypass_suppress=_bypass_suppress)
        return True
    except Exception:
        return False


async def send_email(to: str, subject: str, html: str, text: str | None = None) -> bool:
    """Send a customer-facing email. Honors CONCERTO_SUPPRESS_EMAILS_TO."""
    if not to:
        return False
    if _SUPPRESS_RE and _SUPPRESS_RE.match(to.strip().lower()):
        return True  # smoke-test mode: silently drop
    return await _send_via_client(to, subject, html, text)


async def send_operator_alert(subject: str, body: str) -> bool:
    """System alerts to the operator always go through, regardless of suppress."""
    return await _send_via_client(
        _OPERATOR_EMAIL,
        f"[Concerto Alert] {subject}",
        f"<pre style='font-family:monospace;white-space:pre-wrap'>{body}</pre>",
        text=body,
        _bypass_suppress=True,
    )
