# -*- coding: utf-8 -*-
"""Observed-sales projection and gross purchase triage for Spec 06."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import metrics


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES_DIR = ROOT / "outputs" / "tables"

FORECAST_YEAR = 2026
SAFETY_STOCK_DAYS = 30


def _require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{name}: colunas obrigatorias ausentes: {missing}")


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def prepare_projection_sales(vendas: pd.DataFrame) -> pd.DataFrame:
    """Return observed sales with month indexes and stock-unit quantities."""
    _require_columns(
        vendas,
        {"DATA_VENDA", "CODIGO", "QUANTIDADE_VENDIDA"},
        "vendas",
    )
    out = vendas.copy()
    out["DATA_VENDA"] = pd.to_datetime(out["DATA_VENDA"])
    out["ANO_MES_PERIOD"] = out["DATA_VENDA"].dt.to_period("M")
    out["MES_NUM"] = out["DATA_VENDA"].dt.month
    first_month = out["ANO_MES_PERIOD"].min()
    out["IDX_MES"] = (out["ANO_MES_PERIOD"] - first_month).apply(lambda value: value.n)

    if "QTD_VENDA_ESTOQUE" not in out.columns:
        conversion = (
            _to_number(out["CONVERSAO_VENDA_PARA_ARMAZENAGEM"]).fillna(1)
            if "CONVERSAO_VENDA_PARA_ARMAZENAGEM" in out.columns
            else 1
        )
        out["QTD_VENDA_ESTOQUE"] = _to_number(out["QUANTIDADE_VENDIDA"]).fillna(0) * conversion
    return out


def build_observed_sales_projection(
    vendas: pd.DataFrame,
    produtos: pd.DataFrame,
    estoque_inicial: pd.DataFrame | None = None,
    coverage_audit: pd.DataFrame | None = None,
    assortment_control: pd.DataFrame | None = None,
    forecast_year: int = FORECAST_YEAR,
    safety_stock_days: int = SAFETY_STOCK_DAYS,
) -> pd.DataFrame:
    """Project observed sales and mark final/net purchase as blocked when needed."""
    sales = prepare_projection_sales(vendas)
    _require_columns(produtos, {"CODIGO", "DESCRICAO", "NIVEL_1"}, "produtos")

    observed_monthly = _complete_monthly_product_grid(sales)
    trend = _linear_trend_by_product(observed_monthly)
    seasonality = _seasonality_by_category(sales, produtos)
    future_months = _future_month_grid(sales, forecast_year)

    product_attrs = produtos[["CODIGO", "DESCRICAO", "NIVEL_1"]].drop_duplicates("CODIGO")
    projected = trend.merge(product_attrs, on="CODIGO", how="left", validate="one_to_one")
    projected = projected.merge(future_months, how="cross")
    projected = projected.merge(seasonality, on=["NIVEL_1", "MES_NUM"], how="left")
    projected["indice_sazonal"] = _to_number(projected["indice_sazonal"]).fillna(1.0)
    projected["venda_observada_tendencia"] = (
        projected["slope"] * projected["IDX_MES_FUT"] + projected["intercept"]
    ).clip(lower=0)
    projected["venda_observada_projetada"] = (
        projected["venda_observada_tendencia"] * projected["indice_sazonal"]
    ).clip(lower=0)

    annual = (
        projected.groupby(["CODIGO", "DESCRICAO", "NIVEL_1"], dropna=False)
        .agg(venda_observada_projetada_2026=("venda_observada_projetada", "sum"))
        .reset_index()
    )
    historical = (
        sales.groupby("CODIGO", dropna=False)["QTD_VENDA_ESTOQUE"]
        .sum()
        .reset_index()
        .rename(columns={"QTD_VENDA_ESTOQUE": "venda_observada_24_meses"})
    )
    annual = annual.merge(historical, on="CODIGO", how="left")
    annual["venda_media_anual_observada_historica"] = annual["venda_observada_24_meses"] / 2
    annual["crescimento_pct_vs_media_observada_historica"] = (
        metrics.safe_divide(
            annual["venda_observada_projetada_2026"],
            annual["venda_media_anual_observada_historica"],
        )
        - 1
    ) * 100
    annual["venda_media_diaria_observada_2026"] = annual["venda_observada_projetada_2026"] / 365
    annual["estoque_seguranca_30d"] = annual["venda_media_diaria_observada_2026"] * safety_stock_days
    annual["compra_bruta_sugerida"] = (
        annual["venda_observada_projetada_2026"] + annual["estoque_seguranca_30d"]
    ).round(0)

    annual = _add_stock_reference(annual, estoque_inicial)
    stock_reliable = _coverage_allows_net_purchase(coverage_audit)
    annual["flag_nao_calcular_compra_liquida_por_estoque_inconfiavel"] = not stock_reliable
    annual["compra_liquida_sugerida"] = pd.NA
    annual["status_compra_liquida"] = "BLOQUEADO"
    annual["estoque_a_validar_antes_da_compra"] = (
        "DADO AUSENTE: estoque atual disponivel confiavel por produto e loja"
    )
    annual["nivel_confianca"] = "Baixa"
    annual["limitacao"] = _projection_limitation(assortment_control)
    annual["acao_recomendada"] = (
        "Usar como triagem bruta; validar estoque atual, margem, lead time e lote minimo antes de pedido"
    )
    annual["regra_usada"] = (
        "tendencia linear da venda observada por produto com indice sazonal por categoria; "
        "estoque de seguranca de 30 dias"
    )

    ordered = [
        "CODIGO",
        "DESCRICAO",
        "NIVEL_1",
        "venda_observada_projetada_2026",
        "venda_observada_24_meses",
        "venda_media_anual_observada_historica",
        "crescimento_pct_vs_media_observada_historica",
        "venda_media_diaria_observada_2026",
        "estoque_seguranca_30d",
        "compra_bruta_sugerida",
        "estoque_inicial_total_referencia",
        "compra_liquida_sugerida",
        "status_compra_liquida",
        "flag_nao_calcular_compra_liquida_por_estoque_inconfiavel",
        "estoque_a_validar_antes_da_compra",
        "nivel_confianca",
        "regra_usada",
        "limitacao",
        "acao_recomendada",
    ]
    return annual[ordered].sort_values("venda_observada_projetada_2026", ascending=False).reset_index(drop=True)


def generate_projection_outputs(
    processed_dir: Path = PROCESSED_DIR,
    output_dir: Path = OUTPUT_TABLES_DIR,
) -> dict[str, pd.DataFrame]:
    """Read processed data and write Spec 06 observed-sales projection output."""
    vendas = pd.read_parquet(processed_dir / "fato_vendas.parquet")
    produtos = pd.read_parquet(processed_dir / "dim_produto.parquet")
    estoque_path = processed_dir / "fato_estoque_inicial.parquet"
    estoque_inicial = pd.read_parquet(estoque_path) if estoque_path.exists() else None

    coverage_path = output_dir / "compras_coverage_audit.csv"
    coverage_audit = pd.read_csv(coverage_path) if coverage_path.exists() else None
    assortment_path = output_dir / "sortimento_controlado_por_volume.csv"
    assortment_control = pd.read_csv(assortment_path) if assortment_path.exists() else None

    projection = build_observed_sales_projection(
        vendas,
        produtos,
        estoque_inicial=estoque_inicial,
        coverage_audit=coverage_audit,
        assortment_control=assortment_control,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    projection.to_csv(
        output_dir / "projecao_venda_observada_2026.csv",
        index=False,
        encoding="utf-8",
    )
    return {"projecao_venda_observada_2026": projection}


def _complete_monthly_product_grid(sales: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        sales.groupby(["CODIGO", "IDX_MES", "MES_NUM"], dropna=False)["QTD_VENDA_ESTOQUE"]
        .sum()
        .reset_index()
    )
    max_idx = int(sales["IDX_MES"].max())
    product_ids = sorted(monthly["CODIGO"].dropna().unique().tolist())
    months = pd.DataFrame({"IDX_MES": range(max_idx + 1)})
    months["MES_NUM"] = (months["IDX_MES"] % 12) + 1
    grid = pd.MultiIndex.from_product(
        [product_ids, months["IDX_MES"].tolist()],
        names=["CODIGO", "IDX_MES"],
    ).to_frame(index=False)
    grid = grid.merge(months, on="IDX_MES", how="left")
    complete = grid.merge(monthly, on=["CODIGO", "IDX_MES", "MES_NUM"], how="left")
    complete["QTD_VENDA_ESTOQUE"] = _to_number(complete["QTD_VENDA_ESTOQUE"]).fillna(0)
    return complete


def _linear_trend_by_product(monthly: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for codigo, group in monthly.groupby("CODIGO", dropna=False):
        x = _to_number(group["IDX_MES"]).to_numpy(dtype=float)
        y = _to_number(group["QTD_VENDA_ESTOQUE"]).fillna(0).to_numpy(dtype=float)
        if len(x) < 2 or np.all(y == 0):
            slope = 0.0
            intercept = float(np.mean(y)) if len(y) else 0.0
        else:
            design = np.vstack([x, np.ones(len(x))]).T
            slope, intercept = np.linalg.lstsq(design, y, rcond=None)[0]
        rows.append({"CODIGO": codigo, "slope": float(slope), "intercept": float(intercept)})
    return pd.DataFrame(rows)


def _seasonality_by_category(sales: pd.DataFrame, produtos: pd.DataFrame) -> pd.DataFrame:
    attrs = produtos[["CODIGO", "NIVEL_1"]].drop_duplicates("CODIGO")
    sales_cat = sales.merge(attrs, on="CODIGO", how="left", validate="many_to_one")
    grouped = (
        sales_cat.groupby(["NIVEL_1", "MES_NUM"], dropna=False)["QTD_VENDA_ESTOQUE"]
        .sum()
        .reset_index()
    )
    totals = (
        sales_cat.groupby("NIVEL_1", dropna=False)["QTD_VENDA_ESTOQUE"]
        .sum()
        .reset_index()
        .rename(columns={"QTD_VENDA_ESTOQUE": "total_categoria"})
    )
    grouped = grouped.merge(totals, on="NIVEL_1", how="left")
    grouped["indice_sazonal"] = metrics.safe_divide(
        grouped["QTD_VENDA_ESTOQUE"],
        grouped["total_categoria"] / 12,
    )
    return grouped[["NIVEL_1", "MES_NUM", "indice_sazonal"]]


def _future_month_grid(sales: pd.DataFrame, forecast_year: int) -> pd.DataFrame:
    start_idx = int(sales["IDX_MES"].max()) + 1
    future = pd.DataFrame(
        {
            "IDX_MES_FUT": range(start_idx, start_idx + 12),
            "MES_NUM": list(range(1, 13)),
            "ANO": forecast_year,
        }
    )
    return future


def _add_stock_reference(df: pd.DataFrame, estoque_inicial: pd.DataFrame | None) -> pd.DataFrame:
    out = df.copy()
    if estoque_inicial is None or estoque_inicial.empty:
        out["estoque_inicial_total_referencia"] = pd.NA
        return out
    _require_columns(estoque_inicial, {"CODIGO", "ESTOQUE_INICIAL"}, "estoque_inicial")
    stock = (
        estoque_inicial.groupby("CODIGO", dropna=False)["ESTOQUE_INICIAL"]
        .sum(min_count=1)
        .reset_index()
        .rename(columns={"ESTOQUE_INICIAL": "estoque_inicial_total_referencia"})
    )
    out = out.merge(stock, on="CODIGO", how="left")
    return out


def _coverage_allows_net_purchase(coverage_audit: pd.DataFrame | None) -> bool:
    if coverage_audit is None or coverage_audit.empty:
        return False
    required = {"nivel_agrupamento", "classificacao_confiabilidade"}
    if not required.issubset(coverage_audit.columns):
        return False
    total = coverage_audit[coverage_audit["nivel_agrupamento"].eq("periodo_total")]
    if total.empty:
        return False
    return bool(total["classificacao_confiabilidade"].astype(str).eq("OK").all())


def _projection_limitation(assortment_control: pd.DataFrame | None) -> str:
    base = (
        "NÃO VALIDADO: projeção usa venda observada e pode estar limitada por "
        "disponibilidade, mix, sazonalidade e cobertura parcial de entradas"
    )
    if assortment_control is None or assortment_control.empty:
        return base + "; DADO AUSENTE: controle de sortimento para censura operacional"
    if "status_sortimento_controlado" not in assortment_control.columns:
        return base
    statuses = set(assortment_control["status_sortimento_controlado"].dropna().astype(str))
    if "estreitamento_alem_do_esperado" in statuses:
        return base + "; há meses com sortimento observado abaixo do esperado dado o volume"
    return base


if __name__ == "__main__":
    outputs = generate_projection_outputs()
    print(
        "[SPEC06] projecao_venda_observada_2026.csv:",
        len(outputs["projecao_venda_observada_2026"]),
        "linhas",
    )
