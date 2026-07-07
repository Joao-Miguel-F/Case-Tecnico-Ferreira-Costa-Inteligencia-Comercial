# -*- coding: utf-8 -*-
"""Testes da Spec 02 — checks de qualidade e relatório (SDD.MD seção 9).

Duas camadas:
1. unidades: cada check detecta problema plantado em fixture sintética;
2. ponta a ponta: src/02_quality_audit.py executa sem erro, gera
   outputs/tables/data_quality_report.csv com colunas obrigatórias, status
   restrito a {PASS, WARN, FAIL} e os checks críticos presentes.
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
AUDIT_SCRIPT = SRC / "02_quality_audit.py"
REPORT_CSV = ROOT / "outputs" / "tables" / "data_quality_report.csv"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation import quality_checks as qc  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures sintéticas mínimas
# ---------------------------------------------------------------------------
def _vendas(**overrides) -> pd.DataFrame:
    base = {
        "DATA_VENDA": pd.to_datetime(["2024-01-02", "2024-02-10", "2025-12-31"]),
        "COD_EMPRESA": pd.array([1, 1, 2], dtype="Int64"),
        "CODIGO": pd.array([10, 20, 10], dtype="Int64"),
        "DIGITO": pd.array([5, 7, 5], dtype="Int64"),
        "EMBALAGEM": pd.array([0, 0, 0], dtype="Int64"),
        "QUANTIDADE_VENDIDA": [2.0, 1.0, 4.0],
        "CONVERSAO_VENDA_PARA_ARMAZENAGEM": [1.0, 1.0, 1.0],
        "UNIDADE_DA_VENDA": ["UN", "UN", "UN"],
        "PRECO_UNIT_MEDIO": [10.0, 20.0, 5.0],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def _produto() -> pd.DataFrame:
    return pd.DataFrame({
        "CODIGO": pd.array([10, 20], dtype="Int64"),
        "DIGITO": pd.array([5, 7], dtype="Int64"),
        "UNIDADE_ESTOQUE": ["UN", "UN"],
        "CONVERSAO_COMPRA_ARMAZENAGEM": pd.array([1.0, 12.0], dtype="Float64"),
        "CD_VOLTAGEM": pd.array([0, 110], dtype="Int64"),
    })


def _lojas() -> pd.DataFrame:
    return pd.DataFrame({"COD_EMPRESA": pd.array([1, 2], dtype="Int64")})


def _compras() -> pd.DataFrame:
    return pd.DataFrame({
        "DATA_ENTRADA": pd.to_datetime(["2024-01-05"]),
        "COD_EMPRESA": pd.array([1], dtype="Int64"),
        "CODIGO": pd.array([10], dtype="Int64"),
        "QUANTIDADE_COMPRA": [10.0],
        "PRECO_UNIT_UNIDADE_COMPRA": [5.0],
    })


def _estoque() -> pd.DataFrame:
    return pd.DataFrame({
        "COD_EMPRESA": pd.array([1, 2], dtype="Int64"),
        "CODIGO": pd.array([10, 10], dtype="Int64"),
        "ESTOQUE_INICIAL": pd.array([100.0, 100.0], dtype="Float64"),
    })


# ---------------------------------------------------------------------------
# make_record
# ---------------------------------------------------------------------------
def test_make_record_shape_and_pct():
    rec = qc.make_record("t", "c", "WARN", 5, 50, "media", "d", "i", "a")
    assert list(rec) == qc.REPORT_COLUMNS
    assert rec["pct_afetado"] == 10.0


def test_make_record_rejects_invalid_status():
    with pytest.raises(ValueError):
        qc.make_record("t", "c", "ERRO", 0, 1, "info", "d", "i", "a")


# ---------------------------------------------------------------------------
# Checks unitários: detectam problema plantado / passam em dado limpo
# ---------------------------------------------------------------------------
def test_check_expected_columns_detects_missing():
    df = pd.DataFrame({"A": [1]})
    rec = qc.check_expected_columns(df, ["A", "B"], "t")
    assert rec["status"] == "FAIL" and "B" in rec["descricao"]
    assert qc.check_expected_columns(df, ["A"], "t")["status"] == "PASS"


def test_check_duplicate_grain_detects_planted_duplicate():
    df = _vendas()
    dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    grain = ["CODIGO", "COD_EMPRESA", "DATA_VENDA", "EMBALAGEM"]
    assert qc.check_duplicate_grain(dup, grain, "t")["status"] == "FAIL"
    assert qc.check_duplicate_grain(df, grain, "t")["status"] == "PASS"


def test_check_valid_dates_detects_nat():
    df = _vendas()
    df.loc[0, "DATA_VENDA"] = pd.NaT
    assert qc.check_valid_dates(df, "DATA_VENDA", "t")["status"] == "FAIL"
    assert qc.check_valid_dates(_vendas(), "DATA_VENDA", "t")["status"] == "PASS"


def test_check_dates_in_period_detects_out_of_range():
    df = _vendas()
    df.loc[0, "DATA_VENDA"] = pd.Timestamp("2023-01-01")
    rec = qc.check_dates_in_period(
        df, "DATA_VENDA", "t", pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31"))
    assert rec["status"] == "WARN" and rec["linhas_afetadas"] == 1


def test_check_critical_nulls_detects_planted_null():
    df = _compras()
    df.loc[0, "PRECO_UNIT_UNIDADE_COMPRA"] = None
    rec = qc.check_critical_nulls(
        df, "PRECO_UNIT_UNIDADE_COMPRA", "t",
        status_if_present="FAIL", severidade="critica", impacto="i", acao="a")
    assert rec["status"] == "FAIL" and rec["linhas_afetadas"] == 1


def test_check_structural_nulls_always_pass_but_counts():
    df = pd.DataFrame({"X": [1, None, None]})
    rec = qc.check_structural_nulls(df, "X", "t", "motivo")
    assert rec["status"] == "PASS" and rec["linhas_afetadas"] == 2


def test_check_orphans_detects_planted_orphan():
    vendas = _vendas()
    vendas.loc[0, "CODIGO"] = 999  # sem correspondência na dimensão
    rec = qc.check_orphans(vendas, "CODIGO", _produto(), "CODIGO", "fato_vendas", "dim_produto")
    assert rec["status"] == "FAIL" and rec["linhas_afetadas"] == 1
    rec_ok = qc.check_orphans(_vendas(), "CODIGO", _produto(), "CODIGO", "fato_vendas", "dim_produto")
    assert rec_ok["status"] == "PASS"


def test_check_negative_values_detects_planted_negative():
    df = _vendas()
    df.loc[0, "QUANTIDADE_VENDIDA"] = -3.0
    assert qc.check_negative_values(df, "QUANTIDADE_VENDIDA", "t", "i")["status"] == "FAIL"
    assert qc.check_negative_values(_vendas(), "QUANTIDADE_VENDIDA", "t", "i")["status"] == "PASS"


def test_check_zero_values_detects_planted_zero():
    df = _vendas()
    df.loc[0, "PRECO_UNIT_MEDIO"] = 0.0
    rec = qc.check_zero_values(
        df, "PRECO_UNIT_MEDIO", "t",
        status_if_present="WARN", severidade="alta", impacto="i", acao="a")
    assert rec["status"] == "WARN" and rec["linhas_afetadas"] == 1


def test_check_revenue_consistency_detects_mismatch():
    df = _vendas()
    df["RECEITA"] = df["QUANTIDADE_VENDIDA"] * df["PRECO_UNIT_MEDIO"]
    assert qc.check_revenue_consistency(df, "t")["status"] == "PASS"
    df.loc[0, "RECEITA"] = 1e6
    assert qc.check_revenue_consistency(df, "t")["status"] == "FAIL"


def test_check_months_without_detects_gap():
    df = _vendas()  # só jan/24, fev/24 e dez/25
    rec = qc.check_months_without(df, "DATA_VENDA", "t", "2024-01", "2024-03", "vendas")
    assert rec["status"] == "WARN" and "2024-03" in rec["descricao"]
    rec_ok = qc.check_months_without(df, "DATA_VENDA", "t", "2024-01", "2024-02", "vendas")
    assert rec_ok["status"] == "PASS"


def test_check_purchase_coverage_stores_detects_store_without_purchase():
    rec = qc.check_purchase_coverage_stores(_compras(), _lojas())
    assert rec["status"] == "FAIL" and rec["linhas_afetadas"] == 1  # loja 2 sem compra


def test_check_purchase_coverage_products_detects_uncovered_products():
    rec = qc.check_purchase_coverage_products(_compras(), _produto())
    assert rec["status"] == "FAIL" and rec["linhas_afetadas"] == 1  # produto 20 sem compra


def test_check_sold_without_inflows_detects_planted_case():
    # produto 20 na loja 1: vendido, sem estoque inicial e sem compra
    rec = qc.check_sold_without_inflows(_vendas(), _estoque(), _compras(), _produto())
    assert rec["status"] == "FAIL" and rec["linhas_afetadas"] == 1


def test_check_sales_exceed_inflows_detects_planted_case():
    vendas = _vendas()
    vendas.loc[2, "QUANTIDADE_VENDIDA"] = 500.0  # produto 10 loja 2 > estoque 100
    rec = qc.check_sales_exceed_inflows(vendas, _estoque(), _compras(), _produto())
    assert rec["status"] == "FAIL"
    assert rec["linhas_afetadas"] >= 1


def test_check_sales_exceed_inflows_passes_when_covered():
    rec = qc.check_sales_exceed_inflows(
        _vendas().iloc[[0, 2]], _estoque(), _compras(), _produto())
    assert rec["status"] == "PASS"


def test_check_sale_unit_consistency_detects_suspicious_line():
    vendas = _vendas()
    vendas.loc[0, "UNIDADE_DA_VENDA"] = "CX"  # difere de UN com conversão 1
    rec = qc.check_sale_unit_consistency(vendas, _produto())
    assert rec["status"] == "WARN" and rec["linhas_afetadas"] == 1


def test_check_purchase_unit_difference_counts_products():
    rec = qc.check_purchase_unit_difference(_produto())
    assert rec["status"] == "WARN" and rec["linhas_afetadas"] == 1  # produto 20 (12x)


def test_check_purchases_needing_conversion():
    compras = _compras()
    assert qc.check_purchases_needing_conversion(compras, _produto())["status"] == "PASS"
    compras.loc[0, "CODIGO"] = 20  # produto com conversão 12
    assert qc.check_purchases_needing_conversion(compras, _produto())["status"] == "WARN"


def test_check_digito_consistency_detects_mismatch():
    vendas = _vendas()
    assert qc.check_digito_consistency(vendas, _produto())["status"] == "PASS"
    vendas.loc[0, "DIGITO"] = 9
    assert qc.check_digito_consistency(vendas, _produto())["status"] == "WARN"


def test_check_voltagem_domain_detects_out_of_domain():
    voltagem = pd.DataFrame({
        "CD_VOLTAGEM": pd.array([110, 220], dtype="Int64"),
        "CD_EMPRESA": pd.array([1, 1], dtype="Int64"),
    })
    assert qc.check_voltagem_domain(_produto(), voltagem)["status"] == "PASS"  # 0 é permitido
    produto = _produto()
    produto.loc[1, "CD_VOLTAGEM"] = 999
    assert qc.check_voltagem_domain(produto, voltagem)["status"] == "WARN"


def test_check_negative_balance_detects_negative():
    df = pd.DataFrame({"SALDO": [10.0, -5.0, 0.0]})
    rec = qc.check_negative_balance(df, "SALDO", "t")
    assert rec["status"] == "FAIL" and rec["linhas_afetadas"] == 1
    assert "gap" in rec["impacto_analitico"].lower()


# ---------------------------------------------------------------------------
# Ponta a ponta: 02_quality_audit.py roda e gera o relatório
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def report() -> pd.DataFrame:
    """Executa a auditoria real uma vez por sessão e carrega o relatório."""
    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=600,
    )
    assert result.returncode == 0, f"02_quality_audit.py falhou:\n{result.stderr}"
    assert REPORT_CSV.exists(), "data_quality_report.csv não foi gerado"
    return pd.read_csv(REPORT_CSV)


def test_audit_report_has_required_columns(report):
    assert list(report.columns) == qc.REPORT_COLUMNS


def test_audit_report_statuses_are_valid(report):
    assert set(report["status"].unique()) <= qc.VALID_STATUSES


def test_audit_report_is_not_trivial(report):
    assert len(report) >= 40, "relatório com menos checks que o mínimo esperado"
    assert (report["status"] == "PASS").any()


@pytest.mark.parametrize("check_prefix", [
    "colunas_esperadas",
    "tipos_e_schema",
    "duplicidade_grao",
    "datas_validas",
    "datas_no_periodo",
    "nulos_criticos",
    "orfaos",
    "negativos",
    "zeros",
    "meses_sem_vendas",
    "meses_sem_compras",
    "cobertura_compras",
    "vendidos_sem_estoque_inicial_nem_compras",
    "venda_maior_que_entradas_conhecidas",
    "unidade_venda_difere_armazenagem",
    "unidade_compra_difere_armazenagem",
    "saldo_negativo",
])
def test_audit_report_contains_critical_check(report, check_prefix):
    assert report["check"].str.startswith(check_prefix).any(), (
        f"check crítico ausente do relatório: {check_prefix}*"
    )


def test_audit_report_known_fails_are_fail(report):
    """Problemas que invalidam conclusões do relatório DEVEM estar como FAIL."""
    fails = set(report.loc[report["status"] == "FAIL", "check"])
    expected = {
        "nulos_criticos_PRECO_UNIT_UNIDADE_COMPRA",
        "cobertura_compras_lojas",
        "cobertura_compras_produtos",
        "vendidos_sem_estoque_inicial_nem_compras",
        "venda_maior_que_entradas_conhecidas",
        "saldo_negativo_SALDO_ESTOQUE",
        "saldo_negativo_ESTOQUE_FINAL_PROJETADO",
    }
    assert expected <= fails, f"FAILs esperados ausentes: {expected - fails}"


def test_audit_report_grain_checks_pass_on_real_data(report):
    """Unicidade de grão validada: todas as tabelas reais sem duplicata."""
    grain = report[report["check"] == "duplicidade_grao"]
    assert len(grain) >= 8
    assert (grain["status"] == "PASS").all(), grain[grain["status"] != "PASS"]


def test_audit_report_pct_bounds(report):
    assert report["pct_afetado"].between(0, 100).all()
    assert (report["linhas_afetadas"] >= 0).all()
