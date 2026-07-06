from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from time import perf_counter
from typing import Dict, Iterable, List, Optional, Tuple

from src.domain.master_file_contract import REQUIRED_COLUMNS

from .default_aliases import CANONICAL_FIELDS, DEFAULT_ALIASES

logger = logging.getLogger(__name__)


def _normalize(text: Optional[str]) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = text.strip()
    # remove diacritics
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    # lowercase and remove non-alphanumeric
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


@dataclass(frozen=True)
class HeaderMapping:
    # mapping from original header string to canonical field (or None)
    mapping: Dict[str, Optional[str]]
    # canonical -> list of matched original headers
    canonical_to_headers: Dict[str, List[str]]
    duplicates: List[str]
    missing_required: List[str]
    unmatched_headers: List[str]
    execution_time_seconds: float = 0.0


@dataclass
class HeaderMappingResult:
    header_mapping: HeaderMapping


class HeaderMapper:
    """Map raw headers to canonical ARDO fields using aliases.

    Usage:
        mapper = HeaderMapper(aliases=custom_aliases)
        result = mapper.map(headers)
    """

    def __init__(self, aliases: Optional[Dict[str, List[str]]] = None):
        # build alias map normalized -> canonical
        self.aliases = aliases or DEFAULT_ALIASES
        self._norm_to_canonical: Dict[str, str] = {}
        for canonical in CANONICAL_FIELDS:
            # include canonical name itself
            self._norm_to_canonical[_normalize(canonical)] = canonical
            for a in self.aliases.get(canonical, []):
                self._norm_to_canonical[_normalize(a)] = canonical

    def map(self, headers: Iterable[Optional[str]]) -> HeaderMapping:
        start = perf_counter()
        headers_list = [h for h in headers]
        mapping: Dict[str, Optional[str]] = {}
        canonical_to_headers: Dict[str, List[str]] = {c: [] for c in CANONICAL_FIELDS}
        unmatched: List[str] = []

        for h in headers_list:
            h_raw = h if h is not None else ""
            norm = _normalize(h_raw)
            if norm == "":
                mapping[h_raw] = None
                unmatched.append(h_raw)
                continue
            canonical = self._norm_to_canonical.get(norm)
            if canonical:
                mapping[h_raw] = canonical
                canonical_to_headers[canonical].append(h_raw)
            else:
                mapping[h_raw] = None
                unmatched.append(h_raw)

        duplicates = [c for c, lst in canonical_to_headers.items() if len(lst) > 1]
        missing_required = [
            c
            for c in REQUIRED_COLUMNS
            if len(canonical_to_headers.get(c, [])) == 0
        ]

        duration = perf_counter() - start
        logger.info("Header mapping completed in %.6f seconds: %d headers mapped, %d unmatched", duration, len(headers_list), len(unmatched))

        return HeaderMapping(
            mapping=mapping,
            canonical_to_headers={k: v for k, v in canonical_to_headers.items() if v},
            duplicates=duplicates,
            missing_required=missing_required,
            unmatched_headers=unmatched,
            execution_time_seconds=duration,
        )
