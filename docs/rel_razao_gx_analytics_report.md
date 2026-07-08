# Relatório técnico — Single Source of Truth Rel_Razão G:X

## Fonte e persistência

A camada Analytics utiliza exclusivamente os campos normalizados de `FACT_ACCOUNTING_ENTRY`
originados das colunas G:X da worksheet `Rel_Razão`. A `FACT_DRE` permanece disponível para
estrutura, validação e reconciliação, mas seus valores não compõem KPIs, gráficos ou DRE visual.

Campos adicionados: empresa original, grupo, divisão, grupo DRE, centro de custo, mês, ano,
lote, lançamento, título, histórico, contrapartida, débito, crédito e valor original.

## Cálculos analíticos explícitos

- Receita Bruta: soma de `Valor` onde `DRE = Receita Bruta`.
- Deduções/Cancelamentos: soma assinada de `Valor` onde `DRE = Deduções de Vendas`.
- Receita Líquida: Receita Bruta + Deduções/Cancelamentos.
- EBITDA: Receita Líquida + grupos operacionais, excluindo patrimoniais, depreciação,
  resultado financeiro, equivalência patrimonial e IRPJ/CSLL.
- EBIT: EBITDA + Depreciação.
- Lucro antes do IRPJ/CSLL: EBIT + resultado financeiro + equivalência patrimonial.
- Lucro Líquido: lucro antes do IRPJ/CSLL + IRPJ/CSLL.
- Caixa: soma assinada das contas `1.1.1*`.

Essas fórmulas pertencem somente à camada Analytics. Financial Core, Rule Engine, DRE Engine
e Reconciliation não foram modificados.

## Validação da execução oficial

- Execução: `d5f3c8f2-15f5-4e63-be2f-0e6a80320186`
- Lançamentos na Rel_Razão: `27.972`
- Lançamentos persistidos: `27.972`
- Total Rel_Razão: `-R$ 1.410.855,82`
- Total `FACT_ACCOUNTING_ENTRY.amount`: `-R$ 1.410.855,82`
- Total `FACT_ACCOUNTING_ENTRY.source_value`: `-R$ 1.410.855,82`
- Diferença: `R$ 0,00`

Todos os 27.972 registros possuem AccountingDate, mês, ano, Company, Grupo, Division, DRE,
AccountDescription, AccountCode, CostCenter e Valor persistidos.
