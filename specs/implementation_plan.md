# Plano de implementação — Case (SDD)

> Fase 01 concluída com este plano. Nenhuma spec de implementação (01–09) foi iniciada.
> Referências: [SDD.MD](../SDD.MD), [specs/00_current_state.md](00_current_state.md) e specs 01–09 nesta pasta.

## Ordem de implementação

```text
00. Discovery do repositório                          ✅ CONCLUÍDA (specs/00_current_state.md)
01. Ingestão, encoding e parsing                      → specs/01_ingestion_encoding_spec.md
02. Contratos e qualidade de dados                    → specs/02_data_contract_quality_spec.md
03. Catálogo de métricas e regras de negócio          → specs/03_metrics_business_rules_spec.md
04. Compras, estoque, unidades e reconciliação        → specs/04_inventory_purchase_reconciliation_spec.md
05. Vendas, lojas, categorias e sortimento            → specs/05_sales_store_category_assortment_spec.md
06. Precificação, projeção e recomendações            → specs/06_pricing_projection_recommendations_spec.md
07. Hipóteses e relatório final                       → specs/07_hypothesis_report_spec.md
08. Testes, execução, README e reprodutibilidade      → specs/08_tests_reproducibility_spec.md
09. Dashboard final                                   → specs/09_dashboard_delivery_spec.md  (ÚLTIMA, obrigatoriamente)
```

## Justificativa da ordem

- **01 antes de tudo**: encoding/separador/decimal/tipos contaminam todo o downstream; e é na Spec 01 que o dicionário oficial (`Descritivo_bases_de_dados_2.xlsx`, hoje `DADO AUSENTE`) é lido — insumo das Specs 02 e 04.
- **02 antes de 03**: não se cataloga KPI sobre dado sem contrato; a unicidade do grão de `fato_vendas` (não validada) muda as fórmulas de receita/quantidade.
- **03 antes de 04–06**: as fórmulas e o número oficial da queda (−71,7% vs. −85% vs. −91,7%) precisam estar congelados antes de refazer análises.
- **04 antes de 05–06**: a conversão de unidade das compras e a cobertura da base de compras condicionam sortimento (H5), projeção e a proibição de compra líquida.
- **05 antes de 07**: same-store, YoY e sortimento controlado por volume são a evidência que decide H1–H4.
- **06 antes de 07**: correlação/projeção/triagens com vocabulário correto são insumo direto do relatório.
- **07 antes de 08**: o relatório reescrito entra na suíte consolidada de testes.
- **08 antes de 09**: o dashboard exige pipeline reproduzível (`make run`) e suíte verde.
- **09 por último**: é só camada de apresentação; construí-lo antes institucionalizaria os erros atuais.

## Arquivos que serão criados (por spec)

| Spec | Criados |
|---|---|
| 01 | `src/io.py`, `docs/data_formatting_and_encoding.md`, `outputs/tables/ingestion_audit.csv`, `tests/test_ingestion.py` |
| 02 | `docs/data_contract.md`, `src/validation/schemas.py`, `src/validation/quality_checks.py`, `src/02_quality_audit.py`, `outputs/tables/data_quality_report.csv`, `tests/test_schema.py`, `tests/test_quality_checks.py` |
| 03 | `docs/metric_catalog.md`, `docs/business_rules.md`, `src/metrics.py`, `tests/test_metrics.py` |
| 04 | `src/analysis/inventory_reconciliation.py`, `outputs/tables/compras_coverage_audit.csv`, `outputs/tables/gaps_saldo_contabil_estoque.csv`, `docs/known_limitations.md`, `tests/test_units.py`, `tests/test_reconciliation.py` |
| 05 | `src/analysis/sales_analysis.py`, `src/analysis/assortment_analysis.py`, `outputs/tables/vendas_same_store_yoy.csv`, `outputs/tables/vendas_categorias_yoy.csv`, `outputs/tables/sortimento_controlado_por_volume.csv`, `tests/test_sales_analysis.py`, `tests/test_assortment_analysis.py` |
| 06 | `src/analysis/pricing_analysis.py`, `src/analysis/projection_analysis.py`, `src/analysis/recommendation_triage.py`, `outputs/tables/produtos_correlacao_preco_volume_negativa.csv`, `outputs/tables/projecao_venda_observada_2026.csv`, `outputs/tables/triagem_possivel_promocao.csv`, `outputs/tables/triagem_possivel_descontinuacao.csv`, `tests/test_pricing.py`, `tests/test_projection.py`, `tests/test_recommendations.py` |
| 07 | `docs/hypothesis_validation_matrix.md`, `outputs/tables/hypothesis_status.csv`, cópia de preservação do relatório original, `tests/test_hypothesis_report.py` |
| 08 | `pyproject.toml`, `Makefile`, `requirements.lock`, `tests/test_outputs.py` |
| 09 | `dashboard/app.py` (+ `pages/`, `components/`, `assets/` se multipage), `tests/test_dashboard.py` |

## Arquivos que serão alterados (por spec)

| Spec | Alterados | Observação |
|---|---|---|
| 01 | (idealmente nenhum) | Troca da leitura inline de `01_etl.py` por `src/io.py` só com prova de reprodução idêntica dos Parquet |
| 02 | `requirements.txt` ou `pyproject.toml` | Adição de `pandera` (documentada) |
| 03 | nenhum | Catálogo descreve as fórmulas como estão |
| 04 | nenhum script legado | Nova lógica em `src/analysis/`; outputs legados preservados |
| 05 | nenhum script legado | idem |
| 06 | nenhum script legado | Outputs legados de 05/06/07 preservados; novos nomes são os oficiais |
| 07 | `reports/relatorio_final.md` | Reescrito, com original preservado |
| 08 | `README.md`, scripts `src/01..07` (condicional) | Wrappers `__main__`/paths só com validação de reprodução byte-idêntica |
| 09 | `Makefile`, `README.md`, `pyproject.toml` | Alvo `make dashboard`, deps streamlit/plotly |

## Riscos de cada etapa

| Spec | Riscos principais |
|---|---|
| 01 | Dicionário xlsx contradizer decisões de parsing atuais (retrabalho controlado); `Estudo_de_caso_1.docx` ilegível sem nova dependência; falso negativo de encoding em fallback automático |
| 02 | Duplicidade real no grão de `fato_vendas` invalidaria números do relatório inteiro (é um resultado, não um fracasso — mas muda o cronograma das specs 03+); pandera pode conflitar com pandas 3.x (`NÃO VALIDADO`) |
| 03 | Escolher mal o "número oficial da queda" perpetua a confusão; limiares herdados (0,005; 15d; −0,4) podem ser questionados pelo negócio |
| 04 | Se `CONVERSAO_COMPRA_ARMAZENAGEM ≠ 1` em produtos relevantes, o gap ~2,7× muda de tamanho e o texto do relatório muda em cadeia; ambiguidade de unidade pode ficar `BLOQUEADO` se o dicionário não resolver |
| 05 | Números da Seção 2 (2.490→1.212; 74→14; 0,49; Loja 9 +73%) podem não se reproduzir — exige correção formal do relatório; reamostragem de sortimento é a parte metodologicamente mais delicada |
| 06 | Projeção 2026 herda tendência de queda possivelmente artefactual; risco de vocabulário proibido escapar em colunas/nomes |
| 07 | Dependência de todos os anteriores; tensão entre "reescrever relatório" e "não sobrescrever arquivos importantes" (mitigada com cópia de preservação) |
| 08 | `make` indisponível no Windows nativo (`NÃO VALIDADO`); mexer nos scripts legados para testabilidade pode alterar outputs (mitigação: comparação byte a byte) |
| 09 | Recalcular métrica no app por conveniência (proibido); performance com derivados de 1,09M linhas; escopo de 10 páginas crescer demais |

## Comandos para validar cada etapa

Ambiente: Windows/PowerShell; usar venv do projeto quando existir. Antes da Spec 08 (sem Makefile), os comandos são diretos:

| Spec | Validação |
|---|---|
| 01 | `pytest tests/test_ingestion.py` + inspeção de `outputs/tables/ingestion_audit.csv` |
| 02 | `python src/02_quality_audit.py` (da raiz ou conforme doc da spec) + `pytest tests/test_schema.py tests/test_quality_checks.py` |
| 03 | `pytest tests/test_metrics.py` |
| 04 | `python src/analysis/inventory_reconciliation.py` + `pytest tests/test_units.py tests/test_reconciliation.py` |
| 05 | `python src/analysis/sales_analysis.py` e `python src/analysis/assortment_analysis.py` + `pytest tests/test_sales_analysis.py tests/test_assortment_analysis.py` |
| 06 | scripts de `src/analysis/` da spec + `pytest tests/test_pricing.py tests/test_projection.py tests/test_recommendations.py` |
| 07 | `pytest tests/test_hypothesis_report.py` + revisão humana do relatório |
| 08 | `make install && make lint && make test && make run && make audit` (ou equivalentes documentados sem make) + `pytest tests/test_outputs.py` |
| 09 | `make dashboard` (smoke manual) + `pytest tests/test_dashboard.py` |
| Todas | `pytest tests/test_specs_exist.py` continua verde após qualquer etapa |

## Critérios objetivos de conclusão por etapa

Cada spec traz seus critérios de aceite completos; resumo objetivo:

- **01**: `ingestion_audit.csv` com 1 linha por arquivo bruto e colunas obrigatórias; contagens batem com Spec 00; `pytest tests/test_ingestion.py` verde; Parquet inalterados (ou diff documentado).
- **02**: contrato cobre as 8 tabelas brutas; unicidade de chaves respondida com números; `data_quality_report.csv` só com status {PASS, WARN, FAIL}; testes verdes.
- **03**: catálogo cobre 100% das métricas usadas no relatório; número oficial da queda definido e reconciliado; testes verdes.
- **04**: pergunta da conversão de compra respondida na base completa; `compras_coverage_audit.csv` com classificação nas 4 categorias; nenhum output novo chama gap de "ruptura"; testes verdes.
- **05**: cada número da Seção 2 do relatório reproduzido ou formalmente marcado não reproduzido; 3 outputs gerados; testes verdes.
- **06**: zero ocorrências de "elasticidade" em artefatos novos; compra líquida bloqueada com flag; triagens com os 6 campos; testes verdes.
- **07**: matriz H1–H10 com vocabulário controlado; relatório com 17 seções; todo número rastreável a output; testes verdes.
- **08**: `make all` (ou equivalente) verde numa máquina limpa; lockfile commitado; README completo; testes verdes.
- **09**: `make dashboard` sobe o app; selos epistêmicos e tooltips presentes; nenhuma linguagem proibida; testes verdes ou bloqueio documentado.

## Dependências entre specs

```text
00 ──► 01 ──► 02 ──► 03 ──► 04 ──► 05 ──► 06 ──► 07 ──► 08 ──► 09
        │      │             │      │      │
        │      │             │      │      └─ 06 usa cobertura (04) p/ flag de compra líquida
        │      │             │      └─ 05 usa grão validado (02) e unidades (04)
        │      │             └─ 04 usa dicionário lido em 01 e checks de 02
        │      └─ 02 usa src/io.py e dicionário (01)
        └─ 01 lê o dicionário xlsx (destrava 02 e 04)
```

- 03 pode começar em paralelo à conclusão de 02 (catalogar fórmulas existentes não depende do contrato), mas só **conclui** após 02 responder o grão.
- 07 depende de 02–06 concluídas ou bloqueadas com registro. 09 depende de 01–08.

## Testes a rodar após cada spec

Regra: rodar os testes novos da spec **mais** toda a suíte acumulada (regressão).

| Após | Suíte |
|---|---|
| 01 | `pytest tests/test_specs_exist.py tests/test_ingestion.py` |
| 02 | + `tests/test_schema.py tests/test_quality_checks.py` |
| 03 | + `tests/test_metrics.py` |
| 04 | + `tests/test_units.py tests/test_reconciliation.py` |
| 05 | + `tests/test_sales_analysis.py tests/test_assortment_analysis.py` |
| 06 | + `tests/test_pricing.py tests/test_projection.py tests/test_recommendations.py` |
| 07 | + `tests/test_hypothesis_report.py` |
| 08 | `pytest` (tudo) + `tests/test_outputs.py`, via `make test` |
| 09 | `pytest` (tudo) + `tests/test_dashboard.py` |

## Specs que podem ser bloqueadas por ausência de dados

| Spec | Bloqueio potencial | Dado ausente |
|---|---|---|
| 01 | Parcial | `Estudo_de_caso_1.docx` sem lib de leitura (decisão: nova dependência ou transcrição manual) |
| 02 | Parcial | Contrato "oficial" depende do `Descritivo_bases_de_dados_2.xlsx`; se o dicionário for pobre, contrato fica "conforme observado" |
| 04 | Parcial-alto | Sem transferências/devoluções/ajustes/estoque final real, o gap contábil não é decomponível em causas — entrega classificação de confiabilidade, não veredito. Confirmação de que `fato_compras` é parcial depende do dono do dado (bloqueio externo) |
| 06 | Alto (esperado) | Compra líquida sugerida `BLOQUEADO` por estoque disponível inconfiável; priorização financeira de triagens `BLOQUEADO` sem margem/custo/lead time |
| 07 | Parcial | H9/H10 tendem a `Inválida por limitação de dados` (margem, lead time, estoque confiável ausentes) |
| 05 | Baixo | Calendário oficial de abertura/fechamento de lojas ausente → conclusões sobre fechamento permanecem inferenciais |
| 03/08/09 | Baixo | Sem bloqueio de dados previsto; 09 herda os bloqueios anteriores via selos "bloqueado por dados insuficientes" |

Bloqueios não impedem a conclusão da spec: cada um é registrado no output correspondente (`NÃO VALIDADO` / `DADO AUSENTE` / `BLOQUEADO`) e a spec fecha com status documentado, conforme princípios 15, 19 e 20 do SDD.MD.
