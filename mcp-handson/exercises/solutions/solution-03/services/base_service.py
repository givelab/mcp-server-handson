from abc import ABC, abstractmethod
import logging
from mcp import types

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, service: str, message: str, code: str | None = None):
        self.service = service
        self.code = code
        super().__init__(f"[{service}] {message}")


class BaseService(ABC):
    @property
    @abstractmethod
    def service_name(self) -> str:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @abstractmethod
    def get_tools(self) -> list[types.Tool]:
        ...

    @abstractmethod
    async def dispatch(self, name: str, arguments: dict) -> list[types.TextContent]:
        ...

    def _raise(self, message: str, code: str | None = None) -> None:
        raise ServiceError(self.service_name, message, code)
