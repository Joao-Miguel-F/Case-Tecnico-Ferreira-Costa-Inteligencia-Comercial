# -*- coding: utf-8 -*-
"""Reusable metric formulas for Spec 03.

The functions in this module are pure helpers: they do not read files, write
outputs, or correct legacy pipeline calculations. They encode the documented
business formulas from ``docs/metric_catalog.md`` and the data contract from
Spec 02.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd


FORMULAS = {
    "receita_bruta": "sum(QUANTIDADE_VENDIDA * PRECO_UNIT_MEDIO)",
    "quantidade_vendida": "sum(QUANTIDADE_VENDIDA)",
    "quantidade_vendida_armazenagem": (
        "sum(QUANTIDADE_VENDIDA * CONVERSAO_VENDA_PARA_ARMAZENAGEM)"
    ),
    "linhas_venda_diarias": "count(fato_vendas rows)",
    "ticket_medio_linha": "receita_bruta / linhas_venda_diarias",
    "preco_medio_vendido": "receita_bruta / quantidade_vendida",
    "variacao_percentual": "(valor_atual - valor_base) / valor_base",
    "compras_armazenagem": (
        "sum(QUANTIDADE_COMPRA * CONVERSAO_COMPRA_ARMAZENAGEM)"
    ),
    "entradas_conhecidas": "estoque_inicial + compras_armazenagem",
    "saldo_projetado": "estoque_inicial + compras_armazenagem - vendas_armazenagem",
    "gap_contabil_estoque": (
        "max(vendas_armazenagem - estoque_inicial - compras_armazenagem, 0)"
    ),
    "cobertura_dias": "estoque_inicial / venda_media_diaria",
    "cobertura_compras_lojas": "lojas_com_compra / total_lojas",
    "cobertura_compras_produtos": "produtos_com_compra / total_produtos",
    "preco_valido": "PRECO_EMBALAGEM_n > 0",
    "correlacao_preco_volume": "corr(preco_medio_mensal, quantidade_mensal), n_obs >= 8",
}


def _empty_or_missing_frame(df: pd.DataFrame, required_columns: Iterable[str]) -> bool:
    return df is None or df.empty or any(column not in df.columns for column in required_columns)


def _sum_product(df: pd.DataFrame, left_col: str, right_col: str) -> float:
    if _empty_or_missing_frame(df, [left_col, right_col]):
        return 0.0
    left = pd.to_numeric(df[left_col], errors="coerce").fillna(0)
    right = pd.to_numeric(df[right_col], errors="coerce").fillna(0)
    return float((left * right).sum())


def _is_vector(value: Any) -> bool:
    return isinstance(value, (pd.Series, list, tuple))


def safe_divide(numerator: Any, denominator: Any, zero_result: Any = pd.NA) -> Any:
    """Divide explicitly, replacing zero/null denominators instead of returning inf."""
    if _is_vector(numerator) or _is_vector(denominator):
        num = pd.Series(numerator, dtype="Float64")
        den = pd.Series(denominator, dtype="Float64")
        result = num.div(den)
        result = result.mask(den.isna() | den.eq(0), zero_result)
        return result.mask(result.isin([float("inf"), float("-inf")]), zero_result)

    if denominator is None or pd.isna(denominator) or denominator == 0:
        return zero_result
    if numerator is None or pd.isna(numerator):
        return zero_result
    result = numerator / denominator
    if result in (float("inf"), float("-inf")):
        return zero_result
    return result


def receita_bruta(
    vendas: pd.DataFrame,
    quantidade_col: str = "QUANTIDADE_VENDIDA",
    preco_col: str = "PRECO_UNIT_MEDIO",
) -> float:
    """Formula: sum(QUANTIDADE_VENDIDA * PRECO_UNIT_MEDIO)."""
    return _sum_product(vendas, quantidade_col, preco_col)


def quantidade_total(vendas: pd.DataFrame, quantidade_col: str = "QUANTIDADE_VENDIDA") -> float:
    """Formula: sum(QUANTIDADE_VENDIDA)."""
    if _empty_or_missing_frame(vendas, [quantidade_col]):
        return 0.0
    return float(pd.to_numeric(vendas[quantidade_col], errors="coerce").fillna(0).sum())


def quantidade_vendida_armazenagem(
    vendas: pd.DataFrame,
    quantidade_col: str = "QUANTIDADE_VENDIDA",
    conversao_col: str = "CONVERSAO_VENDA_PARA_ARMAZENAGEM",
) -> float:
    """Formula: sum(QUANTIDADE_VENDIDA * CONVERSAO_VENDA_PARA_ARMAZENAGEM)."""
    return _sum_product(vendas, quantidade_col, conversao_col)


def quantidade_compra_armazenagem(
    compras: pd.DataFrame,
    quantidade_col: str = "QUANTIDADE_COMPRA",
    conversao_col: str = "CONVERSAO_COMPRA_ARMAZENAGEM",
) -> float:
    """Formula: sum(QUANTIDADE_COMPRA * CONVERSAO_COMPRA_ARMAZENAGEM)."""
    return _sum_product(compras, quantidade_col, conversao_col)


def linhas_venda_diarias(vendas: pd.DataFrame) -> int:
    """Count daily aggregated sales rows; this is not a coupon/order count."""
    if vendas is None:
        return 0
    return int(len(vendas))


def skus_vendidos(vendas: pd.DataFrame, produto_col: str = "CODIGO") -> int:
    """Distinct products with at least one observed sale row."""
    if _empty_or_missing_frame(vendas, [produto_col]):
        return 0
    return int(vendas[produto_col].dropna().nunique())


def ticket_medio_linha(receita_total: float, linhas_venda: int) -> Any:
    """Formula: receita_bruta / linhas_venda_diarias."""
    return safe_divide(receita_total, linhas_venda)


def preco_medio_vendido(receita_total: float, quantidade_vendida: float) -> Any:
    """Formula: receita_bruta / quantidade_vendida."""
    return safe_divide(receita_total, quantidade_vendida)


def variacao_percentual(valor_atual: float, valor_base: float) -> Any:
    """Formula: (valor_atual - valor_base) / valor_base."""
    if valor_base is None or pd.isna(valor_base) or valor_base == 0:
        return pd.NA
    if valor_atual is None or pd.isna(valor_atual):
        return pd.NA
    return (valor_atual - valor_base) / valor_base


def entradas_conhecidas(estoque_inicial: Any, compras_armazenagem: Any) -> Any:
    """Formula: estoque_inicial + compras_armazenagem."""
    return estoque_inicial + compras_armazenagem


def saldo_projetado(estoque_inicial: Any, compras_armazenagem: Any, vendas_armazenagem: Any) -> Any:
    """Formula: estoque_inicial + compras_armazenagem - vendas_armazenagem."""
    return estoque_inicial + compras_armazenagem - vendas_armazenagem


def gap_contabil_estoque(
    vendas_armazenagem: Any,
    estoque_inicial: Any,
    compras_armazenagem: Any,
) -> Any:
    """Formula: max(vendas_armazenagem - estoque_inicial - compras_armazenagem, 0)."""
    gap = vendas_armazenagem - estoque_inicial - compras_armazenagem
    if _is_vector(gap):
        return pd.Series(gap).clip(lower=0)
    return max(gap, 0)


def cobertura_dias(estoque_inicial: Any, venda_media_diaria: Any) -> Any:
    """Formula: estoque_inicial / venda_media_diaria."""
    return safe_divide(estoque_inicial, venda_media_diaria)


def cobertura_compras(
    compras: pd.DataFrame,
    total_lojas: int,
    total_produtos: int,
    loja_col: str = "COD_EMPRESA",
    produto_col: str = "CODIGO",
) -> dict[str, Any]:
    """Return store/product purchase coverage ratios from registered purchases."""
    lojas = 0
    produtos = 0
    if compras is not None and not compras.empty:
        if loja_col in compras.columns:
            lojas = int(compras[loja_col].dropna().nunique())
        if produto_col in compras.columns:
            produtos = int(compras[produto_col].dropna().nunique())
    return {
        "lojas_com_compra": lojas,
        "total_lojas": total_lojas,
        "pct_lojas": safe_divide(lojas, total_lojas),
        "produtos_com_compra": produtos,
        "total_produtos": total_produtos,
        "pct_produtos": safe_divide(produtos, total_produtos),
    }


def preco_valido(preco: Any) -> Any:
    """Treat price values <= 0 as missing/invalid for price analyses."""
    if _is_vector(preco):
        series = pd.Series(preco, dtype="Float64")
        return series.where(series.gt(0), pd.NA)
    if preco is None or pd.isna(preco) or preco <= 0:
        return pd.NA
    return preco


def correlacao_preco_volume(
    dados: pd.DataFrame,
    preco_col: str = "preco_medio_mensal",
    volume_col: str = "quantidade_mensal",
    min_obs: int = 8,
) -> Any:
    """Formula: corr(preco_medio_mensal, quantidade_mensal), n_obs >= 8."""
    if _empty_or_missing_frame(dados, [preco_col, volume_col]):
        return pd.NA
    clean = dados[[preco_col, volume_col]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(clean) < min_obs:
        return pd.NA
    return float(clean[preco_col].corr(clean[volume_col]))
