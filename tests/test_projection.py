# -*- coding: utf-8 -*-
"""Tests for Spec 06 observed-sales projection."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis import projection_analysis as projection  # noqa: E402


REQUIRED_PROJECTION_COLUMNS = {
    "CODIGO",
    "venda_observada_projetada_2026",
    "venda_media_anual_observada_historica",
    "compra_bruta_sugerida",
    "compra_liquida_sugerida",
    "status_compra_liquida",
    "flag_nao_calcular_compra_liquida_por_estoque_inconfiavel",
    "nivel_confianca",
    "limitacao",
    "acao_recomendada",
}


def vendas_projection_fixture() -> pd.DataFrame:
    months = pd.date_range("2024-01-01", periods=12, freq="MS")
    rows = []
    for idx, month in enumerate(months):
        quantity = 10 + idx
        rows.append(
            {
                "DATA_VENDA": month,
                "COD_EMPRESA": 1,
                "CODIGO": 10,
                "QUANTIDADE_VENDIDA": float(quantity),
                "CONVERSAO_VENDA_PARA_ARMAZENAGEM": 1.0,
                "PRECO_UNIT_MEDIO": 5.0,
                "RECEITA": float(quantity * 5),
                "QTD_VENDA_ESTOQUE": float(quantity),
            }
        )
    return pd.DataFrame(rows)


def produtos_projection_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CODIGO": [10],
            "DESCRICAO": ["Produto A"],
            "NIVEL_1": ["A - TESTE"],
        }
    )


def estoque_fixture() -> pd.DataFrame:
    return pd.DataFrame({"COD_EMPRESA": [1], "CODIGO": [10], "ESTOQUE_INICIAL": [25.0]})


def coverage_unreliable_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "nivel_agrupamento": ["periodo_total"],
            "classificacao_confiabilidade": ["não confiável para análise causal"],
        }
    )


def assortment_fixture() -> pd.DataFrame:
    return pd.DataFrame({"status_sortimento_controlado": ["estreitamento_alem_do_esperado"]})


def test_projecao_usa_venda_observada_e_nao_nomeia_demanda_real():
    result = projection.build_observed_sales_projection(
        vendas_projection_fixture(),
        produtos_projection_fixture(),
        estoque_inicial=estoque_fixture(),
        coverage_audit=coverage_unreliable_fixture(),
        assortment_control=assortment_fixture(),
    )
    row = result.iloc[0]

    assert REQUIRED_PROJECTION_COLUMNS.issubset(result.columns)
    assert row["venda_observada_projetada_2026"] > 0
    assert row["compra_bruta_sugerida"] > row["venda_observada_projetada_2026"]
    assert all("demanda real" not in column.lower() for column in result.columns)
    assert "venda observada" in row["limitacao"]
    assert "NÃO VALIDADO" in row["limitacao"]


def test_compra_liquida_fica_bloqueada_quando_estoque_confiavel_falta():
    result = projection.build_observed_sales_projection(
        vendas_projection_fixture(),
        produtos_projection_fixture(),
        estoque_inicial=estoque_fixture(),
        coverage_audit=coverage_unreliable_fixture(),
    )
    row = result.iloc[0]

    assert row["status_compra_liquida"] == "BLOQUEADO"
    assert bool(row["flag_nao_calcular_compra_liquida_por_estoque_inconfiavel"]) is True
    assert pd.isna(row["compra_liquida_sugerida"])
    assert row["nivel_confianca"] == "Baixa"
    assert "DADO AUSENTE" in row["estoque_a_validar_antes_da_compra"]


def test_output_projection_gerado_em_diretorio_temporario(tmp_path):
    processed = tmp_path / "processed"
    outputs = tmp_path / "outputs"
    processed.mkdir()
    outputs.mkdir()

    vendas_projection_fixture().to_parquet(processed / "fato_vendas.parquet", index=False)
    produtos_projection_fixture().to_parquet(processed / "dim_produto.parquet", index=False)
    estoque_fixture().to_parquet(processed / "fato_estoque_inicial.parquet", index=False)
    coverage_unreliable_fixture().to_csv(outputs / "compras_coverage_audit.csv", index=False)
    assortment_fixture().to_csv(outputs / "sortimento_controlado_por_volume.csv", index=False)

    generated = projection.generate_projection_outputs(processed, outputs)
    output_path = outputs / "projecao_venda_observada_2026.csv"
    saved = pd.read_csv(output_path)

    assert output_path.exists()
    assert not generated["projecao_venda_observada_2026"].empty
    assert REQUIRED_PROJECTION_COLUMNS.issubset(saved.columns)
    assert "demanda_real" not in saved.to_csv(index=False).lower()
