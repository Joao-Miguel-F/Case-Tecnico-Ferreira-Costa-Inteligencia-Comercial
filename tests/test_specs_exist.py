# -*- coding: utf-8 -*-
"""
tests/test_specs_exist.py

Testes de existência da documentação de specs (Fases 00 e 01 do SDD.MD).

Fase 00: valida specs/00_current_state.md e suas seções mínimas.
Fase 01: valida que as specs 01..09 e o implementation_plan.md existem,
não estão vazios e contêm as seções mínimas exigidas pelo SDD.MD (seção 7).

Depende somente da biblioteca padrão (pathlib), de propósito: o pipeline
depende de pandas/pyarrow, mas o teste de existência de documentação não deve
depender de nada além do Python padrão. Assim ele roda mesmo antes de instalar
as dependências analíticas.

Pode ser executado de duas formas:
    pytest tests/test_specs_exist.py
    python tests/test_specs_exist.py     # runner standalone, sem pytest
"""
from pathlib import Path

# Raiz do repositório = pasta pai de tests/
ROOT = Path(__file__).resolve().parents[1]
SPECS_DIR = ROOT / "specs"

SPEC_00 = SPECS_DIR / "00_current_state.md"

# Todos os arquivos exigidos pela Fase 01 (SDD.MD, seção 7).
ARQUIVOS_FASE_01 = [
    SPECS_DIR / "00_current_state.md",
    SPECS_DIR / "01_ingestion_encoding_spec.md",
    SPECS_DIR / "02_data_contract_quality_spec.md",
    SPECS_DIR / "03_metrics_business_rules_spec.md",
    SPECS_DIR / "04_inventory_purchase_reconciliation_spec.md",
    SPECS_DIR / "05_sales_store_category_assortment_spec.md",
    SPECS_DIR / "06_pricing_projection_recommendations_spec.md",
    SPECS_DIR / "07_hypothesis_report_spec.md",
    SPECS_DIR / "08_tests_reproducibility_spec.md",
    SPECS_DIR / "09_dashboard_delivery_spec.md",
    SPECS_DIR / "implementation_plan.md",
]

# Specs 01..09: devem conter as 12 seções mínimas do SDD.MD.
# (00_current_state.md tem seções próprias da Fase 00; implementation_plan.md
# tem conteúdo próprio de plano — ambos validados separadamente.)
SPECS_COM_SECOES_MINIMAS = ARQUIVOS_FASE_01[1:-1]

# Seções mínimas de cada spec 01..09 (comparação em minúsculas, por substring,
# para tolerar variações de título sem deixar de exigir o conteúdo).
SECOES_MINIMAS_SPEC = [
    "problema",
    "evidência encontrada no repositório",
    "risco para o negócio",
    "arquivos de entrada",
    "arquivos de saída esperados",
    "regras de negócio envolvidas",
    "métricas afetadas",
    "mudanças propostas",
    "testes necessários",
    "critérios de aceite",
    "o que não será feito",
    "dúvidas ou bloqueios",
]

# Conteúdo obrigatório do plano de implementação (SDD.MD, seção 7 + prompt da Fase 01).
SECOES_MINIMAS_PLANO = [
    "ordem de implementação",
    "justificativa da ordem",
    "arquivos que serão criados",
    "arquivos que serão alterados",
    "riscos de cada etapa",
    "comandos para validar",
    "critérios objetivos",
    "dependências entre specs",
    "testes a rodar",
    "bloqueadas por ausência de dados",
]

# Seções mínimas esperadas da Fase 00 (SDD.MD, "Conteúdo obrigatório").
SECOES_MINIMAS_FASE_00 = [
    "objetivo de negócio",
    "estrutura atual do repositório",
    "scripts existentes",
    "ordem atual de execução",
    "bases disponíveis",
    "grão aparente",
    "chaves aparentes",
    "outputs existentes",
    "kpi",
    "hipóteses do relatório",
    "conclusões descritivas",
    "conclusões diagnósticas",
    "conclusões causais",
    "riscos técnicos",
    "riscos analíticos",
    "encoding",
    "unidade de medida",
    "qualidade de dados",
    "precisam ser validados",
    "perguntas em aberto",
]


def _ler(path: Path) -> str:
    assert path.is_file(), f"Arquivo não encontrado: {path}"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Fase 00
# ---------------------------------------------------------------------------

def test_pasta_specs_existe():
    assert SPECS_DIR.is_dir(), f"Pasta specs/ não encontrada em {SPECS_DIR}"


def test_spec_00_existe():
    assert SPEC_00.is_file(), f"Arquivo não encontrado: {SPEC_00}"


def test_spec_00_nao_esta_vazio():
    conteudo = _ler(SPEC_00).strip()
    # Exige conteúdo real, não só um título de uma linha.
    assert len(conteudo) > 500, "specs/00_current_state.md está vazio ou muito curto"


def test_spec_00_contem_secoes_minimas():
    conteudo = _ler(SPEC_00).lower()
    faltando = [s for s in SECOES_MINIMAS_FASE_00 if s not in conteudo]
    assert not faltando, f"Seções mínimas da Fase 00 ausentes em 00_current_state.md: {faltando}"


# ---------------------------------------------------------------------------
# Fase 01 — existência e não-vazio de todos os arquivos exigidos
# ---------------------------------------------------------------------------

def test_todos_arquivos_fase_01_existem():
    faltando = [str(p.relative_to(ROOT)) for p in ARQUIVOS_FASE_01 if not p.is_file()]
    assert not faltando, f"Arquivos da Fase 01 ausentes: {faltando}"


def test_todos_arquivos_fase_01_nao_estao_vazios():
    curtos = []
    for p in ARQUIVOS_FASE_01:
        if not p.is_file():
            curtos.append(f"{p.name} (ausente)")
            continue
        if len(p.read_text(encoding="utf-8").strip()) <= 500:
            curtos.append(p.name)
    assert not curtos, f"Arquivos da Fase 01 vazios ou muito curtos: {curtos}"


# ---------------------------------------------------------------------------
# Fase 01 — seções mínimas de cada spec 01..09
# ---------------------------------------------------------------------------

def test_specs_01_a_09_contem_secoes_minimas():
    problemas = {}
    for p in SPECS_COM_SECOES_MINIMAS:
        if not p.is_file():
            problemas[p.name] = ["arquivo ausente"]
            continue
        conteudo = _ler(p).lower()
        faltando = [s for s in SECOES_MINIMAS_SPEC if s not in conteudo]
        if faltando:
            problemas[p.name] = faltando
    assert not problemas, f"Seções mínimas ausentes por spec: {problemas}"


def test_plano_implementacao_contem_secoes_minimas():
    plano = SPECS_DIR / "implementation_plan.md"
    conteudo = _ler(plano).lower()
    faltando = [s for s in SECOES_MINIMAS_PLANO if s not in conteudo]
    assert not faltando, f"Conteúdo obrigatório ausente em implementation_plan.md: {faltando}"


def test_dashboard_e_a_ultima_etapa_do_plano():
    """A ordem do SDD.MD exige o dashboard como última etapa (09)."""
    conteudo = _ler(SPECS_DIR / "implementation_plan.md").lower()
    pos_dashboard = conteudo.find("09. dashboard")
    assert pos_dashboard != -1, "implementation_plan.md não lista '09. Dashboard' na ordem"


# ---------------------------------------------------------------------------
# Runner standalone
# ---------------------------------------------------------------------------

def _run_standalone():
    """Executa todos os testes sem pytest e imprime um resumo."""
    testes = [
        test_pasta_specs_existe,
        test_spec_00_existe,
        test_spec_00_nao_esta_vazio,
        test_spec_00_contem_secoes_minimas,
        test_todos_arquivos_fase_01_existem,
        test_todos_arquivos_fase_01_nao_estao_vazios,
        test_specs_01_a_09_contem_secoes_minimas,
        test_plano_implementacao_contem_secoes_minimas,
        test_dashboard_e_a_ultima_etapa_do_plano,
    ]
    falhas = 0
    for t in testes:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(testes) - falhas}/{len(testes)} testes passaram.")
    return falhas


if __name__ == "__main__":
    import sys

    sys.exit(1 if _run_standalone() else 0)
