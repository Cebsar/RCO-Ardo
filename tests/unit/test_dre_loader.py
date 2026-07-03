from datetime import date
from pathlib import Path
import tempfile

from openpyxl import Workbook

from src.infrastructure.dre_loader.builder import DRETreeBuilder
from src.infrastructure.dre_loader.reader import OverviewReader
from src.infrastructure.dre_loader.parser import HierarchyParser
from src.infrastructure.dre_loader.models import HierarchyReport


def test_overview_reader_reads_rows():
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "overview.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "Overview RCO"
        ws.append(["N1", "N2", "N3"])
        ws.append(["Revenue", None, None])
        ws.append([None, "Sales", None])
        ws.append([None, None, "Online"])
        wb.save(path)

        reader = OverviewReader(path=path)
        rows, report = reader.read()

        assert report.rows_read == 4
        assert rows[0]["col_1"] == "N1"
        assert rows[1]["col_1"] == "Revenue"


def test_hierarchy_parser_detects_levels():
    rows = [
        {"col_1": "N1", "col_2": "N2", "col_3": "N3", "_row_number": 1},
        {"col_1": "Revenue", "col_2": None, "col_3": None, "_row_number": 2},
        {"col_1": None, "col_2": "Sales", "col_3": None, "_row_number": 3},
        {"col_1": None, "col_2": None, "col_3": "Online", "_row_number": 4},
    ]
    parser = HierarchyParser(rows)
    items = parser.parse()

    assert len(items) == 3
    assert items[0].label == "Revenue" and items[0].level == 1
    assert items[1].label == "Sales" and items[1].level == 2
    assert items[2].label == "Online" and items[2].level == 3


def test_dre_tree_builder_preserves_hierarchy():
    rows = [
        {"col_1": "N1", "col_2": "N2", "col_3": "N3", "_row_number": 1},
        {"col_1": "Revenue", "col_2": None, "col_3": None, "_row_number": 2},
        {"col_1": None, "col_2": "Sales", "col_3": None, "_row_number": 3},
        {"col_1": None, "col_2": None, "col_3": "Online", "_row_number": 4},
    ]

    builder = DRETreeBuilder()
    tree, report = builder.build_from_rows(rows)

    assert report.nodes_count == 3
    assert report.root_nodes == 1
    assert len(tree.roots) == 1
    root = tree.roots[0]
    assert root.name == "Revenue"
    assert len(root.children) == 1
    assert root.children[0].name == "Sales"
    assert len(root.children[0].children) == 1
    assert root.children[0].children[0].name == "Online"


def test_dre_tree_builder_from_path_reads_source():
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "overview.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "Overview RCO"
        ws.append(["N1", "N2", "N3"])
        ws.append(["Revenue", None, None])
        ws.append([None, "Sales", None])
        wb.save(path)

        builder = DRETreeBuilder()
        tree, report = builder.build_from_path(path)

        assert report.rows_read == 3
        assert len(tree.roots) == 1
        assert tree.metadata["sheet_name"] == "Overview RCO"
