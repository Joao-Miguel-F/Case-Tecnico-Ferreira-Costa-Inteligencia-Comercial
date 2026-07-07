# -*- coding: utf-8 -*-
"""Tests for Spec 06 pricing analysis."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis import pricing_analysis as pricing  # noqa: E402


REQUIRED_NEGATIVE_COLUMNS = {
    "CODIGO",
    "correlacao_preco_volume",
    "n_obs",
    "min_obs_exigido",
    "status_correlacao",
    "tipo_analise",
    "interpretacao",
    "limitacao",
}


def vendas_pricing_fixture() -> pd.DataFrame:
    months = pd.date_range("2024-01-01", periods=8, freq="MS")
    rows = []
    for idx, month in enumerate(months):
        price = 10 + idx
        quantity = 80 - idx * 5
        rows.append(
            {
                "DATA_VENDA": month,
                "COD_EMPRESA": 1,
                "CODIGO": 10,
                "QUANTIDADE_VENDIDA": float(quantity),
                "CONVERSAO_VENDA_PARA_ARMAZENAGEM": 1.0,
                "PRECO_UNIT_MEDIO": float(price),
                "RECEITA": float(price * quantity),
                "QTD_VENDA_ESTOQUE": float(quantity),
            }
        )
    for idx, month in enumerate(months[:4]):
        rows.append(
            {
                "DATA_VENDA": month,
                "COD_EMPRESA": 1,
                "CODIGO": 20,
                "QUANTIDADE_VENDIDA": 10.0,
                "CONVERSAO_VENDA_PARA_ARMAZENAGEM": 1.0,
                "PRECO_UNIT_MEDIO": float(20 + idx),
                "RECEITA": float((20 + idx) * 10),
                "QTD_VENDA_ESTOQUE": 10.0,
            }
        )
    return pd.DataFrame(rows)


def produtos_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CODIGO": [10, 20],
            "DESCRICAO": ["Produto A", "Produto B"],
            "NIVEL_1": ["A - TESTE", "B - TESTE"],
        }
    )


def test_correlacao_preco_volume_calcula_associacao_sem_causalidade():
    result = pricing.build_price_volume_correlation(vendas_pricing_fixture(), produtos_fixture())
    product = result[result["CODIGO"].eq(10)].iloc[0]

    assert REQUIRED_NEGATIVE_COLUMNS.issubset(result.columns)
    assert product["correlacao_preco_volume"] == pytest.approx(-1.0)
    assert product["n_obs"] == 8
    assert product["tipo_analise"] == "associacao exploratoria"
    assert "correlacao observacional" in product["interpretacao"]
    assert "nao estabelece efeito causal" in product["interpretacao"]


def test_produto_com_poucos_pontos_fica_com_dado_ausente():
    result = pricing.build_price_volume_correlation(vendas_pricing_fixture(), produtos_fixture())
    product = result[result["CODIGO"].eq(20)].iloc[0]

    assert pd.isna(product["correlacao_preco_volume"])
    assert product["status_correlacao"] == "DADO AUSENTE"
    assert product["n_obs"] == 4
    assert product["min_obs_exigido"] == pricing.MIN_CORRELATION_OBS


def test_output_pricing_gerado_sem_palavra_proibida_no_nome_ou_colunas(tmp_path):
    processed = tmp_path / "processed"
    outputs = tmp_path / "outputs"
    processed.mkdir()
    vendas_pricing_fixture().to_parquet(processed / "fato_vendas.parquet", index=False)
    produtos_fixture().to_parquet(processed / "dim_produto.parquet", index=False)

    generated = pricing.generate_pricing_outputs(processed, outputs)
    output_path = outputs / "produtos_correlacao_preco_volume_negativa.csv"
    saved = pd.read_csv(output_path)

    assert output_path.exists()
    assert not generated["produtos_correlacao_preco_volume_negativa"].empty
    assert REQUIRED_NEGATIVE_COLUMNS.issubset(saved.columns)
    assert "elasticidade" not in output_path.name.lower()
    assert all("elasticidade" not in column.lower() for column in saved.columns)
    assert "efeito causal" in saved["interpretacao"].iloc[0]
