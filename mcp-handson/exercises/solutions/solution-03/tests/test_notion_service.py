import pytest
import respx
import httpx
from services.notion_service import NotionService


@pytest.fixture
def notion_service(notion_env):
    return NotionService()


@pytest.mark.asyncio
@respx.mock
async def test_health_check_ok(notion_service):
    respx.get("https://api.notion.com/v1/users/me").mock(return_value=httpx.Response(200, json={}))
    assert await notion_service.health_check() is True


@pytest.mark.asyncio
@respx.mock
async def test_health_check_fail(notion_service):
    respx.get("https://api.notion.com/v1/users/me").mock(return_value=httpx.Response(401, json={}))
    assert await notion_service.health_check() is False


@pytest.mark.asyncio
@respx.mock
async def test_search(notion_service):
    respx.post("https://api.notion.com/v1/search").mock(
        return_value=httpx.Response(200, json={"results": [{"id": "page-1", "object": "page"}]})
    )
    result = await notion_service.dispatch("notion_search", {"query": "テスト"})
    assert "page-1" in result[0].text
