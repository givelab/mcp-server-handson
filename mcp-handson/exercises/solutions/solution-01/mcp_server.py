import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from handler import dispatch_tool

app = Server("calculator-mcp")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="add",
            description="2つの数値を加算して結果を返す",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "1つ目の数値"},
                    "b": {"type": "number", "description": "2つ目の数値"}
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="multiply",
            description="2つの数値を乗算して結果を返す",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "1つ目の数値"},
                    "b": {"type": "number", "description": "2つ目の数値"}
                },
                "required": ["a", "b"]
            }
        ),
        types.Tool(
            name="divide",
            description="aをbで割った結果を返す（ゼロ除算は不可）",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "被除数"},
                    "b": {"type": "number", "description": "除数（0以外）"}
                },
                "required": ["a", "b"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    return await dispatch_tool(name, arguments)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
