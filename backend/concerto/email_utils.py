import os

from concerto.transactional import get_client

_OPERATOR_EMAIL = os.getenv("OPERATOR_EMAIL", "adjedjethan@gmail.com")


async def send_email(to: str, subject: str, html: str, text: str | None = None) -> bool:
    if not to:
        return False
    try:
        await get_client().send_async(to, subject, html, text)
        return True
    except Exception:
        return False


async def send_operator_alert(subject: str, body: str) -> bool:
    return await send_email(
        _OPERATOR_EMAIL,
        f"[Concerto Alert] {subject}",
        f"<pre style='font-family:monospace;white-space:pre-wrap'>{body}</pre>",
        text=body,
    )
