from __future__ import annotations

import logging
from time import perf_counter
from typing import List, Optional, Tuple

from src.domain.entities import DRENode
from src.domain.enums import DRELevel
from src.domain.value_objects import AccountCode
from .models import DRETree, HierarchyReport
from .parser import HierarchyParser, ParsedHierarchyItem
from .hierarchy_builder import HierarchyBuilder

logger = logging.getLogger(__name__)


class DRETreeBuilder:
    def __init__(self, rows: List[dict] | None = None):
        self.rows = rows or []

    def build_from_rows(self, rows: List[dict]) -> Tuple[DRETree, HierarchyReport]:
        start = perf_counter()
        parser = HierarchyParser(rows)
        parsed_items = parser.parse()
        report = HierarchyReport(rows_read=len(rows))

        builder = HierarchyBuilder()
        roots = builder.build(parsed_items, report)
        report.nodes_count = len(parsed_items)
        report.root_nodes = len(roots)
        report.max_level = max((item.level for item in parsed_items), default=0)
        report.execution_time_seconds = perf_counter() - start
        logger.info("Built DRE tree with %d nodes in %.6f seconds", report.nodes_count, report.execution_time_seconds)
        tree = DRETree(roots=tuple(roots), metadata={"source_rows": len(rows)})
        return tree, report

    def build_from_path(self, path, sheet_name: str = "Overview RCO") -> Tuple[DRETree, HierarchyReport]:
        from .reader import OverviewReader

        reader = OverviewReader(path=path, sheet_name=sheet_name)
        rows, reader_report = reader.read()
        tree, report = self.build_from_rows(rows)
        report.rows_read = reader_report.rows_read
        report.metadata["sheet_name"] = sheet_name
        return tree, report

    def _build_tree(self, items: List[ParsedHierarchyItem], report: HierarchyReport) -> List[DRENode]:
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
            else:
                while stack and stack[-1].level >= node.level:
                    stack.pop()
                if not stack:
                    report.add_warning(f"Row {item.row_number} has level {item.level} without parent; promoting to root")
                    roots.append(node)
                    stack = [node]
                else:
                    parent = stack[-1]
                    parent.children = (*parent.children, node)
                    stack.append(node)
        return roots
