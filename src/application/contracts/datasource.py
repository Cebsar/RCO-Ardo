from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, Any


class IDataSource(ABC):
    @abstractmethod
    def read(self, source: str) -> Any:  # intentionally generic
        raise NotImplementedError


class IDataSourceProtocol(Protocol):
    def read(self, source: str) -> Any: ...
