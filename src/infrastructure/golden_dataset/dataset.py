from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import GoldenDRE, GoldenFactAccounting, GoldenOverview, GoldenWorkbook
from .utilities import compute_dataset_hash, format_dataset_version, write_json


def _serialize_path(path: Path) -> str:
    return path.as_posix()


@dataclass(frozen=True)
class DatasetManifest:
    version: str
    created_at: datetime
    dataset_hash: str
    source_paths: Dict[str, str]
    artifacts: Dict[str, str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RegressionReport:
    generated_at: datetime
    dataset_version: str
    dataset_hash: str
    summary: Dict[str, Any]
    failures: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GoldenDataset:
    workbook: GoldenWorkbook
    overview: GoldenOverview
    fact_accounting: GoldenFactAccounting
    dre: GoldenDRE
    manifest: DatasetManifest

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workbook": {
                "path": _serialize_path(self.workbook.path),
                "fingerprint": self.workbook.fingerprint,
                "row_count": self.workbook.row_count,
                "columns": self.workbook.columns,
                "metadata": self.workbook.metadata,
            },
            "overview": {
                "source": self.overview.source,
                "generated_at": self.overview.generated_at.isoformat(),
                "entries": self.overview.entries,
                "metadata": self.overview.metadata,
            },
            "fact_accounting": {
                "source": self.fact_accounting.source,
                "generated_at": self.fact_accounting.generated_at.isoformat(),
                "records": self.fact_accounting.records,
                "metadata": self.fact_accounting.metadata,
            },
            "dre": {
                "source": self.dre.source,
                "generated_at": self.dre.generated_at.isoformat(),
                "nodes": self.dre.nodes,
                "metadata": self.dre.metadata,
            },
            "manifest": {
                "version": self.manifest.version,
                "created_at": self.manifest.created_at.isoformat(),
                "dataset_hash": self.manifest.dataset_hash,
                "source_paths": self.manifest.source_paths,
                "artifacts": self.manifest.artifacts,
                "metadata": self.manifest.metadata,
            },
        }

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        manifest_path = directory / "golden_dataset_manifest.json"
        write_json(manifest_path, self.to_dict())

    @classmethod
    def build(
        cls,
        workbook: GoldenWorkbook,
        overview: GoldenOverview,
        fact_accounting: GoldenFactAccounting,
        dre: GoldenDRE,
        version: str,
        source_paths: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "GoldenDataset":
        metadata = metadata or {}
        payload = {
            "workbook": {
                "path": _serialize_path(workbook.path),
                "fingerprint": workbook.fingerprint,
                "row_count": workbook.row_count,
                "columns": workbook.columns,
                "metadata": workbook.metadata,
            },
            "overview": {
                "source": overview.source,
                "generated_at": overview.generated_at.isoformat(),
                "entries": overview.entries,
                "metadata": overview.metadata,
            },
            "fact_accounting": {
                "source": fact_accounting.source,
                "generated_at": fact_accounting.generated_at.isoformat(),
                "records": fact_accounting.records,
                "metadata": fact_accounting.metadata,
            },
            "dre": {
                "source": dre.source,
                "generated_at": dre.generated_at.isoformat(),
                "nodes": dre.nodes,
                "metadata": dre.metadata,
            },
        }
        dataset_hash = compute_dataset_hash(payload)
        manifest = DatasetManifest(
            version=version,
            created_at=datetime.utcnow(),
            dataset_hash=dataset_hash,
            source_paths=source_paths,
            artifacts={
                "workbook": _serialize_path(workbook.path),
                "overview": overview.source,
                "fact_accounting": fact_accounting.source,
                "dre": dre.source,
            },
            metadata=metadata,
        )
        return cls(workbook=workbook, overview=overview, fact_accounting=fact_accounting, dre=dre, manifest=manifest)
