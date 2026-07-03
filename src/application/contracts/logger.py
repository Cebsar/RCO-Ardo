from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ILogger(ABC):
    @abstractmethod
    def info(self, msg: str, *args: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def error(self, msg: str, *args: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def debug(self, msg: str, *args: Any) -> None:
        raise NotImplementedError
