from __future__ import annotations

import logging
from typing import List

from src.domain.entities import DRENode
from src.domain.enums import DRELevel
from src.domain.value_objects import AccountCode
from .models import HierarchyReport
from .parser import ParsedHierarchyItem

logger = logging.getLogger(__name__)


class HierarchyBuilder:
    def build(self, items: List[ParsedHierarchyItem], report: HierarchyReport) -> List[DRENode]:
        roots: List[DRENode] = []
        stack: List[DRENode] = []

        for item in items:
            node = DRENode(
                code=AccountCode(item.code),
                name=item.label,
                level=DRELevel(item.level) if item.level in {1, 2, 3} else DRELevel.LEVEL_1,
                amount=None,
                children=(),
            )
            if item.level == 1 or not stack:
                roots.append(node)
                stack = [node]
                continue

            while stack and stack[-1].level >= node.level:
                stack.pop()
            if not stack:
                report.add_warning(
                    f"Row {item.row_number} has level {item.level} without parent; promoting to root"
                )
                roots.append(node)
                stack = [node]
            else:
                parent = stack[-1]
                parent.children = (*parent.children, node)
                stack.append(node)

        return roots
