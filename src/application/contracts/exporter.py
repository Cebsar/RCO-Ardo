from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IExporter(ABC):
    @abstractmethod
    def export(self, data: Any, destination: str) -> None:
        raise NotImplementedError
