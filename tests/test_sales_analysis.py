# -*- coding: utf-8 -*-
"""Tests for Spec 05 sales, store, and category analysis."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DOC = ROOT / "docs" / "sales_store_category_assortment.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis import sales_analysis as sales  # noqa: E402


REQUIRED_STORE_COLUMNS = {
    "ANO_MES",
    "COD_EMPRESA",
    "receita",
    "receita_ano_anterior",
    "variacao_receita_yoy",
    "linhas_venda_diarias",
    "dias_com_venda",
    "loja_comparavel_yoy",
    "status_loja_mes",
    "interpretacao_dias_com_venda",
    "denominador_linhas",
}

REQUIRED_CATEGORY_COLUMNS = {
    "periodicidade",
    "periodo",
    "NIVEL_1",
    "receita",
    "receita_ano_anterior",
    "variacao_receita_yoy",
    "contribuicao_queda_periodo",
    "classificacao_categoria",
}


@pytest.fixture
def vendas_fixture():
    return pd.DataFrame(
        {
            "DATA_VENDA": pd.to_datetime(
                [
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-02-02",
                    "2025-01-02",
                    "2025-01-03",
                    "2025-01-04",
                    "2025-02-02",
                ]
            ),
            "COD_EMPRESA": [1, 1, 3, 1, 1, 2, 3, 1],
            "CODIGO": [10, 20, 10, 10, 10, 10, 30, 20],
            "QUANTIDADE_VENDIDA": [5.0, 5.0, 8.0, 4.0, 6.0, 3.0, 1.0, 2.0],
            "CONVERSAO_VENDA_PARA_ARMAZENAGEM": [1.0] * 8,
            "PRECO_UNIT_MEDIO": [10.0, 10.0, 10.0, 20.0, 20.0, 10.0, 10.0, 20.0],
        }
    )


@pytest.fixture
def lojas_fixture():
    return pd.DataFrame(
        {
            "COD_EMPRESA": [1, 2, 3],
            "CD_CIDADE": ["Recife", "Natal", "Salvador"],
            "CD_ESTADO": ["PE", "RN", "BA"],
        }
    )


@pytest.fixture
def produtos_fixture():
    return pd.DataFrame(
        {
            "CODIGO": [10, 20, 30],
            "NIVEL_1": ["A - BASE", "B - CASA", "C - NOVA"],
        }
    )


def test_yoy_usa_mesmo_mes_do_ano_anterior_e_dias_com_venda(vendas_fixture, lojas_fixture):
    result = sales.build_store_monthly_sales(vendas_fixture, lojas_fixture)
    jan_2025_store_1 = result[
        result["ANO_MES"].eq("2025-01") & result["COD_EMPRESA"].eq(1)
    ].iloc[0]

    assert REQUIRED_STORE_COLUMNS.issubset(result.columns)
    assert jan_2025_store_1["receita"] == pytest.approx(120.0)
    assert jan_2025_store_1["receita_ano_anterior"] == pytest.approx(100.0)
    assert jan_2025_store_1["variacao_receita_yoy"] == pytest.approx(0.20)
    assert jan_2025_store_1["dias_com_venda"] == 1
    assert jan_2025_store_1["dias_com_venda_ano_anterior"] == 2
    assert jan_2025_store_1["denominador_linhas"] == "linhas de venda diarias"


def test_lojas_comparaveis_novas_e_incompletas_sao_flagadas(vendas_fixture, lojas_fixture):
    result = sales.build_store_monthly_sales(vendas_fixture, lojas_fixture)

    store_1 = result[result["ANO_MES"].eq("2025-01") & result["COD_EMPRESA"].eq(1)].iloc[0]
    store_2 = result[result["ANO_MES"].eq("2025-01") & result["COD_EMPRESA"].eq(2)].iloc[0]
    store_3_feb = result[result["ANO_MES"].eq("2025-02") & result["COD_EMPRESA"].eq(3)].iloc[0]

    assert bool(store_1["loja_comparavel_yoy"]) is True
    assert store_2["status_loja_mes"] == "nova_ou_sem_base_yoy"
    assert store_3_feb["status_loja_mes"] == "dados_insuficientes"
    assert set(result["status_loja_mes"]).issubset(sales.STORE_STATUS)
    assert "fechamento" in store_1["interpretacao_dias_com_venda"]


def test_categoria_yoy_e_classificacao_controlada(vendas_fixture, produtos_fixture):
    result = sales.build_category_yoy(vendas_fixture, produtos_fixture)
    monthly = result[result["periodicidade"].eq("mes")]
    jan_2025_base = monthly[
        monthly["periodo"].eq("2025-01") & monthly["NIVEL_1"].eq("A - BASE")
    ].iloc[0]

    assert REQUIRED_CATEGORY_COLUMNS.issubset(result.columns)
    assert jan_2025_base["receita_ano_anterior"] == pytest.approx(130.0)
    assert jan_2025_base["receita"] == pytest.approx(150.0)
    assert jan_2025_base["classificacao_categoria"] in sales.CATEGORY_CLASSES
    assert set(result["classificacao_categoria"]).issubset(sales.CATEGORY_CLASSES)
    assert {"mes", "trimestre"}.issubset(set(result["periodicidade"]))


def test_outputs_gerados_em_diretorio_temporario(
    tmp_path,
    vendas_fixture,
    lojas_fixture,
    produtos_fixture,
):
    processed = tmp_path / "processed"
    outputs = tmp_path / "outputs"
    processed.mkdir()

    vendas_fixture.to_parquet(processed / "fato_vendas.parquet", index=False)
    lojas_fixture.to_parquet(processed / "dim_lojas.parquet", index=False)
    produtos_fixture.to_parquet(processed / "dim_produto.parquet", index=False)

    result = sales.generate_sales_outputs(processed, outputs)

    same_store_path = outputs / "vendas_same_store_yoy.csv"
    categories_path = outputs / "vendas_categorias_yoy.csv"
    assert same_store_path.exists()
    assert categories_path.exists()
    assert not result["vendas_same_store_yoy"].empty
    assert not result["vendas_categorias_yoy"].empty
    assert REQUIRED_STORE_COLUMNS.issubset(pd.read_csv(same_store_path).columns)
    assert REQUIRED_CATEGORY_COLUMNS.issubset(pd.read_csv(categories_path).columns)


def test_documentacao_spec05_existe_e_evita_linguagem_proibida():
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8").lower()

    assert "vendas_same_store_yoy.csv" in text
    assert "vendas_categorias_yoy.csv" in text
    assert "sortimento_controlado_por_volume.csv" in text
    assert "linhas de venda diarias" in text
    assert "ruptura comprovada" not in text


def test_totais_mensais_batem_com_output_legado_quando_arquivo_existe():
    vendas_path = ROOT / "data" / "processed" / "fato_vendas.parquet"
    legacy_path = ROOT / "outputs" / "tables" / "vendas_mensais.csv"
    if not vendas_path.exists() or not legacy_path.exists():
        pytest.skip("dados reais nao disponiveis")

    vendas = pd.read_parquet(vendas_path)
    result = sales.prepare_sales(vendas)
    monthly = (
        result.groupby("ANO_MES", dropna=False)
        .agg(receita=("RECEITA", "sum"), qtd_vendida=("QTD_VENDA_ESTOQUE", "sum"))
        .reset_index()
        .sort_values("ANO_MES")
    )
    legacy = pd.read_csv(legacy_path).sort_values("ANO_MES")

    pd.testing.assert_series_equal(
        monthly["receita"].reset_index(drop=True),
        legacy["receita"].reset_index(drop=True),
        check_names=False,
        rtol=1e-9,
        atol=0.01,
    )
    pd.testing.assert_series_equal(
        monthly["qtd_vendida"].reset_index(drop=True),
        legacy["qtd_vendida"].reset_index(drop=True),
        check_names=False,
        rtol=1e-9,
        atol=0.000001,
    )
