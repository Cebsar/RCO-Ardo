from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IValidator(ABC):
    @abstractmethod
    def validate(self, data: Any) -> bool:
        raise NotImplementedError
