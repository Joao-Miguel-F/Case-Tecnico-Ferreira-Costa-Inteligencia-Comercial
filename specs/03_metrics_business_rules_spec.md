# Spec 03 — Catálogo de métricas e regras de negócio

> Status: **IMPLEMENTADA / CONSOLIDADA** (entregáveis, docs e testes confirmados na consolidação de 2026-07-07).
> Nota: o corpo abaixo preserva a especificação original; o resultado consolidado está em [docs/metric_catalog.md](../docs/metric_catalog.md) e [docs/business_rules.md](../docs/business_rules.md).
> Base de evidência: [specs/00_current_state.md](00_current_state.md), scripts `src/01..07`, [reports/relatorio_final.md](../reports/relatorio_final.md), [README.md](../README.md).

## Problema

Todas as métricas do projeto estão **implícitas no código dos scripts**, sem catálogo, sem fórmula documentada, sem dono e sem teste. Pior: os três documentos do repositório usam **números diferentes para a mesma métrica-título** ("queda de vendas"): README diz ~−85% (nov/24→dez/25), `vendas_mensais.csv` implica −91,7% para esse mesmo par de meses, e o relatório usa −71,7% (1T24→4T25). Não existe `docs/metric_catalog.md`, `docs/business_rules.md`, `src/metrics.py` nem `tests/test_metrics.py`.

## Evidência encontrada no repositório

Métricas extraídas diretamente do código (Spec 00, seção "Principais KPIs usados"):

- Receita = `QUANTIDADE_VENDIDA × PRECO_UNIT_MEDIO` ([01_etl.py:175](../src/01_etl.py#L175)).
- Qtd. em unidade de estoque = `QUANTIDADE_VENDIDA × CONVERSAO_VENDA_PARA_ARMAZENAGEM` ([01_etl.py:177-179](../src/01_etl.py#L177-L179)).
- Saldo projetado = cumsum(estoque inicial + compras − vendas) ([02_estoque_projetado.py:69](../src/02_estoque_projetado.py#L69)).
- Dias de cobertura = `ESTOQUE_INICIAL / VENDA_MEDIA_DIARIA`; estoque parado = `VENDA_MEDIA_DIARIA ≤ ESTOQUE_INICIAL × 0,005`; risco de ruptura = `DIAS_COBERTURA < 15` e venda média > mediana (04_analise_estoque.py).
- Dispersão de preço (`amplitude_pct`, `cv_pct` sobre `PRECO_EMBALAGEM_0`) e correlação preço×volume mensal com filtro `n_obs ≥ 8` e limiar `< −0,4` ([05_precificacao.py:38-40](../src/05_precificacao.py#L38-L40), [86-99](../src/05_precificacao.py#L86-L99)).
- Projeção 2026 = tendência linear por produto × índice sazonal por categoria; estoque de segurança 30d; sugestão de compra = demanda + segurança ([06_projecao_compras.py:96-131](../src/06_projecao_compras.py#L96-L131)).
- Divergência dos números-título: Spec 00, "Riscos analíticos" #1 (−85% vs. −91,7% vs. −71,7%). `NÃO VALIDADO` qual é o oficial.
- Métricas citadas no relatório **sem fórmula nem script**: same-store YoY, YoY por categoria/loja, SKUs vendidos/mês (2.490→1.212), SKUs comprados/mês (74→14), correlação 0,49 (Spec 00, "Outputs existentes").

## Risco para o negócio

- Três números diferentes para "a queda" destroem a credibilidade do diagnóstico perante o negócio.
- Sem fórmula documentada, qualquer refatoração pode mudar silenciosamente um KPI e ninguém detecta.
- Limiares arbitrários não documentados (0,005 para estoque parado; 15 dias; −0,4 de correlação; `n_obs ≥ 8`) viram "regra de negócio de fato" sem nunca terem sido decididos pelo negócio.

## Arquivos de entrada

- `src/01_etl.py` … `src/07_recomendacoes.py` (fonte das fórmulas atuais);
- `outputs/tables/*.csv` (30 arquivos — valores herdados para conferência);
- `reports/relatorio_final.md` e `README.md` (fonte das afirmações a reconciliar);
- `data/processed/*.parquet` (para reproduzir os números com as fórmulas catalogadas).

## Arquivos de saída esperados

- `docs/metric_catalog.md` — por métrica: nome, objetivo, fórmula exata, tabela de origem, colunas, grão, filtros, unidade, periodicidade, limitações, nível de confiança, arquivo de output, seção do relatório, tipo (descritiva/diagnóstica/preditiva/recomendação).
- `docs/business_rules.md` — por regra: nome, descrição, fórmula, justificativa, tabelas/colunas, exceções, risco se errada, impacto no relatório, teste correspondente.
- `src/metrics.py` — funções puras, reutilizáveis e testáveis para as métricas principais.
- `tests/test_metrics.py`.

## Regras de negócio envolvidas

Regras mínimas a documentar (SDD.MD seção 10), todas com contrapartida real no repo:

1. Análise de estoque em unidade comum de armazenagem (hoje violada em compras — ver Spec 04).
2. Venda observada ≠ demanda real (hoje violada: `06` chama venda projetada de "demanda").
3. Saldo negativo ≠ ruptura física (hoje violada: `rupturas_estoque.csv`).
4. Nulo de estoque ≠ estoque zero.
5. Preço de compra nulo não entra em custo sem regra explícita.
6. Loja atípica (Loja 9/Salvador, +73%) deve ser segmentada, não escondida.
7. Comparações temporais respeitam sazonalidade (hoje violada: 1T24×4T25 mistura sazonalidades).
8. Correlação ≠ causalidade (hoje violada: "elasticidade").
9. Recomendações são triagens quando faltam dados críticos (margem, lead time etc. — `DADO AUSENTE`).

## Métricas afetadas

Catálogo mínimo (SDD.MD seção 10): receita bruta; quantidade vendida (unidade de venda e de armazenagem); ticket médio; preço médio; nº de linhas de venda (nota: não há ID de pedido — "nº de vendas" só pode ser linhas ou dias×loja, limitação a documentar); SKUs vendidos; receita por loja/categoria/estado; variação mensal e YoY; same-store YoY (ainda inexistente); dias com venda por loja/mês (inexistente); estoque inicial; compras registradas (nas duas unidades); saldo projetado; **gap contábil** (substitui "ruptura"); cobertura de compras e em dias; produtos vendidos sem compra; preço médio mensal; dispersão por loja; correlação preço-volume; venda observada projetada; estoque de segurança; compra bruta sugerida; candidatos a promoção/descontinuação/repricing com nível de confiança.

## Mudanças propostas

1. Catalogar **primeiro as métricas que já existem** no código, com fórmula exata e limiares atuais, marcando cada limiar como "escolha técnica não validada com o negócio".
2. Definir **um número oficial de queda de vendas** com janela e método explícitos, reconciliando −85%/−91,7%/−71,7% (mostrar os três cálculos e por que divergem).
3. Especificar as métricas citadas no relatório e ainda sem código (same-store YoY, SKUs/mês, correlação compras×vendas) — a implementação fica nas Specs 04/05.
4. Implementar `src/metrics.py` com funções puras (receita, ticket, preço médio, variação %, cobertura, gap contábil), com tratamento de divisão por zero e dados vazios.
5. Escrever `docs/business_rules.md` com as 9 regras mínimas + limiares herdados (0,005; 15 dias; −0,4; n≥8) e seus riscos.

## Testes necessários

`tests/test_metrics.py` deve validar:
- `docs/metric_catalog.md` e `docs/business_rules.md` existem e citam as métricas/regras mínimas;
- `src/metrics.py` existe com as funções principais;
- receita, quantidade, preço médio, ticket médio, variação %, cobertura e gap contábil calculados corretamente em fixtures;
- divisão por zero e DataFrame vazio tratados de forma controlada (sem exceção não tratada, sem `inf` silencioso);
- fórmulas testadas batem com o texto do catálogo (ex.: docstring/teste referencia a mesma fórmula).

## Critérios de aceite

- Nenhuma métrica usada no relatório fica sem entrada no catálogo;
- o número oficial da queda está definido, reproduzível e reconciliado com os três valores divergentes;
- todos os limiares herdados estão documentados como não validados com o negócio;
- `pytest tests/test_metrics.py` passa.

## O que não será feito

- Não serão alterados os scripts `01..07` (as fórmulas atuais são catalogadas como estão, mesmo quando erradas — a correção é das Specs 04–06).
- Não será recalculado nenhum output commitado.
- Não será reescrito o relatório (Spec 07).
- Não serão inventadas métricas sem contrapartida no repo ou no SDD.MD.

## Dúvidas ou bloqueios

- `NÃO VALIDADO` — Qual das três quedas é a "oficial"? A decisão de janela/método precisa ser tomada e registrada nesta spec (proposta: par mensal YoY + acumulado 12m, evitando comparar trimestres de sazonalidade diferente).
- `NÃO VALIDADO` — "Nº de vendas/pedidos" é impossível sem ID de transação; confirmar se linhas de venda são um proxy aceitável.
- `DADO AUSENTE` — Margem, custo, lead time, lote mínimo: métricas de recomendação final ficam bloqueadas (só triagem).
- Dependência: unicidade de grão (Spec 02) precisa estar respondida antes de congelar as fórmulas de receita/quantidade.
