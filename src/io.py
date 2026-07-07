# -*- coding: utf-8 -*-
"""
io.py — Spec 01: leitura centralizada e auditada das bases brutas.

Este módulo NÃO substitui a leitura inline de 01_etl.py (decisão da Spec 01:
a troca só ocorre mediante prova de reprodução idêntica dos Parquet).
Ele nasce em paralelo e é a fonte de `outputs/tables/ingestion_audit.csv`.

Decisões de parsing documentadas em docs/data_formatting_and_encoding.md.
Fontes: SDD.MD (seção 8), specs/01_ingestion_encoding_spec.md e o dicionário
oficial data/raw/Descritivo_bases_de_dados_2.xlsx (lido em 2026-07-07).

Regras centrais:
- encoding com fallback TESTADO byte a byte (utf-8 -> latin1 -> cp1252);
- separador detectado no cabeçalho e conferido contra o esperado;
- decimal brasileiro (vírgula) convertido de forma explícita e contada;
- datas convertidas com formato explícito (ISO ou BR), nunca inferência mista;
- sentinelas ("", "NA", "N/A", "-", "null", "None", "NULL") viram NA e são contadas;
- códigos só viram Int64 após validar ausência de zeros à esquerda; caso
  existam, permanecem string (nenhuma perda silenciosa);
- NBSP (\xa0) normalizado para espaço e strip nas pontas; espaços internos
  duplicados são PRESERVADOS (nenhuma transformação implícita);
- nenhuma linha é descartada na ingestão (integridade referencial é da Spec 02+).

Uso:
    python src/io.py          # gera outputs/tables/ingestion_audit.csv
    from io.py (via importlib) # ver tests/test_ingestion.py
"""

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

logger = logging.getLogger("ingestao")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _h.setFormatter(logging.Formatter("[%(name)s] %(levelname)s %(message)s"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
AUDIT_PATH = ROOT / "outputs" / "tables" / "ingestion_audit.csv"

# Sentinelas tratadas como nulo (comparação exata, após strip)
SENTINELS = {"", "NA", "N/A", "-", "null", "None", "NULL", "na", "n/a"}

ENCODING_CANDIDATES = ("utf-8", "latin1", "cp1252")
SEPARATOR_CANDIDATES = (";", ",", "\t")

_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?$")
_BR_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_BR_TS_RE = re.compile(r"^\d{2}/\d{2}/\d{4}[ T]\d{2}:\d{2}(:\d{2})?$")
_LEADING_ZERO_RE = re.compile(r"^0\d+$")
_THOUSANDS_BR_RE = re.compile(r"^-?\d{1,3}(\.\d{3})+(,\d+)?$")


class IngestionError(Exception):
    """Erro claro de ingestão (arquivo, motivo)."""


@dataclass
class FileSpec:
    """Especificação de leitura de um arquivo bruto."""

    logical_name: str
    filename: str
    expected_sep: str
    # colunas esperadas conforme dicionário oficial (Descritivo_bases_de_dados_2.xlsx);
    # para dimensao_precos o dicionário NÃO tem aba -> esperadas = observadas (documentado)
    expected_columns: list[str] = field(default_factory=list)
    dict_source: str = "Descritivo_bases_de_dados_2.xlsx"
    code_columns: list[str] = field(default_factory=list)      # ids: Int64 se sem zeros à esquerda
    string_code_columns: list[str] = field(default_factory=list)  # ids alfanuméricos: sempre string
    decimal_br_columns: list[str] = field(default_factory=list)   # vírgula decimal
    decimal_us_columns: list[str] = field(default_factory=list)   # ponto decimal
    monetary_columns: list[str] = field(default_factory=list)     # subconjunto informativo (R$/preço)
    date_columns: list[str] = field(default_factory=list)
    drop_unnamed: bool = True


FILE_SPECS: dict[str, FileSpec] = {
    "fato_vendas": FileSpec(
        logical_name="fato_vendas",
        filename="fato_vendas_1.csv",
        expected_sep=",",
        expected_columns=[
            "DATA_VENDA", "COD_EMPRESA", "CODIGO", "DIGITO", "EMBALAGEM",
            "QUANTIDADE_VENDIDA", "CONVERSAO_VENDA_PARA_ARMAZENAGEM",
            "UNIDADE_DA_VENDA", "PRECO_UNIT_MEDIO",
        ],
        code_columns=["COD_EMPRESA", "CODIGO", "DIGITO", "EMBALAGEM"],
        decimal_us_columns=[
            "QUANTIDADE_VENDIDA", "CONVERSAO_VENDA_PARA_ARMAZENAGEM", "PRECO_UNIT_MEDIO",
        ],
        monetary_columns=["PRECO_UNIT_MEDIO"],
        date_columns=["DATA_VENDA"],
    ),
    "fato_compras": FileSpec(
        logical_name="fato_compras",
        filename="fato_compras_2.csv",
        expected_sep=",",
        expected_columns=[
            "DATA_ENTRADA", "COD_EMPRESA", "CODIGO", "EMBALAGEM_FORNECEDOR",
            "QUANTIDADE_COMPRA", "UNIDADE_ESTOQUE", "PRECO_UNIT_UNIDADE_COMPRA",
        ],
        code_columns=["COD_EMPRESA", "CODIGO"],
        decimal_us_columns=["QUANTIDADE_COMPRA", "PRECO_UNIT_UNIDADE_COMPRA"],
        monetary_columns=["PRECO_UNIT_UNIDADE_COMPRA"],
        date_columns=["DATA_ENTRADA"],
    ),
    "fato_estoque_inicial": FileSpec(
        logical_name="fato_estoque_inicial",
        filename="fato_estoque_inicial_2.csv",
        expected_sep=";",
        expected_columns=["COD_EMPRESA", "CODIGO", "ESTOQUE_INICIAL"],
        code_columns=["COD_EMPRESA", "CODIGO"],
        decimal_br_columns=["ESTOQUE_INICIAL"],
    ),
    "dim_produto": FileSpec(
        logical_name="dim_produto",
        filename="dim_produto_1.csv",
        expected_sep=";",
        expected_columns=[
            "CODIGO", "DIGITO", "DESCRICAO", "NIVEL_1", "NIVEL_2", "NIVEL_3",
            "EMBALAGEM_FORNECEDOR", "EMBALAGEM_COMPRA", "CONVERSAO_COMPRA_ARMAZENAGEM",
            "UNIDADE_ESTOQUE", "EMBALAGEM_VENDA_0", "EMBALAGEM_VENDA_1",
            "EMBALAGEM_VENDA_2", "CD_VOLTAGEM",
        ],
        code_columns=["CODIGO", "DIGITO", "CD_VOLTAGEM"],
        decimal_br_columns=["CONVERSAO_COMPRA_ARMAZENAGEM"],
    ),
    "dim_lojas": FileSpec(
        logical_name="dim_lojas",
        filename="dimensao_lojas_2.csv",
        expected_sep=";",
        expected_columns=["COD_EMPRESA", "CD_CIDADE", "CD_ESTADO"],
        code_columns=["COD_EMPRESA"],
    ),
    "dim_precos": FileSpec(
        logical_name="dim_precos",
        filename="dimensao_precos_2.csv",
        expected_sep=";",
        # DADO AUSENTE: o dicionário oficial não possui aba para dimensao_precos;
        # colunas esperadas vêm da inspeção do próprio arquivo (Spec 00)
        expected_columns=[
            "CODIGO", "COD_EMPRESA", "CATEGORIA", "PRECO_EMBALAGEM_0",
            "PERC_DESCTO_ADICIONAL_EMBALAGEM_0", "PRECO_EMBALAGEM_1", "PRECO_EMBALAGEM_2",
        ],
        dict_source="inspecao_do_arquivo (sem aba no dicionario oficial)",
        code_columns=["CODIGO", "COD_EMPRESA"],
        decimal_br_columns=[
            "PRECO_EMBALAGEM_0", "PERC_DESCTO_ADICIONAL_EMBALAGEM_0",
            "PRECO_EMBALAGEM_1", "PRECO_EMBALAGEM_2",
        ],
        monetary_columns=["PRECO_EMBALAGEM_0", "PRECO_EMBALAGEM_1", "PRECO_EMBALAGEM_2"],
    ),
    "dim_voltagem": FileSpec(
        logical_name="dim_voltagem",
        filename="dimensao_voltagem_2.csv",
        expected_sep=";",
        expected_columns=["CD_VOLTAGEM", "CD_EMPRESA"],
        code_columns=["CD_VOLTAGEM", "CD_EMPRESA"],
    ),
    "dim_unidades": FileSpec(
        logical_name="dim_unidades",
        filename="Descr_unidades_medida_2.csv",
        expected_sep=";",
        expected_columns=["COD_UNIDADE", "DESCRICAO", "COD_IBGE"],
        # COD_UNIDADE é alfanumérico ("PC", "KG"...); COD_IBGE é código externo:
        # ambos permanecem string por decisão explícita (são identificadores)
        string_code_columns=["COD_UNIDADE", "COD_IBGE"],
    ),
}


# ---------------------------------------------------------------------------
# Helpers de detecção
# ---------------------------------------------------------------------------
def detect_encoding(path: Path, candidates=ENCODING_CANDIDATES):
    """Testa candidatos por decodificação estrita dos bytes completos.

    Retorna (encoding_usado, lista_de_testados). latin1 nunca falha por
    construção; cp1252 fica após latin1 porque, nos arquivos deste projeto,
    não há bytes 0x80-0x9F (faixa em que os dois divergem) — verificado e
    documentado em docs/data_formatting_and_encoding.md.
    """
    raw = path.read_bytes()
    tested = []
    for enc in candidates:
        tested.append(enc)
        try:
            raw.decode(enc)
            return enc, tested
        except UnicodeDecodeError as e:
            logger.info(
                "%s: decodificação %s falhou no byte %d (0x%02x)",
                path.name, enc, e.start, raw[e.start],
            )
    raise IngestionError(f"{path.name}: nenhum encoding candidato decodifica o arquivo: {candidates}")


def detect_separator(path: Path, encoding: str, candidates=SEPARATOR_CANDIDATES) -> str:
    """Detecta o separador pela contagem no cabeçalho (1ª linha)."""
    with open(path, encoding=encoding) as f:
        header = f.readline()
    counts = {sep: header.count(sep) for sep in candidates}
    best = max(counts, key=counts.get)
    if counts[best] == 0:
        raise IngestionError(f"{path.name}: nenhum separador candidato encontrado no cabeçalho")
    return best


# ---------------------------------------------------------------------------
# Helpers de parsing (todos explícitos e contáveis)
# ---------------------------------------------------------------------------
def clean_text(series: pd.Series) -> pd.Series:
    """Normaliza NBSP -> espaço e faz strip nas pontas.

    Espaços internos duplicados são preservados (transformação de conteúdo
    é decisão da Spec 02, não da ingestão)."""
    return series.str.replace("\xa0", " ", regex=False).str.strip()


def apply_sentinels(series: pd.Series) -> tuple[pd.Series, int]:
    """Converte sentinelas em NA. Retorna (série, nº de sentinelas convertidas)."""
    stripped = clean_text(series)
    mask = stripped.isin(SENTINELS)
    out = stripped.mask(mask)
    return out, int(mask.sum())


def parse_decimal_br(series: pd.Series) -> tuple[pd.Series, int]:
    """Número brasileiro: milhar '.' (opcional) + decimal ','.

    Só remove pontos quando o padrão de milhar é inequívoco (ex.: 1.234,56);
    caso contrário, apenas troca ',' por '.'. Retorna (float, nº de coerções
    que criaram NA a partir de valor não-nulo)."""
    s = series.astype("string")
    thousands_mask = s.str.match(_THOUSANDS_BR_RE, na=False)
    s = s.mask(thousands_mask, s.str.replace(".", "", regex=False))
    s = s.str.replace(",", ".", regex=False)
    out = pd.to_numeric(s, errors="coerce")
    coerced = int((s.notna() & out.isna()).sum())
    return out, coerced


def parse_decimal_us(series: pd.Series) -> tuple[pd.Series, int]:
    """Número com decimal '.' (convenção dos fatos vendas/compras)."""
    out = pd.to_numeric(series, errors="coerce")
    coerced = int((series.notna() & out.isna()).sum())
    return out, coerced


def parse_currency_brl(series: pd.Series) -> tuple[pd.Series, int]:
    """Moeda com prefixo R$: remove 'R$'/espaços e delega ao decimal BR.

    Nenhuma base bruta atual contém 'R$' (validado em 2026-07-07); helper
    existe e é testado para cumprir a validação obrigatória do SDD.MD."""
    s = series.astype("string").str.replace("R$", "", regex=False).str.strip()
    return parse_decimal_br(s)


def parse_dates(series: pd.Series) -> tuple[pd.Series, int, str]:
    """Converte datas com formato EXPLÍCITO detectado (nunca inferência mista).

    Aceita ISO (com/sem hora) ou BR (com/sem hora). Se houver mistura de
    formatos, falha com erro claro. Retorna (datetime, coerções, formato)."""
    s = series.astype("string").str.strip()
    nonnull = s.dropna()
    fmt_map = {
        "%Y-%m-%d": _ISO_RE,
        "%Y-%m-%d %H:%M:%S": _ISO_TS_RE,
        "%d/%m/%Y": _BR_RE,
        "%d/%m/%Y %H:%M:%S": _BR_TS_RE,
    }
    matches = {fmt: rx.match for fmt, rx in fmt_map.items()}
    chosen = None
    for fmt, rx in fmt_map.items():
        if nonnull.str.match(rx).all() and len(nonnull) > 0:
            chosen = fmt
            break
    if chosen is None:
        formats_found = {
            fmt: int(nonnull.str.match(rx).sum()) for fmt, rx in fmt_map.items()
        }
        raise IngestionError(
            f"Coluna de data com formatos mistos ou desconhecidos: {formats_found}"
        )
    out = pd.to_datetime(s, format=chosen, errors="coerce")
    coerced = int((s.notna() & out.isna()).sum())
    return out, coerced, chosen


def parse_code(series: pd.Series, column: str, filename: str) -> tuple[pd.Series, int, bool]:
    """Código identificador: Int64 SOMENTE se não houver zeros à esquerda.

    Se qualquer valor casar com ^0\\d+$, a coluna permanece string e o fato é
    logado (perda de zeros à esquerda quebraria joins externos).
    Retorna (série, coerções, virou_int)."""
    s = series.astype("string").str.strip()
    has_leading_zero = bool(s.str.match(_LEADING_ZERO_RE, na=False).any())
    if has_leading_zero:
        logger.warning(
            "%s.%s: zeros à esquerda detectados — coluna preservada como string",
            filename, column,
        )
        return s, 0, False
    out = pd.to_numeric(s, errors="coerce").astype("Int64")
    coerced = int((s.notna() & out.isna()).sum())
    return out, coerced, True


# ---------------------------------------------------------------------------
# Leitura principal
# ---------------------------------------------------------------------------
def read_raw(name: str, raw_dir: Path | str | None = None) -> tuple[pd.DataFrame, dict]:
    """Lê uma base bruta pelo nome lógico e retorna (DataFrame, registro de auditoria).

    Nomes válidos: ver FILE_SPECS. Nenhuma linha é descartada aqui.
    """
    if name not in FILE_SPECS:
        raise IngestionError(f"Base desconhecida: {name!r}. Válidas: {sorted(FILE_SPECS)}")
    spec = FILE_SPECS[name]
    raw_dir = Path(raw_dir) if raw_dir is not None else RAW_DIR
    path = raw_dir / spec.filename
    if not path.exists():
        raise IngestionError(f"Arquivo bruto não encontrado: {path}")

    encoding, tested = detect_encoding(path)
    sep = detect_separator(path, encoding)
    if sep != spec.expected_sep:
        logger.warning(
            "%s: separador detectado %r difere do esperado %r", spec.filename, sep, spec.expected_sep
        )

    # dtype=str + na_filter=False: nada é interpretado implicitamente pelo pandas
    df = pd.read_csv(path, sep=sep, encoding=encoding, dtype=str, na_filter=False)
    df.columns = [c.strip() for c in df.columns]
    n_rows_read = len(df)

    unnamed = [c for c in df.columns if c.startswith("Unnamed")]
    if spec.drop_unnamed and unnamed:
        logger.info("%s: descartando coluna(s) de índice sem nome: %s", spec.filename, unnamed)
        df = df.drop(columns=unnamed)

    observed = list(df.columns)
    missing = [c for c in spec.expected_columns if c not in observed]
    extra = [c for c in observed if c not in spec.expected_columns]

    parsing_errors: list[str] = []
    nulls_before_sentinels = 0
    date_cols_converted: list[str] = []
    num_cols_converted: list[str] = []
    date_formats: dict[str, str] = {}
    codes_kept_string: list[str] = []

    # 1) sentinelas + limpeza de texto em TODAS as colunas
    for c in df.columns:
        df[c], n_sent = apply_sentinels(df[c])
        nulls_before_sentinels += n_sent

    # 2) códigos
    for c in spec.code_columns:
        if c not in df.columns:
            continue
        df[c], coerced, became_int = parse_code(df[c], c, spec.filename)
        if not became_int:
            codes_kept_string.append(c)
        if coerced:
            parsing_errors.append(f"{c}: {coerced} valores não numéricos viraram NA")
    # códigos que permanecem string por decisão (alfanuméricos)
    # (já limpos na etapa 1; nada a converter)

    # 3) numéricos
    for c in spec.decimal_br_columns:
        if c not in df.columns:
            continue
        df[c], coerced = parse_decimal_br(df[c])
        num_cols_converted.append(c)
        if coerced:
            parsing_errors.append(f"{c}: {coerced} coerções para NA (decimal BR)")
    for c in spec.decimal_us_columns:
        if c not in df.columns:
            continue
        df[c], coerced = parse_decimal_us(df[c])
        num_cols_converted.append(c)
        if coerced:
            parsing_errors.append(f"{c}: {coerced} coerções para NA (decimal US)")

    # 4) datas
    for c in spec.date_columns:
        if c not in df.columns:
            continue
        try:
            df[c], coerced, fmt = parse_dates(df[c])
            date_cols_converted.append(c)
            date_formats[c] = fmt
            if coerced:
                parsing_errors.append(f"{c}: {coerced} datas inválidas viraram NaT")
        except IngestionError as e:
            parsing_errors.append(str(e))

    nulls_after = int(df.isna().sum().sum())
    # zeros criados por tratamento: nenhuma etapa preenche/gera zeros — validado
    zeros_created = 0
    # nenhuma linha é descartada na ingestão (filtragem referencial é Spec 02+)
    n_discarded = 0

    status = "OK"
    if missing or parsing_errors:
        status = "OK_COM_AVISOS"
    if n_rows_read == 0 or len(missing) == len(spec.expected_columns):
        status = "FALHA"

    audit = {
        "arquivo": spec.filename,
        "nome_logico": spec.logical_name,
        "caminho": str(path),
        "encoding_testado": "|".join(tested),
        "encoding_usado": encoding,
        "separador_detectado": sep,
        "linhas_lidas": n_rows_read,
        "colunas_lidas": len(observed),
        "colunas_esperadas": "|".join(spec.expected_columns),
        "fonte_colunas_esperadas": spec.dict_source,
        "colunas_ausentes": "|".join(missing),
        "colunas_extras": "|".join(extra + unnamed),
        "erros_parsing": "; ".join(parsing_errors),
        "colunas_data_convertidas": "|".join(
            f"{c} ({date_formats[c]})" for c in date_cols_converted
        ),
        "colunas_numericas_convertidas": "|".join(num_cols_converted),
        "colunas_monetarias_convertidas": "|".join(
            c for c in spec.monetary_columns if c in num_cols_converted
        ),
        "codigos_mantidos_string": "|".join(codes_kept_string + spec.string_code_columns),
        "nulos_antes": nulls_before_sentinels,
        "nulos_depois": nulls_after,
        "zeros_criados": zeros_created,
        "registros_descartados": n_discarded,
        "motivo_descartes": "nenhum descarte na ingestão (integridade referencial é escopo da Spec 02)",
        "status_ingestao": status,
    }
    logger.info(
        "%s: %d linhas, encoding=%s, sep=%r, nulos %d->%d, status=%s",
        spec.filename, n_rows_read, encoding, sep,
        nulls_before_sentinels, nulls_after, status,
    )
    return df, audit


AUDIT_COLUMNS = [
    "arquivo", "nome_logico", "caminho", "encoding_testado", "encoding_usado",
    "separador_detectado", "linhas_lidas", "colunas_lidas", "colunas_esperadas",
    "fonte_colunas_esperadas", "colunas_ausentes", "colunas_extras", "erros_parsing",
    "colunas_data_convertidas", "colunas_numericas_convertidas",
    "colunas_monetarias_convertidas", "codigos_mantidos_string",
    "nulos_antes", "nulos_depois", "zeros_criados",
    "registros_descartados", "motivo_descartes", "status_ingestao",
]


def read_all_raw(raw_dir: Path | str | None = None) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Lê as 8 bases brutas e retorna ({nome: df}, DataFrame de auditoria)."""
    frames: dict[str, pd.DataFrame] = {}
    records = []
    for name in FILE_SPECS:
        df, audit = read_raw(name, raw_dir=raw_dir)
        frames[name] = df
        records.append(audit)
    audit_df = pd.DataFrame.from_records(records, columns=AUDIT_COLUMNS)
    return frames, audit_df


def write_ingestion_audit(
    audit_path: Path | str | None = None, raw_dir: Path | str | None = None
) -> Path:
    """Gera outputs/tables/ingestion_audit.csv (1 linha por arquivo bruto)."""
    audit_path = Path(audit_path) if audit_path is not None else AUDIT_PATH
    _, audit_df = read_all_raw(raw_dir=raw_dir)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_df.to_csv(audit_path, index=False, encoding="utf-8")
    logger.info("Auditoria de ingestão gravada em %s", audit_path)
    return audit_path


if __name__ == "__main__":
    write_ingestion_audit()
