# -*- coding: utf-8 -*-
"""Sales, store, and category analysis for Spec 05.

The functions in this module are intentionally pure where possible. They do
not infer store closure, physical stock-out, or real demand from observed
sales. Counts of rows are named daily sales lines because the sales fact has no
coupon/order identifier.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

import metrics


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES_DIR = ROOT / "outputs" / "tables"

STORE_STATUS = {
    "comparavel",
    "nova_ou_sem_base_yoy",
    "incompleta_sem_venda_atual",
    "dados_insuficientes",
    "comportamento_atipico",
}

CATEGORY_CLASSES = {
    "queda generalizada",
    "queda concentrada",
    "crescimento",
    "comportamento atipico",
    "dados insuficientes",
}


def _require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{name}: colunas obrigatorias ausentes: {missing}")


def _to_month(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.to_period("M")


def _safe_variation(current: Any, base: Any) -> Any:
    return metrics.variacao_percentual(current, base)


def prepare_sales(vendas: pd.DataFrame) -> pd.DataFrame:
    """Return sales with explicit month and validated revenue/stock quantity columns."""
    _require_columns(
        vendas,
        {
            "DATA_VENDA",
            "COD_EMPRESA",
            "CODIGO",
            "QUANTIDADE_VENDIDA",
            "CONVERSAO_VENDA_PARA_ARMAZENAGEM",
            "PRECO_UNIT_MEDIO",
        },
        "vendas",
    )

    out = vendas.copy()
    out["DATA_VENDA"] = pd.to_datetime(out["DATA_VENDA"])
    out["ANO_MES_PERIOD"] = _to_month(out["DATA_VENDA"])
    out["ANO_MES"] = out["ANO_MES_PERIOD"].astype(str)

    receita_calc = (
        pd.to_numeric(out["QUANTIDADE_VENDIDA"], errors="coerce").fillna(0)
        * pd.to_numeric(out["PRECO_UNIT_MEDIO"], errors="coerce").fillna(0)
    )
    if "RECEITA" in out.columns:
        existing = pd.to_numeric(out["RECEITA"], errors="coerce")
        if (existing.sub(receita_calc).abs().fillna(0) > 0.01).any():
            raise ValueError("RECEITA diverge da formula documentada")
    else:
        out["RECEITA"] = receita_calc

    qtd_calc = (
        pd.to_numeric(out["QUANTIDADE_VENDIDA"], errors="coerce").fillna(0)
        * pd.to_numeric(out["CONVERSAO_VENDA_PARA_ARMAZENAGEM"], errors="coerce").fillna(0)
    )
    if "QTD_VENDA_ESTOQUE" in out.columns:
        existing = pd.to_numeric(out["QTD_VENDA_ESTOQUE"], errors="coerce")
        if (existing.sub(qtd_calc).abs().fillna(0) > 0.000001).any():
            raise ValueError("QTD_VENDA_ESTOQUE diverge da formula documentada")
    else:
        out["QTD_VENDA_ESTOQUE"] = qtd_calc

    return out


def build_store_monthly_sales(vendas: pd.DataFrame, lojas: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build store-month sales with YoY and comparability flags."""
    sales = prepare_sales(vendas)
    store_ids = _store_ids(sales, lojas)
    months = pd.period_range(sales["ANO_MES_PERIOD"].min(), sales["ANO_MES_PERIOD"].max(), freq="M")
    grid = pd.MultiIndex.from_product(
        [store_ids, months],
        names=["COD_EMPRESA", "ANO_MES_PERIOD"],
    ).to_frame(index=False)

    grouped = (
        sales.groupby(["COD_EMPRESA", "ANO_MES_PERIOD"], dropna=False)
        .agg(
            receita=("RECEITA", "sum"),
            quantidade_vendida=("QUANTIDADE_VENDIDA", "sum"),
            qtd_vendida_estoque=("QTD_VENDA_ESTOQUE", "sum"),
            linhas_venda_diarias=("CODIGO", "size"),
            skus_vendidos=("CODIGO", "nunique"),
            dias_com_venda=("DATA_VENDA", "nunique"),
        )
        .reset_index()
    )
    out = grid.merge(grouped, on=["COD_EMPRESA", "ANO_MES_PERIOD"], how="left")
    metric_cols = [
        "receita",
        "quantidade_vendida",
        "qtd_vendida_estoque",
        "linhas_venda_diarias",
        "skus_vendidos",
        "dias_com_venda",
    ]
    out[metric_cols] = out[metric_cols].fillna(0)
    out["ticket_medio_linha"] = metrics.safe_divide(out["receita"], out["linhas_venda_diarias"])
    out["preco_medio_vendido"] = metrics.safe_divide(out["receita"], out["quantidade_vendida"])
    out["ANO_MES"] = out["ANO_MES_PERIOD"].astype(str)

    out = _add_previous_year_values(
        out,
        key_cols=["COD_EMPRESA"],
        value_cols=[
            "receita",
            "quantidade_vendida",
            "qtd_vendida_estoque",
            "linhas_venda_diarias",
            "skus_vendidos",
            "dias_com_venda",
        ],
    )
    out["loja_comparavel_yoy"] = out["linhas_venda_diarias"].gt(0) & out[
        "linhas_venda_diarias_ano_anterior"
    ].gt(0)
    out["variacao_receita_yoy"] = _vector_variation(out["receita"], out["receita_ano_anterior"])
    out["variacao_qtd_vendida_estoque_yoy"] = _vector_variation(
        out["qtd_vendida_estoque"],
        out["qtd_vendida_estoque_ano_anterior"],
    )
    out["variacao_linhas_venda_diarias_yoy"] = _vector_variation(
        out["linhas_venda_diarias"],
        out["linhas_venda_diarias_ano_anterior"],
    )
    out["variacao_dias_com_venda_yoy"] = _vector_variation(
        out["dias_com_venda"],
        out["dias_com_venda_ano_anterior"],
    )
    out["status_loja_mes"] = out.apply(_classify_store_month, axis=1)
    out["interpretacao_dias_com_venda"] = (
        "dias com ao menos uma linha de venda; nao prova abertura ou fechamento operacional"
    )
    out["denominador_linhas"] = "linhas de venda diarias"

    if lojas is not None and not lojas.empty:
        attrs = lojas.drop_duplicates("COD_EMPRESA")
        keep = [column for column in ["COD_EMPRESA", "CD_CIDADE", "CD_ESTADO"] if column in attrs.columns]
        out = out.merge(attrs[keep], on="COD_EMPRESA", how="left")

    ordered = [
        "ANO_MES",
        "COD_EMPRESA",
        "CD_CIDADE",
        "CD_ESTADO",
        "receita",
        "receita_ano_anterior",
        "variacao_receita_yoy",
        "quantidade_vendida",
        "qtd_vendida_estoque",
        "qtd_vendida_estoque_ano_anterior",
        "variacao_qtd_vendida_estoque_yoy",
        "linhas_venda_diarias",
        "linhas_venda_diarias_ano_anterior",
        "variacao_linhas_venda_diarias_yoy",
        "skus_vendidos",
        "skus_vendidos_ano_anterior",
        "dias_com_venda",
        "dias_com_venda_ano_anterior",
        "variacao_dias_com_venda_yoy",
        "ticket_medio_linha",
        "preco_medio_vendido",
        "loja_comparavel_yoy",
        "status_loja_mes",
        "interpretacao_dias_com_venda",
        "denominador_linhas",
    ]
    existing = [column for column in ordered if column in out.columns]
    return out[existing].sort_values(["ANO_MES", "COD_EMPRESA"]).reset_index(drop=True)


def build_category_yoy(vendas: pd.DataFrame, produtos: pd.DataFrame) -> pd.DataFrame:
    """Build category monthly and quarterly YoY rows."""
    sales = prepare_sales(vendas)
    _require_columns(produtos, {"CODIGO", "NIVEL_1"}, "produtos")
    sales = sales.merge(
        produtos[["CODIGO", "NIVEL_1"]].drop_duplicates("CODIGO"),
        on="CODIGO",
        how="left",
        validate="many_to_one",
    )
    sales["NIVEL_1"] = sales["NIVEL_1"].fillna("DADO AUSENTE")

    monthly = _category_period_yoy(sales, "mes")
    quarterly_sales = sales.copy()
    quarterly_sales["ANO_MES_PERIOD"] = pd.to_datetime(quarterly_sales["DATA_VENDA"]).dt.to_period("Q")
    quarterly = _category_period_yoy(quarterly_sales, "trimestre")
    return pd.concat([monthly, quarterly], ignore_index=True).sort_values(
        ["periodicidade", "periodo", "NIVEL_1"]
    ).reset_index(drop=True)


def generate_sales_outputs(
    processed_dir: Path = PROCESSED_DIR,
    output_dir: Path = OUTPUT_TABLES_DIR,
) -> dict[str, pd.DataFrame]:
    """Read processed data and write Spec 05 sales/category CSV outputs."""
    vendas = pd.read_parquet(processed_dir / "fato_vendas.parquet")
    produtos = pd.read_parquet(processed_dir / "dim_produto.parquet")
    lojas = pd.read_parquet(processed_dir / "dim_lojas.parquet")

    same_store = build_store_monthly_sales(vendas, lojas)
    categories = build_category_yoy(vendas, produtos)

    output_dir.mkdir(parents=True, exist_ok=True)
    same_store.to_csv(output_dir / "vendas_same_store_yoy.csv", index=False, encoding="utf-8")
    categories.to_csv(output_dir / "vendas_categorias_yoy.csv", index=False, encoding="utf-8")
    return {
        "vendas_same_store_yoy": same_store,
        "vendas_categorias_yoy": categories,
    }


def _store_ids(sales: pd.DataFrame, lojas: pd.DataFrame | None) -> list[Any]:
    if lojas is not None and "COD_EMPRESA" in lojas.columns and not lojas.empty:
        return sorted(lojas["COD_EMPRESA"].dropna().unique().tolist())
    return sorted(sales["COD_EMPRESA"].dropna().unique().tolist())


def _add_previous_year_values(
    df: pd.DataFrame,
    key_cols: list[str],
    value_cols: list[str],
) -> pd.DataFrame:
    previous = df[key_cols + ["ANO_MES_PERIOD"] + value_cols].copy()
    previous["ANO_MES_PERIOD"] = previous["ANO_MES_PERIOD"] + 12
    previous = previous.rename(columns={column: f"{column}_ano_anterior" for column in value_cols})
    return df.merge(previous, on=key_cols + ["ANO_MES_PERIOD"], how="left")


def _vector_variation(current: pd.Series, base: pd.Series) -> pd.Series:
    return pd.Series(
        [metrics.variacao_percentual(now, old) for now, old in zip(current, base, strict=False)],
        index=current.index,
        dtype="Float64",
    )


def _classify_store_month(row: pd.Series) -> str:
    current = row["linhas_venda_diarias"]
    base = row["linhas_venda_diarias_ano_anterior"]
    if pd.isna(base):
        return "nova_ou_sem_base_yoy" if current > 0 else "dados_insuficientes"
    if base > 0 and current == 0:
        return "incompleta_sem_venda_atual"
    if base == 0 and current > 0:
        return "nova_ou_sem_base_yoy"
    if base == 0 and current == 0:
        return "dados_insuficientes"

    revenue_yoy = row["variacao_receita_yoy"]
    days_yoy = row["variacao_dias_com_venda_yoy"]
    if (
        pd.notna(revenue_yoy)
        and abs(float(revenue_yoy)) >= 0.50
        or pd.notna(days_yoy)
        and abs(float(days_yoy)) >= 0.50
    ):
        return "comportamento_atipico"
    return "comparavel"


def _category_period_yoy(sales: pd.DataFrame, periodicity: str) -> pd.DataFrame:
    grouped = (
        sales.groupby(["NIVEL_1", "ANO_MES_PERIOD"], dropna=False)
        .agg(
            receita=("RECEITA", "sum"),
            quantidade_vendida=("QUANTIDADE_VENDIDA", "sum"),
            qtd_vendida_estoque=("QTD_VENDA_ESTOQUE", "sum"),
            linhas_venda_diarias=("CODIGO", "size"),
            skus_vendidos=("CODIGO", "nunique"),
        )
        .reset_index()
    )
    grouped["periodo"] = grouped["ANO_MES_PERIOD"].astype(str)
    grouped["periodicidade"] = periodicity
    grouped = _add_previous_year_values(
        grouped,
        key_cols=["NIVEL_1"],
        value_cols=["receita", "qtd_vendida_estoque", "linhas_venda_diarias", "skus_vendidos"],
    )
    grouped["variacao_receita_yoy"] = _vector_variation(
        grouped["receita"],
        grouped["receita_ano_anterior"],
    )
    grouped["variacao_qtd_vendida_estoque_yoy"] = _vector_variation(
        grouped["qtd_vendida_estoque"],
        grouped["qtd_vendida_estoque_ano_anterior"],
    )

    totals = (
        grouped.groupby("ANO_MES_PERIOD", dropna=False)
        .agg(receita_total_periodo=("receita", "sum"), receita_total_ano_anterior=("receita_ano_anterior", "sum"))
        .reset_index()
    )
    totals["variacao_receita_total_yoy"] = _vector_variation(
        totals["receita_total_periodo"],
        totals["receita_total_ano_anterior"],
    )
    grouped = grouped.merge(totals, on="ANO_MES_PERIOD", how="left")
    grouped["queda_receita_categoria"] = (
        grouped["receita_ano_anterior"].fillna(0) - grouped["receita"].fillna(0)
    ).clip(lower=0)
    drop_totals = (
        grouped.groupby("ANO_MES_PERIOD", dropna=False)["queda_receita_categoria"]
        .sum()
        .reset_index()
        .rename(columns={"queda_receita_categoria": "queda_receita_total_categorias"})
    )
    grouped = grouped.merge(drop_totals, on="ANO_MES_PERIOD", how="left")
    grouped["contribuicao_queda_periodo"] = metrics.safe_divide(
        grouped["queda_receita_categoria"],
        grouped["queda_receita_total_categorias"],
    )
    grouped["classificacao_categoria"] = grouped.apply(_classify_category, axis=1)
    grouped["interpretacao"] = (
        "YoY compara mesmo periodo do ano anterior; venda observada nao mede demanda real"
    )

    columns = [
        "periodicidade",
        "periodo",
        "NIVEL_1",
        "receita",
        "receita_ano_anterior",
        "variacao_receita_yoy",
        "receita_total_periodo",
        "receita_total_ano_anterior",
        "variacao_receita_total_yoy",
        "contribuicao_queda_periodo",
        "quantidade_vendida",
        "qtd_vendida_estoque",
        "qtd_vendida_estoque_ano_anterior",
        "variacao_qtd_vendida_estoque_yoy",
        "linhas_venda_diarias",
        "linhas_venda_diarias_ano_anterior",
        "skus_vendidos",
        "skus_vendidos_ano_anterior",
        "classificacao_categoria",
        "interpretacao",
    ]
    return grouped[columns]


def _classify_category(row: pd.Series) -> str:
    current = row["receita"]
    base = row["receita_ano_anterior"]
    yoy = row["variacao_receita_yoy"]
    total_yoy = row["variacao_receita_total_yoy"]
    contribution = row["contribuicao_queda_periodo"]

    if pd.isna(base) or base <= 0 or current <= 0 or pd.isna(yoy):
        return "dados insuficientes"
    if yoy > 0:
        return "crescimento"
    if pd.notna(total_yoy) and pd.notna(yoy) and abs(float(yoy) - float(total_yoy)) >= 0.50:
        return "comportamento atipico"
    if pd.notna(contribution) and contribution >= 0.10:
        return "queda concentrada"
    return "queda generalizada"


if __name__ == "__main__":
    outputs = generate_sales_outputs()
    print("[SPEC05] vendas_same_store_yoy.csv:", len(outputs["vendas_same_store_yoy"]), "linhas")
    print("[SPEC05] vendas_categorias_yoy.csv:", len(outputs["vendas_categorias_yoy"]), "linhas")

