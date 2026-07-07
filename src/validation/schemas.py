# -*- coding: utf-8 -*-
"""schemas.py — Spec 02: schemas pandera das tabelas brutas e processadas.

Contrato legível: docs/data_contract.md (mesma fonte de verdade; divergência
entre este módulo e o contrato é bug).

Decisão de dependência (Spec 02, 2026-07-07): pandera==0.32.1 instalado e
testado com pandas 3.0.3 / numpy 2.5.1 / Python 3.14.6 — versão congelada
em requirements.txt. Import via `pandera.pandas` (API >= 0.32).

Convenções de dtype (o que src/io.py realmente produz — validado):
- códigos: Int64 (nullable);
- numéricos decimal-US (fatos vendas/compras): float64;
- numéricos decimal-BR (estoque, conversões, preços de tabela): Float64;
- datas: datetime64 (resolução não fixada — checada por kind, não por unidade);
- texto: dtype não fixado (str/object variam entre versões do pandas) —
  nulidade e domínio são checados, o dtype físico não.

Os schemas validam; NUNCA transformam (coerce=False em tudo).
"""

import pandas as pd
import pandera as pa
import pandera.pandas as pap

# ---------------------------------------------------------------------------
# Grão / chaves esperadas (validadas empiricamente em 2026-07-07 — ver
# docs/data_contract.md, seção "Unicidade validada"). Usadas pelos schemas
# (unique=) e reutilizadas pelos quality checks.
# ---------------------------------------------------------------------------
EXPECTED_GRAIN: dict[str, list[str]] = {
    "dim_produto": ["CODIGO"],
    "dim_lojas": ["COD_EMPRESA"],
    "dim_precos": ["CODIGO", "COD_EMPRESA"],
    "dim_voltagem": ["CD_VOLTAGEM", "CD_EMPRESA"],
    "dim_unidades": ["COD_UNIDADE"],
    "fato_vendas": ["CODIGO", "COD_EMPRESA", "DATA_VENDA", "EMBALAGEM"],
    "fato_compras": ["CODIGO", "COD_EMPRESA", "DATA_ENTRADA", "EMBALAGEM_FORNECEDOR"],
    "fato_estoque_inicial": ["CODIGO", "COD_EMPRESA"],
}

# Período coberto pelos dados (validado na Spec 01: 100% das datas dentro)
PERIOD_START = pd.Timestamp("2024-01-01")
PERIOD_END = pd.Timestamp("2025-12-31")


def _is_datetime(series: pd.Series) -> bool:
    """Check de dtype datetime independente da resolução (ns/us)."""
    return pd.api.types.is_datetime64_any_dtype(series)


def _date_col(nullable: bool = False) -> pap.Column:
    return pap.Column(
        dtype=None,
        nullable=nullable,
        checks=[
            pa.Check(_is_datetime, element_wise=False, error="coluna deve ser datetime"),
            pa.Check(
                lambda s: s.dropna().between(PERIOD_START, PERIOD_END).all(),
                element_wise=False,
                error=f"datas fora de {PERIOD_START.date()}–{PERIOD_END.date()}",
            ),
        ],
    )


def _code_col(nullable: bool = False, ge: int = 0) -> pap.Column:
    return pap.Column("Int64", nullable=nullable, checks=pa.Check.ge(ge))


def _text_col(nullable: bool = False) -> pap.Column:
    return pap.Column(dtype=None, nullable=nullable)


# ---------------------------------------------------------------------------
# Tabelas BRUTAS (pós-parsing do src/io.py)
# ---------------------------------------------------------------------------
dim_produto_schema = pap.DataFrameSchema(
    columns={
        "CODIGO": _code_col(ge=1),
        # DIGITO é dígito verificador (dicionário oficial) — NÃO é parte da chave
        "DIGITO": _code_col(),
        "DESCRICAO": _text_col(),
        "NIVEL_1": _text_col(),
        "NIVEL_2": _text_col(),
        "NIVEL_3": _text_col(),
        "EMBALAGEM_FORNECEDOR": _text_col(nullable=True),  # 59 nulos reais no bruto
        "EMBALAGEM_COMPRA": _text_col(),
        "CONVERSAO_COMPRA_ARMAZENAGEM": pap.Column("Float64", checks=pa.Check.gt(0)),
        "UNIDADE_ESTOQUE": _text_col(),
        "EMBALAGEM_VENDA_0": _text_col(),
        "EMBALAGEM_VENDA_1": _text_col(nullable=True),  # ~2/3 nulos (estrutural)
        "EMBALAGEM_VENDA_2": _text_col(nullable=True),  # ~2/3 nulos (estrutural)
        # Contrato: 0 = "sem voltagem" (dicionário); VAZIO = dado faltante (48
        # casos) — vazio NÃO é equiparado a 0 (decisão documentada no contrato)
        "CD_VOLTAGEM": _code_col(nullable=True),
    },
    unique=EXPECTED_GRAIN["dim_produto"],
    strict=True,
    coerce=False,
    name="dim_produto",
)

dim_lojas_schema = pap.DataFrameSchema(
    columns={
        "COD_EMPRESA": _code_col(ge=1),
        "CD_CIDADE": _text_col(),
        "CD_ESTADO": _text_col(),
    },
    unique=EXPECTED_GRAIN["dim_lojas"],
    strict=True,
    coerce=False,
    name="dim_lojas",
)

dim_precos_schema = pap.DataFrameSchema(
    columns={
        "CODIGO": _code_col(ge=1),
        "COD_EMPRESA": _code_col(ge=1),
        "CATEGORIA": _text_col(),
        "PRECO_EMBALAGEM_0": pap.Column("Float64", checks=pa.Check.gt(0)),
        "PERC_DESCTO_ADICIONAL_EMBALAGEM_0": pap.Column("Float64", checks=pa.Check.ge(0)),
        # preços 1/2 são estruturais (embalagem especial pode não existir);
        # zeros existem no dado real (364/600) e são medidos como WARN no
        # quality report — o schema aceita ge(0) para não mascarar a medição
        "PRECO_EMBALAGEM_1": pap.Column("Float64", nullable=True, checks=pa.Check.ge(0)),
        "PRECO_EMBALAGEM_2": pap.Column("Float64", nullable=True, checks=pa.Check.ge(0)),
    },
    unique=EXPECTED_GRAIN["dim_precos"],
    strict=True,
    coerce=False,
    name="dim_precos",
)

dim_voltagem_schema = pap.DataFrameSchema(
    columns={
        "CD_VOLTAGEM": _code_col(),
        # nomenclatura divergente das demais tabelas (CD_ vs COD_) — herdada da origem
        "CD_EMPRESA": _code_col(ge=1),
    },
    unique=EXPECTED_GRAIN["dim_voltagem"],
    strict=True,
    coerce=False,
    name="dim_voltagem",
)

dim_unidades_schema = pap.DataFrameSchema(
    columns={
        "COD_UNIDADE": _text_col(),  # alfanumérico ("PC", "KG") — sempre string
        "DESCRICAO": _text_col(),
        "COD_IBGE": _text_col(nullable=True),  # 1 nulo real (linha "EB")
    },
    unique=EXPECTED_GRAIN["dim_unidades"],
    strict=True,
    coerce=False,
    name="dim_unidades",
)

fato_vendas_schema = pap.DataFrameSchema(
    columns={
        "DATA_VENDA": _date_col(),
        "COD_EMPRESA": _code_col(ge=1),
        "CODIGO": _code_col(ge=1),
        "DIGITO": _code_col(),
        # dicionário: 0 = padrão, 1 e 2 = preço especial (no dado real só há 0 e 1)
        "EMBALAGEM": pap.Column("Int64", checks=pa.Check.isin([0, 1, 2])),
        "QUANTIDADE_VENDIDA": pap.Column(float, checks=pa.Check.gt(0)),
        "CONVERSAO_VENDA_PARA_ARMAZENAGEM": pap.Column(float, checks=pa.Check.gt(0)),
        "UNIDADE_DA_VENDA": _text_col(),
        # PRECO_UNIT_MEDIO é média DIÁRIA (dicionário) → grão diário, sem ID de transação
        "PRECO_UNIT_MEDIO": pap.Column(float, checks=pa.Check.gt(0)),
    },
    unique=EXPECTED_GRAIN["fato_vendas"],
    strict=True,
    coerce=False,
    name="fato_vendas",
)

fato_compras_schema = pap.DataFrameSchema(
    columns={
        "DATA_ENTRADA": _date_col(),
        "COD_EMPRESA": _code_col(ge=1),
        "CODIGO": _code_col(ge=1),
        "EMBALAGEM_FORNECEDOR": _text_col(nullable=True),  # 1 nulo real
        # ATENÇÃO (dicionário oficial): quantidade em EMBALAGEM DE COMPRA do
        # fornecedor — exige CONVERSAO_COMPRA_ARMAZENAGEM para unidade de estoque
        "QUANTIDADE_COMPRA": pap.Column(float, checks=pa.Check.gt(0)),
        "UNIDADE_ESTOQUE": _text_col(),
        # 132 nulos reais (9,5%) — nulo CRÍTICO medido como FAIL no quality
        # report; o schema aceita nullable para refletir o dado real e não
        # bloquear a medição (contrato: não pode entrar em custo sem regra)
        "PRECO_UNIT_UNIDADE_COMPRA": pap.Column(float, nullable=True, checks=pa.Check.gt(0)),
    },
    unique=EXPECTED_GRAIN["fato_compras"],
    strict=True,
    coerce=False,
    name="fato_compras",
)

fato_estoque_inicial_schema = pap.DataFrameSchema(
    columns={
        "COD_EMPRESA": _code_col(ge=1),
        "CODIGO": _code_col(ge=1),
        # zeros são 47,6% — explícitos na origem; contrato: zero explícito ≠ nulo
        "ESTOQUE_INICIAL": pap.Column("Float64", checks=pa.Check.ge(0)),
    },
    unique=EXPECTED_GRAIN["fato_estoque_inicial"],
    strict=True,
    coerce=False,
    name="fato_estoque_inicial",
)

# ---------------------------------------------------------------------------
# Tabelas PROCESSADAS principais (data/processed/*.parquet, geradas pelo
# pipeline legado — schemas descrevem o que existe, sem endossar o cálculo;
# a correção de unidades do estoque projetado é escopo da Spec 04)
# ---------------------------------------------------------------------------
fato_vendas_processed_schema = pap.DataFrameSchema(
    columns={
        **fato_vendas_schema.columns,
        "RECEITA": pap.Column(float, checks=pa.Check.ge(0)),
        "QTD_VENDA_ESTOQUE": pap.Column(float, checks=pa.Check.gt(0)),
    },
    checks=[
        pa.Check(
            lambda df: ((df["RECEITA"] - df["QUANTIDADE_VENDIDA"] * df["PRECO_UNIT_MEDIO"]).abs() <= 0.01),
            error="RECEITA != QUANTIDADE_VENDIDA x PRECO_UNIT_MEDIO (tol 0,01)",
        ),
        pa.Check(
            lambda df: (
                (df["QTD_VENDA_ESTOQUE"] - df["QUANTIDADE_VENDIDA"] * df["CONVERSAO_VENDA_PARA_ARMAZENAGEM"]).abs()
                <= 1e-9
            ),
            error="QTD_VENDA_ESTOQUE != QUANTIDADE_VENDIDA x CONVERSAO_VENDA_PARA_ARMAZENAGEM",
        ),
    ],
    unique=EXPECTED_GRAIN["fato_vendas"],
    strict=True,
    coerce=False,
    name="fato_vendas_processed",
)

estoque_diario_schema = pap.DataFrameSchema(
    columns={
        "COD_EMPRESA": _code_col(ge=1),
        "CODIGO": _code_col(ge=1),
        "DATA": _date_col(),
        "QTD_COMPRA": pap.Column(float, checks=pa.Check.ge(0)),
        "QTD_VENDA": pap.Column(float, checks=pa.Check.ge(0)),
        "VARIACAO": pap.Column(float),
        # SALDO_ESTOQUE pode ser negativo: é GAP CONTÁBIL (base de compras
        # incompleta + unidade de compra não convertida), NÃO ruptura física
        "SALDO_ESTOQUE": pap.Column(float),
    },
    strict=True,
    coerce=False,
    name="estoque_diario",
)

estoque_final_projetado_schema = pap.DataFrameSchema(
    columns={
        "COD_EMPRESA": _code_col(ge=1),
        "CODIGO": _code_col(ge=1),
        "DATA_ULTIMO_EVENTO": _date_col(),
        "ESTOQUE_FINAL_PROJETADO": pap.Column(float),  # negativo = gap contábil
    },
    strict=True,
    coerce=False,
    name="estoque_final_projetado",
)

cobertura_estoque_schema = pap.DataFrameSchema(
    columns={
        "COD_EMPRESA": _code_col(ge=1),
        "CODIGO": _code_col(ge=1),
        "ESTOQUE_INICIAL": pap.Column(float, checks=pa.Check.ge(0)),
        "QTD_VENDIDA_TOTAL": pap.Column(float, checks=pa.Check.ge(0)),
        "VENDA_MEDIA_DIARIA": pap.Column(float, checks=pa.Check.ge(0)),
        "DIAS_COBERTURA_ESTOQUE_INICIAL": pap.Column(float, nullable=True),
        "DESCRICAO": _text_col(nullable=True),
        "NIVEL_1": _text_col(nullable=True),
        "CD_CIDADE": _text_col(nullable=True),
        "CD_ESTADO": _text_col(nullable=True),
    },
    unique=["CODIGO", "COD_EMPRESA"],
    strict=True,
    coerce=False,
    name="cobertura_estoque",
)

RAW_SCHEMAS: dict[str, pap.DataFrameSchema] = {
    "dim_produto": dim_produto_schema,
    "dim_lojas": dim_lojas_schema,
    "dim_precos": dim_precos_schema,
    "dim_voltagem": dim_voltagem_schema,
    "dim_unidades": dim_unidades_schema,
    "fato_vendas": fato_vendas_schema,
    "fato_compras": fato_compras_schema,
    "fato_estoque_inicial": fato_estoque_inicial_schema,
}

PROCESSED_SCHEMAS: dict[str, pap.DataFrameSchema] = {
    "fato_vendas_processed": fato_vendas_processed_schema,
    "estoque_diario": estoque_diario_schema,
    "estoque_final_projetado": estoque_final_projetado_schema,
    "cobertura_estoque": cobertura_estoque_schema,
}

ALL_SCHEMAS: dict[str, pap.DataFrameSchema] = {**RAW_SCHEMAS, **PROCESSED_SCHEMAS}


def validate_table(name: str, df: pd.DataFrame) -> tuple[bool, pd.DataFrame | None]:
    """Valida `df` contra o schema `name` (lazy: coleta todas as falhas).

    Retorna (ok, failure_cases): failure_cases é None quando válido, ou o
    DataFrame de casos de falha do pandera. NÃO transforma o df de entrada.
    """
    if name not in ALL_SCHEMAS:
        raise KeyError(f"Schema desconhecido: {name!r}. Válidos: {sorted(ALL_SCHEMAS)}")
    try:
        ALL_SCHEMAS[name].validate(df, lazy=True)
        return True, None
    except pa.errors.SchemaErrors as err:
        return False, err.failure_cases
