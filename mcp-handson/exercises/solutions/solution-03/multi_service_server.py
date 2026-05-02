import asyncio
import logging
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from services import SlackService, NotionService, GitHubService
from services.base_service import BaseService, ServiceError
from utils.logger import setup_logger

load_dotenv()
logger = setup_logger("mcp-server")


class ServiceRegistry:
    def __init__(self):
        self._services: dict[str, BaseService] = {}

    def register(self, service: BaseService) -> None:
        self._services[service.service_name] = service
        logger.info(f"{service.service_name} サービスを登録しました")

    def get(self, name: str) -> BaseService | None:
        return self._services.get(name)

    async def get_available_tools(self) -> list[types.Tool]:
        tools = []
        for service in self._services.values():
            try:
                if await service.health_check():
                    tools.extend(service.get_tools())
                else:
                    logger.warning(f"{service.service_name} は利用不可 - ツールをスキップ")
            except Exception:
                logger.exception(f"{service.service_name} のヘルスチェックで例外発生")
        return tools


registry = ServiceRegistry()

for svc_class in [SlackService, NotionService, GitHubService]:
    try:
        registry.register(svc_class())
    except RuntimeError as e:
        logger.warning(f"サービス初期化スキップ: {e}")

app = Server("multi-service-mcp")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return await registry.get_available_tools()


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    service_prefix = name.split("_")[0]
    service = registry.get(service_prefix)

    if service is None:
        return [types.TextContent(type="text", text=f"サービス '{service_prefix}' は登録されていません")]

    try:
        return await service.dispatch(name, arguments)
    except ServiceError as e:
        logger.error(f"サービスエラー: {e}")
        return [types.TextContent(type="text", text=f"サービスエラー ({e.service}): {e}")]
    except Exception:
        logger.exception(f"予期しないエラー: tool={name}")
        return [types.TextContent(type="text", text="予期しないエラーが発生しました")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
