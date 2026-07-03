from __future__ import annotations

from typing import Any


def read_cell(cell) -> Any:
    """Return raw cell.value without transformations."""
    return None if cell is None else getattr(cell, "value", None)
