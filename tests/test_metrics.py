# -*- coding: utf-8 -*-
"""Tests for Spec 03 metric catalog, business rules, and pure formulas."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
METRIC_CATALOG = ROOT / "docs" / "metric_catalog.md"
BUSINESS_RULES = ROOT / "docs" / "business_rules.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import metrics  # noqa: E402


def _read(path: Path) -> str:
    assert path.exists(), f"Arquivo ausente: {path}"
    return path.read_text(encoding="utf-8")


def test_spec_03_files_exist_and_are_not_empty():
    for path in [METRIC_CATALOG, BUSINESS_RULES, SRC / "metrics.py", ROOT / "tests" / "test_metrics.py"]:
        assert path.exists(), f"Arquivo ausente: {path}"
        assert path.stat().st_size > 1000, f"Arquivo incompleto: {path}"


@pytest.mark.parametrize("term", [
    "Receita bruta",
    "Quantidade vendida",
    "Quantidade vendida em unidade de armazenagem",
    "Ticket medio por linha diaria",
    "Preco medio vendido",
    "Numero de vendas/pedidos",
    "Linhas de venda diarias",
    "SKUs vendidos",
    "Receita por loja",
    "Receita por categoria",
    "Receita same-store YoY",
    "Variacao mensal",
    "Variacao YoY",
    "Dias com venda por loja/mes",
    "Estoque inicial",
    "Compras registradas",
    "Compras em unidade de armazenagem",
    "Gap contabil de estoque",
    "Cobertura de compras",
    "Cobertura em dias",
    "Preco medio mensal",
    "Dispersao de preco por loja",
    "Correlacao preco-volume",
    "Candidatos a investigacao de preco",
    "Venda observada projetada",
    "Demanda potencial",
    "Compra liquida sugerida",
    "Nivel de confianca da recomendacao",
])
def test_metric_catalog_documents_minimum_metrics(term):
    assert term in _read(METRIC_CATALOG)


def test_metric_catalog_covers_minimum_metric_families():
    text = _read(METRIC_CATALOG)
    for family in ["## Vendas", "## Compras e estoque", "## Precificacao", "## Projecao e recomendacao"]:
        assert family in text


def test_metric_catalog_marks_blocked_and_absent_items():
    text = _read(METRIC_CATALOG)
    for term in [
        "BLOQUEADA",
        "DADO AUSENTE",
        "Numero de vendas/pedidos",
        "Demanda potencial",
        "Compra liquida sugerida",
        "Custo, CMV e margem",
        "gap contabil, nunca prova de ruptura fisica",
    ]:
        assert term in text


@pytest.mark.parametrize("rule", [
    "Unidade comum de armazenagem",
    "Venda observada nao e demanda real",
    "Saldo negativo nao prova ruptura fisica",
    "Nulo de estoque nao e estoque zero",
    "Preco de compra nulo bloqueia CMV sem regra",
    "Loja atipica segmentada",
    "Comparacoes temporais respeitam sazonalidade",
    "Correlacao nao e causalidade",
    "Recomendacoes sao triagens",
])
def test_business_rules_document_all_minimum_rules(rule):
    assert rule in _read(BUSINESS_RULES)


@pytest.mark.parametrize("test_name", [
    "test_quantidade_compra_armazenagem_aplica_conversao",
    "test_gap_contabil_clip_positivo",
    "test_variacao_percentual_calcula_e_bloqueia_base_zero",
    "test_correlacao_preco_volume_respeita_minimo_observacoes",
])
def test_business_rules_reference_automated_tests(test_name):
    assert test_name in _read(BUSINESS_RULES)


def test_main_metric_functions_exist():
    for name in [
        "receita_bruta",
        "quantidade_total",
        "quantidade_vendida_armazenagem",
        "quantidade_compra_armazenagem",
        "linhas_venda_diarias",
        "skus_vendidos",
        "ticket_medio_linha",
        "preco_medio_vendido",
        "variacao_percentual",
        "cobertura_compras",
        "cobertura_dias",
        "gap_contabil_estoque",
        "preco_valido",
        "correlacao_preco_volume",
    ]:
        assert callable(getattr(metrics, name, None)), f"funcao ausente: {name}"


@pytest.fixture
def vendas_fixture():
    return pd.DataFrame({
        "CODIGO": [10, 10, 20],
        "COD_EMPRESA": [1, 1, 2],
        "QUANTIDADE_VENDIDA": [2.0, 3.0, 5.0],
        "CONVERSAO_VENDA_PARA_ARMAZENAGEM": [1.0, 2.0, 0.5],
        "PRECO_UNIT_MEDIO": [10.0, 20.0, 4.0],
    })


def test_receita_quantidade_preco_e_ticket(vendas_fixture):
    receita = metrics.receita_bruta(vendas_fixture)
    quantidade = metrics.quantidade_total(vendas_fixture)

    assert receita == pytest.approx(100.0)
    assert quantidade == pytest.approx(10.0)
    assert metrics.preco_medio_vendido(receita, quantidade) == pytest.approx(10.0)
    assert metrics.linhas_venda_diarias(vendas_fixture) == 3
    assert metrics.ticket_medio_linha(receita, 3) == pytest.approx(100.0 / 3.0)
    assert metrics.skus_vendidos(vendas_fixture) == 2


def test_quantidade_vendida_armazenagem(vendas_fixture):
    assert metrics.quantidade_vendida_armazenagem(vendas_fixture) == pytest.approx(10.5)


def test_quantidade_compra_armazenagem_aplica_conversao():
    compras = pd.DataFrame({
        "QUANTIDADE_COMPRA": [10.0, 3.0],
        "CONVERSAO_COMPRA_ARMAZENAGEM": [12.0, 1.5],
    })

    assert metrics.quantidade_compra_armazenagem(compras) == pytest.approx(124.5)


def test_variacao_percentual_calcula_e_bloqueia_base_zero():
    assert metrics.variacao_percentual(80, 100) == pytest.approx(-0.2)
    assert pd.isna(metrics.variacao_percentual(80, 0))
    assert pd.isna(metrics.variacao_percentual(None, 100))


def test_cobertura_compras_calcula_lojas_e_produtos():
    compras = pd.DataFrame({
        "COD_EMPRESA": [1, 1, 2, 2],
        "CODIGO": [10, 20, 10, 30],
    })

    result = metrics.cobertura_compras(compras, total_lojas=4, total_produtos=6)

    assert result["lojas_com_compra"] == 2
    assert result["produtos_com_compra"] == 3
    assert result["pct_lojas"] == pytest.approx(0.5)
    assert result["pct_produtos"] == pytest.approx(0.5)


def test_gap_contabil_clip_positivo():
    assert metrics.gap_contabil_estoque(100, 40, 30) == 30
    assert metrics.gap_contabil_estoque(50, 40, 30) == 0

    result = metrics.gap_contabil_estoque(
        pd.Series([100, 50]),
        pd.Series([40, 40]),
        pd.Series([30, 30]),
    )
    assert result.tolist() == [30, 0]


def test_divisao_por_zero_e_dados_vazios_sem_inf():
    assert pd.isna(metrics.ticket_medio_linha(100, 0))
    assert pd.isna(metrics.preco_medio_vendido(100, 0))
    assert pd.isna(metrics.cobertura_dias(10, 0))
    assert metrics.receita_bruta(pd.DataFrame()) == 0.0
    assert metrics.quantidade_total(pd.DataFrame()) == 0.0
    assert metrics.linhas_venda_diarias(pd.DataFrame()) == 0

    divided = metrics.safe_divide([1, 2, 3], [1, 0, None])
    assert divided.iloc[0] == 1
    assert pd.isna(divided.iloc[1])
    assert pd.isna(divided.iloc[2])


def test_preco_valido_trata_zero_como_sem_preco_valido():
    result = metrics.preco_valido([10.0, 0.0, -1.0, None])
    assert result.iloc[0] == pytest.approx(10.0)
    assert pd.isna(result.iloc[1])
    assert pd.isna(result.iloc[2])
    assert pd.isna(result.iloc[3])


def test_correlacao_preco_volume_respeita_minimo_observacoes():
    few = pd.DataFrame({
        "preco_medio_mensal": [10, 11, 12],
        "quantidade_mensal": [100, 90, 80],
    })
    enough = pd.DataFrame({
        "preco_medio_mensal": [10, 11, 12, 13, 14, 15, 16, 17],
        "quantidade_mensal": [100, 95, 90, 85, 80, 75, 70, 65],
    })

    assert pd.isna(metrics.correlacao_preco_volume(few))
    assert metrics.correlacao_preco_volume(enough) == pytest.approx(-1.0)


def test_formulas_documentadas_batem_com_codigo():
    catalog = _read(METRIC_CATALOG)

    for formula_id, formula in metrics.FORMULAS.items():
        assert formula_id in catalog
        assert f"`{formula}`" in catalog
