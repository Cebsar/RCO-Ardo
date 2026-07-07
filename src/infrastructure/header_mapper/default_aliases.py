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
    "Division": ["division", "divisao", "divisão", "dept", "department"],
    "CostCenter": ["costcenter", "cost_center", "centrocusto", "centro de custo", "cc"],
    "AccountCode": ["accountcode", "account_code", "codigo", "account", "contacontabil", "conta contabil", "conta contábil"],
    "AccountDescription": ["accountdescription", "account_description", "descricao", "description", "nomeconta", "nome conta"],
    "AccountingDate": ["accountingdate", "date", "data", "postingdate"],
    "DocumentNumber": ["documentnumber", "docnumber", "document", "numero", "lancamento", "lançamento"],
    "History": ["history", "historico", "hisorico", "histórico", "narrative"],
    "Debit": ["debit", "debito", "débito", "dr"],
    "Credit": ["credit", "credito", "crédito", "cr"],
    "Balance": ["balance", "saldo", "bal", "valor"],
}
