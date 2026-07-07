# -*- coding: utf-8 -*-
"""Tests for Spec 06 recommendation triage."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DOC = ROOT / "docs" / "pricing_projection_recommendations.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis import recommendation_triage as triage  # noqa: E402


PROHIBITED_OUTPUT_PHRASES = [
    "elasticidade",
    "demanda real",
    "compras causaram queda",
    "ruptura",
    "desabastecimento",
]


def negative_correlation_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CODIGO": [10],
            "DESCRICAO": ["Produto A"],
            "NIVEL_1": ["A - TESTE"],
            "correlacao_preco_volume": [-0.8],
            "n_obs": [12],
            "receita_total": [1000.0],
            "regra_usada": ["correlacao_preco_volume < -0.4 e receita relevante"],
            "evidencia": ["correlacao=-0.8000; n_obs=12; receita_total=1000.00"],
            "limitacao": ["NÃO VALIDADO: associação observacional"],
        }
    )


def projection_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CODIGO": [10],
            "DESCRICAO": ["Produto A"],
            "NIVEL_1": ["A - TESTE"],
            "venda_observada_projetada_2026": [120.0],
            "compra_bruta_sugerida": [130.0],
            "status_compra_liquida": ["BLOQUEADO"],
            "regra_usada": ["projecao de venda observada + estoque de seguranca"],
            "limitacao": ["NÃO VALIDADO: venda observada projetada nao define pedido final"],
        }
    )


def promotion_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CODIGO": [20],
            "DESCRICAO": ["Produto B"],
            "NIVEL_1": ["B - TESTE"],
            "estoque_parado_total": [50.0],
            "lojas_com_estoque_parado": [2],
            "receita": [500.0],
            "qtd_vendida": [30.0],
        }
    )


def discontinuation_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "CODIGO": [30],
            "DESCRICAO": ["Produto C"],
            "NIVEL_1": ["C - TESTE"],
            "motivo": ["Zero vendas em 24 meses"],
            "receita": [pd.NA],
            "qtd_vendida": [pd.NA],
        }
    )


def test_triagens_possuem_colunas_obrigatorias_confianca_e_limitacao():
    frames = [
        triage.build_repricing_triage(negative_correlation_fixture()),
        triage.build_purchase_triage(projection_fixture()),
        triage.build_promotion_triage(promotion_fixture()),
        triage.build_discontinuation_triage(discontinuation_fixture()),
    ]

    for frame in frames:
        assert triage.REQUIRED_TRIAGE_COLUMNS.issubset(frame.columns)
        assert {"dado_faltante", "risco_decisao", "proxima_validacao_necessaria"}.issubset(frame.columns)
        assert frame["nivel_confianca"].notna().all()
        assert frame["limitacao"].str.contains("NÃO VALIDADO|DADO AUSENTE|BLOQUEADO").all()
        assert frame["acao_recomendada"].notna().all()
        assert frame["status_decisao_final"].eq("BLOQUEADO").all()


def test_triagem_compras_bloqueia_pedido_final_quando_faltam_dados_criticos():
    result = triage.build_purchase_triage(projection_fixture())
    row = result.iloc[0]

    assert row["nivel_confianca"] == "BLOQUEADO"
    assert row["status_decisao_final"] == "BLOQUEADO"
    assert "DADO AUSENTE" in row["dado_faltante"]
    assert "pedido final permanece bloqueado" in row["acao_recomendada"]


def test_outputs_de_triagem_sao_gerados_sem_linguagem_proibida(tmp_path):
    negative_correlation_fixture().to_csv(
        tmp_path / "produtos_correlacao_preco_volume_negativa.csv",
        index=False,
    )
    projection_fixture().to_csv(tmp_path / "projecao_venda_observada_2026.csv", index=False)
    promotion_fixture().to_csv(tmp_path / "rec_candidatos_promocao.csv", index=False)
    discontinuation_fixture().to_csv(tmp_path / "rec_candidatos_descontinuacao.csv", index=False)

    generated = triage.generate_recommendation_outputs(tmp_path)
    expected = [
        "triagem_repricing.csv",
        "triagem_compras.csv",
        "triagem_promocao.csv",
        "triagem_descontinuacao.csv",
        "triagem_possivel_promocao.csv",
        "triagem_possivel_descontinuacao.csv",
    ]

    for filename in expected:
        path = tmp_path / filename
        assert path.exists()
        saved = pd.read_csv(path)
        assert triage.REQUIRED_TRIAGE_COLUMNS.issubset(saved.columns)
        text = path.name.lower() + "\n" + saved.to_csv(index=False).lower()
        for phrase in PROHIBITED_OUTPUT_PHRASES:
            assert phrase not in text

    assert not generated["triagem_repricing"].empty
    assert not generated["triagem_compras"].empty
    assert not generated["triagem_promocao"].empty
    assert not generated["triagem_descontinuacao"].empty


def test_documentacao_spec06_existe_e_registra_bloqueios():
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8")

    assert "projecao_venda_observada_2026.csv" in text
    assert "triagem_repricing.csv" in text
    assert "BLOQUEADO" in text
    assert "DADO AUSENTE" in text
    assert "NÃO VALIDADO" in text
