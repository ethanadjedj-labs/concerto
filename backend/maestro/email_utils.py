import os

import httpx

_RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
_EMAIL_FROM = os.getenv("MAESTRO_EMAIL_FROM", os.getenv("EMAIL_FROM", "hello@maestro.run"))
_OPERATOR_EMAIL = os.getenv("OPERATOR_EMAIL", "adjedjethan@gmail.com")


async def send_email(to: str, subject: str, html: str) -> bool:
    if not _RESEND_API_KEY or not to:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {_RESEND_API_KEY}"},
                json={"from": _EMAIL_FROM, "to": [to], "subject": subject, "html": html},
            )
            return resp.status_code in (200, 201)
    except Exception:
        return False


async def send_operator_alert(subject: str, body: str) -> bool:
    return await send_email(
        _OPERATOR_EMAIL,
        f"[Maestro Alert] {subject}",
        f"<pre style='font-family:monospace;white-space:pre-wrap'>{body}</pre>",
    )
