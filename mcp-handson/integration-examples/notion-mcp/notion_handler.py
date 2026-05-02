import os
import httpx
from mcp import types

NOTION_API_BASE = "https://api.notion.com/v1"


def get_headers() -> dict:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN が設定されていません")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }


async def dispatch_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        headers = get_headers()

        if name == "create_page":
            payload = {
                "parent": {"database_id": arguments["parent_id"]},
                "properties": {
                    "title": {"title": [{"type": "text", "text": {"content": arguments["title"]}}]}
                },
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": arguments["content"]}}]
                        }
                    }
                ]
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{NOTION_API_BASE}/pages", headers=headers, json=payload)
            if resp.status_code != 200:
                return [types.TextContent(type="text", text=f"エラー: {resp.json().get('message', resp.status_code)}")]
            return [types.TextContent(type="text", text=f"ページ作成完了 (ID: {resp.json()['id']})")]

        if name == "search":
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{NOTION_API_BASE}/search",
                    headers=headers,
                    json={"query": arguments["query"], "page_size": 10}
                )
            results = resp.json().get("results", [])
            if not results:
                return [types.TextContent(type="text", text="検索結果がありません")]
            lines = [f"- {r.get('id', '')} ({r.get('object', '')})" for r in results]
            return [types.TextContent(type="text", text="\n".join(lines))]

        raise ValueError(f"Unknown tool: {name}")

    except RuntimeError as e:
        return [types.TextContent(type="text", text=str(e))]
