# -*- coding: utf-8 -*-
"""Testes da Spec 02 — schemas de contrato de dados (SDD.MD seção 9).

Valida que:
- docs/data_contract.md existe e não está vazio;
- os schemas principais existem;
- schemas aceitam DataFrames válidos (fixtures sintéticas com os dtypes reais);
- schemas rejeitam DataFrames inválidos (duplicata de chave, negativo,
  nulo proibido, coluna ausente, data fora do período).
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CONTRACT = ROOT / "docs" / "data_contract.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation import schemas  # noqa: E402


# ---------------------------------------------------------------------------
# Contrato de dados (documento)
# ---------------------------------------------------------------------------
def test_data_contract_exists_and_not_empty():
    assert CONTRACT.exists(), "docs/data_contract.md não existe"
    assert CONTRACT.stat().st_size > 1000, "docs/data_contract.md está vazio/incompleto"


@pytest.mark.parametrize("section", [
    "Unicidade validada",
    "fato_vendas",
    "fato_compras",
    "fato_estoque_inicial",
    "dim_produto",
    "dim_lojas",
    "dim_precos",
    "dim_voltagem",
    "dim_unidades",
    "integridade referencial",
    "completude temporal",
    "consistência de unidades",
    "Impacto consolidado no relatório",
    "pandera==0.32.1",
])
def test_data_contract_has_section(section):
    text = CONTRACT.read_text(encoding="utf-8")
    assert section in text, f"seção/termo obrigatório ausente do contrato: {section!r}"


# ---------------------------------------------------------------------------
# Existência dos schemas
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", [
    "dim_produto", "dim_lojas", "dim_precos", "dim_voltagem", "dim_unidades",
    "fato_vendas", "fato_compras", "fato_estoque_inicial",
])
def test_raw_schema_exists(name):
    assert name in schemas.RAW_SCHEMAS


@pytest.mark.parametrize("name", [
    "fato_vendas_processed", "estoque_diario", "estoque_final_projetado",
    "cobertura_estoque",
])
def test_processed_schema_exists(name):
    assert name in schemas.PROCESSED_SCHEMAS


def test_expected_grain_covers_all_raw_tables():
    assert set(schemas.EXPECTED_GRAIN) == set(schemas.RAW_SCHEMAS)


# ---------------------------------------------------------------------------
# Fixtures sintéticas válidas (dtypes idênticos aos produzidos por src/io.py)
# ---------------------------------------------------------------------------
def _valid_fato_vendas() -> pd.DataFrame:
    return pd.DataFrame({
        "DATA_VENDA": pd.to_datetime(["2024-01-02", "2024-01-02", "2025-12-31"]),
        "COD_EMPRESA": pd.array([1, 2, 1], dtype="Int64"),
        "CODIGO": pd.array([10, 10, 20], dtype="Int64"),
        "DIGITO": pd.array([5, 5, 7], dtype="Int64"),
        "EMBALAGEM": pd.array([0, 0, 1], dtype="Int64"),
        "QUANTIDADE_VENDIDA": [2.0, 1.0, 3.5],
        "CONVERSAO_VENDA_PARA_ARMAZENAGEM": [1.0, 1.0, 12.0],
        "UNIDADE_DA_VENDA": ["UN", "UN", "CX"],
        "PRECO_UNIT_MEDIO": [9.9, 10.5, 99.0],
    })


def _valid_fato_compras() -> pd.DataFrame:
    return pd.DataFrame({
        "DATA_ENTRADA": pd.to_datetime(["2024-01-03", "2025-12-17"]),
        "COD_EMPRESA": pd.array([2, 3], dtype="Int64"),
        "CODIGO": pd.array([10, 20], dtype="Int64"),
        "EMBALAGEM_FORNECEDOR": ["CX-12-UN", None],
        "QUANTIDADE_COMPRA": [5.0, 2.0],
        "UNIDADE_ESTOQUE": ["UN", "UN"],
        "PRECO_UNIT_UNIDADE_COMPRA": [50.0, None],  # nulo permitido (medido como FAIL no report)
    })


def _valid_fato_estoque_inicial() -> pd.DataFrame:
    return pd.DataFrame({
        "COD_EMPRESA": pd.array([1, 1, 2], dtype="Int64"),
        "CODIGO": pd.array([10, 20, 10], dtype="Int64"),
        "ESTOQUE_INICIAL": pd.array([0.0, 50.0, 3.0], dtype="Float64"),
    })


def _valid_dim_produto() -> pd.DataFrame:
    return pd.DataFrame({
        "CODIGO": pd.array([10, 20], dtype="Int64"),
        "DIGITO": pd.array([5, 7], dtype="Int64"),
        "DESCRICAO": ["PRODUTO A", "PRODUTO B"],
        "NIVEL_1": ["CAT", "CAT"],
        "NIVEL_2": ["SUB", "SUB"],
        "NIVEL_3": ["SEG", "SEG"],
        "EMBALAGEM_FORNECEDOR": ["CX-12-UN", None],
        "EMBALAGEM_COMPRA": ["CX", "UN"],
        "CONVERSAO_COMPRA_ARMAZENAGEM": pd.array([12.0, 1.0], dtype="Float64"),
        "UNIDADE_ESTOQUE": ["UN", "UN"],
        "EMBALAGEM_VENDA_0": ["UN", "UN"],
        "EMBALAGEM_VENDA_1": [None, "CX"],
        "EMBALAGEM_VENDA_2": [None, None],
        "CD_VOLTAGEM": pd.array([0, None], dtype="Int64"),
    })


def _valid_dim_lojas() -> pd.DataFrame:
    return pd.DataFrame({
        "COD_EMPRESA": pd.array([1, 2], dtype="Int64"),
        "CD_CIDADE": ["Cidade A", "Cidade B"],
        "CD_ESTADO": ["BA", "SP"],
    })


def _valid_dim_precos() -> pd.DataFrame:
    return pd.DataFrame({
        "CODIGO": pd.array([10, 20], dtype="Int64"),
        "COD_EMPRESA": pd.array([1, 1], dtype="Int64"),
        "CATEGORIA": ["ELETRO", "ELETRO"],
        "PRECO_EMBALAGEM_0": pd.array([9.9, 19.9], dtype="Float64"),
        "PERC_DESCTO_ADICIONAL_EMBALAGEM_0": pd.array([0.0, 5.0], dtype="Float64"),
        "PRECO_EMBALAGEM_1": pd.array([None, 18.0], dtype="Float64"),
        "PRECO_EMBALAGEM_2": pd.array([None, None], dtype="Float64"),
    })


def _valid_dim_voltagem() -> pd.DataFrame:
    return pd.DataFrame({
        "CD_VOLTAGEM": pd.array([0, 110, 220], dtype="Int64"),
        "CD_EMPRESA": pd.array([1, 1, 2], dtype="Int64"),
    })


def _valid_dim_unidades() -> pd.DataFrame:
    return pd.DataFrame({
        "COD_UNIDADE": ["UN", "CX", "EB"],
        "DESCRICAO": ["UNIDADE (UN)", "CAIXA (CX)", "EMBALAGEM (EB)"],
        "COD_IBGE": ["1", "2", None],
    })


VALID_FIXTURES = {
    "fato_vendas": _valid_fato_vendas,
    "fato_compras": _valid_fato_compras,
    "fato_estoque_inicial": _valid_fato_estoque_inicial,
    "dim_produto": _valid_dim_produto,
    "dim_lojas": _valid_dim_lojas,
    "dim_precos": _valid_dim_precos,
    "dim_voltagem": _valid_dim_voltagem,
    "dim_unidades": _valid_dim_unidades,
}


# ---------------------------------------------------------------------------
# Schemas aceitam DataFrames válidos
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(VALID_FIXTURES))
def test_schema_accepts_valid_dataframe(name):
    ok, failures = schemas.validate_table(name, VALID_FIXTURES[name]())
    assert ok, f"schema {name} rejeitou DataFrame válido: {failures}"


def test_validate_table_unknown_name_raises():
    with pytest.raises(KeyError):
        schemas.validate_table("tabela_inexistente", pd.DataFrame())


# ---------------------------------------------------------------------------
# Schemas rejeitam DataFrames inválidos
# ---------------------------------------------------------------------------
def test_schema_rejects_duplicate_grain_fato_vendas():
    df = _valid_fato_vendas()
    df.loc[1, ["CODIGO", "COD_EMPRESA", "DATA_VENDA", "EMBALAGEM"]] = df.loc[
        0, ["CODIGO", "COD_EMPRESA", "DATA_VENDA", "EMBALAGEM"]
    ]
    ok, failures = schemas.validate_table("fato_vendas", df)
    assert not ok, "duplicata no grão de fato_vendas não foi rejeitada"


def test_schema_rejects_duplicate_key_dim_produto():
    df = _valid_dim_produto()
    df.loc[1, "CODIGO"] = df.loc[0, "CODIGO"]
    ok, _ = schemas.validate_table("dim_produto", df)
    assert not ok, "CODIGO duplicado em dim_produto não foi rejeitado"


def test_schema_rejects_negative_quantity():
    df = _valid_fato_vendas()
    df.loc[0, "QUANTIDADE_VENDIDA"] = -1.0
    ok, _ = schemas.validate_table("fato_vendas", df)
    assert not ok, "quantidade negativa não foi rejeitada"


def test_schema_rejects_zero_price():
    df = _valid_fato_vendas()
    df.loc[0, "PRECO_UNIT_MEDIO"] = 0.0
    ok, _ = schemas.validate_table("fato_vendas", df)
    assert not ok, "preço zero não foi rejeitado (contrato exige > 0)"


def test_schema_rejects_null_in_required_column():
    df = _valid_fato_vendas()
    df.loc[0, "CODIGO"] = pd.NA
    ok, _ = schemas.validate_table("fato_vendas", df)
    assert not ok, "nulo em CODIGO não foi rejeitado"


def test_schema_rejects_missing_column():
    df = _valid_fato_compras().drop(columns=["QUANTIDADE_COMPRA"])
    ok, _ = schemas.validate_table("fato_compras", df)
    assert not ok, "coluna obrigatória ausente não foi rejeitada"


def test_schema_rejects_date_out_of_period():
    df = _valid_fato_vendas()
    df.loc[0, "DATA_VENDA"] = pd.Timestamp("2023-05-01")
    ok, _ = schemas.validate_table("fato_vendas", df)
    assert not ok, "data fora de jan/2024–dez/2025 não foi rejeitada"


def test_schema_rejects_negative_estoque_inicial():
    df = _valid_fato_estoque_inicial()
    df.loc[0, "ESTOQUE_INICIAL"] = -5.0
    ok, _ = schemas.validate_table("fato_estoque_inicial", df)
    assert not ok, "estoque inicial negativo não foi rejeitado"


def test_schema_rejects_invalid_embalagem_domain():
    df = _valid_fato_vendas()
    df.loc[0, "EMBALAGEM"] = 9
    ok, _ = schemas.validate_table("fato_vendas", df)
    assert not ok, "EMBALAGEM fora do domínio {0,1,2} não foi rejeitada"


def test_processed_schema_rejects_inconsistent_receita():
    df = _valid_fato_vendas()
    df["RECEITA"] = df["QUANTIDADE_VENDIDA"] * df["PRECO_UNIT_MEDIO"]
    df["QTD_VENDA_ESTOQUE"] = df["QUANTIDADE_VENDIDA"] * df["CONVERSAO_VENDA_PARA_ARMAZENAGEM"]
    ok, _ = schemas.validate_table("fato_vendas_processed", df)
    assert ok, "fato_vendas_processed válido foi rejeitado"
    df.loc[0, "RECEITA"] = 999999.0
    ok, _ = schemas.validate_table("fato_vendas_processed", df)
    assert not ok, "RECEITA inconsistente não foi rejeitada"


# ---------------------------------------------------------------------------
# Schemas validam as bases brutas reais (contrato vale para o dado de verdade;
# dims pequenas — leitura barata). Os Parquet legados têm dtypes divergentes
# (documentado no contrato) e são cobertos pelo 02_quality_audit.py.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def pio():
    import importlib.util

    spec = importlib.util.spec_from_file_location("painel_io", SRC / "io.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("name", ["dim_produto", "dim_lojas", "dim_voltagem", "dim_unidades"])
def test_schema_accepts_real_raw_dimension(pio, name):
    df, _ = pio.read_raw(name)
    ok, failures = schemas.validate_table(name, df)
    assert ok, f"schema {name} rejeitou a base real: {failures}"
