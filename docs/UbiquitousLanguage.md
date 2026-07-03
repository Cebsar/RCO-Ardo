# Ubiquitous Language — ARDO Financial Analytics

This document standardizes terminology used across the codebase, documentation, and team conversations.

Core concepts

- Company: Legal entity that owns financial data. Identified by `CompanyCode`.
- Division: Organizational subdivision of a `Company`. Identified by `DivisionCode`.
- Cost Center: Operational unit used for cost tracking. Identified by `CostCenterCode`.
- Period: Accounting period with a `PeriodCode`, `start` and `end` dates.
- Account: Ledger account identified by `AccountCode` and typed by `AccountType`.
- Accounting Entry: Single ledger movement (`AccountingEntry`) with amount (`Money`), date, and `EntryType` (debit/credit).
- DRE (Demonstração do Resultado do Exercício): Profit & Loss structured as a tree of `DRENode` elements with levels (`DRELevel`).

Artifacts

- Master File: Source spreadsheet (binary artifact) containing raw accounting data.
- Warehouse: Canonical, cleaned SQLite storage snapshot used for downstream reporting.
- Presentation: Output artifacts (spreadsheets, PDFs) for stakeholders.

Architectural constraints

- Domain layer is the single source of truth for terminology and models.
- Application layer expresses use cases in domain terms and coordinates contracts.
- Infrastructure implements contracts but is not part of the ubiquitous language.
