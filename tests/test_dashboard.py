# -*- coding: utf-8 -*-
"""Testes da Spec 09 - dashboard estatico (GitHub Pages).

O dashboard e camada de apresentacao: consome somente outputs validados
(Specs 01-08) via JSON derivado em docs/data/, nao le dados brutos e nao pode
usar linguagem proibida (hipotese vendida como conclusao).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
INDEX = DOCS / "index.html"
APP_JS = DOCS / "assets" / "app.js"
STYLES = DOCS / "assets" / "styles.css"
DATA_JSON = DOCS / "data" / "dashboard_data.json"
DATA_JS = DOCS / "data" / "dashboard_data.js"
BUILD = ROOT / "src" / "dashboard_build.py"
README = ROOT / "README.md"
MAKEFILE = ROOT / "Makefile"

ARQUIVOS_DASHBOARD = [INDEX, APP_JS, STYLES, DATA_JS, DATA_JSON]

FONTES_VALIDADAS_ESPERADAS = [
    "outputs/tables/data_quality_report.csv",
    "outputs/tables/ingestion_audit.csv",
    "outputs/tables/compras_coverage_audit.csv",
    "outputs/tables/gaps_saldo_contabil_estoque.csv",
    "outputs/tables/vendas_same_store_yoy.csv",
    "outputs/tables/vendas_categorias_yoy.csv",
    "outputs/tables/sortimento_controlado_por_volume.csv",
    "outputs/tables/produtos_correlacao_preco_volume_negativa.csv",
    "outputs/tables/projecao_venda_observada_2026.csv",
    "outputs/tables/triagem_repricing.csv",
    "outputs/tables/triagem_compras.csv",
    "outputs/tables/triagem_promocao.csv",
    "outputs/tables/triagem_descontinuacao.csv",
    "outputs/tables/hypothesis_status.csv",
    "reports/relatorio_final.md",
]

SECOES_OBRIGATORIAS = [
    "Sumário executivo",
    "Qualidade dos dados",
    "Vendas",
    "Lojas",
    "Categorias",
    "Sortimento",
    "Compras, estoque e gap contábil",
    "Precificação",
    "Projeção e triagens",
    "Hipóteses e conclusão",
    "Glossário",
]

SELOS_OBRIGATORIOS = [
    "Fato validado",
    "Evidência descritiva",
    "Associação exploratória",
    "Triagem",
    "Bloqueado",
    "Dado ausente",
    "Não validado",
]

LINGUAGEM_DE_LIMITACAO = [
    "venda observada",
    "gap contábil",
    "correlação",
    "triagem",
    "BLOQUEADO",
    "DADO AUSENTE",
    "NÃO VALIDADO",
]

# Frases proibidas em forma afirmativa (case-insensitive, apos remocao das
# negacoes permitidas).
PROIBIDAS_DIRETAS = [
    "ruptura comprovada",
    "ruptura fisica comprovada",
    "ruptura física comprovada",
    "elasticidade comprovada",
    "desabastecimento comprovado",
    "compras causaram a queda",
    "compras causaram queda",
    "demanda_real",
]

# Contextos permitidos: negacoes/limitacoes que citam o termo proibido para
# nega-lo, nomes de coluna do contrato e o enunciado da hipotese H7.
CONTEXTOS_PERMITIDOS = [
    r"n[aã]o [eé] ruptura f[ií]sica comprovada",
    r"n[aã]o [eé] demanda real",
    r"nem demanda real",
    r"n[aã]o mede[m]? demanda real",
    r"n[aã]o representa demanda real",
    r"pode ser demanda real",
    r"demanda real e n[aã]o ruptura",
    r"demanda real ou prova",
    r"n[aã]o s[aã]o decis[oõ]es finais",
    r"n[aã]o [eé] decis[aã]o final",
    r"bloquead[ao] para decis[aã]o final",
    r"status_decisao_final",
    r"status de decis[aã]o",
]


def _texto(path: Path) -> str:
    assert path.exists(), f"arquivo ausente: {path.relative_to(ROOT)}"
    assert path.stat().st_size > 0, f"arquivo vazio: {path.relative_to(ROOT)}"
    return path.read_text(encoding="utf-8")


def _normalizar(texto: str) -> str:
    """Minusculas + colapso de espacos/quebras de linha (HTML tem wrap)."""
    return re.sub(r"\s+", " ", texto.lower())


def _texto_sem_contextos_permitidos(texto: str) -> str:
    limpo = _normalizar(texto)
    for padrao in CONTEXTOS_PERMITIDOS:
        limpo = re.sub(padrao, " ", limpo)
    return limpo


def _payload_para_checagem_de_linguagem() -> str:
    """Payload sem o campo conclusao_proibida (que cita, para proibir,
    exatamente as frases proibidas)."""
    payload = json.loads(_texto(DATA_JSON))
    for hipotese in payload.get("hipoteses", []):
        hipotese.pop("conclusao_proibida", None)
    return json.dumps(payload, ensure_ascii=False)


def test_arquivos_principais_do_dashboard_existem():
    for path in ARQUIVOS_DASHBOARD + [BUILD, DOCS / ".nojekyll"]:
        assert path.exists(), f"arquivo do dashboard ausente: {path.relative_to(ROOT)}"
        if path.name != ".nojekyll":
            assert path.stat().st_size > 0, f"arquivo vazio: {path.relative_to(ROOT)}"


def test_dashboard_nao_referencia_dados_brutos():
    for path in ARQUIVOS_DASHBOARD + [BUILD]:
        texto = _texto(path).lower()
        assert "data/raw" not in texto, f"{path.relative_to(ROOT)} referencia data/raw"
        assert "data\\raw" not in texto, f"{path.relative_to(ROOT)} referencia data\\raw"


def test_build_le_somente_outputs_validados_e_gera_docs_data():
    build = _texto(BUILD)
    assert 'TABLES = ROOT / "outputs" / "tables"' in build
    assert '"docs" / "data"' in build
    for fonte in FONTES_VALIDADAS_ESPERADAS:
        nome = fonte.split("/")[-1]
        if nome.endswith(".csv"):
            assert nome in build, f"build nao referencia fonte validada: {fonte}"
    # Nenhuma leitura de parquet/processed nem de dados brutos.
    assert "data/processed" not in build.lower()
    assert "read_parquet" not in build


def test_dashboard_consome_somente_jsons_derivados_dos_outputs_validados():
    index = _texto(INDEX)
    assert 'src="data/dashboard_data.js"' in index
    assert 'src="assets/app.js"' in index
    assert 'href="assets/styles.css"' in index
    app = _texto(APP_JS)
    assert "window.DASHBOARD_DATA" in app
    assert "fetch(" not in app, "app.js nao deve buscar dados externos"
    payload = json.loads(_texto(DATA_JSON))
    assert set(FONTES_VALIDADAS_ESPERADAS).issubset(set(payload["meta"]["fontes"]))
    js = _texto(DATA_JS)
    assert "window.DASHBOARD_DATA" in js


def test_payload_tem_blocos_principais():
    payload = json.loads(_texto(DATA_JSON))
    for chave in [
        "meta",
        "kpis",
        "vendas_mensais",
        "lojas_yoy_anual_2025",
        "same_store",
        "categorias_yoy",
        "sortimento",
        "qualidade",
        "ingestao",
        "cobertura",
        "gaps",
        "correlacao",
        "projecao",
        "triagens",
        "hipoteses",
    ]:
        assert chave in payload, f"payload sem bloco: {chave}"
    assert len(payload["vendas_mensais"]) == 24
    assert len(payload["hipoteses"]) == 10
    assert payload["projecao"]["totais"]["status_compra_liquida"].keys() == {"BLOQUEADO"}
    for triagem in payload["triagens"].values():
        assert triagem["status_decisao_final"].keys() == {"BLOQUEADO"}


def test_dashboard_contem_secoes_principais():
    index = _texto(INDEX)
    for secao in SECOES_OBRIGATORIAS:
        assert secao in index, f"secao ausente no dashboard: {secao}"


def test_dashboard_contem_selos_epistemicos_e_notas_metodologicas():
    index = _texto(INDEX)
    app = _texto(APP_JS)
    conteudo = index + app
    for selo in SELOS_OBRIGATORIOS:
        assert selo in conteudo, f"selo epistemico ausente: {selo}"
    # Tooltips/notas dos KPIs: formula, fonte, unidade, confianca, limitacao.
    for campo in ["Fórmula", "Fonte", "Unidade", "Confiança", "Limitação"]:
        assert campo in app, f"nota metodologica sem campo: {campo}"
    assert "nota metodológica" in app


def test_dashboard_contem_linguagem_de_limitacao():
    index = _texto(INDEX)
    for termo in LINGUAGEM_DE_LIMITACAO:
        assert termo in index, f"linguagem de limitacao ausente no dashboard: {termo}"
    # Normaliza hifens tipograficos e espacos antes de comparar frases completas.
    index_normalizado = _normalizar(index).replace("‑", "-").replace("‐", "-")
    for frase in [
        "venda observada não é demanda real",
        "gap contábil de estoque não é ruptura física comprovada",
        "correlação preço-volume não é elasticidade",
        "triagens não são decisões finais",
    ]:
        assert frase in index_normalizado, f"frase de limitacao ausente: {frase}"


def test_dashboard_nao_usa_linguagem_proibida():
    textos = {
        "index.html": _texto(INDEX),
        "app.js": _texto(APP_JS),
        "dashboard_data.json": _payload_para_checagem_de_linguagem(),
    }
    for nome, texto in textos.items():
        limpo = _texto_sem_contextos_permitidos(texto)
        for frase in PROIBIDAS_DIRETAS:
            assert frase not in limpo, f"{nome} contem linguagem proibida: {frase}"
        # Apos remover as negacoes permitidas, "demanda real" nao pode sobrar
        # (venda observada nunca pode ser apresentada como demanda real).
        assert "demanda real" not in limpo, f"{nome} usa 'demanda real' fora de negacao"
        # Triagens nunca como decisao final (fora das negacoes permitidas).
        assert "decisão final" not in limpo and "decisao final" not in limpo and "decisões finais" not in limpo and "decisoes finais" not in limpo, (
            f"{nome} apresenta triagem como decisao final"
        )


def test_makefile_tem_alvos_do_dashboard():
    makefile = _texto(MAKEFILE)
    for alvo in ["dashboard:", "dashboard-build:", "dashboard-test:"]:
        assert alvo in makefile, f"Makefile sem alvo {alvo}"
    assert "http.server" in makefile
    assert "dashboard_build.py" in makefile


def test_readme_explica_dashboard_e_github_pages():
    readme = _normalizar(_texto(README))
    for termo in [
        "github pages",
        "settings",
        "deploy from",
        "/docs",
        "make dashboard",
        "python -m http.server",
        "src/dashboard_build.py",
        "docs/index.html",
    ]:
        assert termo in readme, f"README sem instrucao do dashboard: {termo}"
