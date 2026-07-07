# -*- coding: utf-8 -*-
"""quality_checks.py — Spec 02: funções de check de qualidade reutilizáveis.

Cada check recebe DataFrames prontos e devolve um (ou mais) registros no
formato do relatório de qualidade (ver REPORT_COLUMNS). Nenhum check
transforma, corrige ou descarta dados: a Spec 02 MEDE e REPORTA.

Convenções de status:
- PASS: 0 linhas afetadas, ou achado sem impacto analítico (informativo);
- WARN: problema real que degrada análises mas não invalida conclusão;
- FAIL: problema que invalida (ou torna não comprovável) conclusão
  importante do relatório atual — ex.: cobertura de compras.

Severidade: critica > alta > media > baixa > info.
"""

import pandas as pd

REPORT_COLUMNS = [
    "tabela",
    "check",
    "status",
    "linhas_afetadas",
    "pct_afetado",
    "severidade",
    "descricao",
    "impacto_analitico",
    "acao_recomendada",
]

VALID_STATUSES = {"PASS", "WARN", "FAIL"}


def make_record(
    tabela: str,
    check: str,
    status: str,
    linhas_afetadas: int,
    total_linhas: int,
    severidade: str,
    descricao: str,
    impacto_analitico: str,
    acao_recomendada: str,
) -> dict:
    """Monta um registro padronizado do relatório de qualidade."""
    if status not in VALID_STATUSES:
        raise ValueError(f"status inválido: {status!r} (use PASS/WARN/FAIL)")
    pct = round(100.0 * linhas_afetadas / total_linhas, 2) if total_linhas else 0.0
    return {
        "tabela": tabela,
        "check": check,
        "status": status,
        "linhas_afetadas": int(linhas_afetadas),
        "pct_afetado": pct,
        "severidade": severidade,
        "descricao": descricao,
        "impacto_analitico": impacto_analitico,
        "acao_recomendada": acao_recomendada,
    }


def _status_if_present(n: int, status: str) -> str:
    return "PASS" if n == 0 else status


# ---------------------------------------------------------------------------
# Estrutura e tipos
# ---------------------------------------------------------------------------
def check_expected_columns(df: pd.DataFrame, expected: list[str], tabela: str) -> dict:
    """Colunas esperadas presentes (e nenhuma inesperada)."""
    missing = [c for c in expected if c not in df.columns]
    extra = [c for c in df.columns if c not in expected]
    n = len(missing) + len(extra)
    desc = "colunas conforme o contrato"
    if n:
        desc = f"ausentes: {missing or '-'}; extras: {extra or '-'}"
    return make_record(
        tabela, "colunas_esperadas", _status_if_present(n, "FAIL"), n, len(expected),
        "critica" if missing else ("baixa" if extra else "info"),
        desc,
        "coluna ausente quebra o pipeline e as métricas derivadas",
        "corrigir extração/contrato antes de qualquer análise" if n else "nenhuma",
    )


def check_schema(name: str, df: pd.DataFrame, tabela: str | None = None) -> dict:
    """Tipos, nulidade, domínio e unicidade de grão via schema pandera."""
    from . import schemas  # import tardio: permite testar checks sem pandera

    tabela = tabela or name
    ok, failures = schemas.validate_table(name, df)
    n = 0 if ok else len(failures)
    desc = "schema pandera válido (tipos, nulidade, domínio, unicidade)"
    if not ok:
        top = failures["check"].value_counts().head(3).to_dict()
        desc = f"{n} casos de falha no schema; principais checks violados: {top}"
    return make_record(
        tabela, "tipos_e_schema", _status_if_present(n, "FAIL"), n, len(df),
        "critica" if n else "info", desc,
        "tipo/domínio errado corrompe silenciosamente todas as métricas",
        "investigar failure_cases do pandera" if n else "nenhuma",
    )


def check_duplicate_grain(df: pd.DataFrame, grain: list[str], tabela: str) -> dict:
    """Duplicidade no grão esperado (chave primária/composta)."""
    n = int(df.duplicated(subset=grain).sum())
    return make_record(
        tabela, "duplicidade_grao", _status_if_present(n, "FAIL"), n, len(df),
        "critica" if n else "info",
        f"grão {grain}: {n} duplicatas em {len(df)} linhas",
        "duplicidade no grão infla receita, quantidades e rankings",
        "deduplicar com regra explícita e reprocessar" if n else "nenhuma",
    )


# ---------------------------------------------------------------------------
# Datas
# ---------------------------------------------------------------------------
def check_valid_dates(df: pd.DataFrame, col: str, tabela: str) -> dict:
    """Datas inválidas (NaT) na coluna."""
    n = int(df[col].isna().sum())
    return make_record(
        tabela, f"datas_validas_{col}", _status_if_present(n, "FAIL"), n, len(df),
        "alta" if n else "info",
        f"{col}: {n} datas inválidas/nulas",
        "linhas sem data não entram em séries temporais e somem de agregações mensais",
        "investigar origem das datas inválidas" if n else "nenhuma",
    )


def check_dates_in_period(
    df: pd.DataFrame, col: str, tabela: str,
    start: pd.Timestamp, end: pd.Timestamp,
) -> dict:
    """Datas fora do período contratado (jan/2024–dez/2025)."""
    s = df[col].dropna()
    n = int(((s < start) | (s > end)).sum())
    return make_record(
        tabela, f"datas_no_periodo_{col}", _status_if_present(n, "WARN"), n, len(df),
        "media" if n else "info",
        f"{col}: {n} datas fora de {start.date()}–{end.date()}",
        "datas fora do período distorcem comparações YoY e sazonalidade",
        "filtrar/investigar datas fora do período" if n else "nenhuma",
    )


# ---------------------------------------------------------------------------
# Nulos
# ---------------------------------------------------------------------------
def check_critical_nulls(
    df: pd.DataFrame, col: str, tabela: str,
    status_if_present: str, severidade: str,
    impacto: str, acao: str,
) -> dict:
    """Nulos em coluna crítica; criticidade é decisão de contrato do chamador."""
    n = int(df[col].isna().sum())
    return make_record(
        tabela, f"nulos_criticos_{col}", _status_if_present(n, status_if_present),
        n, len(df), severidade if n else "info",
        f"{col}: {n} nulos",
        impacto, acao if n else "nenhuma",
    )


def check_structural_nulls(df: pd.DataFrame, col: str, tabela: str, motivo: str) -> dict:
    """Nulos estruturais (esperados pelo contrato) — medidos, nunca preenchidos."""
    n = int(df[col].isna().sum())
    return make_record(
        tabela, f"nulos_estruturais_{col}", "PASS", n, len(df), "info",
        f"{col}: {n} nulos estruturais ({motivo})",
        "nulo estrutural não é erro; preenchê-lo com 0 criaria dado falso",
        "nenhuma",
    )


# ---------------------------------------------------------------------------
# Integridade referencial
# ---------------------------------------------------------------------------
def check_orphans(
    df: pd.DataFrame, col: str, dim: pd.DataFrame, dim_col: str,
    tabela: str, dim_nome: str,
) -> dict:
    """Valores de FK sem correspondência na dimensão."""
    valid = set(dim[dim_col].dropna())
    n = int((~df[col].isin(valid)).sum())
    return make_record(
        tabela, f"orfaos_{col}_vs_{dim_nome}", _status_if_present(n, "FAIL"),
        n, len(df), "critica" if n else "info",
        f"{col}: {n} valores sem correspondência em {dim_nome}.{dim_col}",
        "órfãos somem em joins internos e inflam/deflacionam métricas por dimensão",
        "reconciliar cadastro ou documentar exclusão explícita" if n else "nenhuma",
    )


# ---------------------------------------------------------------------------
# Valores (quantidades e preços)
# ---------------------------------------------------------------------------
def check_negative_values(df: pd.DataFrame, col: str, tabela: str, impacto: str) -> dict:
    s = df[col]
    n = int((s < 0).sum())
    return make_record(
        tabela, f"negativos_{col}", _status_if_present(n, "FAIL"), n, len(df),
        "critica" if n else "info",
        f"{col}: {n} valores negativos", impacto,
        "investigar sinal na origem (estorno? erro de extração?)" if n else "nenhuma",
    )


def check_zero_values(
    df: pd.DataFrame, col: str, tabela: str,
    status_if_present: str, severidade: str, impacto: str, acao: str,
) -> dict:
    """Zeros onde zero exige justificativa; a criticidade é decisão de contrato."""
    s = df[col]
    n = int((s == 0).sum())
    return make_record(
        tabela, f"zeros_{col}", _status_if_present(n, status_if_present), n, len(df),
        severidade if n else "info",
        f"{col}: {n} valores exatamente zero", impacto,
        acao if n else "nenhuma",
    )


def check_revenue_consistency(df: pd.DataFrame, tabela: str, tol: float = 0.01) -> dict:
    """RECEITA == QUANTIDADE_VENDIDA × PRECO_UNIT_MEDIO (tolerância em R$)."""
    diff = (df["RECEITA"] - df["QUANTIDADE_VENDIDA"] * df["PRECO_UNIT_MEDIO"]).abs()
    n = int((diff > tol).sum())
    return make_record(
        tabela, "receita_consistente", _status_if_present(n, "FAIL"), n, len(df),
        "critica" if n else "info",
        f"RECEITA difere de QUANTIDADE x PRECO em {n} linhas (tol {tol})",
        "receita inconsistente invalida todos os rankings e diagnósticos de venda",
        "reprocessar a coluna RECEITA" if n else "nenhuma",
    )


# ---------------------------------------------------------------------------
# Completude temporal
# ---------------------------------------------------------------------------
def check_months_without(
    df: pd.DataFrame, date_col: str, tabela: str,
    start: str, end: str, evento: str,
) -> dict:
    """Meses do período sem nenhum registro (venda/compra)."""
    expected = pd.period_range(start, end, freq="M")
    present = set(df[date_col].dropna().dt.to_period("M"))
    missing = [str(m) for m in expected if m not in present]
    n = len(missing)
    return make_record(
        tabela, f"meses_sem_{evento}", _status_if_present(n, "WARN"), n, len(expected),
        "alta" if n else "info",
        f"meses sem {evento}: {missing if missing else 'nenhum'} (de {len(expected)} meses)",
        f"mês sem {evento} quebra séries mensais e comparações YoY",
        "verificar extração do período faltante" if n else "nenhuma",
    )


# ---------------------------------------------------------------------------
# Cobertura da base de compras (FAIL: invalida conclusão causal do relatório)
# ---------------------------------------------------------------------------
def check_purchase_coverage_stores(
    compras: pd.DataFrame, lojas: pd.DataFrame,
) -> dict:
    """Lojas sem nenhuma compra registrada no período inteiro."""
    com_compra = set(compras["COD_EMPRESA"].dropna())
    todas = set(lojas["COD_EMPRESA"].dropna())
    sem = sorted(int(x) for x in todas - com_compra)
    n = len(sem)
    return make_record(
        "fato_compras", "cobertura_compras_lojas", _status_if_present(n, "FAIL"),
        n, len(todas), "critica" if n else "info",
        f"{n} de {len(todas)} lojas sem NENHUMA compra em 24 meses: {sem}",
        "base de compras estruturalmente incompleta: qualquer conclusão causal "
        "'compras caíram → vendas caíram' fica não comprovável",
        "obter extração completa de entradas (compras, transferências, ajustes)" if n else "nenhuma",
    )


def check_purchase_coverage_products(
    compras: pd.DataFrame, produtos: pd.DataFrame,
) -> dict:
    """Produtos do cadastro sem nenhuma compra registrada no período inteiro."""
    com_compra = compras["CODIGO"].nunique()
    total = produtos["CODIGO"].nunique()
    n = total - com_compra
    return make_record(
        "fato_compras", "cobertura_compras_produtos", _status_if_present(n, "FAIL"),
        n, total, "critica" if n else "info",
        f"{n} de {total} produtos sem nenhuma compra registrada ({com_compra} com compra)",
        "1.393 registros para 2.731 produtos x 11 lojas x 24 meses é implausível como "
        "universo de reposição; conclusões de ruptura/reposição não são comprováveis",
        "obter universo completo de entradas antes de qualquer diagnóstico causal" if n else "nenhuma",
    )


# ---------------------------------------------------------------------------
# Reconciliação vendas × entradas conhecidas (medição; correção é Spec 04)
# ---------------------------------------------------------------------------
def _inflows_by_product_store(
    vendas: pd.DataFrame, estoque: pd.DataFrame,
    compras: pd.DataFrame, produtos: pd.DataFrame,
) -> pd.DataFrame:
    """Agrega, por produto × loja, venda/estoque/compra em unidade de armazenagem.

    Compras convertidas via CONVERSAO_COMPRA_ARMAZENAGEM (dicionário oficial:
    QUANTIDADE_COMPRA está em embalagem de compra). Medição apenas — nenhum
    dado de origem é alterado.
    """
    v = vendas[["CODIGO", "COD_EMPRESA"]].copy()
    v["QTD_VENDA_ESTQ"] = vendas["QUANTIDADE_VENDIDA"] * vendas["CONVERSAO_VENDA_PARA_ARMAZENAGEM"]
    v = v.groupby(["CODIGO", "COD_EMPRESA"], as_index=False)["QTD_VENDA_ESTQ"].sum()

    e = estoque.groupby(["CODIGO", "COD_EMPRESA"], as_index=False)["ESTOQUE_INICIAL"].sum()

    c = compras.merge(
        produtos[["CODIGO", "CONVERSAO_COMPRA_ARMAZENAGEM"]], on="CODIGO", how="left"
    )
    c["QTD_COMPRA_ESTQ"] = c["QUANTIDADE_COMPRA"] * c["CONVERSAO_COMPRA_ARMAZENAGEM"]
    c = c.groupby(["CODIGO", "COD_EMPRESA"], as_index=False)["QTD_COMPRA_ESTQ"].sum()

    m = v.merge(e, on=["CODIGO", "COD_EMPRESA"], how="left").merge(
        c, on=["CODIGO", "COD_EMPRESA"], how="left"
    )
    # fillna(0) apenas na MEDIÇÃO agregada (par sem registro = 0 entradas
    # conhecidas); os dados de origem permanecem intocados
    m["ESTOQUE_INICIAL"] = m["ESTOQUE_INICIAL"].fillna(0)
    m["QTD_COMPRA_ESTQ"] = m["QTD_COMPRA_ESTQ"].fillna(0)
    return m


def check_sold_without_inflows(
    vendas: pd.DataFrame, estoque: pd.DataFrame,
    compras: pd.DataFrame, produtos: pd.DataFrame,
) -> dict:
    """Pares produto×loja vendidos sem estoque inicial e sem compra registrada."""
    m = _inflows_by_product_store(vendas, estoque, compras, produtos)
    n = int(((m["ESTOQUE_INICIAL"] <= 0) & (m["QTD_COMPRA_ESTQ"] <= 0)).sum())
    return make_record(
        "fato_vendas", "vendidos_sem_estoque_inicial_nem_compras",
        _status_if_present(n, "FAIL"), n, len(m), "critica" if n else "info",
        f"{n} de {len(m)} pares produto x loja com venda, mas estoque inicial 0 "
        "e nenhuma compra registrada",
        "vender sem entrada conhecida prova que as entradas do período não estão "
        "todas na base; saldo projetado e 'rupturas' derivadas não são confiáveis",
        "obter entradas completas; até lá, tratar saldo negativo como gap contábil" if n else "nenhuma",
    )


def check_sales_exceed_inflows(
    vendas: pd.DataFrame, estoque: pd.DataFrame,
    compras: pd.DataFrame, produtos: pd.DataFrame,
) -> dict:
    """Pares produto×loja com venda acumulada > estoque inicial + compras (unid. armazenagem)."""
    m = _inflows_by_product_store(vendas, estoque, compras, produtos)
    n = int((m["QTD_VENDA_ESTQ"] > m["ESTOQUE_INICIAL"] + m["QTD_COMPRA_ESTQ"]).sum())
    tot_v = m["QTD_VENDA_ESTQ"].sum()
    tot_in = (m["ESTOQUE_INICIAL"] + m["QTD_COMPRA_ESTQ"]).sum()
    return make_record(
        "fato_vendas", "venda_maior_que_entradas_conhecidas",
        _status_if_present(n, "FAIL"), n, len(m), "critica" if n else "info",
        f"{n} de {len(m)} pares produto x loja com venda > estoque inicial + compras; "
        f"totais em unid. armazenagem: vendido {tot_v:,.0f} vs entradas {tot_in:,.0f}",
        "gap contábil generalizado: a base não fecha o balanço de estoque; qualquer "
        "conclusão de ruptura física ou de queda de reposição é não comprovável",
        "tratar como gap contábil (Spec 04); nunca reportar como ruptura física" if n else "nenhuma",
    )


# ---------------------------------------------------------------------------
# Consistência de unidades (venda / compra / armazenagem)
# ---------------------------------------------------------------------------
def check_sale_unit_consistency(vendas: pd.DataFrame, produtos: pd.DataFrame) -> dict:
    """Vendas cuja UNIDADE_DA_VENDA difere da UNIDADE_ESTOQUE do produto com conversão = 1."""
    m = vendas.merge(produtos[["CODIGO", "UNIDADE_ESTOQUE"]], on="CODIGO", how="left")
    difere = m["UNIDADE_DA_VENDA"] != m["UNIDADE_ESTOQUE"]
    suspeito = difere & (m["CONVERSAO_VENDA_PARA_ARMAZENAGEM"] == 1)
    n = int(suspeito.sum())
    return make_record(
        "fato_vendas", "unidade_venda_difere_armazenagem_sem_conversao",
        _status_if_present(n, "WARN"), n, len(m), "media" if n else "info",
        f"{int(difere.sum())} linhas com unidade de venda != unidade de estoque; "
        f"destas, {n} com conversão = 1 (possível conversão faltante)",
        "se a conversão estiver errada, quantidades em unidade de armazenagem "
        "ficam distorcidas para esses itens",
        "validar fator de conversão desses SKUs com o negócio" if n else "nenhuma",
    )


def check_purchase_unit_difference(produtos: pd.DataFrame) -> dict:
    """Produtos cuja embalagem de compra difere da unidade de armazenagem (conversão ≠ 1)."""
    n = int((produtos["CONVERSAO_COMPRA_ARMAZENAGEM"] != 1).sum())
    return make_record(
        "dim_produto", "unidade_compra_difere_armazenagem",
        _status_if_present(n, "WARN"), n, len(produtos), "media" if n else "info",
        f"{n} produtos com CONVERSAO_COMPRA_ARMAZENAGEM != 1 (embalagem de compra "
        "difere da unidade de estoque)",
        "somar QUANTIDADE_COMPRA crua para esses produtos mistura unidades "
        "(erro latente do 02_estoque_projetado.py — correção é escopo da Spec 04)",
        "aplicar conversão de compra em qualquer soma de entradas (Spec 04)" if n else "nenhuma",
    )


def check_purchases_needing_conversion(compras: pd.DataFrame, produtos: pd.DataFrame) -> dict:
    """Linhas de compra existentes cujo produto tem conversão de compra ≠ 1."""
    m = compras.merge(
        produtos[["CODIGO", "CONVERSAO_COMPRA_ARMAZENAGEM"]], on="CODIGO", how="left"
    )
    n = int((m["CONVERSAO_COMPRA_ARMAZENAGEM"] != 1).sum())
    return make_record(
        "fato_compras", "compras_com_conversao_diferente_de_1",
        _status_if_present(n, "WARN"), n, len(m), "alta" if n else "info",
        f"{n} de {len(m)} linhas de compra são de produtos com conversão != 1",
        "quando 0, o erro de unidade do estoque projetado não se materializa no dado "
        "atual, mas o risco é latente para novas extrações",
        "aplicar conversão antes de somar (Spec 04)" if n else "nenhuma",
    )


# ---------------------------------------------------------------------------
# Consistências auxiliares de domínio
# ---------------------------------------------------------------------------
def check_digito_consistency(vendas: pd.DataFrame, produtos: pd.DataFrame) -> dict:
    """DIGITO da venda bate com o dígito verificador do cadastro do produto."""
    m = vendas[["CODIGO", "DIGITO"]].merge(
        produtos[["CODIGO", "DIGITO"]], on="CODIGO", how="left", suffixes=("", "_dim")
    )
    n = int((m["DIGITO"] != m["DIGITO_dim"]).sum())
    return make_record(
        "fato_vendas", "digito_consistente_com_dim_produto",
        _status_if_present(n, "WARN"), n, len(m), "media" if n else "info",
        f"{n} linhas de venda com DIGITO divergente do cadastro",
        "dígito divergente sugere código de produto corrompido na extração",
        "auditar códigos divergentes" if n else "nenhuma",
    )


def check_voltagem_domain(produtos: pd.DataFrame, voltagem: pd.DataFrame) -> dict:
    """CD_VOLTAGEM do produto pertence ao domínio de dim_voltagem ∪ {0} (0 = sem voltagem)."""
    dominio = set(voltagem["CD_VOLTAGEM"].dropna()) | {0}
    s = produtos["CD_VOLTAGEM"].dropna()
    n = int((~s.isin(dominio)).sum())
    return make_record(
        "dim_produto", "dominio_cd_voltagem",
        _status_if_present(n, "WARN"), n, len(produtos), "media" if n else "info",
        f"{n} produtos com CD_VOLTAGEM fora do domínio (dim_voltagem + 0='sem voltagem'); "
        f"{int(produtos['CD_VOLTAGEM'].isna().sum())} nulos avaliados em check próprio",
        "voltagem fora do domínio quebra filtros e cruzamentos por voltagem",
        "reconciliar cadastro de voltagem" if n else "nenhuma",
    )


# ---------------------------------------------------------------------------
# Processadas: saldo/estoque projetado (medição do sintoma; leitura correta
# é "gap contábil", não ruptura — linguagem é escopo das Specs 04/07)
# ---------------------------------------------------------------------------
def check_negative_balance(df: pd.DataFrame, col: str, tabela: str) -> dict:
    """Linhas com saldo/estoque projetado negativo (gap contábil, não ruptura)."""
    n = int((df[col] < 0).sum())
    return make_record(
        tabela, f"saldo_negativo_{col}", _status_if_present(n, "FAIL"), n, len(df),
        "critica" if n else "info",
        f"{col}: {n} de {len(df)} linhas negativas",
        "com cobertura de compras incompleta e unidade de compra não convertida, "
        "saldo negativo é GAP CONTÁBIL; o relatório atual o interpreta como ruptura — "
        "conclusão invalidada",
        "renomear/reinterpretar como gap contábil e refazer o saldo na Spec 04" if n else "nenhuma",
    )
