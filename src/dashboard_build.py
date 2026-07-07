# -*- coding: utf-8 -*-
"""Spec 09 - build dos dados estaticos do dashboard.

Este script NAO recalcula regras de negocio. Ele apenas:
- le outputs ja validados em outputs/tables/ (Specs 01-07);
- seleciona colunas, agrega para apresentacao (contagens, somas e razoes
  usando as formulas documentadas em docs/metric_catalog.md);
- grava JSON estatico em docs/data/ para consumo do dashboard GitHub Pages.

Ele nao le dados brutos, nao regrava nada fora de docs/data/ e nao altera
scripts legados.
Qualquer divergencia entre os numeros aqui e o relatorio final e tratada como
erro de build (cross-checks abaixo falham cedo).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
DATA_OUT = ROOT / "docs" / "data"

FONTES = [
    "outputs/tables/vendas_mensais.csv",
    "outputs/tables/vendas_same_store_yoy.csv",
    "outputs/tables/vendas_categorias_yoy.csv",
    "outputs/tables/sortimento_controlado_por_volume.csv",
    "outputs/tables/data_quality_report.csv",
    "outputs/tables/ingestion_audit.csv",
    "outputs/tables/compras_coverage_audit.csv",
    "outputs/tables/gaps_saldo_contabil_estoque.csv",
    "outputs/tables/produtos_correlacao_preco_volume_negativa.csv",
    "outputs/tables/projecao_venda_observada_2026.csv",
    "outputs/tables/triagem_repricing.csv",
    "outputs/tables/triagem_compras.csv",
    "outputs/tables/triagem_promocao.csv",
    "outputs/tables/triagem_descontinuacao.csv",
    "outputs/tables/hypothesis_status.csv",
    "reports/relatorio_final.md",
]

ALLOWED_HYPOTHESIS_STATUS = {
    "Confirmada descritivamente",
    "Parcialmente suportada",
    "Exploratória",
    "Não comprovada",
    "Rejeitada",
    "Inválida por limitação de dados",
}
ALLOWED_QUALITY_STATUS = {"PASS", "WARN", "FAIL"}
ALLOWED_COVERAGE_CLASS = {"OK", "suspeito", "crítico", "não confiável para análise causal"}

# Fragmentos proibidos pela Spec 09 no payload do dashboard (afirmativos).
FORBIDDEN_FRAGMENTS = [
    "elasticidade comprovada",
    "ruptura comprovada",
    "ruptura fisica comprovada",
    "compras causaram a queda",
    "demanda_real",
]


def _read(name: str) -> pd.DataFrame:
    path = TABLES / name
    if not path.exists():
        raise FileNotFoundError(f"output validado ausente: {path.relative_to(ROOT)}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"output validado vazio: {path.relative_to(ROOT)}")
    return frame


def _records(frame: pd.DataFrame, columns: list[str] | None = None, round_map: dict | None = None) -> list[dict]:
    view = frame if columns is None else frame[columns].copy()
    if round_map:
        for col, digits in round_map.items():
            if col in view.columns:
                view[col] = pd.to_numeric(view[col], errors="coerce").round(digits)
    # to_json trata NaN -> null e tipos numpy -> tipos JSON.
    return json.loads(view.to_json(orient="records", force_ascii=False))


def _variacao_percentual(atual: float, base: float) -> float | None:
    # Formula documentada em docs/metric_catalog.md (variacao_percentual).
    if base == 0 or pd.isna(base) or pd.isna(atual):
        return None
    return (atual - base) / base


def build_payload() -> dict:
    vendas_mensais = _read("vendas_mensais.csv")
    same_store = _read("vendas_same_store_yoy.csv")
    categorias = _read("vendas_categorias_yoy.csv")
    sortimento = _read("sortimento_controlado_por_volume.csv")
    qualidade = _read("data_quality_report.csv")
    ingestao = _read("ingestion_audit.csv")
    cobertura = _read("compras_coverage_audit.csv")
    gaps = _read("gaps_saldo_contabil_estoque.csv")
    correlacao = _read("produtos_correlacao_preco_volume_negativa.csv")
    projecao = _read("projecao_venda_observada_2026.csv")
    hipoteses = _read("hypothesis_status.csv")
    triagens_arquivos = {
        "repricing": "triagem_repricing.csv",
        "compras": "triagem_compras.csv",
        "promocao": "triagem_promocao.csv",
        "descontinuacao": "triagem_descontinuacao.csv",
    }
    triagens_df = {nome: _read(arq) for nome, arq in triagens_arquivos.items()}

    # ---- Validacoes de vocabulario (fail early) --------------------------
    if not set(qualidade["status"].dropna()).issubset(ALLOWED_QUALITY_STATUS):
        raise ValueError("data_quality_report.csv com status fora de PASS/WARN/FAIL")
    if not set(hipoteses["status"].dropna()).issubset(ALLOWED_HYPOTHESIS_STATUS):
        raise ValueError("hypothesis_status.csv com status fora do vocabulario da Spec 07")
    if not set(cobertura["classificacao_confiabilidade"].dropna()).issubset(ALLOWED_COVERAGE_CLASS):
        raise ValueError("compras_coverage_audit.csv com classificacao inesperada")
    for nome, frame in triagens_df.items():
        if not frame["status_decisao_final"].eq("BLOQUEADO").all():
            raise ValueError(f"triagem_{nome}: status_decisao_final diferente de BLOQUEADO")

    # ---- Vendas mensais + YoY mensal (formula do catalogo) ---------------
    vm = vendas_mensais.sort_values("ANO_MES").reset_index(drop=True)
    receita_por_mes = dict(zip(vm["ANO_MES"], vm["receita"]))
    qtd_por_mes = dict(zip(vm["ANO_MES"], vm["qtd_vendida"]))

    def _mes_anterior_ano(ano_mes: str) -> str:
        ano, mes = ano_mes.split("-")
        return f"{int(ano) - 1}-{mes}"

    vendas_rows = []
    for _, row in vm.iterrows():
        base_key = _mes_anterior_ano(row["ANO_MES"])
        var_receita = _variacao_percentual(row["receita"], receita_por_mes.get(base_key, float("nan")))
        var_qtd = _variacao_percentual(row["qtd_vendida"], qtd_por_mes.get(base_key, float("nan")))
        vendas_rows.append(
            {
                "ano_mes": row["ANO_MES"],
                "receita": round(float(row["receita"]), 2),
                "qtd_vendida": round(float(row["qtd_vendida"]), 2),
                "variacao_receita_yoy": None if var_receita is None else round(var_receita, 4),
                "variacao_qtd_yoy": None if var_qtd is None else round(var_qtd, 4),
            }
        )

    receita_total = float(vm["receita"].sum())
    receita_2024_11 = float(receita_por_mes["2024-11"])
    receita_2025_12 = float(receita_por_mes["2025-12"])
    queda_janela_extrema = _variacao_percentual(receita_2025_12, receita_2024_11)

    # Cross-check com reports/relatorio_final.md (janela 2024-11 -> 2025-12: -91,7%).
    if abs(queda_janela_extrema - (-0.917)) > 0.005:
        raise ValueError(
            "cross-check falhou: queda 2024-11->2025-12 nao reproduz o relatorio final "
            f"(calculado {queda_janela_extrema:.4f}, esperado ~-0.917)"
        )

    # ---- Lojas: agregacao anual 2025 vs 2024 (apresentacao) --------------
    ss = same_store.copy()
    ss_2025 = ss[ss["ANO_MES"].str.startswith("2025")]
    lojas_anual = (
        ss_2025.groupby(["COD_EMPRESA", "CD_CIDADE", "CD_ESTADO"], as_index=False)[
            ["receita", "receita_ano_anterior"]
        ].sum()
    )
    lojas_anual["variacao_receita_yoy"] = (
        lojas_anual["receita"] / lojas_anual["receita_ano_anterior"] - 1
    )
    # Cross-check com o relatorio final: quedas anuais entre -30,6% e -66,5%.
    var_min = float(lojas_anual["variacao_receita_yoy"].min())
    var_max = float(lojas_anual["variacao_receita_yoy"].max())
    if abs(var_min - (-0.665)) > 0.005 or abs(var_max - (-0.306)) > 0.005:
        raise ValueError(
            "cross-check falhou: YoY anual por loja nao reproduz o relatorio final "
            f"(min {var_min:.4f}, max {var_max:.4f})"
        )
    lojas_comparaveis_2025 = int(ss_2025["loja_comparavel_yoy"].sum())
    pares_loja_mes_2025 = int(len(ss_2025))

    same_store_cols = [
        "ANO_MES",
        "COD_EMPRESA",
        "CD_CIDADE",
        "CD_ESTADO",
        "receita",
        "receita_ano_anterior",
        "variacao_receita_yoy",
        "qtd_vendida_estoque",
        "linhas_venda_diarias",
        "skus_vendidos",
        "dias_com_venda",
        "dias_com_venda_ano_anterior",
        "loja_comparavel_yoy",
        "status_loja_mes",
    ]

    # ---- Categorias -------------------------------------------------------
    cat_cols = [
        "periodicidade",
        "periodo",
        "NIVEL_1",
        "receita",
        "receita_ano_anterior",
        "variacao_receita_yoy",
        "contribuicao_queda_periodo",
        "classificacao_categoria",
    ]
    cat_2025_mensal = categorias[
        (categorias["periodicidade"] == "mes") & (categorias["periodo"].astype(str).str.startswith("2025"))
    ]
    classif_por_mes = (
        cat_2025_mensal.groupby(["periodo", "classificacao_categoria"]).size().unstack(fill_value=0)
    )
    classificacao_mensal_2025 = [
        {"periodo": periodo, **{str(k): int(v) for k, v in row.items()}}
        for periodo, row in classif_por_mes.iterrows()
    ]

    # ---- Cobertura de compras (sem nivel produto: 2.731 linhas ficam no CSV) --
    cob_cols = [
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
        "classificacao_confiabilidade",
    ]
    cob_total_df = cobertura[cobertura["nivel_agrupamento"] == "periodo_total"]
    if len(cob_total_df) != 1:
        raise ValueError("compras_coverage_audit.csv sem linha unica de periodo_total")
    cob_total = _records(cob_total_df, cob_cols + ["interpretacao", "limitacao"], {
        "total_vendido_estoque": 2,
        "estoque_inicial_estoque": 2,
        "compras_registradas_estoque": 2,
        "entradas_conhecidas_estoque": 2,
        "diferenca_saidas_entradas": 2,
        "pct_cobertura_entradas": 4,
        "pct_eventos_saldo_projetado_negativo": 4,
        "pct_skus_venda_sem_compra": 4,
    })[0]

    def _cobertura_nivel(nivel: str) -> list[dict]:
        sub = cobertura[cobertura["nivel_agrupamento"] == nivel]
        return _records(sub, cob_cols, {
            "total_vendido_estoque": 2,
            "entradas_conhecidas_estoque": 2,
            "estoque_inicial_estoque": 2,
            "compras_registradas_estoque": 2,
            "diferenca_saidas_entradas": 2,
            "pct_cobertura_entradas": 4,
            "pct_eventos_saldo_projetado_negativo": 4,
            "pct_skus_venda_sem_compra": 4,
        })

    # ---- Gaps: resumo + top 50 (arquivo completo tem 28.721 linhas / 11 MB) --
    gaps_pos = gaps[gaps["GAP_CONTABIL_ESTOQUE"] > 0]
    gaps_top = gaps.sort_values("GAP_CONTABIL_ESTOQUE", ascending=False).head(50)
    gaps_resumo = {
        "n_pares_produto_loja": int(len(gaps)),
        "n_pares_com_gap_positivo": int(len(gaps_pos)),
        "interpretacao_saldo_negativo": str(gaps["INTERPRETACAO_SALDO_NEGATIVO"].iloc[0]),
        "possiveis_causas_gap": str(gaps["POSSIVEIS_CAUSAS_GAP"].iloc[0]),
        "nota_amostra": "Top 50 pares por gap contábil; arquivo completo em outputs/tables/gaps_saldo_contabil_estoque.csv",
    }
    gaps_top_rows = _records(
        gaps_top,
        [
            "COD_EMPRESA",
            "CODIGO",
            "DESCRICAO",
            "NIVEL_1",
            "ESTOQUE_INICIAL",
            "COMPRAS_REGISTRADAS_ESTOQUE",
            "VENDAS_ESTOQUE",
            "SALDO_PROJETADO_CONTABIL",
            "GAP_CONTABIL_ESTOQUE",
        ],
        {c: 2 for c in [
            "ESTOQUE_INICIAL",
            "COMPRAS_REGISTRADAS_ESTOQUE",
            "VENDAS_ESTOQUE",
            "SALDO_PROJETADO_CONTABIL",
            "GAP_CONTABIL_ESTOQUE",
        ]},
    )

    # ---- Correlacao preco-volume (associacao exploratoria) ----------------
    corr_vals = pd.to_numeric(correlacao["correlacao_preco_volume"], errors="coerce").dropna()
    bins = [round(-1.0 + i * 0.05, 2) for i in range(13)]  # -1.00 .. -0.40
    hist = pd.cut(corr_vals, bins=bins, include_lowest=True).value_counts().sort_index()
    corr_hist = [
        {"faixa": f"{interval.left:.2f} a {interval.right:.2f}", "produtos": int(qtd)}
        for interval, qtd in hist.items()
    ]

    # ---- Projecao ----------------------------------------------------------
    flag_col = "flag_nao_calcular_compra_liquida_por_estoque_inconfiavel"
    proj_totais = {
        "n_produtos": int(len(projecao)),
        "venda_observada_projetada_2026_total": round(float(projecao["venda_observada_projetada_2026"].sum()), 2),
        "venda_media_anual_observada_historica_total": round(
            float(projecao["venda_media_anual_observada_historica"].sum()), 2
        ),
        "compra_bruta_sugerida_total": round(float(projecao["compra_bruta_sugerida"].sum()), 2),
        "n_compra_liquida_bloqueada": int(projecao[flag_col].astype(bool).sum()),
        "status_compra_liquida": {
            str(k): int(v) for k, v in projecao["status_compra_liquida"].value_counts().items()
        },
    }
    # Cross-check com o relatorio final (1.370.582,76 projetado; 1.483.220 compra bruta).
    if abs(proj_totais["venda_observada_projetada_2026_total"] - 1_370_582.76) > 1.0:
        raise ValueError("cross-check falhou: total projetado 2026 nao reproduz o relatorio final")
    proj_top = projecao.sort_values("venda_observada_projetada_2026", ascending=False).head(30)
    proj_top_rows = _records(
        proj_top,
        [
            "CODIGO",
            "DESCRICAO",
            "NIVEL_1",
            "venda_observada_projetada_2026",
            "venda_media_anual_observada_historica",
            "compra_bruta_sugerida",
            "status_compra_liquida",
            "nivel_confianca",
        ],
        {
            "venda_observada_projetada_2026": 2,
            "venda_media_anual_observada_historica": 2,
            "compra_bruta_sugerida": 2,
        },
    )

    # ---- Triagens ----------------------------------------------------------
    def _unique(series: pd.Series) -> list[str]:
        return sorted({str(v) for v in series.dropna() if str(v).strip()})

    triagens = {}
    for nome, frame in triagens_df.items():
        triagens[nome] = {
            "arquivo": f"outputs/tables/{triagens_arquivos[nome]}",
            "n_linhas": int(len(frame)),
            "nivel_confianca": {str(k): int(v) for k, v in frame["nivel_confianca"].value_counts().items()},
            "status_decisao_final": {
                str(k): int(v) for k, v in frame["status_decisao_final"].value_counts().items()
            },
            "regra_usada": _unique(frame["regra_usada"]),
            "dado_faltante": _unique(frame["dado_faltante"]),
            "limitacao": _unique(frame["limitacao"]),
            "risco_decisao": _unique(frame["risco_decisao"]),
            "proxima_validacao_necessaria": _unique(frame["proxima_validacao_necessaria"]),
            "acao_recomendada": _unique(frame["acao_recomendada"]),
            "amostra": _records(
                frame.head(40),
                ["CODIGO", "DESCRICAO", "NIVEL_1", "nivel_confianca", "status_decisao_final", "evidencia"],
            ),
            "nota_amostra": f"Amostra das 40 primeiras linhas de {len(frame)}; lista completa no CSV de origem.",
        }

    # ---- Qualidade / ingestao ----------------------------------------------
    qual_counts = {str(k): int(v) for k, v in qualidade["status"].value_counts().items()}

    hip_counts = {str(k): int(v) for k, v in hipoteses["status"].value_counts().items()}

    payload = {
        "meta": {
            "gerado_em": date.today().isoformat(),
            "periodo": "2024-01 a 2025-12",
            "fontes": FONTES,
            "gerador": "src/dashboard_build.py (Spec 09)",
            "avisos": [
                "Venda observada não é demanda real.",
                "Gap contábil de estoque não é ruptura física comprovada.",
                "Correlação preço-volume não é elasticidade.",
                "Triagens não são decisões finais.",
                "Compras não podem ser tratadas como causa comprovada da queda de vendas.",
            ],
        },
        "kpis": {
            "receita_total_24m": round(receita_total, 2),
            "receita_2024_11": round(receita_2024_11, 2),
            "receita_2025_12": round(receita_2025_12, 2),
            "queda_janela_2024_11_a_2025_12": round(queda_janela_extrema, 4),
            "skus_2024_11": int(sortimento.loc[sortimento["ANO_MES"] == "2024-11", "skus_observados"].iloc[0]),
            "skus_2025_12": int(sortimento.loc[sortimento["ANO_MES"] == "2025-12", "skus_observados"].iloc[0]),
            "lojas": int(same_store["COD_EMPRESA"].nunique()),
            "lojas_comparaveis_2025": lojas_comparaveis_2025,
            "pares_loja_mes_2025": pares_loja_mes_2025,
            "cobertura_entradas_pct": cob_total["pct_cobertura_entradas"],
            "classificacao_cobertura": cob_total["classificacao_confiabilidade"],
            "qualidade_checks": qual_counts,
            "hipoteses_status": hip_counts,
        },
        "vendas_mensais": vendas_rows,
        "lojas_yoy_anual_2025": _records(
            lojas_anual.sort_values("variacao_receita_yoy"),
            ["COD_EMPRESA", "CD_CIDADE", "CD_ESTADO", "receita", "receita_ano_anterior", "variacao_receita_yoy"],
            {"receita": 2, "receita_ano_anterior": 2, "variacao_receita_yoy": 4},
        ),
        "same_store": _records(
            same_store.sort_values(["COD_EMPRESA", "ANO_MES"]),
            same_store_cols,
            {"receita": 2, "receita_ano_anterior": 2, "variacao_receita_yoy": 4, "qtd_vendida_estoque": 2},
        ),
        "categorias_yoy": _records(
            categorias,
            cat_cols,
            {
                "receita": 2,
                "receita_ano_anterior": 2,
                "variacao_receita_yoy": 4,
                "contribuicao_queda_periodo": 4,
            },
        ),
        "classificacao_categorias_mensal_2025": classificacao_mensal_2025,
        "sortimento": _records(
            sortimento,
            [
                "ANO_MES",
                "skus_observados",
                "linhas_venda_diarias",
                "skus_esperados_media",
                "skus_esperados_p05",
                "skus_esperados_p95",
                "status_sortimento_controlado",
            ],
            {"skus_esperados_media": 1, "skus_esperados_p05": 1, "skus_esperados_p95": 1},
        ),
        "qualidade": {
            "contagem_status": qual_counts,
            "checks": _records(qualidade, None, {"pct_afetado": 4}),
        },
        "ingestao": _records(
            ingestao,
            [
                "arquivo",
                "encoding_usado",
                "separador_detectado",
                "linhas_lidas",
                "colunas_lidas",
                "erros_parsing",
                "nulos_antes",
                "nulos_depois",
                "zeros_criados",
                "registros_descartados",
                "status_ingestao",
            ],
        ),
        "cobertura": {
            "periodo_total": cob_total,
            "por_mes": _cobertura_nivel("mes"),
            "por_loja": _cobertura_nivel("loja"),
            "por_categoria": _cobertura_nivel("categoria"),
            "nota": "Nível produto (2.731 linhas) não embarcado; consulte outputs/tables/compras_coverage_audit.csv",
        },
        "gaps": {"resumo": gaps_resumo, "top": gaps_top_rows},
        "correlacao": {
            "n_produtos": int(len(correlacao)),
            "histograma": corr_hist,
            "rows": _records(
                correlacao,
                [
                    "CODIGO",
                    "DESCRICAO",
                    "NIVEL_1",
                    "correlacao_preco_volume",
                    "n_obs",
                    "receita_total",
                    "nivel_confianca",
                    "tipo_analise",
                ],
                {"correlacao_preco_volume": 4, "receita_total": 2},
            ),
        },
        "projecao": {"totais": proj_totais, "top": proj_top_rows},
        "triagens": triagens,
        "hipoteses": _records(hipoteses),
    }
    return payload


def write_outputs(payload: dict) -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=1)
    lowered = text.lower()
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"payload do dashboard contem linguagem proibida: {fragment}")
    (DATA_OUT / "dashboard_data.json").write_text(text, encoding="utf-8")
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    (DATA_OUT / "dashboard_data.js").write_text(
        "// Gerado por src/dashboard_build.py a partir de outputs validados. Nao editar manualmente.\n"
        f"window.DASHBOARD_DATA = {compact};\n",
        encoding="utf-8",
    )
    print(f"OK: docs/data/dashboard_data.json ({(DATA_OUT / 'dashboard_data.json').stat().st_size / 1024:.0f} KB)")
    print(f"OK: docs/data/dashboard_data.js ({(DATA_OUT / 'dashboard_data.js').stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    write_outputs(build_payload())
