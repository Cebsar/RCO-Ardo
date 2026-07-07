from __future__ import annotations

import logging
from time import perf_counter
from typing import List, Tuple

from .models import DRETree, HierarchyReport
from .parser import HierarchyParser
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
        report.metadata["row_classifications"] = getattr(parser, "row_classifications", {})
        report.metadata["hidden_rows"] = [
            int(row.get("_row_number", 0))
            for row in rows
            if row.get("_hidden")
        ]
        report.metadata["formula_rows"] = [
            int(row.get("_row_number", 0))
            for row in rows
            if row.get("_formulas")
        ]

        builder = HierarchyBuilder()
        roots = builder.build(parsed_items, report)
        report.nodes_count = len(parsed_items)
        report.root_nodes = len(roots)
        report.max_level = max((item.level for item in parsed_items), default=0)
        report.execution_time_seconds = perf_counter() - start
        if report.execution_metrics is not None:
            report.execution_metrics = type(report.execution_metrics)(
                nodes_processed=report.execution_metrics.nodes_processed,
                max_depth=report.execution_metrics.max_depth,
                execution_time_seconds=report.execution_time_seconds,
            )
        logger.info("Built DRE tree with %d nodes in %.6f seconds", report.nodes_count, report.execution_time_seconds)
        tree = DRETree(
            roots=tuple(roots),
            metadata={
                "source_rows": len(rows),
                "row_classifications": report.metadata["row_classifications"],
                "hidden_rows": report.metadata["hidden_rows"],
                "formula_rows": report.metadata["formula_rows"],
            },
        )
        return tree, report

    def build_from_path(self, path, sheet_name: str = "Overview RCO") -> Tuple[DRETree, HierarchyReport]:
        from .reader import OverviewReader

        reader = OverviewReader(path=path, sheet_name=sheet_name)
        rows, reader_report = reader.read()
        tree, report = self.build_from_rows(rows)
        report.rows_read = reader_report.rows_read
        report.metadata["sheet_name"] = sheet_name
        tree = DRETree(
            roots=tree.roots,
            source=tree.source,
            metadata={**tree.metadata, "sheet_name": sheet_name},
        )
        return tree, report
