# -*- coding: utf-8 -*-
"""Recommendation triage layer for Spec 06.

The outputs produced here are queues for validation, not final commercial,
purchase, promotion, or assortment decisions.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_TABLES_DIR = ROOT / "outputs" / "tables"

REQUIRED_TRIAGE_COLUMNS = {
    "tipo_triagem",
    "nivel_confianca",
    "evidencia",
    "limitacao",
    "acao_recomendada",
}

AUDIT_TRIAGE_COLUMNS = [
    "tipo_triagem",
    "CODIGO",
    "DESCRICAO",
    "NIVEL_1",
    "nivel_confianca",
    "status_decisao_final",
    "regra_usada",
    "evidencia",
    "dado_faltante",
    "limitacao",
    "risco_decisao",
    "proxima_validacao_necessaria",
    "acao_recomendada",
]

COMMON_MISSING_DATA = (
    "DADO AUSENTE: margem, estoque atual confiavel, lead time, lote minimo, fornecedor e plano comercial"
)
COMMON_RISK = (
    "Risco de decisao operacional sem validacao: excesso de estoque, perda de margem ou corte indevido de SKU"
)


def build_repricing_triage(
    negative_correlation: pd.DataFrame,
    price_dispersion: pd.DataFrame | None = None,
    dispersion_limit: int = 50,
) -> pd.DataFrame:
    """Build price-investigation triage from correlation and dispersion evidence."""
    rows: list[dict[str, object]] = []

    if negative_correlation is not None and not negative_correlation.empty:
        for row in negative_correlation.itertuples(index=False):
            rows.append(
                _triage_row(
                    tipo_triagem="repricing_investigacao_correlacao",
                    codigo=getattr(row, "CODIGO", pd.NA),
                    descricao=getattr(row, "DESCRICAO", pd.NA),
                    nivel_1=getattr(row, "NIVEL_1", pd.NA),
                    nivel_confianca="Baixa",
                    regra_usada=getattr(row, "regra_usada", "correlacao_preco_volume negativa com receita relevante"),
                    evidencia=getattr(row, "evidencia", "correlacao_preco_volume negativa observada"),
                    dado_faltante="DADO AUSENTE: margem, concorrencia, campanhas, disponibilidade e politica comercial",
                    limitacao=getattr(
                        row,
                        "limitacao",
                        "NÃO VALIDADO: associação observacional pode refletir sazonalidade, mix ou loja",
                    ),
                    proxima_validacao="Validar margem, concorrencia, campanhas e disponibilidade antes de teste controlado",
                    acao="Investigar preco e cadastro; qualquer ajuste exige aprovacao comercial",
                )
            )

    if price_dispersion is not None and not price_dispersion.empty:
        dispersion = price_dispersion.sort_values("amplitude_pct", ascending=False).head(dispersion_limit)
        for row in dispersion.itertuples(index=False):
            evidence = (
                f"amplitude_pct={float(getattr(row, 'amplitude_pct', 0)):.2f}; "
                f"qtd_lojas={int(getattr(row, 'qtd_lojas', 0))}; "
                f"receita_total={float(getattr(row, 'receita_total', 0)):.2f}"
            )
            rows.append(
                _triage_row(
                    tipo_triagem="repricing_investigacao_dispersao",
                    codigo=getattr(row, "CODIGO", pd.NA),
                    descricao=getattr(row, "DESCRICAO", pd.NA),
                    nivel_1=getattr(row, "NIVEL_1", pd.NA),
                    nivel_confianca="Baixa",
                    regra_usada="alta dispersao de preco cadastrado entre lojas",
                    evidencia=evidence,
                    dado_faltante="DADO AUSENTE: politica de preco por loja, margem e concorrencia local",
                    limitacao="NÃO VALIDADO: dispersao pode ser regra comercial legitima por loja ou embalagem",
                    proxima_validacao="Conferir cadastro, embalagem, margem e regra comercial por loja",
                    acao="Revisar cadastro e politica de preco antes de qualquer mudanca",
                )
            )

    return _ordered_triage(pd.DataFrame(rows))


def build_purchase_triage(projection: pd.DataFrame) -> pd.DataFrame:
    """Build gross-purchase triage from observed-sales projection."""
    if projection is None or projection.empty:
        return _ordered_triage(pd.DataFrame())

    rows = []
    for row in projection.itertuples(index=False):
        evidence = (
            f"venda_observada_projetada_2026={float(getattr(row, 'venda_observada_projetada_2026', 0)):.2f}; "
            f"compra_bruta_sugerida={float(getattr(row, 'compra_bruta_sugerida', 0)):.2f}; "
            f"status_compra_liquida={getattr(row, 'status_compra_liquida', 'BLOQUEADO')}"
        )
        rows.append(
            _triage_row(
                tipo_triagem="compras_triagem_bruta",
                codigo=getattr(row, "CODIGO", pd.NA),
                descricao=getattr(row, "DESCRICAO", pd.NA),
                nivel_1=getattr(row, "NIVEL_1", pd.NA),
                nivel_confianca="BLOQUEADO"
                if getattr(row, "status_compra_liquida", "BLOQUEADO") == "BLOQUEADO"
                else "Baixa",
                regra_usada=getattr(row, "regra_usada", "projecao de venda observada + estoque de seguranca"),
                evidencia=evidence,
                dado_faltante=COMMON_MISSING_DATA,
                limitacao=getattr(
                    row,
                    "limitacao",
                    "NÃO VALIDADO: venda observada projetada nao define pedido final",
                ),
                proxima_validacao="Validar estoque atual, margem, lead time, lote minimo e fornecedor",
                acao="Usar como fila de validacao de compra bruta; pedido final permanece bloqueado",
            )
        )
    return _ordered_triage(pd.DataFrame(rows))


def build_promotion_triage(promotion_candidates: pd.DataFrame) -> pd.DataFrame:
    """Convert legacy promotion candidates into auditable triage rows."""
    if promotion_candidates is None or promotion_candidates.empty:
        return _ordered_triage(pd.DataFrame())

    rows = []
    for row in promotion_candidates.itertuples(index=False):
        evidence = (
            f"estoque_parado_total={float(getattr(row, 'estoque_parado_total', 0)):.2f}; "
            f"receita={float(getattr(row, 'receita', 0)):.2f}; "
            f"lojas_com_estoque_parado={int(getattr(row, 'lojas_com_estoque_parado', 0))}"
        )
        rows.append(
            _triage_row(
                tipo_triagem="promocao_possivel",
                codigo=getattr(row, "CODIGO", pd.NA),
                descricao=getattr(row, "DESCRICAO", pd.NA),
                nivel_1=getattr(row, "NIVEL_1", pd.NA),
                nivel_confianca="Baixa",
                regra_usada="estoque parado legado com alguma venda observada",
                evidencia=evidence,
                dado_faltante=COMMON_MISSING_DATA,
                limitacao="NÃO VALIDADO: estoque parado usa estoque inicial e nao confirma disponibilidade atual",
                proxima_validacao="Validar margem, estoque atual, campanha, categoria e substitutos",
                acao="Avaliar campanha piloto somente apos validacao comercial e financeira",
            )
        )
    return _ordered_triage(pd.DataFrame(rows))


def build_discontinuation_triage(discontinuation_candidates: pd.DataFrame) -> pd.DataFrame:
    """Convert legacy assortment-removal candidates into blocked triage rows."""
    if discontinuation_candidates is None or discontinuation_candidates.empty:
        return _ordered_triage(pd.DataFrame())

    rows = []
    for row in discontinuation_candidates.itertuples(index=False):
        reason = getattr(row, "motivo", "regra legada de baixa venda")
        evidence = (
            f"motivo_legado={reason}; "
            f"receita={_format_optional_number(getattr(row, 'receita', pd.NA))}; "
            f"qtd_vendida={_format_optional_number(getattr(row, 'qtd_vendida', pd.NA))}"
        )
        rows.append(
            _triage_row(
                tipo_triagem="descontinuacao_possivel",
                codigo=getattr(row, "CODIGO", pd.NA),
                descricao=getattr(row, "DESCRICAO", pd.NA),
                nivel_1=getattr(row, "NIVEL_1", pd.NA),
                nivel_confianca="BLOQUEADO",
                regra_usada="zero venda observada ou baixa receita com estoque parado em regra legada",
                evidencia=evidence,
                dado_faltante=(
                    "DADO AUSENTE: margem, papel estrategico do SKU, substitutos, fornecedor, "
                    "estoque atual, devolucoes e garantias"
                ),
                limitacao="NÃO VALIDADO: ausencia ou baixa venda observada nao mede potencial de venda",
                proxima_validacao="Revisar margem, papel na categoria, substitutos, fornecedor e historico comercial",
                acao="Manter como revisao de sortimento bloqueada para decisao final",
            )
        )
    return _ordered_triage(pd.DataFrame(rows))


def generate_recommendation_outputs(
    output_dir: Path = OUTPUT_TABLES_DIR,
) -> dict[str, pd.DataFrame]:
    """Read Spec 06/legacy inputs and write recommendation triage CSV outputs."""
    negative = _read_optional(output_dir / "produtos_correlacao_preco_volume_negativa.csv")
    projection = _read_optional(output_dir / "projecao_venda_observada_2026.csv")
    dispersion = _read_optional(output_dir / "dispersao_preco_entre_lojas.csv")
    promotion = _read_optional(output_dir / "rec_candidatos_promocao.csv")
    discontinuation = _read_optional(output_dir / "rec_candidatos_descontinuacao.csv")

    repricing = build_repricing_triage(negative, dispersion)
    purchases = build_purchase_triage(projection)
    promotion_triage = build_promotion_triage(promotion)
    discontinuation_triage = build_discontinuation_triage(discontinuation)

    output_dir.mkdir(parents=True, exist_ok=True)
    repricing.to_csv(output_dir / "triagem_repricing.csv", index=False, encoding="utf-8")
    purchases.to_csv(output_dir / "triagem_compras.csv", index=False, encoding="utf-8")
    promotion_triage.to_csv(output_dir / "triagem_promocao.csv", index=False, encoding="utf-8")
    discontinuation_triage.to_csv(output_dir / "triagem_descontinuacao.csv", index=False, encoding="utf-8")
    promotion_triage.to_csv(output_dir / "triagem_possivel_promocao.csv", index=False, encoding="utf-8")
    discontinuation_triage.to_csv(
        output_dir / "triagem_possivel_descontinuacao.csv",
        index=False,
        encoding="utf-8",
    )

    return {
        "triagem_repricing": repricing,
        "triagem_compras": purchases,
        "triagem_promocao": promotion_triage,
        "triagem_descontinuacao": discontinuation_triage,
    }


def _triage_row(
    tipo_triagem: str,
    codigo: object,
    descricao: object,
    nivel_1: object,
    nivel_confianca: str,
    regra_usada: str,
    evidencia: str,
    dado_faltante: str,
    limitacao: str,
    proxima_validacao: str,
    acao: str,
) -> dict[str, object]:
    return {
        "tipo_triagem": tipo_triagem,
        "CODIGO": codigo,
        "DESCRICAO": descricao,
        "NIVEL_1": nivel_1,
        "nivel_confianca": nivel_confianca,
        "status_decisao_final": "BLOQUEADO",
        "regra_usada": regra_usada,
        "evidencia": evidencia,
        "dado_faltante": dado_faltante,
        "limitacao": limitacao,
        "risco_decisao": COMMON_RISK,
        "proxima_validacao_necessaria": proxima_validacao,
        "acao_recomendada": acao,
    }


def _ordered_triage(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=AUDIT_TRIAGE_COLUMNS)
    for column in AUDIT_TRIAGE_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA
    return df[AUDIT_TRIAGE_COLUMNS].reset_index(drop=True)


def _read_optional(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _format_optional_number(value: object) -> str:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return "DADO AUSENTE"
    return f"{float(number):.2f}"


if __name__ == "__main__":
    outputs = generate_recommendation_outputs()
    for name, frame in outputs.items():
        print(f"[SPEC06] {name}.csv:", len(frame), "linhas")
