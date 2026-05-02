import os
import httpx
from mcp import types
from .base_service import BaseService

NOTION_API_BASE = "https://api.notion.com/v1"


class NotionService(BaseService):
    service_name = "notion"

    def __init__(self):
        token = os.environ.get("NOTION_TOKEN")
        if not token:
            raise RuntimeError("NOTION_TOKEN が設定されていません")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{NOTION_API_BASE}/users/me", headers=self._headers)
                return resp.status_code == 200
        except Exception:
            return False

    async def create_page(self, title: str, content: str, parent_id: str) -> str:
        payload = {
            "parent": {"database_id": parent_id},
            "properties": {
                "title": {"title": [{"type": "text", "text": {"content": title}}]}
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    }
                }
            ]
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{NOTION_API_BASE}/pages", headers=self._headers, json=payload)
        if resp.status_code != 200:
            self._raise(f"ページ作成失敗: {resp.json().get('message', resp.status_code)}")
        return resp.json()["id"]

    async def get_page(self, page_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{NOTION_API_BASE}/pages/{page_id}", headers=self._headers)
        if resp.status_code == 404:
            self._raise(f"ページが見つかりません: {page_id}", "page_not_found")
        if resp.status_code != 200:
            self._raise(f"ページ取得失敗: {resp.status_code}")
        return resp.json()

    async def search(self, query: str) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{NOTION_API_BASE}/search",
                headers=self._headers,
                json={"query": query, "page_size": 10}
            )
        if resp.status_code != 200:
            self._raise(f"検索失敗: {resp.status_code}")
        return resp.json().get("results", [])

    def get_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="notion_create_page",
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
                name="notion_get_page",
                description="NotionページをIDで取得する",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "page_id": {"type": "string", "description": "NotionページID"}
                    },
                    "required": ["page_id"]
                }
            ),
            types.Tool(
                name="notion_search",
                description="Notionワークスペース内のページを検索する",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "検索キーワード"}
                    },
                    "required": ["query"]
                }
            )
        ]

    async def dispatch(self, name: str, arguments: dict) -> list[types.TextContent]:
        if name == "notion_create_page":
            page_id = await self.create_page(
                arguments["title"],
                arguments["content"],
                arguments["parent_id"]
            )
            return [types.TextContent(type="text", text=f"ページ作成完了 (ID: {page_id})")]
        if name == "notion_get_page":
            page = await self.get_page(arguments["page_id"])
            title_prop = page.get("properties", {}).get("title", {})
            title_list = title_prop.get("title", [])
            title = title_list[0]["text"]["content"] if title_list else "（タイトルなし）"
            return [types.TextContent(type="text", text=f"ページタイトル: {title}\nID: {page['id']}")]
        if name == "notion_search":
            results = await self.search(arguments["query"])
            if not results:
                return [types.TextContent(type="text", text="検索結果がありません")]
            lines = [f"- {r.get('id', '')} ({r.get('object', '')})" for r in results]
            return [types.TextContent(type="text", text="\n".join(lines))]
        raise ValueError(f"Unknown Notion tool: {name}")
