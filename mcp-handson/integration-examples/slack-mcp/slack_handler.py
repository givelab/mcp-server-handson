import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from mcp import types

_client: WebClient | None = None


def get_client() -> WebClient:
    global _client
    if _client is None:
        token = os.environ.get("SLACK_BOT_TOKEN")
        if not token:
            raise RuntimeError("SLACK_BOT_TOKEN が設定されていません")
        _client = WebClient(token=token)
    return _client


async def dispatch_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "send_message":
            response = get_client().chat_postMessage(
                channel=arguments["channel"],
                text=arguments["message"]
            )
            return [types.TextContent(type="text", text=f"送信完了 (ts: {response['ts']})")]

        if name == "get_messages":
            response = get_client().conversations_history(
                channel=arguments["channel"],
                limit=arguments.get("limit", 10)
            )
            messages = response.get("messages", [])
            if not messages:
                return [types.TextContent(type="text", text="メッセージがありません")]
            lines = [f"[{m.get('ts', '')}] {m.get('user', 'unknown')}: {m.get('text', '')}" for m in messages]
            return [types.TextContent(type="text", text="\n".join(lines))]

        raise ValueError(f"Unknown tool: {name}")

    except SlackApiError as e:
        return [types.TextContent(type="text", text=f"Slack APIエラー: {e.response['error']}")]
    except RuntimeError as e:
        return [types.TextContent(type="text", text=str(e))]
