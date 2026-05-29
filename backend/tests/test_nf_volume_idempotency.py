"""Regression tests for Northflank volume-already-exists handling.

The NF API has returned both 409 (documented) and 400 with "already exists"
in the body (observed 2026-05-21 production behaviour). Both must be treated
as idempotent reuse, not errors — otherwise re-provision fails on the first
step and the buyer is left stranded.
"""
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

from concerto.provider_northflank import _create_volume


def _mock_response(status_code: int, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.raise_for_status.side_effect = (
        httpx.HTTPStatusError(
            f"HTTP {status_code}",
            request=MagicMock(),
            response=MagicMock(status_code=status_code),
        )
        if status_code >= 400
        else None
    )
    return resp


@pytest.mark.asyncio
async def test_create_volume_201_succeeds():
    client = AsyncMock()
    client.post = AsyncMock(return_value=_mock_response(201))
    await _create_volume(client, "cvol-abc123", "concerto-abc123")
    client.post.assert_called_once()


@pytest.mark.asyncio
async def test_create_volume_200_succeeds():
    client = AsyncMock()
    client.post = AsyncMock(return_value=_mock_response(200))
    await _create_volume(client, "cvol-abc123", "concerto-abc123")
    client.post.assert_called_once()


@pytest.mark.asyncio
async def test_create_volume_409_is_idempotent():
    """NF 409 = volume already exists → reuse silently, don't abort provision."""
    client = AsyncMock()
    client.post = AsyncMock(return_value=_mock_response(409))
    await _create_volume(client, "cvol-abc123", "concerto-abc123")  # must not raise


@pytest.mark.asyncio
async def test_create_volume_400_already_exists_is_idempotent():
    """NF 400 + 'already exists' body = idempotent reuse (observed production drift)."""
    client = AsyncMock()
    body = '{"error":{"message":"Volume already exists"}}'
    client.post = AsyncMock(return_value=_mock_response(400, text=body))
    await _create_volume(client, "cvol-abc123", "concerto-abc123")  # must not raise


@pytest.mark.asyncio
async def test_create_volume_400_other_raises():
    """400 not about 'already exists' must propagate — it's a real API error."""
    client = AsyncMock()
    resp = _mock_response(400, text='{"error":{"message":"Invalid spec"}}')
    client.post = AsyncMock(return_value=resp)
    with pytest.raises(httpx.HTTPStatusError):
        await _create_volume(client, "cvol-abc123", "concerto-abc123")


@pytest.mark.asyncio
async def test_create_volume_500_raises():
    """Server errors must propagate so provisioning aborts and alerts fire."""
    client = AsyncMock()
    resp = _mock_response(500, text="Internal server error")
    client.post = AsyncMock(return_value=resp)
    with pytest.raises(httpx.HTTPStatusError):
        await _create_volume(client, "cvol-abc123", "concerto-abc123")
