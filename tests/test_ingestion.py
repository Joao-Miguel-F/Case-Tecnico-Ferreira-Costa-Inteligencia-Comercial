# -*- coding: utf-8 -*-
"""Testes da Spec 01 — Ingestão, encoding e parsing (SDD.MD seção 8).

O módulo src/io.py é carregado via importlib por caminho de arquivo para não
colidir com o módulo stdlib `io`.
"""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
IO_PATH = ROOT / "src" / "io.py"
RAW_DIR = ROOT / "data" / "raw"
AUDIT_CSV = ROOT / "outputs" / "tables" / "ingestion_audit.csv"

# contagens conhecidas (Spec 00 / specs/01_ingestion_encoding_spec.md)
EXPECTED_ROWS = {
    "fato_vendas": 1_090_390,
    "fato_compras": 1_393,
    "fato_estoque_inicial": 25_330,
    "dim_produto": 2_731,
    "dim_lojas": 11,
    "dim_precos": 28_560,
    "dim_voltagem": 67,
    "dim_unidades": 51,
}

REQUIRED_AUDIT_COLUMNS = [
    "arquivo", "caminho", "encoding_testado", "encoding_usado",
    "separador_detectado", "linhas_lidas", "colunas_lidas", "colunas_esperadas",
    "colunas_ausentes", "colunas_extras", "erros_parsing",
    "colunas_data_convertidas", "colunas_numericas_convertidas",
    "colunas_monetarias_convertidas", "nulos_antes", "nulos_depois",
    "zeros_criados", "registros_descartados", "motivo_descartes",
    "status_ingestao",
]


def _load_io():
    spec = importlib.util.spec_from_file_location("painel_io", IO_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def pio():
    assert IO_PATH.exists(), "src/io.py não existe"
    return _load_io()


@pytest.fixture(scope="session")
def all_frames(pio):
    """Lê as 8 bases reais uma única vez (sessão)."""
    frames, audit = pio.read_all_raw()
    return frames, audit


# ---------------------------------------------------------------------------
# Existência e API
# ---------------------------------------------------------------------------
def test_io_module_exists():
    assert IO_PATH.exists()


def test_main_functions_exist(pio):
    for fn in [
        "read_raw", "read_all_raw", "write_ingestion_audit", "detect_encoding",
        "detect_separator", "parse_decimal_br", "parse_decimal_us",
        "parse_currency_brl", "parse_dates", "parse_code",
    ]:
        assert callable(getattr(pio, fn, None)), f"função ausente: {fn}"


def test_read_raw_nome_invalido_erro_claro(pio):
    with pytest.raises(pio.IngestionError, match="Base desconhecida"):
        pio.read_raw("nao_existe")


# ---------------------------------------------------------------------------
# Leitura das 8 bases reais
# ---------------------------------------------------------------------------
def test_todas_as_bases_lidas_sem_erro(all_frames):
    frames, _ = all_frames
    assert set(frames) == set(EXPECTED_ROWS)
    for name, df in frames.items():
        assert len(df) > 0, f"{name} vazio"


def test_contagens_batem_com_spec00(all_frames):
    frames, _ = all_frames
    for name, expected in EXPECTED_ROWS.items():
        assert len(frames[name]) == expected, (
            f"{name}: {len(frames[name])} linhas != esperado {expected}"
        )


def test_nenhum_registro_descartado_na_ingestao(all_frames):
    _, audit = all_frames
    assert (audit["registros_descartados"] == 0).all()


def test_nenhuma_coercao_criou_nulos_nas_bases_reais(all_frames):
    # nulos_depois == nulos_antes: conversões numéricas/data não perderam valores
    _, audit = all_frames
    assert (audit["nulos_depois"] == audit["nulos_antes"]).all()
    assert (audit["erros_parsing"].fillna("") == "").all()


def test_zeros_criados_zero(all_frames):
    _, audit = all_frames
    assert (audit["zeros_criados"] == 0).all()


def test_datas_convertidas_de_forma_controlada(all_frames):
    frames, audit = all_frames
    vendas = frames["fato_vendas"]
    compras = frames["fato_compras"]
    assert str(vendas["DATA_VENDA"].dtype).startswith("datetime64")
    assert str(compras["DATA_ENTRADA"].dtype).startswith("datetime64")
    assert vendas["DATA_VENDA"].isna().sum() == 0
    assert compras["DATA_ENTRADA"].isna().sum() == 0
    # dentro do período conhecido jan/2024–dez/2025
    assert vendas["DATA_VENDA"].min() >= pd.Timestamp("2024-01-01")
    assert vendas["DATA_VENDA"].max() <= pd.Timestamp("2025-12-31")
    # formato registrado no audit
    row = audit.set_index("nome_logico").loc["fato_vendas"]
    assert "%Y-%m-%d" in row["colunas_data_convertidas"]


def test_decimal_convertido_nas_bases_reais(all_frames):
    frames, _ = all_frames
    for name, col in [
        ("fato_estoque_inicial", "ESTOQUE_INICIAL"),
        ("dim_produto", "CONVERSAO_COMPRA_ARMAZENAGEM"),
        ("dim_precos", "PRECO_EMBALAGEM_0"),
        ("fato_vendas", "PRECO_UNIT_MEDIO"),
    ]:
        assert pd.api.types.is_float_dtype(frames[name][col]), f"{name}.{col} não é float"


def test_codigos_reais_sem_zeros_a_esquerda_viram_int64(all_frames):
    frames, _ = all_frames
    assert frames["fato_vendas"]["CODIGO"].dtype == "Int64"
    assert frames["dim_produto"]["CODIGO"].dtype == "Int64"
    assert frames["dim_lojas"]["COD_EMPRESA"].dtype == "Int64"
    # alfanuméricos permanecem string por decisão explícita
    assert pd.api.types.is_string_dtype(frames["dim_unidades"]["COD_UNIDADE"])


# ---------------------------------------------------------------------------
# Prova de encoding: dim_produto corrompe em utf-8, não corrompe em latin1
# ---------------------------------------------------------------------------
def test_dim_produto_utf8_corrompe_latin1_nao():
    raw = (RAW_DIR / "dim_produto_1.csv").read_bytes()
    with pytest.raises(UnicodeDecodeError):
        raw.decode("utf-8")
    texto = raw.decode("latin1")  # não levanta
    assert "\xa0" in texto  # NBSP presente (byte que quebra o utf-8)
    with pytest.raises(UnicodeDecodeError):
        pd.read_csv(RAW_DIR / "dim_produto_1.csv", sep=";", encoding="utf-8")
    df = pd.read_csv(RAW_DIR / "dim_produto_1.csv", sep=";", encoding="latin1")
    assert len(df) == EXPECTED_ROWS["dim_produto"]


def test_encoding_registrado_no_audit(all_frames):
    _, audit = all_frames
    audit = audit.set_index("nome_logico")
    assert audit.loc["dim_produto", "encoding_usado"] == "latin1"
    assert "utf-8" in audit.loc["dim_produto", "encoding_testado"]
    assert audit.loc["fato_vendas", "encoding_usado"] == "utf-8"


def test_separador_registrado_no_audit(all_frames):
    _, audit = all_frames
    audit = audit.set_index("nome_logico")
    assert audit.loc["fato_vendas", "separador_detectado"] == ","
    assert audit.loc["dim_produto", "separador_detectado"] == ";"


# ---------------------------------------------------------------------------
# Auditoria de ingestão (arquivo gerado)
# ---------------------------------------------------------------------------
def test_ingestion_audit_csv_existe_e_tem_colunas_obrigatorias():
    assert AUDIT_CSV.exists(), "outputs/tables/ingestion_audit.csv não existe"
    audit = pd.read_csv(AUDIT_CSV)
    assert len(audit) == 8, "audit deve ter 1 linha por arquivo bruto"
    faltando = [c for c in REQUIRED_AUDIT_COLUMNS if c not in audit.columns]
    assert not faltando, f"colunas obrigatórias ausentes no audit: {faltando}"
    assert (audit["linhas_lidas"] > 0).all()
    assert audit["status_ingestao"].isin(["OK", "OK_COM_AVISOS", "FALHA"]).all()


def test_write_ingestion_audit_gera_arquivo(pio, tmp_path):
    out = pio.write_ingestion_audit(audit_path=tmp_path / "audit.csv")
    assert out.exists()
    audit = pd.read_csv(out)
    assert len(audit) == 8
    assert list(audit["linhas_lidas"]) == [
        EXPECTED_ROWS[n] for n in audit["nome_logico"]
    ]


# ---------------------------------------------------------------------------
# Zeros à esquerda (fixture sintética — inexistentes nas bases reais)
# ---------------------------------------------------------------------------
def test_parse_code_preserva_zeros_a_esquerda(pio):
    s = pd.Series(["007", "123", "045"])
    out, coerced, became_int = pio.parse_code(s, "CODIGO", "sintetico.csv")
    assert became_int is False
    assert list(out) == ["007", "123", "045"]  # nada perdido
    assert coerced == 0


def test_parse_code_sem_zeros_vira_int64(pio):
    s = pd.Series(["7", "123", "45"])
    out, coerced, became_int = pio.parse_code(s, "CODIGO", "sintetico.csv")
    assert became_int is True
    assert out.dtype == "Int64"
    assert list(out) == [7, 123, 45]


def test_leitura_completa_com_zeros_a_esquerda_sinteticos(pio, tmp_path):
    """End-to-end: arquivo com códigos 0-prefixados fica string e é auditado."""
    csv = tmp_path / "sintetico_zeros.csv"
    csv.write_text(
        "CODIGO;VALOR\n007;1,5\n123;2,0\n", encoding="utf-8"
    )
    spec = pio.FileSpec(
        logical_name="sintetico_zeros",
        filename="sintetico_zeros.csv",
        expected_sep=";",
        expected_columns=["CODIGO", "VALOR"],
        code_columns=["CODIGO"],
        decimal_br_columns=["VALOR"],
    )
    pio.FILE_SPECS["sintetico_zeros"] = spec
    try:
        df, audit = pio.read_raw("sintetico_zeros", raw_dir=tmp_path)
    finally:
        del pio.FILE_SPECS["sintetico_zeros"]
    assert list(df["CODIGO"]) == ["007", "123"]
    assert "CODIGO" in audit["codigos_mantidos_string"]
    assert list(df["VALOR"]) == [1.5, 2.0]


# ---------------------------------------------------------------------------
# Decimal brasileiro / moeda (fixtures sintéticas)
# ---------------------------------------------------------------------------
def test_parse_decimal_br(pio):
    s = pd.Series(["1.234,56", "10,5", "1000", "1,000000", "-2,5"])
    out, coerced = pio.parse_decimal_br(s)
    assert coerced == 0
    assert list(out) == [1234.56, 10.5, 1000.0, 1.0, -2.5]


def test_parse_decimal_br_coercao_contada(pio):
    s = pd.Series(["abc", "10,5"])
    out, coerced = pio.parse_decimal_br(s)
    assert coerced == 1
    assert pd.isna(out.iloc[0]) and out.iloc[1] == 10.5


def test_parse_decimal_us(pio):
    s = pd.Series(["1234.56", "10.5"])
    out, coerced = pio.parse_decimal_us(s)
    assert coerced == 0
    assert list(out) == [1234.56, 10.5]


def test_parse_currency_brl(pio):
    s = pd.Series(["R$ 1.234,56", "R$10,00", "R$ 0,99"])
    out, coerced = pio.parse_currency_brl(s)
    assert coerced == 0
    assert list(out) == [1234.56, 10.0, 0.99]


# ---------------------------------------------------------------------------
# Datas BR / ISO / mistas (fixtures sintéticas)
# ---------------------------------------------------------------------------
def test_parse_dates_iso(pio):
    out, coerced, fmt = pio.parse_dates(pd.Series(["2024-01-02", "2025-12-31"]))
    assert fmt == "%Y-%m-%d"
    assert coerced == 0
    assert out.iloc[0] == pd.Timestamp("2024-01-02")


def test_parse_dates_br(pio):
    out, coerced, fmt = pio.parse_dates(pd.Series(["02/01/2024", "31/12/2025"]))
    assert fmt == "%d/%m/%Y"
    assert coerced == 0
    # 02/01/2024 é 2 de janeiro (dayfirst), não 1º de fevereiro
    assert out.iloc[0] == pd.Timestamp("2024-01-02")


def test_parse_dates_timestamp_iso(pio):
    out, coerced, fmt = pio.parse_dates(pd.Series(["2024-01-02 13:45:00"]))
    assert fmt == "%Y-%m-%d %H:%M:%S"
    assert out.iloc[0] == pd.Timestamp("2024-01-02 13:45:00")


def test_parse_dates_formatos_mistos_erro_claro(pio):
    with pytest.raises(pio.IngestionError, match="formatos mistos"):
        pio.parse_dates(pd.Series(["2024-01-02", "31/12/2025"]))


# ---------------------------------------------------------------------------
# Sentinelas e erros de parsing registrados (fixture sintética)
# ---------------------------------------------------------------------------
def test_sentinelas_e_erros_de_parsing_registrados(pio, tmp_path):
    csv = tmp_path / "sintetico_erros.csv"
    csv.write_text(
        "CODIGO;VALOR;DATA\n1;abc;2024-01-01\n2;N/A;2024-01-02\n3;7,5;-\n",
        encoding="utf-8",
    )
    spec = pio.FileSpec(
        logical_name="sintetico_erros",
        filename="sintetico_erros.csv",
        expected_sep=";",
        expected_columns=["CODIGO", "VALOR", "DATA"],
        code_columns=["CODIGO"],
        decimal_br_columns=["VALOR"],
        date_columns=["DATA"],
    )
    pio.FILE_SPECS["sintetico_erros"] = spec
    try:
        df, audit = pio.read_raw("sintetico_erros", raw_dir=tmp_path)
    finally:
        del pio.FILE_SPECS["sintetico_erros"]
    # sentinelas ("N/A" e "-") contadas antes; "abc" vira NA por coerção contada
    assert audit["nulos_antes"] == 2
    assert audit["nulos_depois"] == 3
    assert "VALOR" in audit["erros_parsing"]
    assert audit["status_ingestao"] == "OK_COM_AVISOS"
    assert pd.isna(df.loc[0, "VALOR"]) and df.loc[2, "VALOR"] == 7.5


def test_nbsp_e_espacos_normalizados(pio):
    s = pd.Series(["\xa0ABC \xa0", "  X  Y  "])
    out = pio.clean_text(s)
    assert out.iloc[0] == "ABC"
    assert out.iloc[1] == "X  Y"  # espaços internos preservados
