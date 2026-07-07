# -*- coding: utf-8 -*-
"""02_quality_audit.py — Spec 02: auditoria de qualidade de dados.

Roda os checks do contrato (docs/data_contract.md) sobre as bases brutas
(lidas via src/io.py) e as processadas principais (data/processed/*.parquet)
e grava outputs/tables/data_quality_report.csv.

Este script MEDE e REPORTA. Ele não corrige, não transforma e não regrava
nenhum dado de origem. FAILs no relatório não derrubam a execução (o
produto é o relatório); dado obrigatório AUSENTE derruba (falhar cedo).

Nota de nomenclatura: o prefixo "02_" coexiste com src/02_estoque_projetado.py
(legado). O SDD.MD exige exatamente este nome; o prefixo numérico dos scripts
legados não é ordem de execução do novo pipeline.

Uso:
    python src/02_quality_audit.py
"""

import importlib.util
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORT_PATH = ROOT / "outputs" / "tables" / "data_quality_report.csv"

# src/ no path para importar o pacote validation (io.py vai via importlib
# porque o nome colide com o módulo stdlib `io`)
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation import quality_checks as qc  # noqa: E402
from validation import schemas  # noqa: E402

logger = logging.getLogger("quality_audit")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _h.setFormatter(logging.Formatter("[%(name)s] %(levelname)s %(message)s"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)


def _load_io_module():
    """Carrega src/io.py sem colidir com o módulo stdlib `io`."""
    spec = importlib.util.spec_from_file_location("projeto_io", SRC / "io.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read_processed(name: str) -> pd.DataFrame:
    path = PROCESSED_DIR / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Tabela processada obrigatória ausente: {path}")
    return pd.read_parquet(path)


def run_quality_audit(report_path: Path | str | None = None) -> pd.DataFrame:
    """Executa todos os checks e grava o relatório. Retorna o DataFrame do relatório."""
    report_path = Path(report_path) if report_path is not None else REPORT_PATH

    pio = _load_io_module()
    logging.getLogger("ingestao").setLevel(logging.WARNING)
    frames, _ = pio.read_all_raw()

    vendas = frames["fato_vendas"]
    compras = frames["fato_compras"]
    estoque = frames["fato_estoque_inicial"]
    produto = frames["dim_produto"]
    lojas = frames["dim_lojas"]
    precos = frames["dim_precos"]
    voltagem = frames["dim_voltagem"]
    unidades = frames["dim_unidades"]

    records: list[dict] = []

    # ------------------------------------------------------------------
    # 1) Estrutura, tipos e grão (todas as brutas)
    # ------------------------------------------------------------------
    for name, df in frames.items():
        expected = pio.FILE_SPECS[name].expected_columns
        records.append(qc.check_expected_columns(df, expected, name))
        records.append(qc.check_schema(name, df))
        records.append(qc.check_duplicate_grain(df, schemas.EXPECTED_GRAIN[name], name))

    # ------------------------------------------------------------------
    # 2) Datas (validade e período)
    # ------------------------------------------------------------------
    for name, df, col in [("fato_vendas", vendas, "DATA_VENDA"),
                          ("fato_compras", compras, "DATA_ENTRADA")]:
        records.append(qc.check_valid_dates(df, col, name))
        records.append(qc.check_dates_in_period(
            df, col, name, schemas.PERIOD_START, schemas.PERIOD_END))

    # ------------------------------------------------------------------
    # 3) Nulos críticos e estruturais (contrato decide a criticidade)
    # ------------------------------------------------------------------
    records.append(qc.check_critical_nulls(
        compras, "PRECO_UNIT_UNIDADE_COMPRA", "fato_compras",
        status_if_present="FAIL", severidade="critica",
        impacto="9,5% das compras sem preço: CMV/custo médio não pode ser calculado "
                "sem regra explícita de imputação; qualquer análise de custo fica inválida",
        acao="definir regra explícita (excluir, imputar com fonte, ou bloquear análise de custo)",
    ))
    records.append(qc.check_critical_nulls(
        produto, "CD_VOLTAGEM", "dim_produto",
        status_if_present="WARN", severidade="media",
        impacto="contrato distingue 0='sem voltagem' de vazio=dado faltante; "
                "48 produtos sem informação de voltagem (não equiparar a 0)",
        acao="completar cadastro; não imputar 0 silenciosamente",
    ))
    records.append(qc.check_critical_nulls(
        unidades, "COD_IBGE", "dim_unidades",
        status_if_present="WARN", severidade="baixa",
        impacto="1 unidade (EB) sem código IBGE; sem impacto nas métricas atuais",
        acao="completar cadastro se a unidade for usada",
    ))
    records.append(qc.check_critical_nulls(
        compras, "EMBALAGEM_FORNECEDOR", "fato_compras",
        status_if_present="WARN", severidade="baixa",
        impacto="1 compra sem embalagem do fornecedor; grão da tabela usa esta coluna",
        acao="confirmar embalagem na origem",
    ))
    records.append(qc.check_structural_nulls(
        produto, "EMBALAGEM_VENDA_1", "dim_produto",
        "embalagem especial 1 não existe para ~2/3 dos produtos"))
    records.append(qc.check_structural_nulls(
        produto, "EMBALAGEM_VENDA_2", "dim_produto",
        "embalagem especial 2 não existe para ~2/3 dos produtos"))
    records.append(qc.check_structural_nulls(
        precos, "PRECO_EMBALAGEM_1", "dim_precos",
        "sem preço porque a embalagem especial 1 não existe para o par produto x loja"))
    records.append(qc.check_structural_nulls(
        precos, "PRECO_EMBALAGEM_2", "dim_precos",
        "sem preço porque a embalagem especial 2 não existe para o par produto x loja"))
    records.append(qc.check_structural_nulls(
        produto, "EMBALAGEM_FORNECEDOR", "dim_produto",
        "59 produtos sem embalagem de fornecedor cadastrada"))

    # ------------------------------------------------------------------
    # 4) Integridade referencial (órfãos)
    # ------------------------------------------------------------------
    for name, df in [("fato_vendas", vendas), ("fato_compras", compras),
                     ("fato_estoque_inicial", estoque), ("dim_precos", precos)]:
        records.append(qc.check_orphans(df, "CODIGO", produto, "CODIGO", name, "dim_produto"))
        records.append(qc.check_orphans(df, "COD_EMPRESA", lojas, "COD_EMPRESA", name, "dim_lojas"))
    records.append(qc.check_orphans(
        voltagem, "CD_EMPRESA", lojas, "COD_EMPRESA", "dim_voltagem", "dim_lojas"))
    records.append(qc.check_orphans(
        vendas, "UNIDADE_DA_VENDA", unidades, "COD_UNIDADE", "fato_vendas", "dim_unidades"))
    records.append(qc.check_orphans(
        compras, "UNIDADE_ESTOQUE", unidades, "COD_UNIDADE", "fato_compras", "dim_unidades"))

    # ------------------------------------------------------------------
    # 5) Quantidades e preços (negativos e zeros)
    # ------------------------------------------------------------------
    records.append(qc.check_negative_values(
        vendas, "QUANTIDADE_VENDIDA", "fato_vendas",
        "quantidade negativa em venda inverte receita e quantidade"))
    records.append(qc.check_negative_values(
        compras, "QUANTIDADE_COMPRA", "fato_compras",
        "quantidade negativa em compra inverte o balanço de entradas"))
    records.append(qc.check_negative_values(
        estoque, "ESTOQUE_INICIAL", "fato_estoque_inicial",
        "estoque inicial negativo é impossível fisicamente"))
    records.append(qc.check_negative_values(
        vendas, "PRECO_UNIT_MEDIO", "fato_vendas",
        "preço negativo inverte receita"))
    records.append(qc.check_negative_values(
        compras, "PRECO_UNIT_UNIDADE_COMPRA", "fato_compras",
        "preço de compra negativo corrompe custo"))
    for col in ["PRECO_EMBALAGEM_0", "PRECO_EMBALAGEM_1", "PRECO_EMBALAGEM_2"]:
        records.append(qc.check_negative_values(
            precos, col, "dim_precos", "preço de tabela negativo corrompe análises de preço"))

    records.append(qc.check_zero_values(
        vendas, "QUANTIDADE_VENDIDA", "fato_vendas",
        status_if_present="FAIL", severidade="alta",
        impacto="linha de venda com quantidade 0 não é venda",
        acao="investigar origem"))
    records.append(qc.check_zero_values(
        compras, "QUANTIDADE_COMPRA", "fato_compras",
        status_if_present="FAIL", severidade="alta",
        impacto="compra com quantidade 0 não é entrada",
        acao="investigar origem"))
    records.append(qc.check_zero_values(
        vendas, "PRECO_UNIT_MEDIO", "fato_vendas",
        status_if_present="WARN", severidade="alta",
        impacto="preço médio 0 zera receita da linha (doação? erro?)",
        acao="investigar origem"))
    records.append(qc.check_zero_values(
        estoque, "ESTOQUE_INICIAL", "fato_estoque_inicial",
        status_if_present="WARN", severidade="media",
        impacto="47,6% dos pares com estoque inicial exatamente 0: zero explícito na origem; "
                "não confundir com ausência de registro (nulo de estoque não é estoque zero), "
                "mas zero em massa pode ser posição não inventariada",
        acao="confirmar com o negócio se 0 é posição real ou falta de inventário"))
    records.append(qc.check_zero_values(
        precos, "PRECO_EMBALAGEM_1", "dim_precos",
        status_if_present="WARN", severidade="media",
        impacto="preço 0 em embalagem especial cadastrada distorce comparações de preço",
        acao="tratar 0 como 'sem preço válido' nas análises de preço (regra explícita)"))
    records.append(qc.check_zero_values(
        precos, "PRECO_EMBALAGEM_2", "dim_precos",
        status_if_present="WARN", severidade="media",
        impacto="preço 0 em embalagem especial cadastrada distorce comparações de preço",
        acao="tratar 0 como 'sem preço válido' nas análises de preço (regra explícita)"))

    # ------------------------------------------------------------------
    # 6) Completude temporal
    # ------------------------------------------------------------------
    records.append(qc.check_months_without(
        vendas, "DATA_VENDA", "fato_vendas", "2024-01", "2025-12", "vendas"))
    records.append(qc.check_months_without(
        compras, "DATA_ENTRADA", "fato_compras", "2024-01", "2025-12", "compras"))

    # ------------------------------------------------------------------
    # 7) Cobertura da base de compras e reconciliação vendas x entradas
    # ------------------------------------------------------------------
    records.append(qc.check_purchase_coverage_stores(compras, lojas))
    records.append(qc.check_purchase_coverage_products(compras, produto))
    records.append(qc.check_sold_without_inflows(vendas, estoque, compras, produto))
    records.append(qc.check_sales_exceed_inflows(vendas, estoque, compras, produto))

    # ------------------------------------------------------------------
    # 8) Consistência de unidades e domínios auxiliares
    # ------------------------------------------------------------------
    records.append(qc.check_sale_unit_consistency(vendas, produto))
    records.append(qc.check_purchase_unit_difference(produto))
    records.append(qc.check_purchases_needing_conversion(compras, produto))
    records.append(qc.check_digito_consistency(vendas, produto))
    records.append(qc.check_voltagem_domain(produto, voltagem))

    # ------------------------------------------------------------------
    # 9) Tabelas processadas principais
    # ------------------------------------------------------------------
    fv_proc = _read_processed("fato_vendas")
    records.append(qc.check_schema("fato_vendas_processed", fv_proc, tabela="fato_vendas_processed"))
    records.append(qc.check_duplicate_grain(
        fv_proc, schemas.EXPECTED_GRAIN["fato_vendas"], "fato_vendas_processed"))
    records.append(qc.check_revenue_consistency(fv_proc, "fato_vendas_processed"))

    estoque_diario = _read_processed("estoque_diario")
    records.append(qc.check_schema("estoque_diario", estoque_diario))
    records.append(qc.check_negative_balance(estoque_diario, "SALDO_ESTOQUE", "estoque_diario"))

    estoque_final = _read_processed("estoque_final_projetado")
    records.append(qc.check_schema("estoque_final_projetado", estoque_final))
    records.append(qc.check_negative_balance(
        estoque_final, "ESTOQUE_FINAL_PROJETADO", "estoque_final_projetado"))

    cobertura = _read_processed("cobertura_estoque")
    records.append(qc.check_schema("cobertura_estoque", cobertura))

    # ------------------------------------------------------------------
    # Relatório
    # ------------------------------------------------------------------
    report = pd.DataFrame.from_records(records, columns=qc.REPORT_COLUMNS)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(report_path, index=False, encoding="utf-8")

    counts = report["status"].value_counts()
    logger.info("Relatório gravado em %s", report_path)
    logger.info(
        "%d checks: %d PASS, %d WARN, %d FAIL",
        len(report), counts.get("PASS", 0), counts.get("WARN", 0), counts.get("FAIL", 0),
    )
    for _, row in report[report["status"] == "FAIL"].iterrows():
        logger.warning("FAIL [%s] %s: %s", row["tabela"], row["check"], row["descricao"])
    return report


if __name__ == "__main__":
    run_quality_audit()
