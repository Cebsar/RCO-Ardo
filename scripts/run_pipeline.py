"""Run the ARDO ETL + rules + reconciliation pipeline."""
import argparse
from pathlib import Path
import logging

from src.execution.runner import PipelineRunner
from src.execution.configuration import ExecutionConfiguration
from src.infrastructure.excel.excel_adapter import ExcelAdapter
from src.infrastructure.header_mapper.mapper import HeaderMapper
from src.infrastructure.schema_validator.validator import SchemaValidator
from src.infrastructure.warehouse.builder import WarehouseBuilder
from src.infrastructure.dre_loader.builder import DRETreeBuilder
from src.infrastructure.business_rules.provider import BusinessRuleProvider
from src.infrastructure.rule_engine.engine import RuleEngine
from src.infrastructure.reconciliation.engine import ReconciliationEngine
from src.infrastructure.golden_dataset.comparators import GoldenDatasetComparator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ARDO financial analytics pipeline")
    parser.add_argument("--source", "-s", required=True, help="Source master Excel file path")
    parser.add_argument("--rules", "-r", default="config/business_rules.yaml", help="Business rules config path")
    parser.add_argument("--accounting-sheet", default="Rel_Razão", help="Accounting movements worksheet name")
    parser.add_argument("--dre-sheet", default="Overview RCO", help="DRE overview worksheet name")
    parser.add_argument("--golden-dir", default=None, help="Directory to save golden dataset manifest")
    parser.add_argument("--no-reconcile", dest="reconcile", action="store_false", help="Skip reconciliation stage")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logger = logging.getLogger("run_pipeline")

    source_path = Path(args.source)
    rules_path = Path(args.rules)
    golden_dir = Path(args.golden_dir) if args.golden_dir else None

    config = ExecutionConfiguration(
        source_path=source_path,
        rules_config_path=rules_path,
        accounting_sheet_name=args.accounting_sheet,
        dre_sheet_name=args.dre_sheet,
        golden_dataset_output_dir=golden_dir,
        enable_golden_dataset=bool(golden_dir),
    )

    excel_adapter = ExcelAdapter(path=str(source_path))
    header_mapper = HeaderMapper()
    schema_validator = SchemaValidator()
    warehouse_builder = WarehouseBuilder()
    dre_tree_builder = DRETreeBuilder()
    business_rule_provider = BusinessRuleProvider(config.rules_config_path)
    rule_engine = RuleEngine()
    reconciliation_engine = ReconciliationEngine() if args.reconcile else None
    golden_dataset_comparator = GoldenDatasetComparator() if golden_dir else None

    runner = PipelineRunner(
        excel_adapter=excel_adapter,
        header_mapper=header_mapper,
        schema_validator=schema_validator,
        warehouse_builder=warehouse_builder,
        dre_tree_builder=dre_tree_builder,
        business_rule_provider=business_rule_provider,
        rule_engine=rule_engine,
        reconciliation_engine=reconciliation_engine,
        golden_dataset_comparator=golden_dataset_comparator,
        logger=logger,
    )

    report = runner.run(config)

    logger.info("Pipeline finished: success=%s duration=%.3f seconds", report.success, report.duration_seconds)
    for stage in report.stage_results:
        logger.info("  stage=%s success=%s duration=%.3f errors=%s", stage.name, stage.success, stage.duration_seconds, stage.errors)

    if report.errors:
        logger.error("Pipeline completed with errors: %s", report.errors)
        raise SystemExit(1)

    if report.reconciliation:
        logger.info("Reconciliation mismatches=%s", report.reconciliation.reconciliation.mismatches)


if __name__ == "__main__":
    main()
