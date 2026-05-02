import pytest
import respx
import httpx
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
@respx.mock
async def test_github_to_notion_workflow(github_env, notion_env, slack_env):
    """GitHubのIssueをNotionに記録してSlackに通知するワークフロー"""
    respx.get("https://api.github.com/repos/test/repo/issues").mock(
        return_value=httpx.Response(200, json=[
            {"number": 42, "title": "バグ報告", "state": "open", "html_url": "https://github.com/test/repo/issues/42"}
        ])
    )
    respx.post("https://api.notion.com/v1/pages").mock(
        return_value=httpx.Response(200, json={"id": "notion-page-999"})
    )

    from services.github_service import GitHubService
    from services.notion_service import NotionService

    github = GitHubService()
    notion = NotionService()

    github_result = await github.dispatch("github_list_issues", {"owner": "test", "repo": "repo"})
    assert "#42" in github_result[0].text

    notion_result = await notion.dispatch("notion_create_page", {
        "title": "Issue #42: バグ報告",
        "content": github_result[0].text,
        "parent_id": "fake-db-id"
    })
    assert "notion-page-999" in notion_result[0].text


@pytest.mark.asyncio
async def test_service_unavailable_does_not_affect_others(github_env, notion_env, slack_env):
    """Slackが落ちてもGitHubは動き続ける"""
    from services.github_service import GitHubService
    from services.slack_service import SlackService

    with patch("slack_sdk.WebClient"):
        slack = SlackService()
        slack._client.auth_test.side_effect = Exception("Slack down")

    with respx.mock:
        respx.get("https://api.github.com/user").mock(return_value=httpx.Response(200, json={"login": "u"}))
        github = GitHubService()
        assert await slack.health_check() is False
        assert await github.health_check() is True
