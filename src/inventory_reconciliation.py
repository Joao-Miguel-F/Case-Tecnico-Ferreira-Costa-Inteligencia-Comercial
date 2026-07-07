# -*- coding: utf-8 -*-
"""Inventory, purchase, and unit reconciliation for Spec 04.

This module builds a new auditable reconciliation layer. It does not rewrite
legacy stock outputs and does not infer physical stock-outs from negative
projected balances.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

import metrics


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES_DIR = ROOT / "outputs" / "tables"

CONFIDENCE_CLASSES = {
    "OK",
    "suspeito",
    "crítico",
    "não confiável para análise causal",
}

GAP_CAUSES = (
    "compra ausente; transferencia nao capturada; ajuste de inventario ausente; "
    "devolucao nao modelada; falha de extracao; erro de unidade; "
    "estoque inicial incompleto; erro de data; indisponibilidade operacional nao validada"
)

PURCHASE_STORAGE_FORMULA = (
    "QTD_COMPRA_ESTOQUE = QUANTIDADE_COMPRA * CONVERSAO_COMPRA_ARMAZENAGEM"
)
SALES_STORAGE_FORMULA = (
    "QTD_VENDA_ESTOQUE = QUANTIDADE_VENDIDA * CONVERSAO_VENDA_PARA_ARMAZENAGEM"
)


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{name}: colunas obrigatorias ausentes: {missing}")


def with_purchase_storage_quantity(compras: pd.DataFrame, produtos: pd.DataFrame) -> pd.DataFrame:
    """Return purchases with explicit quantity in storage units."""
    _require_columns(compras, {"CODIGO", "QUANTIDADE_COMPRA"}, "compras")
    _require_columns(produtos, {"CODIGO", "CONVERSAO_COMPRA_ARMAZENAGEM"}, "produtos")

    conversion = produtos[["CODIGO", "CONVERSAO_COMPRA_ARMAZENAGEM"]].drop_duplicates("CODIGO")
    out = compras.copy().merge(conversion, on="CODIGO", how="left", validate="many_to_one")

    if out["CONVERSAO_COMPRA_ARMAZENAGEM"].isna().any():
        missing = out.loc[out["CONVERSAO_COMPRA_ARMAZENAGEM"].isna(), "CODIGO"].drop_duplicates().tolist()
        raise ValueError(f"compras sem conversao de compra cadastrada: {missing[:10]}")

    conversion_values = _to_number(out["CONVERSAO_COMPRA_ARMAZENAGEM"])
    if conversion_values.le(0).any() or conversion_values.isna().any():
        raise ValueError("CONVERSAO_COMPRA_ARMAZENAGEM deve ser numerica e maior que zero")

    out["QTD_COMPRA_ESTOQUE"] = (
        _to_number(out["QUANTIDADE_COMPRA"]).fillna(0) * conversion_values
    )
    return out


def with_sales_storage_quantity(vendas: pd.DataFrame, tolerance: float = 0.000001) -> pd.DataFrame:
    """Return sales with explicit quantity in storage units, validating if already present."""
    _require_columns(
        vendas,
        {"QUANTIDADE_VENDIDA", "CONVERSAO_VENDA_PARA_ARMAZENAGEM"},
        "vendas",
    )

    out = vendas.copy()
    calculated = (
        _to_number(out["QUANTIDADE_VENDIDA"]).fillna(0)
        * _to_number(out["CONVERSAO_VENDA_PARA_ARMAZENAGEM"]).fillna(0)
    )

    if "QTD_VENDA_ESTOQUE" in out.columns:
        existing = _to_number(out["QTD_VENDA_ESTOQUE"])
        divergence = (existing - calculated).abs().fillna(0)
        if divergence.gt(tolerance).any():
            raise ValueError("QTD_VENDA_ESTOQUE diverge da formula documentada")
    else:
        out["QTD_VENDA_ESTOQUE"] = calculated

    return out


def build_movement_ledger(
    vendas: pd.DataFrame,
    compras: pd.DataFrame,
    estoque_inicial: pd.DataFrame,
    produtos: pd.DataFrame,
) -> pd.DataFrame:
    """Build daily accounting movements with purchases and sales in storage units."""
    vendas = with_sales_storage_quantity(vendas)
    compras = with_purchase_storage_quantity(compras, produtos)

    _require_columns(vendas, {"COD_EMPRESA", "CODIGO", "DATA_VENDA", "QTD_VENDA_ESTOQUE"}, "vendas")
    _require_columns(
        compras,
        {"COD_EMPRESA", "CODIGO", "DATA_ENTRADA", "QTD_COMPRA_ESTOQUE"},
        "compras",
    )
    _require_columns(estoque_inicial, {"COD_EMPRESA", "CODIGO", "ESTOQUE_INICIAL"}, "estoque_inicial")

    compras_diarias = (
        compras.groupby(["COD_EMPRESA", "CODIGO", "DATA_ENTRADA"], dropna=False)["QTD_COMPRA_ESTOQUE"]
        .sum()
        .reset_index()
        .rename(columns={"DATA_ENTRADA": "DATA"})
    )
    vendas_diarias = (
        vendas.groupby(["COD_EMPRESA", "CODIGO", "DATA_VENDA"], dropna=False)["QTD_VENDA_ESTOQUE"]
        .sum()
        .reset_index()
        .rename(columns={"DATA_VENDA": "DATA"})
    )

    movements = compras_diarias.merge(
        vendas_diarias,
        on=["COD_EMPRESA", "CODIGO", "DATA"],
        how="outer",
    )
    if movements.empty:
        data_inicio = pd.Timestamp("2024-01-01")
    else:
        data_inicio = pd.to_datetime(movements["DATA"]).min()

    movements["QTD_COMPRA_ESTOQUE"] = _to_number(movements["QTD_COMPRA_ESTOQUE"]).fillna(0)
    movements["QTD_VENDA_ESTOQUE"] = _to_number(movements["QTD_VENDA_ESTOQUE"]).fillna(0)
    movements["ESTOQUE_INICIAL_EVENTO"] = 0.0
    movements["VARIACAO_CONTABIL"] = (
        movements["QTD_COMPRA_ESTOQUE"] - movements["QTD_VENDA_ESTOQUE"]
    )

    initial = estoque_inicial.copy()
    initial["DATA"] = data_inicio - pd.Timedelta(days=1)
    initial["QTD_COMPRA_ESTOQUE"] = 0.0
    initial["QTD_VENDA_ESTOQUE"] = 0.0
    initial["ESTOQUE_INICIAL_EVENTO"] = _to_number(initial["ESTOQUE_INICIAL"])
    initial["VARIACAO_CONTABIL"] = initial["ESTOQUE_INICIAL_EVENTO"]
    initial = initial[
        [
            "COD_EMPRESA",
            "CODIGO",
            "DATA",
            "QTD_COMPRA_ESTOQUE",
            "QTD_VENDA_ESTOQUE",
            "ESTOQUE_INICIAL_EVENTO",
            "VARIACAO_CONTABIL",
        ]
    ]

    ledger = pd.concat(
        [
            initial,
            movements[
                [
                    "COD_EMPRESA",
                    "CODIGO",
                    "DATA",
                    "QTD_COMPRA_ESTOQUE",
                    "QTD_VENDA_ESTOQUE",
                    "ESTOQUE_INICIAL_EVENTO",
                    "VARIACAO_CONTABIL",
                ]
            ],
        ],
        ignore_index=True,
    )
    ledger = ledger.sort_values(["COD_EMPRESA", "CODIGO", "DATA"])
    ledger["SALDO_PROJETADO_CONTABIL"] = ledger.groupby(["COD_EMPRESA", "CODIGO"], dropna=False)[
        "VARIACAO_CONTABIL"
    ].cumsum()
    ledger["EVENTO_SALDO_PROJETADO_NEGATIVO"] = ledger["SALDO_PROJETADO_CONTABIL"].lt(0)
    ledger["ANO_MES"] = pd.to_datetime(ledger["DATA"]).dt.to_period("M").astype(str)
    return _add_product_attributes(ledger, produtos)


def build_pair_reconciliation(
    vendas: pd.DataFrame,
    compras: pd.DataFrame,
    estoque_inicial: pd.DataFrame,
    produtos: pd.DataFrame,
) -> pd.DataFrame:
    """Reconcile known entries and observed exits by product-store pair."""
    vendas = with_sales_storage_quantity(vendas)
    compras = with_purchase_storage_quantity(compras, produtos)

    sales_pair = (
        vendas.groupby(["COD_EMPRESA", "CODIGO"], dropna=False)["QTD_VENDA_ESTOQUE"]
        .sum()
        .reset_index()
        .rename(columns={"QTD_VENDA_ESTOQUE": "VENDAS_ESTOQUE"})
    )
    purchase_pair = (
        compras.groupby(["COD_EMPRESA", "CODIGO"], dropna=False)["QTD_COMPRA_ESTOQUE"]
        .sum()
        .reset_index()
        .rename(columns={"QTD_COMPRA_ESTOQUE": "COMPRAS_REGISTRADAS_ESTOQUE"})
    )
    stock_pair = (
        estoque_inicial.groupby(["COD_EMPRESA", "CODIGO"], dropna=False)["ESTOQUE_INICIAL"]
        .sum(min_count=1)
        .reset_index()
    )

    base = stock_pair.merge(purchase_pair, on=["COD_EMPRESA", "CODIGO"], how="outer")
    base = base.merge(sales_pair, on=["COD_EMPRESA", "CODIGO"], how="outer")
    base = _add_product_attributes(base, produtos)

    base["ESTOQUE_INICIAL_AUSENTE"] = base["ESTOQUE_INICIAL"].isna()
    base["COMPRAS_REGISTRADAS_ESTOQUE"] = _to_number(
        base["COMPRAS_REGISTRADAS_ESTOQUE"]
    ).fillna(0)
    base["VENDAS_ESTOQUE"] = _to_number(base["VENDAS_ESTOQUE"]).fillna(0)
    base["ENTRADAS_CONHECIDAS_ESTOQUE"] = (
        base["ESTOQUE_INICIAL"] + base["COMPRAS_REGISTRADAS_ESTOQUE"]
    )
    base["SALDO_PROJETADO_CONTABIL"] = metrics.saldo_projetado(
        base["ESTOQUE_INICIAL"],
        base["COMPRAS_REGISTRADAS_ESTOQUE"],
        base["VENDAS_ESTOQUE"],
    )
    base["GAP_CONTABIL_ESTOQUE"] = metrics.gap_contabil_estoque(
        base["VENDAS_ESTOQUE"],
        base["ESTOQUE_INICIAL"],
        base["COMPRAS_REGISTRADAS_ESTOQUE"],
    )
    base.loc[base["ESTOQUE_INICIAL_AUSENTE"], ["SALDO_PROJETADO_CONTABIL", "GAP_CONTABIL_ESTOQUE"]] = pd.NA
    base["TEVE_VENDA"] = base["VENDAS_ESTOQUE"].gt(0)
    base["TEVE_COMPRA_REGISTRADA"] = base["COMPRAS_REGISTRADAS_ESTOQUE"].gt(0)
    base["VENDA_SEM_COMPRA_REGISTRADA"] = base["TEVE_VENDA"] & ~base["TEVE_COMPRA_REGISTRADA"]
    base["VENDA_SEM_ESTOQUE_INICIAL_SUFICIENTE"] = (
        base["TEVE_VENDA"]
        & (base["ESTOQUE_INICIAL"].isna() | base["ESTOQUE_INICIAL"].lt(base["VENDAS_ESTOQUE"]))
    )
    base["INTERPRETACAO_SALDO_NEGATIVO"] = "gap contabil; nao prova fisica operacional"
    base["POSSIVEIS_CAUSAS_GAP"] = GAP_CAUSES

    ordered = [
        "COD_EMPRESA",
        "CODIGO",
        "DESCRICAO",
        "NIVEL_1",
        "ESTOQUE_INICIAL",
        "ESTOQUE_INICIAL_AUSENTE",
        "COMPRAS_REGISTRADAS_ESTOQUE",
        "VENDAS_ESTOQUE",
        "ENTRADAS_CONHECIDAS_ESTOQUE",
        "SALDO_PROJETADO_CONTABIL",
        "GAP_CONTABIL_ESTOQUE",
        "TEVE_VENDA",
        "TEVE_COMPRA_REGISTRADA",
        "VENDA_SEM_COMPRA_REGISTRADA",
        "VENDA_SEM_ESTOQUE_INICIAL_SUFICIENTE",
        "INTERPRETACAO_SALDO_NEGATIVO",
        "POSSIVEIS_CAUSAS_GAP",
    ]
    return base[ordered].sort_values(["COD_EMPRESA", "CODIGO"]).reset_index(drop=True)


def build_monthly_pair_reconciliation(ledger: pd.DataFrame) -> pd.DataFrame:
    """Aggregate movement ledger by month and product-store pair."""
    grouped = (
        ledger.groupby(["ANO_MES", "COD_EMPRESA", "CODIGO", "DESCRICAO", "NIVEL_1"], dropna=False)
        .agg(
            ESTOQUE_INICIAL=("ESTOQUE_INICIAL_EVENTO", "sum"),
            COMPRAS_REGISTRADAS_ESTOQUE=("QTD_COMPRA_ESTOQUE", "sum"),
            VENDAS_ESTOQUE=("QTD_VENDA_ESTOQUE", "sum"),
        )
        .reset_index()
    )
    grouped["ENTRADAS_CONHECIDAS_ESTOQUE"] = (
        grouped["ESTOQUE_INICIAL"] + grouped["COMPRAS_REGISTRADAS_ESTOQUE"]
    )
    grouped["SALDO_PROJETADO_CONTABIL"] = (
        grouped["ENTRADAS_CONHECIDAS_ESTOQUE"] - grouped["VENDAS_ESTOQUE"]
    )
    grouped["GAP_CONTABIL_ESTOQUE"] = metrics.gap_contabil_estoque(
        grouped["VENDAS_ESTOQUE"],
        grouped["ESTOQUE_INICIAL"],
        grouped["COMPRAS_REGISTRADAS_ESTOQUE"],
    )
    grouped["TEVE_VENDA"] = grouped["VENDAS_ESTOQUE"].gt(0)
    grouped["TEVE_COMPRA_REGISTRADA"] = grouped["COMPRAS_REGISTRADAS_ESTOQUE"].gt(0)
    grouped["VENDA_SEM_COMPRA_REGISTRADA"] = grouped["TEVE_VENDA"] & ~grouped["TEVE_COMPRA_REGISTRADA"]
    grouped["VENDA_SEM_ESTOQUE_INICIAL_SUFICIENTE"] = (
        grouped["TEVE_VENDA"] & grouped["ESTOQUE_INICIAL"].lt(grouped["VENDAS_ESTOQUE"])
    )
    return grouped


def build_coverage_audit(pair_reconciliation: pd.DataFrame, ledger: pd.DataFrame) -> pd.DataFrame:
    """Build coverage audit rows for total, month, store, category, and product."""
    monthly_pairs = build_monthly_pair_reconciliation(ledger)
    rows = [
        _coverage_for_group(pair_reconciliation, ledger, "periodo_total", []),
        _coverage_for_group(monthly_pairs, ledger, "mes", ["ANO_MES"]),
        _coverage_for_group(pair_reconciliation, ledger, "loja", ["COD_EMPRESA"]),
        _coverage_for_group(pair_reconciliation, ledger, "categoria", ["NIVEL_1"]),
        _coverage_for_group(pair_reconciliation, ledger, "produto", ["CODIGO", "DESCRICAO", "NIVEL_1"]),
    ]
    audit = pd.concat(rows, ignore_index=True)
    audit["formula_compras_armazenagem"] = PURCHASE_STORAGE_FORMULA
    audit["formula_vendas_armazenagem"] = SALES_STORAGE_FORMULA
    audit["interpretacao"] = "cobertura de entradas conhecidas; não evidencia causal"
    audit["limitacao"] = (
        "DADO AUSENTE: transferencias, ajustes, devolucoes e estoque final real; "
        "NÃO VALIDADO: universo completo das compras"
    )
    return audit.sort_values(["nivel_agrupamento", "chave_agrupamento"]).reset_index(drop=True)


def generate_reconciliation_outputs(
    processed_dir: Path = PROCESSED_DIR,
    output_dir: Path = OUTPUT_TABLES_DIR,
) -> dict[str, pd.DataFrame]:
    """Read processed data and write Spec 04 reconciliation CSV outputs."""
    vendas = pd.read_parquet(processed_dir / "fato_vendas.parquet")
    compras = pd.read_parquet(processed_dir / "fato_compras.parquet")
    estoque_inicial = pd.read_parquet(processed_dir / "fato_estoque_inicial.parquet")
    produtos = pd.read_parquet(processed_dir / "dim_produto.parquet")

    pair_reconciliation = build_pair_reconciliation(vendas, compras, estoque_inicial, produtos)
    ledger = build_movement_ledger(vendas, compras, estoque_inicial, produtos)
    coverage_audit = build_coverage_audit(pair_reconciliation, ledger)

    output_dir.mkdir(parents=True, exist_ok=True)
    gaps_path = output_dir / "gaps_saldo_contabil_estoque.csv"
    coverage_path = output_dir / "compras_coverage_audit.csv"

    pair_reconciliation.to_csv(gaps_path, index=False, encoding="utf-8")
    coverage_audit.to_csv(coverage_path, index=False, encoding="utf-8")

    return {
        "gaps_saldo_contabil_estoque": pair_reconciliation,
        "compras_coverage_audit": coverage_audit,
        "movement_ledger": ledger,
    }


def conversion_diagnostics(compras: pd.DataFrame, produtos: pd.DataFrame) -> dict[str, Any]:
    """Return counts that answer whether purchase conversion is materialized today."""
    converted = with_purchase_storage_quantity(compras, produtos)
    conversion_differs_products = int(
        _to_number(produtos["CONVERSAO_COMPRA_ARMAZENAGEM"]).ne(1).sum()
    )
    purchase_lines_conversion_differs = int(
        _to_number(converted["CONVERSAO_COMPRA_ARMAZENAGEM"]).ne(1).sum()
    )
    return {
        "produtos_conversao_compra_diferente_1": conversion_differs_products,
        "linhas_compra_conversao_compra_diferente_1": purchase_lines_conversion_differs,
        "linhas_compra": int(len(compras)),
    }


def _add_product_attributes(df: pd.DataFrame, produtos: pd.DataFrame) -> pd.DataFrame:
    attributes = produtos[["CODIGO", "DESCRICAO", "NIVEL_1"]].drop_duplicates("CODIGO")
    return df.merge(attributes, on="CODIGO", how="left", validate="many_to_one")


def _coverage_for_group(
    base: pd.DataFrame,
    ledger: pd.DataFrame,
    level: str,
    group_cols: list[str],
) -> pd.DataFrame:
    if group_cols:
        grouped = (
            base.groupby(group_cols, dropna=False)
            .agg(
                total_vendido_estoque=("VENDAS_ESTOQUE", "sum"),
                estoque_inicial_estoque=("ESTOQUE_INICIAL", "sum"),
                compras_registradas_estoque=("COMPRAS_REGISTRADAS_ESTOQUE", "sum"),
                pares_produto_loja=("CODIGO", "size"),
                pares_com_venda=("TEVE_VENDA", "sum"),
                pares_venda_sem_compra=("VENDA_SEM_COMPRA_REGISTRADA", "sum"),
                pares_venda_sem_estoque_inicial_suficiente=(
                    "VENDA_SEM_ESTOQUE_INICIAL_SUFICIENTE",
                    "sum",
                ),
            )
            .reset_index()
        )
        negative_events = (
            ledger.groupby(group_cols, dropna=False)["EVENTO_SALDO_PROJETADO_NEGATIVO"]
            .mean()
            .reset_index()
            .rename(columns={"EVENTO_SALDO_PROJETADO_NEGATIVO": "pct_eventos_saldo_projetado_negativo"})
        )
        grouped = grouped.merge(negative_events, on=group_cols, how="left")
        grouped["chave_agrupamento"] = grouped[group_cols].astype(str).agg(" | ".join, axis=1)
    else:
        grouped = pd.DataFrame(
            {
                "total_vendido_estoque": [base["VENDAS_ESTOQUE"].sum()],
                "estoque_inicial_estoque": [base["ESTOQUE_INICIAL"].sum()],
                "compras_registradas_estoque": [base["COMPRAS_REGISTRADAS_ESTOQUE"].sum()],
                "pares_produto_loja": [len(base)],
                "pares_com_venda": [int(base["TEVE_VENDA"].sum())],
                "pares_venda_sem_compra": [int(base["VENDA_SEM_COMPRA_REGISTRADA"].sum())],
                "pares_venda_sem_estoque_inicial_suficiente": [
                    int(base["VENDA_SEM_ESTOQUE_INICIAL_SUFICIENTE"].sum())
                ],
                "pct_eventos_saldo_projetado_negativo": [
                    float(ledger["EVENTO_SALDO_PROJETADO_NEGATIVO"].mean())
                    if len(ledger)
                    else pd.NA
                ],
                "chave_agrupamento": ["total"],
            }
        )

    grouped["nivel_agrupamento"] = level
    grouped["entradas_conhecidas_estoque"] = (
        grouped["estoque_inicial_estoque"] + grouped["compras_registradas_estoque"]
    )
    grouped["diferenca_saidas_entradas"] = (
        grouped["total_vendido_estoque"] - grouped["entradas_conhecidas_estoque"]
    )
    grouped["pct_cobertura_entradas"] = metrics.safe_divide(
        grouped["entradas_conhecidas_estoque"],
        grouped["total_vendido_estoque"],
    )
    grouped["pct_skus_venda_sem_compra"] = metrics.safe_divide(
        grouped["pares_venda_sem_compra"],
        grouped["pares_com_venda"],
    )
    grouped["pct_skus_venda_sem_estoque_inicial_suficiente"] = metrics.safe_divide(
        grouped["pares_venda_sem_estoque_inicial_suficiente"],
        grouped["pares_com_venda"],
    )
    grouped["classificacao_confiabilidade"] = grouped.apply(_classify_coverage_row, axis=1)

    columns = [
        "nivel_agrupamento",
        "chave_agrupamento",
        "total_vendido_estoque",
        "estoque_inicial_estoque",
        "compras_registradas_estoque",
        "entradas_conhecidas_estoque",
        "diferenca_saidas_entradas",
        "pct_cobertura_entradas",
        "pct_eventos_saldo_projetado_negativo",
        "pct_skus_venda_sem_compra",
        "pct_skus_venda_sem_estoque_inicial_suficiente",
        "pares_produto_loja",
        "pares_com_venda",
        "pares_venda_sem_compra",
        "pares_venda_sem_estoque_inicial_suficiente",
        "classificacao_confiabilidade",
    ]
    return grouped[columns]


def _classify_coverage_row(row: pd.Series) -> str:
    sold = row["total_vendido_estoque"]
    coverage = row["pct_cobertura_entradas"]
    pct_negative = row["pct_eventos_saldo_projetado_negativo"]
    pct_without_purchase = row["pct_skus_venda_sem_compra"]

    if pd.isna(sold) or sold == 0:
        return "OK"
    if pd.isna(coverage):
        return "não confiável para análise causal"
    if coverage >= 1 and (pd.isna(pct_negative) or pct_negative <= 0.05):
        return "OK"
    if coverage >= 0.8 and (pd.isna(pct_without_purchase) or pct_without_purchase <= 0.25):
        return "suspeito"
    if coverage >= 0.5:
        return "crítico"
    return "não confiável para análise causal"


if __name__ == "__main__":
    outputs = generate_reconciliation_outputs()
    print(
        "[SPEC04] compras_coverage_audit.csv:",
        len(outputs["compras_coverage_audit"]),
        "linhas",
    )
    print(
        "[SPEC04] gaps_saldo_contabil_estoque.csv:",
        len(outputs["gaps_saldo_contabil_estoque"]),
        "linhas",
    )
