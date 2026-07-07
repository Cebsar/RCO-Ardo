from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from src.domain.entities import DRENode
from src.domain.enums import DRELevel
from src.domain.value_objects import AccountCode, Money
from .models import ExecutionMetrics, HierarchyReport, TraversalReport, TreeValidationReport
from .parser import ParsedHierarchyItem

logger = logging.getLogger(__name__)


@dataclass
class _BuildNode:
    item: ParsedHierarchyItem
    node: DRENode
    parent: "_BuildNode | None" = None
    children: List["_BuildNode"] = field(default_factory=list)


class HierarchyBuilder:
    def build(self, items: List[ParsedHierarchyItem], report: HierarchyReport) -> List[DRENode]:
        build_roots: List[_BuildNode] = []
        stack: List[_BuildNode] = []

        for item in items:
            build_node = _BuildNode(
                item=item,
                node=DRENode(
                code=AccountCode(item.code),
                name=item.label,
                level=DRELevel(item.level) if item.level in {level.value for level in DRELevel} else DRELevel.LEVEL_1,
                amount=Money(item.amount) if item.amount is not None else None,
                children=(),
                ),
            )
            if item.level == 1:
                build_roots.append(build_node)
                stack = [build_node]
                continue

            if not stack:
                report.add_warning(
                    f"Row {item.row_number} has level {item.level} without parent; promoting to root"
                )
                build_roots.append(build_node)
                stack = [build_node]
                continue

            while stack and stack[-1].item.level >= item.level:
                stack.pop()
            if not stack:
                report.add_warning(
                    f"Row {item.row_number} has level {item.level} without parent; promoting to root"
                )
                build_roots.append(build_node)
                stack = [build_node]
            else:
                parent = stack[-1]
                build_node.parent = parent
                parent.children.append(build_node)
                stack.append(build_node)

        roots = [self._materialize(root) for root in build_roots]
        self._attach_reports(build_roots, report)
        return roots

    def _materialize(self, build_node: _BuildNode) -> DRENode:
        children = tuple(self._materialize(child) for child in build_node.children)
        return DRENode(
            code=build_node.node.code,
            name=build_node.node.name,
            level=build_node.node.level,
            amount=build_node.node.amount,
            percentage=build_node.node.percentage,
            children=children,
            rule=build_node.node.rule,
        )

    def _attach_reports(self, roots: List[_BuildNode], report: HierarchyReport) -> None:
        traversal_order: List[str] = []
        parent_by_code: dict[str, str | None] = {}
        leaf_nodes = 0
        max_depth = 0

        def walk(node: _BuildNode, depth: int) -> None:
            nonlocal leaf_nodes, max_depth
            code = node.node.code.value
            traversal_order.append(code)
            parent_by_code[code] = node.parent.node.code.value if node.parent else None
            if not node.children:
                leaf_nodes += 1
            max_depth = max(max_depth, depth)
            for child in node.children:
                walk(child, depth + 1)

        for root in roots:
            walk(root, 1)

        warnings = tuple(report.warnings)
        is_valid = len(warnings) == 0
        report.tree_validation = TreeValidationReport(
            is_valid=is_valid,
            nodes_validated=len(traversal_order),
            root_nodes=len(roots),
            leaf_nodes=leaf_nodes,
            max_depth=max_depth,
            warnings=warnings,
            parent_by_code=parent_by_code,
        )
        report.traversal = TraversalReport(
            traversal_order=tuple(traversal_order),
            nodes_visited=len(traversal_order),
            deterministic=True,
            parent_by_code=parent_by_code,
        )
        report.execution_metrics = ExecutionMetrics(
            nodes_processed=len(traversal_order),
            max_depth=max_depth,
        )
