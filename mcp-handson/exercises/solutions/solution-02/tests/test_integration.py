import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.environ.get("SLACK_BOT_TOKEN"),
    reason="SLACK_BOT_TOKEN が未設定のためスキップ"
)

TEST_CHANNEL = os.environ.get("SLACK_TEST_CHANNEL", "#mcp-test")


@pytest.mark.asyncio
async def test_real_list_channels():
    from handler import handle_list_channels
    result = await handle_list_channels()
    assert "エラー" not in result[0].text


@pytest.mark.asyncio
async def test_real_send_message():
    from handler import handle_send_message
    result = await handle_send_message(TEST_CHANNEL, "MCPハンズオン課題2 統合テスト")
    assert "送信完了" in result[0].text


@pytest.mark.asyncio
async def test_real_get_messages():
    from handler import handle_get_messages
    result = await handle_get_messages(TEST_CHANNEL, 5)
    assert "エラー" not in result[0].text
