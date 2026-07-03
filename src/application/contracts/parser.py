from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Any

from src.application.dtos.masterfile_dto import MasterFileValidationResultDTO  # type: ignore


class IMasterFileParser(ABC):
    """Parser interface for the master file (Rel_Razão).

    Implementations must validate headers and provide parsed row streams.
    """

    @abstractmethod
    def validate_headers(self, headers: Iterable[str]) -> MasterFileValidationResultDTO:
        raise NotImplementedError

    @abstractmethod
    def parse_rows(self, source: str) -> Iterable[Any]:
        """Return an iterable of raw parsed rows (structure defined by DTOs).

        Implementations must not perform persistence.
        """
        raise NotImplementedError
