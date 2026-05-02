import asyncio
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from handler import dispatch_tool

load_dotenv()

app = Server("slack-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="send_message",
            description="Slackチャンネルにメッセージを送信する",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "#general 形式のチャンネル名"},
                    "message": {"type": "string", "description": "送信するテキスト"},
                    "thread_ts": {"type": "string", "description": "スレッドに返信する場合のタイムスタンプ（任意）"}
                },
                "required": ["channel", "message"]
            }
        ),
        types.Tool(
            name="get_messages",
            description="チャンネルの最新メッセージを取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "#general 形式のチャンネル名"},
                    "limit": {"type": "integer", "description": "取得件数（1〜100、デフォルト10）", "default": 10}
                },
                "required": ["channel"]
            }
        ),
        types.Tool(
            name="list_channels",
            description="参加しているパブリックチャンネルの一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    return await dispatch_tool(name, arguments)


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
