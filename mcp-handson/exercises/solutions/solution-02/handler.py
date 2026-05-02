from mcp import types
from slack_integration import SlackClient, SlackError

_slack: SlackClient | None = None


def get_slack() -> SlackClient:
    global _slack
    if _slack is None:
        _slack = SlackClient()
    return _slack


async def handle_send_message(
    channel: str,
    message: str,
    thread_ts: str | None = None
) -> list[types.TextContent]:
    try:
        ts = get_slack().send_message(channel, message, thread_ts)
        return [types.TextContent(type="text", text=f"送信完了 (ts: {ts})")]
    except SlackError as e:
        return [types.TextContent(type="text", text=f"エラー: {e}")]


async def handle_get_messages(channel: str, limit: int = 10) -> list[types.TextContent]:
    try:
        messages = get_slack().get_messages(channel, limit)
        if not messages:
            return [types.TextContent(type="text", text="メッセージがありません")]
        lines = [f"[{m.timestamp}] {m.user}: {m.text}" for m in messages]
        return [types.TextContent(type="text", text="\n".join(lines))]
    except SlackError as e:
        return [types.TextContent(type="text", text=f"エラー: {e}")]


async def handle_list_channels() -> list[types.TextContent]:
    try:
        channels = get_slack().list_channels()
        if not channels:
            return [types.TextContent(type="text", text="チャンネルがありません")]
        lines = [f"#{ch['name']} (ID: {ch['id']})" for ch in channels]
        return [types.TextContent(type="text", text="\n".join(lines))]
    except SlackError as e:
        return [types.TextContent(type="text", text=f"エラー: {e}")]


async def dispatch_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "send_message":
        return await handle_send_message(
            arguments["channel"],
            arguments["message"],
            arguments.get("thread_ts")
        )
    if name == "get_messages":
        return await handle_get_messages(
            arguments["channel"],
            arguments.get("limit", 10)
        )
    if name == "list_channels":
        return await handle_list_channels()
    raise ValueError(f"Unknown tool: {name}")
