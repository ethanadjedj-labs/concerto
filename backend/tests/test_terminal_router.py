"""Tests for terminal_router helpers (F1, F2, F3 findings)."""
import sys
import os

# Allow importing from backend/concerto without installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from concerto.terminal_router import _ttyd_ws_url, _basic_auth_header, _CSP_FRAME_ANCESTORS
import base64


def test_ttyd_ws_url_https():
    """F1: HTTPS ttyd URL converts to WSS with /ws appended."""
    url = _ttyd_ws_url("https://abc-123.trycloudflare.com/terminal")
    assert url == "wss://abc-123.trycloudflare.com/terminal/ws"


def test_ttyd_ws_url_http():
    """F1: HTTP ttyd URL converts to WS with /ws appended."""
    url = _ttyd_ws_url("http://127.0.0.1:7681")
    assert url == "ws://127.0.0.1:7681/ws"


def test_ttyd_ws_url_strips_trailing_slash():
    """F1: Trailing slash is stripped before /ws is appended."""
    url = _ttyd_ws_url("https://abc.trycloudflare.com/terminal/")
    assert url == "wss://abc.trycloudflare.com/terminal/ws"


def test_basic_auth_header_format():
    """F2: Basic Auth header is correctly base64-encoded."""
    header = _basic_auth_header("s3cr3t")
    assert header.startswith("Basic ")
    decoded = base64.b64decode(header[6:]).decode()
    assert decoded == "concerto:s3cr3t"


def test_basic_auth_header_empty_password():
    """F2: Empty password still produces valid Basic Auth header."""
    header = _basic_auth_header("")
    assert header.startswith("Basic ")
    decoded = base64.b64decode(header[6:]).decode()
    assert decoded == "concerto:"


def test_csp_frame_ancestors_includes_concerto_run():
    """F3: CSP header covers production domain."""
    assert "https://concerto.run" in _CSP_FRAME_ANCESTORS


def test_csp_frame_ancestors_includes_vercel():
    """F3: CSP header covers Vercel preview deployments."""
    assert "https://*.vercel.app" in _CSP_FRAME_ANCESTORS
