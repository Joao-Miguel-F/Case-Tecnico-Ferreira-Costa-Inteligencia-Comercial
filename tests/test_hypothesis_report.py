# -*- coding: utf-8 -*-
"""Tests for Spec 07 hypothesis matrix and final report."""
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MATRIX_MD = ROOT / "docs" / "hypothesis_validation_matrix.md"
STATUS_CSV = ROOT / "outputs" / "tables" / "hypothesis_status.csv"
REPORT = ROOT / "reports" / "relatorio_final.md"

REQUIRED_COLUMNS = {
    "hipotese_id",
    "hipotese",
    "evidencia_usada",
    "teste_executado",
    "resultado",
    "status",
    "nivel_confianca",
    "riscos",
    "dados_ausentes",
    "conclusao_permitida",
    "conclusao_proibida",
}

ALLOWED_STATUS = {
    "Confirmada descritivamente",
    "Parcialmente suportada",
    "Exploratória",
    "Não comprovada",
    "Rejeitada",
    "Inválida por limitação de dados",
}

REQUIRED_HYPOTHESES = {f"H{i}" for i in range(1, 11)}


def _report_text() -> str:
    return REPORT.read_text(encoding="utf-8").lower()


def test_spec07_files_exist_and_are_not_empty():
    for path in [MATRIX_MD, STATUS_CSV, REPORT]:
        assert path.exists(), f"{path} should exist"
        assert path.stat().st_size > 0, f"{path} should not be empty"


def test_hypothesis_status_has_required_columns_statuses_and_h1_to_h10():
    status = pd.read_csv(STATUS_CSV)

    assert REQUIRED_COLUMNS.issubset(status.columns)
    assert set(status["status"]).issubset(ALLOWED_STATUS)
    assert REQUIRED_HYPOTHESES.issubset(set(status["hipotese_id"]))
    assert len(status[status["hipotese_id"].isin(REQUIRED_HYPOTHESES)]) >= 10


def test_each_hypothesis_has_allowed_and_prohibited_conclusions():
    status = pd.read_csv(STATUS_CSV)
    required = status[status["hipotese_id"].isin(REQUIRED_HYPOTHESES)]

    assert required["conclusao_permitida"].notna().all()
    assert required["conclusao_proibida"].notna().all()
    assert required["conclusao_permitida"].str.strip().ne("").all()
    assert required["conclusao_proibida"].str.strip().ne("").all()


def test_report_contains_required_sections():
    text = _report_text()

    required_terms = [
        "sumario executivo",
        "qualidade e cobertura dos dados",
        "hipotese",
        "projecao como venda observada",
        "recomendacoes como triagens",
        "dados adicionais necessarios",
        "dado ausente",
        "não validado",
        "bloqueado",
    ]
    for term in required_terms:
        assert term in text


def test_report_avoids_prohibited_analytical_language():
    text = _report_text()

    prohibited_phrases = [
        "elasticidade",
        "demanda real",
        "ruptura comprovada",
        "desabastecimento comprovado",
        "ruptura fisica comprovada",
        "desabastecimento fisico comprovado",
        "compras causaram a queda",
        "compras causaram queda",
        "decisão final",
        "decisões finais",
        "decisao final",
        "decisoes finais",
    ]
    for phrase in prohibited_phrases:
        assert phrase not in text


def test_report_does_not_treat_observed_sales_as_real_demand_or_triages_as_final_actions():
    text = _report_text()

    assert "venda observada" in text
    assert "pedido final de compra" not in text
    assert "acao automatica" in text or "ação automática" in text
    assert "triagens" in text
    assert "prova fisica" not in text
