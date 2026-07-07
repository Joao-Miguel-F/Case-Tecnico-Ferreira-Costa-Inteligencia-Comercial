# -*- coding: utf-8 -*-
"""Assortment analysis controlled by observed sales-line volume for Spec 05."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_TABLES_DIR = ROOT / "outputs" / "tables"

ASSORTMENT_STATUS = {
    "DADO AUSENTE",
    "dados insuficientes",
    "dentro_do_esperado",
    "estreitamento_alem_do_esperado",
    "ampliacao_alem_do_esperado",
}


def _require_columns(df: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{name}: colunas obrigatorias ausentes: {missing}")


def prepare_assortment_sales(vendas: pd.DataFrame) -> pd.DataFrame:
    """Return sales with month and explicit revenue for assortment summaries."""
    _require_columns(vendas, {"DATA_VENDA", "CODIGO", "QUANTIDADE_VENDIDA", "PRECO_UNIT_MEDIO"}, "vendas")
    out = vendas.copy()
    out["DATA_VENDA"] = pd.to_datetime(out["DATA_VENDA"])
    out["ANO_MES_PERIOD"] = out["DATA_VENDA"].dt.to_period("M")
    out["ANO_MES"] = out["ANO_MES_PERIOD"].astype(str)
    if "RECEITA" not in out.columns:
        out["RECEITA"] = (
            pd.to_numeric(out["QUANTIDADE_VENDIDA"], errors="coerce").fillna(0)
            * pd.to_numeric(out["PRECO_UNIT_MEDIO"], errors="coerce").fillna(0)
        )
    if "QTD_VENDA_ESTOQUE" not in out.columns and "CONVERSAO_VENDA_PARA_ARMAZENAGEM" in out.columns:
        out["QTD_VENDA_ESTOQUE"] = (
            pd.to_numeric(out["QUANTIDADE_VENDIDA"], errors="coerce").fillna(0)
            * pd.to_numeric(out["CONVERSAO_VENDA_PARA_ARMAZENAGEM"], errors="coerce").fillna(0)
        )
    return out


def observed_monthly_assortment(vendas: pd.DataFrame) -> pd.DataFrame:
    """Count observed SKUs and daily sales lines by month."""
    sales = prepare_assortment_sales(vendas)
    return (
        sales.groupby("ANO_MES_PERIOD", dropna=False)
        .agg(
            skus_observados=("CODIGO", "nunique"),
            linhas_venda_diarias=("CODIGO", "size"),
            receita=("RECEITA", "sum"),
            qtd_vendida_estoque=(
                "QTD_VENDA_ESTOQUE" if "QTD_VENDA_ESTOQUE" in sales.columns else "QUANTIDADE_VENDIDA",
                "sum",
            ),
        )
        .reset_index()
        .assign(ANO_MES=lambda df: df["ANO_MES_PERIOD"].astype(str))
        .sort_values("ANO_MES_PERIOD")
        .reset_index(drop=True)
    )


def build_assortment_controlled_by_volume(
    vendas: pd.DataFrame,
    iterations: int = 120,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Estimate expected observed assortment from prior-year same-month mix.

    The control uses the number of daily sales lines in the current month as the
    sample size and the prior-year same-month line mix as the reference
    distribution. Missing prior-year months are explicitly marked.
    """
    sales = prepare_assortment_sales(vendas)
    observed = observed_monthly_assortment(sales)
    rng = np.random.default_rng(random_seed)
    rows: list[dict[str, Any]] = []

    for row in observed.itertuples(index=False):
        month = row.ANO_MES_PERIOD
        reference_month = month - 12
        reference = sales.loc[sales["ANO_MES_PERIOD"].eq(reference_month), "CODIGO"].dropna()
        current_lines = int(row.linhas_venda_diarias)

        result = {
            "ANO_MES": row.ANO_MES,
            "skus_observados": int(row.skus_observados),
            "linhas_venda_diarias": current_lines,
            "receita": float(row.receita),
            "qtd_vendida_estoque": float(row.qtd_vendida_estoque),
            "mes_referencia_mix": str(reference_month),
            "linhas_referencia_mix": int(len(reference)),
            "skus_referencia_mix": int(reference.nunique()) if len(reference) else 0,
            "iteracoes_bootstrap": int(iterations),
            "interpretacao": (
                "sortimento observado controlado por volume de linhas de venda diarias; "
                "evidencia descritiva, nao prova disponibilidade fisica"
            ),
        }

        if current_lines <= 0:
            rows.append(_with_missing_estimate(result, "dados insuficientes"))
            continue
        if reference.empty:
            rows.append(_with_missing_estimate(result, "DADO AUSENTE"))
            continue

        sample_counts = _bootstrap_unique_counts(
            reference.to_numpy(),
            sample_size=current_lines,
            iterations=iterations,
            rng=rng,
        )
        result["skus_esperados_media"] = float(np.mean(sample_counts))
        result["skus_esperados_p05"] = float(np.percentile(sample_counts, 5))
        result["skus_esperados_p50"] = float(np.percentile(sample_counts, 50))
        result["skus_esperados_p95"] = float(np.percentile(sample_counts, 95))
        result["diferenca_skus_vs_esperado"] = float(row.skus_observados - result["skus_esperados_media"])
        result["razao_skus_observado_esperado"] = (
            float(row.skus_observados / result["skus_esperados_media"])
            if result["skus_esperados_media"]
            else pd.NA
        )
        result["status_sortimento_controlado"] = _classify_assortment(
            observed_skus=int(row.skus_observados),
            p05=result["skus_esperados_p05"],
            p95=result["skus_esperados_p95"],
        )
        rows.append(result)

    columns = [
        "ANO_MES",
        "skus_observados",
        "linhas_venda_diarias",
        "receita",
        "qtd_vendida_estoque",
        "mes_referencia_mix",
        "linhas_referencia_mix",
        "skus_referencia_mix",
        "skus_esperados_media",
        "skus_esperados_p05",
        "skus_esperados_p50",
        "skus_esperados_p95",
        "diferenca_skus_vs_esperado",
        "razao_skus_observado_esperado",
        "status_sortimento_controlado",
        "iteracoes_bootstrap",
        "interpretacao",
    ]
    return pd.DataFrame(rows, columns=columns)


def generate_assortment_outputs(
    processed_dir: Path = PROCESSED_DIR,
    output_dir: Path = OUTPUT_TABLES_DIR,
    iterations: int = 120,
    random_seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """Read processed sales and write Spec 05 assortment CSV output."""
    vendas = pd.read_parquet(processed_dir / "fato_vendas.parquet")
    assortment = build_assortment_controlled_by_volume(
        vendas,
        iterations=iterations,
        random_seed=random_seed,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    assortment.to_csv(
        output_dir / "sortimento_controlado_por_volume.csv",
        index=False,
        encoding="utf-8",
    )
    return {"sortimento_controlado_por_volume": assortment}


def _bootstrap_unique_counts(
    reference_codes: np.ndarray,
    sample_size: int,
    iterations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    counts = np.empty(iterations, dtype=float)
    for index in range(iterations):
        sample = rng.choice(reference_codes, size=sample_size, replace=True)
        counts[index] = len(np.unique(sample))
    return counts


def _classify_assortment(observed_skus: int, p05: float, p95: float) -> str:
    if observed_skus < p05:
        return "estreitamento_alem_do_esperado"
    if observed_skus > p95:
        return "ampliacao_alem_do_esperado"
    return "dentro_do_esperado"


def _with_missing_estimate(row: dict[str, Any], status: str) -> dict[str, Any]:
    row["skus_esperados_media"] = pd.NA
    row["skus_esperados_p05"] = pd.NA
    row["skus_esperados_p50"] = pd.NA
    row["skus_esperados_p95"] = pd.NA
    row["diferenca_skus_vs_esperado"] = pd.NA
    row["razao_skus_observado_esperado"] = pd.NA
    row["status_sortimento_controlado"] = status
    return row


if __name__ == "__main__":
    outputs = generate_assortment_outputs()
    print(
        "[SPEC05] sortimento_controlado_por_volume.csv:",
        len(outputs["sortimento_controlado_por_volume"]),
        "linhas",
    )
