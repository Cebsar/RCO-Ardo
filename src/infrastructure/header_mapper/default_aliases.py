"""Default aliases for canonical header names."""
from typing import Dict, List

CANONICAL_FIELDS: List[str] = [
    "Company",
    "Division",
    "CostCenter",
    "AccountCode",
    "AccountDescription",
    "AccountingDate",
    "DocumentNumber",
    "History",
    "Debit",
    "Credit",
    "Balance",
]

DEFAULT_ALIASES: Dict[str, List[str]] = {
    "Company": ["company", "empresa", "comp"],
    "Division": ["division", "divisao", "dept", "department"],
    "CostCenter": ["costcenter", "cost_center", "centrocusto", "cc"],
    "AccountCode": ["accountcode", "account_code", "codigo", "account"],
    "AccountDescription": ["accountdescription", "account_description", "descricao", "description"],
    "AccountingDate": ["accountingdate", "date", "data", "postingdate"],
    "DocumentNumber": ["documentnumber", "docnumber", "document", "numero"],
    "History": ["history", "historico", "narrative"],
    "Debit": ["debit", "debito", "dr"],
    "Credit": ["credit", "credito", "cr"],
    "Balance": ["balance", "saldo", "bal"],
}
