from mcp import types


async def handle_add(a: float, b: float) -> list[types.TextContent]:
    result = a + b
    return [types.TextContent(type="text", text=str(result))]


async def handle_multiply(a: float, b: float) -> list[types.TextContent]:
    result = a * b
    return [types.TextContent(type="text", text=str(result))]


async def handle_divide(a: float, b: float) -> list[types.TextContent]:
    if b == 0:
        raise ValueError("ゼロ除算は不可です")
    result = a / b
    return [types.TextContent(type="text", text=str(result))]


async def dispatch_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "add":
        return await handle_add(arguments["a"], arguments["b"])
    if name == "multiply":
        return await handle_multiply(arguments["a"], arguments["b"])
    if name == "divide":
        return await handle_divide(arguments["a"], arguments["b"])
    raise ValueError(f"Unknown tool: {name}")
