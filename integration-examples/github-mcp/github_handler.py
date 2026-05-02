import os
import httpx
from mcp import types

GITHUB_API_BASE = "https://api.github.com"


def get_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN が設定されていません")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


async def dispatch_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        headers = get_headers()

        if name == "list_issues":
            owner = arguments["owner"]
            repo = arguments["repo"]
            state = arguments.get("state", "open")
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                    headers=headers,
                    params={"state": state, "per_page": 20}
                )
            if resp.status_code == 404:
                return [types.TextContent(type="text", text=f"リポジトリ {owner}/{repo} が見つかりません")]
            if resp.status_code != 200:
                return [types.TextContent(type="text", text=f"APIエラー: {resp.status_code}")]
            issues = resp.json()
            if not issues:
                return [types.TextContent(type="text", text="Issueがありません")]
            lines = [f"#{i['number']}: {i['title']} ({i['state']})" for i in issues]
            return [types.TextContent(type="text", text="\n".join(lines))]

        if name == "create_issue":
            owner = arguments["owner"]
            repo = arguments["repo"]
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
                    headers=headers,
                    json={"title": arguments["title"], "body": arguments["body"]}
                )
            if resp.status_code not in (200, 201):
                return [types.TextContent(type="text", text=f"Issue作成失敗: {resp.status_code}")]
            issue = resp.json()
            return [types.TextContent(type="text", text=f"Issue作成完了: #{issue['number']} {issue['html_url']}")]

        raise ValueError(f"Unknown tool: {name}")

    except RuntimeError as e:
        return [types.TextContent(type="text", text=str(e))]
