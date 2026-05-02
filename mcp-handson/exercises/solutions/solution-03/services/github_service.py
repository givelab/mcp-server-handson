import os
import httpx
from mcp import types
from .base_service import BaseService

GITHUB_API_BASE = "https://api.github.com"


class GitHubService(BaseService):
    service_name = "github"

    def __init__(self):
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN が設定されていません")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{GITHUB_API_BASE}/user", headers=self._headers)
                return resp.status_code == 200
        except Exception:
            return False

    async def list_issues(self, owner: str, repo: str, state: str = "open") -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                headers=self._headers,
                params={"state": state, "per_page": 20}
            )
        if resp.status_code == 404:
            self._raise(f"リポジトリ {owner}/{repo} が見つかりません", "repo_not_found")
        if resp.status_code != 200:
            self._raise(f"Issue取得失敗: {resp.status_code}")
        return resp.json()

    async def create_issue(self, owner: str, repo: str, title: str, body: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                headers=self._headers,
                json={"title": title, "body": body}
            )
        if resp.status_code not in (200, 201):
            self._raise(f"Issue作成失敗: {resp.status_code}")
        return resp.json()

    async def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=self._headers
            )
        if resp.status_code == 404:
            self._raise(f"PR #{pr_number} が見つかりません", "pr_not_found")
        if resp.status_code != 200:
            self._raise(f"PR取得失敗: {resp.status_code}")
        return resp.json()

    def get_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="github_list_issues",
                description="GitHubリポジトリのIssue一覧を取得する",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "リポジトリオーナー名"},
                        "repo": {"type": "string", "description": "リポジトリ名"},
                        "state": {
                            "type": "string",
                            "enum": ["open", "closed", "all"],
                            "description": "Issueの状態（デフォルト: open）",
                            "default": "open"
                        }
                    },
                    "required": ["owner", "repo"]
                }
            ),
            types.Tool(
                name="github_create_issue",
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
            ),
            types.Tool(
                name="github_get_pr",
                description="GitHubのPull Requestを番号で取得する",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "リポジトリオーナー名"},
                        "repo": {"type": "string", "description": "リポジトリ名"},
                        "pr_number": {"type": "integer", "description": "PR番号"}
                    },
                    "required": ["owner", "repo", "pr_number"]
                }
            )
        ]

    async def dispatch(self, name: str, arguments: dict) -> list[types.TextContent]:
        if name == "github_list_issues":
            issues = await self.list_issues(
                arguments["owner"],
                arguments["repo"],
                arguments.get("state", "open")
            )
            if not issues:
                return [types.TextContent(type="text", text="Issueがありません")]
            lines = [f"#{i['number']}: {i['title']} ({i['state']})" for i in issues]
            return [types.TextContent(type="text", text="\n".join(lines))]
        if name == "github_create_issue":
            issue = await self.create_issue(
                arguments["owner"],
                arguments["repo"],
                arguments["title"],
                arguments["body"]
            )
            return [types.TextContent(type="text", text=f"Issue作成完了: #{issue['number']} {issue['html_url']}")]
        if name == "github_get_pr":
            pr = await self.get_pr(arguments["owner"], arguments["repo"], arguments["pr_number"])
            return [types.TextContent(
                type="text",
                text=f"PR #{pr['number']}: {pr['title']}\n状態: {pr['state']}\nURL: {pr['html_url']}"
            )]
        raise ValueError(f"Unknown GitHub tool: {name}")
