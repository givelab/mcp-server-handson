import pytest
import respx
import httpx
from services.github_service import GitHubService


@pytest.fixture
def github_service(github_env):
    return GitHubService()


@pytest.mark.asyncio
@respx.mock
async def test_health_check_ok(github_service):
    respx.get("https://api.github.com/user").mock(return_value=httpx.Response(200, json={"login": "testuser"}))
    assert await github_service.health_check() is True


@pytest.mark.asyncio
@respx.mock
async def test_list_issues(github_service):
    respx.get("https://api.github.com/repos/test/repo/issues").mock(
        return_value=httpx.Response(200, json=[
            {"number": 1, "title": "テストIssue", "state": "open"}
        ])
    )
    result = await github_service.dispatch("github_list_issues", {"owner": "test", "repo": "repo"})
    assert "#1" in result[0].text
    assert "テストIssue" in result[0].text


@pytest.mark.asyncio
@respx.mock
async def test_list_issues_repo_not_found(github_service):
    respx.get("https://api.github.com/repos/notexist/repo/issues").mock(
        return_value=httpx.Response(404, json={})
    )
    from services.base_service import ServiceError
    with pytest.raises(ServiceError):
        await github_service.list_issues("notexist", "repo")
