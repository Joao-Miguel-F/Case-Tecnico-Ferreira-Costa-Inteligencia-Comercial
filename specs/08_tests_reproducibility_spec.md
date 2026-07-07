# Spec 08 — Testes, execução, README e reprodutibilidade

> Status: **PLANEJADA** (nenhuma implementação feita nesta fase).
> Base de evidência: [specs/00_current_state.md](00_current_state.md), [README.md](../README.md), [requirements.txt](../requirements.txt), estrutura real do repo.

## Problema

O projeto não tem infraestrutura de execução e teste:

1. Não existem `Makefile`, `pyproject.toml`, lockfile de dependências, `ruff`, nem `pytest` configurado; a única suíte é `tests/test_specs_exist.py` (criada nas Fases 00/01 do SDD).
2. Os scripts usam caminhos relativos (`../data/raw`) e **precisam ser executados de dentro de `src/`**; rodar da raiz quebra tudo (Spec 00, "Ordem atual de execução").
3. Os 7 scripts executam no nível do módulo (sem `if __name__ == "__main__"` nem funções), o que impede import para teste unitário.
4. `requirements.txt` usa pisos abertos (`pandas>=2.0`, `numpy>=1.24`); o pip de hoje resolve pandas 3.0.3/numpy 2.5.1. A reprodução foi validada em 2026-07-06 (todos os 38 outputs idênticos em cópia isolada), mas não há lockfile congelando as versões provadas.
5. O README descreve pipeline "01_ a 08_" via relatório e não menciona testes, auditoria nem limitações de conclusão.

## Evidência encontrada no repositório

- Spec 00, "Estrutura atual": ausência confirmada de `Makefile`, `pyproject.toml`, `docs/`, `tests/` (além do criado pelo SDD).
- Spec 00, "Riscos técnicos" #2, #3, #4: caminhos relativos frágeis, sem entrypoint, trabalho no nível de módulo.
- Spec 00, "Riscos técnicos" #1: reprodução validada com pandas 3.0.3/numpy 2.5.1/pyarrow 24.0.0/matplotlib 3.11.0/openpyxl 3.1.5 (Python 3.14.6) — versões exatas provadas, ainda não congeladas.
- Spec 00, "Riscos técnicos" #5: relatório referencia scripts `3b` e `08` inexistentes.
- [requirements.txt](../requirements.txt): 5 dependências com pisos abertos; sem pytest/ruff/pandera.

## Risco para o negócio

- Sem `make run`/lockfile, uma atualização de dependência pode mudar números silenciosamente e ninguém detecta (o risco não se materializou hoje, mas não está blindado).
- Sem suíte de testes consolidada, as correções das Specs 01–07 podem regredir sem alarme.
- Um novo analista não consegue rodar/auditar o projeto sem ler a Spec 00 inteira — o conhecimento operacional não está no README.

## Arquivos de entrada

- Todos os testes criados nas Specs 00–07 (`tests/test_specs_exist.py`, `test_ingestion.py`, `test_schema.py`, `test_quality_checks.py`, `test_metrics.py`, `test_units.py`, `test_reconciliation.py`, `test_sales_analysis.py`, `test_assortment_analysis.py`, `test_pricing.py`, `test_projection.py`, `test_recommendations.py`, `test_hypothesis_report.py`);
- `requirements.txt` atual; scripts `src/01..07`; outputs e docs produzidos pelas specs anteriores.

## Arquivos de saída esperados

- `pyproject.toml` — dependências (incluindo as novas: pytest, ruff, pandera), configuração de pytest e ruff, versão mínima de Python.
- `Makefile` — alvos `install`, `lint`, `test`, `run`, `audit`, `report`, `all` (e `dashboard` na Spec 09).
- `README.md` atualizado — objetivo, estrutura, bases, limitações, como instalar/rodar/testar/auditar, o que é conclusão confiável vs. hipótese, dados adicionais necessários.
- `tests/test_outputs.py` — validação de existência/colunas dos outputs principais.
- Lockfile de versões provadas (ex.: `requirements.lock` via `pip freeze` — recomendação da Spec 00).

## Regras de negócio envolvidas

- O pipeline deve rodar do zero e falhar cedo quando dados obrigatórios estiverem ausentes (princípios 13–14 do SDD.MD).
- `make run` deve funcionar da raiz do repo (resolver a fragilidade dos caminhos relativos — via `cd src` no Makefile ou correção de paths, decisão a registrar).
- Nenhum resultado analítico muda nesta spec: é infraestrutura; qualquer diff em outputs é regressão.

## Métricas afetadas

Nenhuma diretamente. Indiretamente, todas — esta spec garante que os valores validados nas Specs 01–07 permaneçam reproduzíveis.

## Mudanças propostas

1. Criar `pyproject.toml` com dependências pinadas/testadas e configs de pytest/ruff.
2. Criar `Makefile` com os 7 alvos; `make run` executa `01→07` (+ novos scripts de auditoria/análise) na ordem correta a partir da raiz.
3. Gerar lockfile com as versões exatas provadas em 2026-07-06.
4. Atualizar `README.md` (incluindo correção da referência a "01_ a 08_" e instruções de auditoria/testes).
5. Criar `tests/test_outputs.py` cobrindo: `ingestion_audit.csv`, `data_quality_report.csv`, `compras_coverage_audit.csv`, `hypothesis_status.csv`, specs, docs, relatório, Makefile, pyproject, README.
6. Rodar `make lint`, `make test`, `make run`, `make audit`; documentar falhas reais (comando, erro, causa, impacto, próximo passo).
7. Se necessário para testabilidade, envolver os scripts legados em `if __name__ == "__main__"`/funções — **somente** se a reexecução continuar reproduzindo os outputs byte-idêntico (validação obrigatória, como feito na Spec 00).

## Testes necessários

- `tests/test_outputs.py` (lista acima);
- suíte completa `pytest` verde (ou bloqueios documentados);
- `ruff check` limpo ou com exceções configuradas e justificadas;
- verificação de reprodutibilidade: reexecução completa reproduz os outputs validados (tolerância documentada).

## Critérios de aceite

- `make install && make all` funciona numa máquina limpa (ou bloqueios reais documentados);
- pipeline roda da raiz do repositório;
- lockfile commitado com as versões provadas;
- README explica instalação, execução, testes, auditoria e o status epistêmico das conclusões;
- `pytest` completo passa.

## O que não será feito

- Não será adotado Airflow/orquestrador (SDD.MD, seção 3: simplicidade e reprodutibilidade local).
- Não será feito CI/CD (fora do escopo do SDD.MD; pode ser recomendação futura).
- Não serão alterados resultados analíticos (qualquer mudança de número é bug desta spec).
- Não será criado o dashboard (Spec 09) — apenas o alvo `make dashboard` fica reservado.

## Dúvidas ou bloqueios

- **Dependência**: consolida testes das Specs 01–07; só conclui quando eles existirem (ou estiverem bloqueados com registro).
- `NÃO VALIDADO` — Estratégia para caminhos relativos: `cd src` no Makefile (zero mudança de código) vs. parametrizar paths nos scripts (melhor, porém toca código legado). Proposta: começar com `cd src` e evoluir apenas com validação de reprodução.
- `NÃO VALIDADO` — Python 3.14.6 foi o interpretador provado; definir versão mínima suportada no `pyproject.toml` exige decidir se versões anteriores serão testadas.
- Ambiente Windows (PowerShell) do repositório: `make` pode não estar disponível nativamente; documentar alternativa (ex.: `make` via Git Bash) no README. `NÃO VALIDADO` se `make` existe na máquina-alvo.
