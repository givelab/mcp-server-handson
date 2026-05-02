import pytest
from unittest.mock import MagicMock
from slack_integration import SlackError, SlackMessage


@pytest.fixture
def mock_slack(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr("handler._slack", mock)
    return mock


@pytest.mark.asyncio
async def test_send_message_success(mock_slack):
    mock_slack.send_message.return_value = "1234567890.123456"

    from handler import handle_send_message
    result = await handle_send_message("#general", "テストメッセージ")

    assert "1234567890.123456" in result[0].text
    mock_slack.send_message.assert_called_once_with("#general", "テストメッセージ", None)


@pytest.mark.asyncio
async def test_send_message_channel_not_found(mock_slack):
    mock_slack.send_message.side_effect = SlackError("チャンネルが見つかりません: #nonexistent")

    from handler import handle_send_message
    result = await handle_send_message("#nonexistent", "test")

    assert "エラー" in result[0].text


@pytest.mark.asyncio
async def test_get_messages_success(mock_slack):
    mock_slack.get_messages.return_value = [
        SlackMessage(user="U123", text="Hello", timestamp="1234567890.000001"),
        SlackMessage(user="U456", text="World", timestamp="1234567890.000002"),
    ]

    from handler import handle_get_messages
    result = await handle_get_messages("#general", 2)

    assert "Hello" in result[0].text
    assert "World" in result[0].text


@pytest.mark.asyncio
async def test_get_messages_empty(mock_slack):
    mock_slack.get_messages.return_value = []

    from handler import handle_get_messages
    result = await handle_get_messages("#general")

    assert "メッセージがありません" in result[0].text


@pytest.mark.asyncio
async def test_list_channels_success(mock_slack):
    mock_slack.list_channels.return_value = [
        {"id": "C001", "name": "general"},
        {"id": "C002", "name": "random"},
    ]

    from handler import handle_list_channels
    result = await handle_list_channels()

    assert "general" in result[0].text
    assert "random" in result[0].text


@pytest.mark.asyncio
async def test_dispatch_unknown_tool(mock_slack):
    from handler import dispatch_tool
    with pytest.raises(ValueError, match="Unknown tool"):
        await dispatch_tool("nonexistent", {})
