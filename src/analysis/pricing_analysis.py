# -*- coding: utf-8 -*-
"""Exploratory price-volume association analysis for Spec 06.

This module deliberately treats price-volume results as correlation only. It
does not estimate causal effects and does not produce final pricing decisions.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

import metrics


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES_DIR = ROOT / "outputs" / "tables"

MIN_CORRELATION_OBS = 8
NEGATIVE_CORRELATION_THRESHOLD = -0.4

CORRELATION_STATUS = {
    "correlacao_calculada",
    "DADO AUSENTE",
}


def _require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{name}: colunas obrigatorias ausentes: {missing}")


def _to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def prepare_monthly_price_volume(vendas: pd.DataFrame) -> pd.DataFrame:
    """Aggregate observed sales to product-store-month price and volume."""
    _require_columns(
        vendas,
        {
            "DATA_VENDA",
            "CODIGO",
            "COD_EMPRESA",
            "QUANTIDADE_VENDIDA",
            "PRECO_UNIT_MEDIO",
        },
        "vendas",
    )

    out = vendas.copy()
    out["DATA_VENDA"] = pd.to_datetime(out["DATA_VENDA"])
    out["ANO_MES"] = out["DATA_VENDA"].dt.to_period("M").astype(str)

    if "RECEITA" not in out.columns:
        out["RECEITA"] = (
            _to_number(out["QUANTIDADE_VENDIDA"]).fillna(0)
            * _to_number(out["PRECO_UNIT_MEDIO"]).fillna(0)
        )
    if "QTD_VENDA_ESTOQUE" not in out.columns:
        conversion = (
            _to_number(out["CONVERSAO_VENDA_PARA_ARMAZENAGEM"]).fillna(1)
            if "CONVERSAO_VENDA_PARA_ARMAZENAGEM" in out.columns
            else 1
        )
        out["QTD_VENDA_ESTOQUE"] = _to_number(out["QUANTIDADE_VENDIDA"]).fillna(0) * conversion

    monthly = (
        out.groupby(["CODIGO", "COD_EMPRESA", "ANO_MES"], dropna=False)
        .agg(
            quantidade_mensal=("QTD_VENDA_ESTOQUE", "sum"),
            receita_mensal=("RECEITA", "sum"),
            linhas_venda_diarias=("CODIGO", "size"),
        )
        .reset_index()
    )
    monthly["preco_medio_mensal"] = metrics.safe_divide(
        monthly["receita_mensal"],
        monthly["quantidade_mensal"],
    )
    return monthly


def build_price_volume_correlation(
    vendas: pd.DataFrame,
    produtos: pd.DataFrame | None = None,
    min_obs: int = MIN_CORRELATION_OBS,
) -> pd.DataFrame:
    """Calculate product-level exploratory price-volume correlations."""
    monthly = prepare_monthly_price_volume(vendas)
    rows: list[dict[str, Any]] = []

    for codigo, group in monthly.groupby("CODIGO", dropna=False):
        clean = group[["preco_medio_mensal", "quantidade_mensal"]].apply(
            pd.to_numeric,
            errors="coerce",
        ).dropna()
        n_obs = int(len(clean))
        receita_total = float(group["receita_mensal"].sum())
        quantidade_total = float(group["quantidade_mensal"].sum())
        preco_distintos = int(clean["preco_medio_mensal"].nunique()) if n_obs else 0
        volume_distintos = int(clean["quantidade_mensal"].nunique()) if n_obs else 0

        if n_obs < min_obs or preco_distintos < 3 or volume_distintos < 2 or quantidade_total <= 0:
            correlation = pd.NA
            status = "DADO AUSENTE"
        else:
            correlation = metrics.correlacao_preco_volume(
                clean,
                preco_col="preco_medio_mensal",
                volume_col="quantidade_mensal",
                min_obs=min_obs,
            )
            status = "correlacao_calculada" if pd.notna(correlation) else "DADO AUSENTE"

        rows.append(
            {
                "CODIGO": codigo,
                "correlacao_preco_volume": correlation,
                "n_obs": n_obs,
                "min_obs_exigido": int(min_obs),
                "precos_mensais_distintos": preco_distintos,
                "volumes_mensais_distintos": volume_distintos,
                "receita_total": receita_total,
                "quantidade_total_observada": quantidade_total,
                "status_correlacao": status,
                "tipo_analise": "associacao exploratoria",
                "interpretacao": "correlacao observacional; nao estabelece efeito causal",
                "limitacao": (
                    "NÃO VALIDADO: sazonalidade, mix, campanhas, disponibilidade e loja "
                    "podem variar junto com preco e volume"
                ),
            }
        )

    result = pd.DataFrame(rows)
    if produtos is not None and not produtos.empty:
        _require_columns(produtos, {"CODIGO"}, "produtos")
        keep = [column for column in ["CODIGO", "DESCRICAO", "NIVEL_1"] if column in produtos.columns]
        result = result.merge(
            produtos[keep].drop_duplicates("CODIGO"),
            on="CODIGO",
            how="left",
            validate="one_to_one",
        )

    ordered = [
        "CODIGO",
        "DESCRICAO",
        "NIVEL_1",
        "correlacao_preco_volume",
        "n_obs",
        "min_obs_exigido",
        "precos_mensais_distintos",
        "volumes_mensais_distintos",
        "receita_total",
        "quantidade_total_observada",
        "status_correlacao",
        "tipo_analise",
        "interpretacao",
        "limitacao",
    ]
    existing = [column for column in ordered if column in result.columns]
    return result[existing].sort_values(["correlacao_preco_volume", "CODIGO"], na_position="last").reset_index(drop=True)


def select_negative_price_volume_candidates(
    correlations: pd.DataFrame,
    threshold: float = NEGATIVE_CORRELATION_THRESHOLD,
) -> pd.DataFrame:
    """Select high-revenue products with strong negative exploratory correlation."""
    _require_columns(
        correlations,
        {"CODIGO", "correlacao_preco_volume", "receita_total", "status_correlacao"},
        "correlations",
    )
    valid = correlations[
        correlations["status_correlacao"].eq("correlacao_calculada")
        & pd.to_numeric(correlations["correlacao_preco_volume"], errors="coerce").notna()
    ].copy()
    if valid.empty:
        return valid

    revenue_cutoff = valid["receita_total"].quantile(0.5)
    candidates = valid[
        valid["correlacao_preco_volume"].lt(threshold)
        & valid["receita_total"].ge(revenue_cutoff)
    ].copy()
    if candidates.empty:
        return candidates
    candidates["tipo_triagem"] = "investigacao_preco_correlacao"
    candidates["nivel_confianca"] = "Baixa"
    candidates["regra_usada"] = (
        f"correlacao_preco_volume < {threshold} e receita acima da mediana dos produtos validos"
    )
    candidates["evidencia"] = candidates.apply(
        lambda row: (
            f"correlacao={row['correlacao_preco_volume']:.4f}; "
            f"n_obs={int(row['n_obs'])}; receita_total={row['receita_total']:.2f}"
        ),
        axis=1,
    )
    candidates["acao_recomendada"] = (
        "Investigar cadastro, margem, concorrencia e campanhas antes de teste comercial controlado"
    )
    return candidates.sort_values("correlacao_preco_volume").reset_index(drop=True)


def generate_pricing_outputs(
    processed_dir: Path = PROCESSED_DIR,
    output_dir: Path = OUTPUT_TABLES_DIR,
) -> dict[str, pd.DataFrame]:
    """Read processed data and write Spec 06 pricing CSV output."""
    vendas = pd.read_parquet(processed_dir / "fato_vendas.parquet")
    produtos = pd.read_parquet(processed_dir / "dim_produto.parquet")

    correlations = build_price_volume_correlation(vendas, produtos)
    negative = select_negative_price_volume_candidates(correlations)

    output_dir.mkdir(parents=True, exist_ok=True)
    negative.to_csv(
        output_dir / "produtos_correlacao_preco_volume_negativa.csv",
        index=False,
        encoding="utf-8",
    )
    return {
        "correlacao_preco_volume": correlations,
        "produtos_correlacao_preco_volume_negativa": negative,
    }


if __name__ == "__main__":
    outputs = generate_pricing_outputs()
    print(
        "[SPEC06] produtos_correlacao_preco_volume_negativa.csv:",
        len(outputs["produtos_correlacao_preco_volume_negativa"]),
        "linhas",
    )
