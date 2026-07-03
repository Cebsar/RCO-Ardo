from __future__ import annotations

from typing import Iterable

from src.domain.master_file_contract import validate_headers as domain_validate_headers


def validate(headers: Iterable[str]):
    """Validate headers using domain contract helper.

    Returns a simple object with lists: missing_columns, duplicated_columns, unexpected_columns
    """
    return domain_validate_headers(headers)
