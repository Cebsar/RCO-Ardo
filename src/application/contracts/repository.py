from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional


class IRepository(ABC):
    @abstractmethod
    def get(self, id: Any) -> Optional[Any]:
        raise NotImplementedError

    @abstractmethod
    def list(self, *args: Any, **kwargs: Any) -> Iterable[Any]:
        raise NotImplementedError

    @abstractmethod
    def save(self, obj: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, id: Any) -> None:
        raise NotImplementedError
