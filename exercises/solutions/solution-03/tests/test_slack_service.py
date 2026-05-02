import pytest
from unittest.mock import MagicMock, patch
from services.base_service import ServiceError


@pytest.fixture
def slack_service(slack_env):
    with patch("slack_sdk.WebClient"):
        from services.slack_service import SlackService
        return SlackService()


@pytest.mark.asyncio
async def test_health_check_ok(slack_service):
    slack_service._client.auth_test.return_value = {"ok": True}
    assert await slack_service.health_check() is True


@pytest.mark.asyncio
async def test_health_check_fail(slack_service):
    slack_service._client.auth_test.side_effect = Exception("network error")
    assert await slack_service.health_check() is False


@pytest.mark.asyncio
async def test_dispatch_send_message(slack_service):
    slack_service._client.chat_postMessage.return_value = {"ts": "1234567890.000001"}
    result = await slack_service.dispatch("slack_send_message", {"channel": "#general", "message": "hello"})
    assert "送信完了" in result[0].text


@pytest.mark.asyncio
async def test_dispatch_unknown_tool(slack_service):
    with pytest.raises(ValueError):
        await slack_service.dispatch("slack_unknown", {})
