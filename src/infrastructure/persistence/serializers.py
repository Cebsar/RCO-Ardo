from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Iterable


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "value") and isinstance(getattr(value, "value"), (str, int, float, bool)):
        return getattr(value, "value")
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if is_dataclass(value):
        return json_safe(asdict(value))
    return str(value)


def decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    if hasattr(value, "amount"):
        value = value.amount
    return Decimal(str(value))


def enum_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def account_code(entry: Any) -> str:
    return str(entry.account.code.value)


def flatten_dre_nodes(roots: Iterable[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def walk(node: Any, parent_code: str | None = None, ordinal: int = 0) -> None:
        amount = getattr(node, "amount", None)
        rule = getattr(node, "rule", None)
        rows.append(
            {
                "node_code": str(node.code.value),
                "node_name": str(node.name),
                "level": int(node.level),
                "amount": decimal_or_none(amount),
                "currency": getattr(amount, "currency", "BRL") if amount is not None else "BRL",
                "percentage": decimal_or_none(getattr(node, "percentage", None)),
                "parent_node_code": parent_code,
                "ordinal": ordinal,
                "rule_id": getattr(rule, "id", None) if rule is not None else None,
                "payload": json_safe(node),
            }
        )
        for child_index, child in enumerate(getattr(node, "children", ())):
            walk(child, str(node.code.value), child_index)

    for root_index, root in enumerate(roots):
        walk(root, None, root_index)
    return rows
