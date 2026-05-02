from mcp import types


async def dispatch_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "example_tool":
        return [types.TextContent(type="text", text=arguments["message"])]
    raise ValueError(f"Unknown tool: {name}")
