# -*- coding: utf-8 -*-
"""Consolidated output checks for Spec 08.

These tests validate the reproducibility surface built by Specs 01-07. They do
not recalculate analyses and do not treat legacy filenames as new contracts.
"""
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs" / "tables"
DOCS = ROOT / "docs"
SPECS = ROOT / "specs"
REPORT = ROOT / "reports" / "relatorio_final.md"

ALLOWED_QUALITY_STATUS = {"PASS", "WARN", "FAIL"}
ALLOWED_HYPOTHESIS_STATUS = {
    "Confirmada descritivamente",
    "Parcialmente suportada",
    "Explorat\u00f3ria",
    "N\u00e3o comprovada",
    "Rejeitada",
    "Inv\u00e1lida por limita\u00e7\u00e3o de dados",
}

REQUIRED_TABLES = {
    "ingestion_audit.csv": {
        "arquivo",
        "encoding_testado",
        "encoding_usado",
        "separador_detectado",
        "linhas_lidas",
        "colunas_lidas",
        "status_ingestao",
    },
    "data_quality_report.csv": {
        "tabela",
        "check",
        "status",
        "linhas_afetadas",
        "pct_afetado",
        "severidade",
        "descricao",
        "impacto_analitico",
        "acao_recomendada",
    },
    "compras_coverage_audit.csv": {
        "nivel_agrupamento",
        "chave_agrupamento",
        "total_vendido_estoque",
        "entradas_conhecidas_estoque",
        "pct_cobertura_entradas",
        "classificacao_confiabilidade",
        "interpretacao",
        "limitacao",
    },
    "gaps_saldo_contabil_estoque.csv": {
        "COD_EMPRESA",
        "CODIGO",
        "ENTRADAS_CONHECIDAS_ESTOQUE",
        "SALDO_PROJETADO_CONTABIL",
        "GAP_CONTABIL_ESTOQUE",
        "INTERPRETACAO_SALDO_NEGATIVO",
        "POSSIVEIS_CAUSAS_GAP",
    },
    "vendas_same_store_yoy.csv": {
        "ANO_MES",
        "COD_EMPRESA",
        "receita",
        "receita_ano_anterior",
        "variacao_receita_yoy",
        "loja_comparavel_yoy",
        "status_loja_mes",
        "interpretacao_dias_com_venda",
    },
    "vendas_categorias_yoy.csv": {
        "periodicidade",
        "periodo",
        "NIVEL_1",
        "receita",
        "receita_ano_anterior",
        "variacao_receita_yoy",
        "classificacao_categoria",
        "interpretacao",
    },
    "sortimento_controlado_por_volume.csv": {
        "ANO_MES",
        "skus_observados",
        "linhas_venda_diarias",
        "skus_esperados_media",
        "status_sortimento_controlado",
        "interpretacao",
    },
    "produtos_correlacao_preco_volume_negativa.csv": {
        "CODIGO",
        "correlacao_preco_volume",
        "n_obs",
        "min_obs_exigido",
        "status_correlacao",
        "tipo_analise",
        "interpretacao",
        "limitacao",
        "evidencia",
    },
    "projecao_venda_observada_2026.csv": {
        "CODIGO",
        "venda_observada_projetada_2026",
        "compra_bruta_sugerida",
        "compra_liquida_sugerida",
        "status_compra_liquida",
        "flag_nao_calcular_compra_liquida_por_estoque_inconfiavel",
        "nivel_confianca",
        "limitacao",
        "acao_recomendada",
    },
    "triagem_repricing.csv": set(),
    "triagem_compras.csv": set(),
    "triagem_promocao.csv": set(),
    "triagem_descontinuacao.csv": set(),
    "hypothesis_status.csv": {
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
    },
}

TRIAGE_COLUMNS = {
    "tipo_triagem",
    "nivel_confianca",
    "status_decisao_final",
    "regra_usada",
    "evidencia",
    "dado_faltante",
    "limitacao",
    "risco_decisao",
    "proxima_validacao_necessaria",
    "acao_recomendada",
}

REQUIRED_DOCS = [
    DOCS / "data_formatting_and_encoding.md",
    DOCS / "data_contract.md",
    DOCS / "metric_catalog.md",
    DOCS / "business_rules.md",
    DOCS / "inventory_reconciliation.md",
    DOCS / "sales_store_category_assortment.md",
    DOCS / "pricing_projection_recommendations.md",
    DOCS / "hypothesis_validation_matrix.md",
]

REQUIRED_SPECS = [
    SPECS / "00_current_state.md",
    SPECS / "01_ingestion_encoding_spec.md",
    SPECS / "02_data_contract_quality_spec.md",
    SPECS / "03_metrics_business_rules_spec.md",
    SPECS / "04_inventory_purchase_reconciliation_spec.md",
    SPECS / "05_sales_store_category_assortment_spec.md",
    SPECS / "06_pricing_projection_recommendations_spec.md",
    SPECS / "07_hypothesis_report_spec.md",
    SPECS / "08_tests_reproducibility_spec.md",
    SPECS / "09_dashboard_delivery_spec.md",
    SPECS / "implementation_plan.md",
]

SPEC06_NEW_OUTPUTS = [
    OUTPUTS / "produtos_correlacao_preco_volume_negativa.csv",
    OUTPUTS / "projecao_venda_observada_2026.csv",
    OUTPUTS / "triagem_repricing.csv",
    OUTPUTS / "triagem_compras.csv",
    OUTPUTS / "triagem_promocao.csv",
    OUTPUTS / "triagem_descontinuacao.csv",
    OUTPUTS / "triagem_possivel_promocao.csv",
    OUTPUTS / "triagem_possivel_descontinuacao.csv",
]

PROHIBITED_REPORT_PHRASES = [
    "elasticidade",
    "demanda real",
    "ruptura comprovada",
    "ruptura fisica comprovada",
    "desabastecimento comprovado",
    "compras causaram a queda",
    "compras causaram queda",
    "decisao final",
    "decisoes finais",
    "decis\u00e3o final",
    "decis\u00f5es finais",
]


def _read_csv(name: str) -> pd.DataFrame:
    path = OUTPUTS / name
    assert path.exists(), f"output ausente: {path.relative_to(ROOT)}"
    assert path.stat().st_size > 0, f"output vazio: {path.relative_to(ROOT)}"
    frame = pd.read_csv(path)
    assert not frame.empty, f"output sem linhas: {path.relative_to(ROOT)}"
    return frame


def _text(path: Path) -> str:
    assert path.exists(), f"arquivo ausente: {path.relative_to(ROOT)}"
    assert path.stat().st_size > 0, f"arquivo vazio: {path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8").lower()


def test_required_outputs_exist_are_not_empty_and_have_required_columns():
    for filename, required_columns in REQUIRED_TABLES.items():
        frame = _read_csv(filename)
        if filename.startswith("triagem_"):
            required_columns = TRIAGE_COLUMNS
        missing = required_columns - set(frame.columns)
        assert not missing, f"{filename}: colunas obrigatorias ausentes: {sorted(missing)}"


def test_quality_and_hypothesis_status_vocabularies_are_controlled():
    quality = _read_csv("data_quality_report.csv")
    hypothesis = _read_csv("hypothesis_status.csv")

    assert set(quality["status"].dropna()).issubset(ALLOWED_QUALITY_STATUS)
    assert set(hypothesis["status"].dropna()).issubset(ALLOWED_HYPOTHESIS_STATUS)
    assert {f"H{i}" for i in range(1, 11)}.issubset(set(hypothesis["hipotese_id"]))


def test_triage_outputs_have_evidence_limitations_confidence_and_blocked_status():
    for filename in [
        "triagem_repricing.csv",
        "triagem_compras.csv",
        "triagem_promocao.csv",
        "triagem_descontinuacao.csv",
    ]:
        frame = _read_csv(filename)
        missing = TRIAGE_COLUMNS - set(frame.columns)
        assert not missing, f"{filename}: colunas de triagem ausentes: {sorted(missing)}"
        for column in ["evidencia", "limitacao", "nivel_confianca", "status_decisao_final"]:
            assert frame[column].notna().all(), f"{filename}: {column} contem nulos"
            assert frame[column].astype(str).str.strip().ne("").all(), f"{filename}: {column} contem vazios"
        assert frame["status_decisao_final"].eq("BLOQUEADO").all()
        assert frame["limitacao"].astype(str).str.contains("DADO AUSENTE|NAO VALIDADO|N\u00c3O VALIDADO|BLOQUEADO").all()


def test_docs_specs_readme_makefile_pyproject_and_report_exist():
    for path in [*REQUIRED_DOCS, *REQUIRED_SPECS, REPORT, ROOT / "README.md", ROOT / "Makefile", ROOT / "pyproject.toml"]:
        _text(path)


def test_final_report_avoids_prohibited_language():
    report_text = _text(REPORT)
    for phrase in PROHIBITED_REPORT_PHRASES:
        assert phrase not in report_text


def test_new_outputs_do_not_call_observed_sales_real_demand_or_correlation_elasticity():
    prohibited_fragments = [
        "demanda_real",
        "demanda real projetada",
        "venda observada como demanda real",
        "elasticidade",
    ]
    for path in SPEC06_NEW_OUTPUTS:
        assert path.exists(), f"output ausente: {path.relative_to(ROOT)}"
        full_text = (path.name + "\n" + path.read_text(encoding="utf-8")).lower()
        for fragment in prohibited_fragments:
            assert fragment not in full_text, f"{path.name} contem linguagem proibida: {fragment}"


def test_readme_documents_reproducibility_and_spec09_boundary():
    # Spec 09 implementou o dashboard; o README passa a documentar como abrir
    # e publicar (antes exigia-se "nao foi implementado").
    readme = _text(ROOT / "README.md")
    required_terms = [
        "make install",
        "make test",
        "make audit",
        "make report",
        "python -m pytest tests/",
        "dashboard",
        "spec 09",
        "github pages",
        "make dashboard",
        "venda observada",
        "gap contabil",
        "correlacao",
        "triagem",
        "dado ausente",
        "nao validado",
        "bloqueado",
    ]
    missing = [term for term in required_terms if term not in readme]
    assert not missing, f"README sem termos obrigatorios da Spec 08: {missing}"
