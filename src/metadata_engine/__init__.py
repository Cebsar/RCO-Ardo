"""Metadata engine package: extracts metadata from Excel workbooks."""
from .extractor import MetadataExtractor
from .models import WorkbookMetadata, WorksheetMetadata, ColumnMetadata, NamedRangeMetadata

__all__ = ["MetadataExtractor", "WorkbookMetadata", "WorksheetMetadata", "ColumnMetadata", "NamedRangeMetadata"]
