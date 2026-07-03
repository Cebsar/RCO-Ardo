from __future__ import annotations

from typing import Iterable, List


def map_headers(headers: Iterable[str]) -> List[str]:
    """Map headers from raw cell values to normalized header strings.

    This function performs minimal normalization (strip) but does not alter semantic names.
    """
    return [h.strip() if isinstance(h, str) else "" for h in headers]
