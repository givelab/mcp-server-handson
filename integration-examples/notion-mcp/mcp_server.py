import asyncio
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from notion_handler import dispatch_tool

load_dotenv()

app = Server("notion-mcp-example")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="create_page",
            description="Notionデータベースに新しいページを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "ページタイトル"},
                    "content": {"type": "string", "description": "本文テキスト"},
                    "parent_id": {"type": "string", "description": "親データベースのID"}
                },
                "required": ["title", "content", "parent_id"]
            }
        ),
        types.Tool(
            name="search",
            description="Notionワークスペース内を検索する",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "検索キーワード"}
                },
                "required": ["query"]
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
