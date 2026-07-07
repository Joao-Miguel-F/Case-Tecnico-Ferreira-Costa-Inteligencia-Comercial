# -*- coding: utf-8 -*-
"""Tests for Spec 04 inventory and purchase reconciliation."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import inventory_reconciliation as inv  # noqa: E402


REQUIRED_COVERAGE_COLUMNS = {
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
    "classificacao_confiabilidade",
    "formula_compras_armazenagem",
    "formula_vendas_armazenagem",
    "interpretacao",
    "limitacao",
}

REQUIRED_GAP_COLUMNS = {
    "COD_EMPRESA",
    "CODIGO",
    "ESTOQUE_INICIAL",
    "COMPRAS_REGISTRADAS_ESTOQUE",
    "VENDAS_ESTOQUE",
    "ENTRADAS_CONHECIDAS_ESTOQUE",
    "SALDO_PROJETADO_CONTABIL",
    "GAP_CONTABIL_ESTOQUE",
    "VENDA_SEM_COMPRA_REGISTRADA",
    "INTERPRETACAO_SALDO_NEGATIVO",
    "POSSIVEIS_CAUSAS_GAP",
}


@pytest.fixture
def produtos_fixture():
    return pd.DataFrame(
        {
            "CODIGO": [10, 20],
            "DESCRICAO": ["Produto A", "Produto B"],
            "NIVEL_1": ["Categoria 1", "Categoria 2"],
            "CONVERSAO_COMPRA_ARMAZENAGEM": [12.0, 2.0],
        }
    )


@pytest.fixture
def compras_fixture():
    return pd.DataFrame(
        {
            "DATA_ENTRADA": pd.to_datetime(["2024-01-03", "2024-01-04"]),
            "COD_EMPRESA": [1, 1],
            "CODIGO": [10, 20],
            "QUANTIDADE_COMPRA": [3.0, 5.0],
        }
    )


@pytest.fixture
def vendas_fixture():
    return pd.DataFrame(
        {
            "DATA_VENDA": pd.to_datetime(["2024-01-05", "2024-01-05", "2024-02-01"]),
            "COD_EMPRESA": [1, 1, 1],
            "CODIGO": [10, 20, 20],
            "QUANTIDADE_VENDIDA": [40.0, 5.0, 20.0],
            "CONVERSAO_VENDA_PARA_ARMAZENAGEM": [1.0, 2.0, 2.0],
        }
    )


@pytest.fixture
def estoque_fixture():
    return pd.DataFrame(
        {
            "COD_EMPRESA": [1, 1],
            "CODIGO": [10, 20],
            "ESTOQUE_INICIAL": [1.0, 0.0],
        }
    )


def test_compra_em_unidade_armazenagem_aplica_conversao(compras_fixture, produtos_fixture):
    result = inv.with_purchase_storage_quantity(compras_fixture, produtos_fixture)

    assert result.loc[result["CODIGO"].eq(10), "QTD_COMPRA_ESTOQUE"].iloc[0] == pytest.approx(36.0)
    assert result.loc[result["CODIGO"].eq(20), "QTD_COMPRA_ESTOQUE"].iloc[0] == pytest.approx(10.0)
    assert inv.PURCHASE_STORAGE_FORMULA in result.attrs.get("formula", inv.PURCHASE_STORAGE_FORMULA)


def test_venda_em_unidade_armazenagem_e_validada(vendas_fixture):
    vendas = vendas_fixture.copy()
    vendas["QTD_VENDA_ESTOQUE"] = [40.0, 10.0, 40.0]

    result = inv.with_sales_storage_quantity(vendas)

    assert result["QTD_VENDA_ESTOQUE"].sum() == pytest.approx(90.0)


def test_venda_em_unidade_armazenagem_rejeita_divergencia(vendas_fixture):
    vendas = vendas_fixture.copy()
    vendas["QTD_VENDA_ESTOQUE"] = [999.0, 10.0, 40.0]

    with pytest.raises(ValueError, match="diverge"):
        inv.with_sales_storage_quantity(vendas)


def test_gap_contabil_por_produto_loja_nunca_fica_negativo(
    vendas_fixture,
    compras_fixture,
    estoque_fixture,
    produtos_fixture,
):
    gaps = inv.build_pair_reconciliation(vendas_fixture, compras_fixture, estoque_fixture, produtos_fixture)

    produto_10 = gaps[gaps["CODIGO"].eq(10)].iloc[0]
    produto_20 = gaps[gaps["CODIGO"].eq(20)].iloc[0]

    assert produto_10["ENTRADAS_CONHECIDAS_ESTOQUE"] == pytest.approx(37.0)
    assert produto_10["VENDAS_ESTOQUE"] == pytest.approx(40.0)
    assert produto_10["SALDO_PROJETADO_CONTABIL"] == pytest.approx(-3.0)
    assert produto_10["GAP_CONTABIL_ESTOQUE"] == pytest.approx(3.0)
    assert produto_20["GAP_CONTABIL_ESTOQUE"] == pytest.approx(40.0)
    assert gaps["GAP_CONTABIL_ESTOQUE"].dropna().ge(0).all()


def test_saldo_negativo_nao_e_classificado_como_ruptura_fisica(
    vendas_fixture,
    compras_fixture,
    estoque_fixture,
    produtos_fixture,
):
    gaps = inv.build_pair_reconciliation(vendas_fixture, compras_fixture, estoque_fixture, produtos_fixture)
    text = gaps.to_csv(index=False).lower()

    assert "gap contabil" in text
    assert "ruptura" not in text


def test_auditoria_de_cobertura_por_niveis_e_classificacao(
    vendas_fixture,
    compras_fixture,
    estoque_fixture,
    produtos_fixture,
):
    gaps = inv.build_pair_reconciliation(vendas_fixture, compras_fixture, estoque_fixture, produtos_fixture)
    ledger = inv.build_movement_ledger(vendas_fixture, compras_fixture, estoque_fixture, produtos_fixture)
    audit = inv.build_coverage_audit(gaps, ledger)

    assert REQUIRED_COVERAGE_COLUMNS.issubset(audit.columns)
    assert {"periodo_total", "mes", "loja", "categoria", "produto"}.issubset(
        set(audit["nivel_agrupamento"])
    )
    assert set(audit["classificacao_confiabilidade"]).issubset(inv.CONFIDENCE_CLASSES)
    assert "QTD_COMPRA_ESTOQUE = QUANTIDADE_COMPRA * CONVERSAO_COMPRA_ARMAZENAGEM" in set(
        audit["formula_compras_armazenagem"]
    )


def test_caso_sem_compras_e_limitacao_nao_prova_causal(
    vendas_fixture,
    estoque_fixture,
    produtos_fixture,
):
    compras_vazias = pd.DataFrame(
        columns=["DATA_ENTRADA", "COD_EMPRESA", "CODIGO", "QUANTIDADE_COMPRA"]
    )
    gaps = inv.build_pair_reconciliation(vendas_fixture, compras_vazias, estoque_fixture, produtos_fixture)
    ledger = inv.build_movement_ledger(vendas_fixture, compras_vazias, estoque_fixture, produtos_fixture)
    audit = inv.build_coverage_audit(gaps, ledger)

    total = audit[audit["nivel_agrupamento"].eq("periodo_total")].iloc[0]
    assert total["pares_venda_sem_compra"] == 2
    assert total["classificacao_confiabilidade"] == "não confiável para análise causal"
    assert "não evidencia causal" in total["interpretacao"]


def test_outputs_gerados_em_diretorio_temporario(
    tmp_path,
    vendas_fixture,
    compras_fixture,
    estoque_fixture,
    produtos_fixture,
):
    processed = tmp_path / "processed"
    outputs = tmp_path / "outputs"
    processed.mkdir()

    vendas_fixture.to_parquet(processed / "fato_vendas.parquet", index=False)
    compras_fixture.to_parquet(processed / "fato_compras.parquet", index=False)
    estoque_fixture.to_parquet(processed / "fato_estoque_inicial.parquet", index=False)
    produtos_fixture.to_parquet(processed / "dim_produto.parquet", index=False)

    result = inv.generate_reconciliation_outputs(processed, outputs)

    coverage_path = outputs / "compras_coverage_audit.csv"
    gaps_path = outputs / "gaps_saldo_contabil_estoque.csv"
    assert coverage_path.exists()
    assert gaps_path.exists()
    assert not result["compras_coverage_audit"].empty
    assert not result["gaps_saldo_contabil_estoque"].empty
    assert REQUIRED_COVERAGE_COLUMNS.issubset(pd.read_csv(coverage_path).columns)
    assert REQUIRED_GAP_COLUMNS.issubset(pd.read_csv(gaps_path).columns)
