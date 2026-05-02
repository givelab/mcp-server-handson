import asyncio
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from handler import dispatch_tool

load_dotenv()

app = Server("my-mcp-server")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="example_tool",
            description="サンプルツール：引数をそのまま返す",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "返すメッセージ"}
                },
                "required": ["message"]
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
