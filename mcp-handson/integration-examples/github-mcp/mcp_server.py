import asyncio
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from github_handler import dispatch_tool

load_dotenv()

app = Server("github-mcp-example")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_issues",
            description="GitHubリポジトリのIssue一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "リポジトリオーナー名"},
                    "repo": {"type": "string", "description": "リポジトリ名"},
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "description": "Issueの状態",
                        "default": "open"
                    }
                },
                "required": ["owner", "repo"]
            }
        ),
        types.Tool(
            name="create_issue",
            description="GitHubリポジトリにIssueを作成する",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "リポジトリオーナー名"},
                    "repo": {"type": "string", "description": "リポジトリ名"},
                    "title": {"type": "string", "description": "Issueタイトル"},
                    "body": {"type": "string", "description": "Issue本文"}
                },
                "required": ["owner", "repo", "title", "body"]
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
