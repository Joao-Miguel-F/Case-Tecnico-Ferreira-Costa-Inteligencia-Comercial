# Regras de negocio - Spec 03

Status: Spec 03. Estas regras documentam como interpretar as metricas antes de novas analises. Cada regra tem teste automatizado correspondente em `tests/test_metrics.py`.

## 1. Unidade comum de armazenagem

- Nome: Toda analise de estoque deve usar unidade comum de armazenagem.
- Descricao: vendas, compras e estoque so podem ser comparados depois de convertidos para a unidade de estoque.
- Formula: venda em armazenagem = `QUANTIDADE_VENDIDA * CONVERSAO_VENDA_PARA_ARMAZENAGEM`; compra em armazenagem = `QUANTIDADE_COMPRA * CONVERSAO_COMPRA_ARMAZENAGEM`.
- Justificativa: `QUANTIDADE_COMPRA` esta em embalagem de compra do fornecedor; 226 produtos tem conversao de compra diferente de 1, risco latente medido pela Spec 02.
- Tabelas/colunas: `fato_vendas.QUANTIDADE_VENDIDA`, `fato_vendas.CONVERSAO_VENDA_PARA_ARMAZENAGEM`, `fato_compras.QUANTIDADE_COMPRA`, `dim_produto.CONVERSAO_COMPRA_ARMAZENAGEM`, `fato_estoque_inicial.ESTOQUE_INICIAL`.
- Excecoes: no dado atual, 0 das 1.393 compras registradas exigem conversao diferente de 1, mas isso nao autoriza manter a formula errada.
- Risco se errada: saldo, cobertura, compras sugeridas e gap contabil misturam caixas/unidades.
- Impacto no relatorio: conclusoes de ruptura/reposicao ficam invalidas ou degradadas ate a Spec 04 corrigir o uso.
- Teste automatizado correspondente: `test_quantidade_compra_armazenagem_aplica_conversao`.

## 2. Venda observada nao e demanda real

- Nome: Venda observada nao e demanda real.
- Descricao: vendas registradas medem o que foi vendido, nao o que o cliente teria comprado se houvesse disponibilidade e preco ideais.
- Formula: demanda real = `DADO AUSENTE`; venda observada = `sum(QTD_VENDA_ESTOQUE)`.
- Justificativa: nao ha pedidos perdidos, disponibilidade em gondola, ruptura fisica validada ou estoque atual confiavel.
- Tabelas/colunas: `fato_vendas`, `estoque_diario`, `projecao_demanda_2026.csv` legado.
- Excecoes: pode-se projetar venda observada, desde que o nome nao seja "demanda potencial".
- Risco se errada: recomendacoes de compra podem perpetuar falta de disponibilidade ou superestimar demanda.
- Impacto no relatorio: a projecao de 2026 deve ser lida como venda observada projetada.
- Teste automatizado correspondente: `test_business_rules_document_all_minimum_rules`.

## 3. Saldo negativo nao prova ruptura fisica

- Nome: Saldo negativo e gap contabil, nao ruptura fisica.
- Descricao: quando vendas conhecidas superam estoque inicial e compras conhecidas, a conclusao valida e lacuna de entradas, nao ruptura real.
- Formula: `gap_contabil_estoque = max(vendas_armazenagem - estoque_inicial - compras_armazenagem, 0)`.
- Justificativa: qualidade mediu venda maior que entradas conhecidas em 83,7% dos pares produto x loja e saldo negativo em 74,3% do `estoque_diario`.
- Tabelas/colunas: `fato_vendas.QTD_VENDA_ESTOQUE`, `fato_estoque_inicial.ESTOQUE_INICIAL`, `fato_compras.QUANTIDADE_COMPRA`, `dim_produto.CONVERSAO_COMPRA_ARMAZENAGEM`.
- Excecoes: ruptura fisica exige evidencia operacional adicional, ausente nesta fase.
- Risco se errada: relatorio transforma problema de dados/contabilidade em diagnostico operacional falso.
- Impacto no relatorio: outputs legados com "ruptura" devem ser reinterpretados como gap contabil ate a Spec 04.
- Teste automatizado correspondente: `test_gap_contabil_clip_positivo`.

## 4. Nulo de estoque nao e estoque zero

- Nome: Nulo de estoque nao e automaticamente estoque zero.
- Descricao: ausencia de registro/informacao nao pode ser imputada como zero; zero explicito tambem deve ser tratado com cuidado.
- Formula: `ESTOQUE_INICIAL nulo -> DADO AUSENTE`; `ESTOQUE_INICIAL = 0` -> zero explicito, nao nulo.
- Justificativa: 47,6% do estoque inicial e zero explicito; isso nao prova ausencia fisica se houver falha de inventario.
- Tabelas/colunas: `fato_estoque_inicial.ESTOQUE_INICIAL`.
- Excecoes: a base atual nao tem nulos em estoque inicial, mas a regra vale para novas cargas.
- Risco se errada: cobertura de dias e risco de ruptura ficam artificialmente extremos.
- Impacto no relatorio: cobertura e estoque parado tem confianca baixa/media, nao prova de disponibilidade.
- Teste automatizado correspondente: `test_business_rules_document_all_minimum_rules`.

## 5. Preco de compra nulo bloqueia CMV sem regra

- Nome: Preco de compra nulo nao entra no CMV sem regra explicita.
- Descricao: compras sem `PRECO_UNIT_UNIDADE_COMPRA` nao podem ser usadas para custo, margem ou CMV por imputacao silenciosa.
- Formula: CMV = `BLOQUEADA` enquanto nulos nao tiverem regra aprovada.
- Justificativa: 132 compras sem preco (9,5%) foram classificadas como FAIL na Spec 02.
- Tabelas/colunas: `fato_compras.PRECO_UNIT_UNIDADE_COMPRA`, `fato_compras.QUANTIDADE_COMPRA`.
- Excecoes: analises de quantidade de compra podem prosseguir sem custo; analises financeiras nao.
- Risco se errada: margem e recomendacoes financeiras ficam enviesadas.
- Impacto no relatorio: recomendacoes de promocao/descontinuacao nao devem ser decisao financeira final.
- Teste automatizado correspondente: `test_metric_catalog_marks_blocked_and_absent_items`.

## 6. Loja atipica segmentada

- Nome: Loja atipica deve ser segmentada, nao escondida.
- Descricao: loja com comportamento divergente deve aparecer separada nos agregados e diagnosticos.
- Formula: analise geral + analise segmentada para `COD_EMPRESA` atipico; no legado, Loja 9/Salvador cresce +73%.
- Justificativa: medias consolidadas podem mascarar padroes opostos.
- Tabelas/colunas: `fato_vendas.COD_EMPRESA`, `dim_lojas.CD_CIDADE`, `dim_lojas.CD_ESTADO`.
- Excecoes: nenhum corte deve excluir a loja sem declarar o filtro.
- Risco se errada: conclusoes "todas as lojas caem" ficam falsas ou incompletas.
- Impacto no relatorio: H3 deve declarar a loja atipica e seu tratamento.
- Teste automatizado correspondente: `test_business_rules_document_all_minimum_rules`.

## 7. Comparacoes temporais respeitam sazonalidade

- Nome: Comparacoes temporais devem respeitar sazonalidade.
- Descricao: quedas e crescimentos devem comparar janelas equivalentes ou declarar a diferenca sazonal.
- Formula: YoY recomendado = `(valor_mes_ano_atual - valor_mes_ano_anterior) / valor_mes_ano_anterior` para mesmo mes; trimestre deve comparar trimestre equivalente.
- Justificativa: novembro tem Black Friday; 1T24 x 4T25 mistura sazonalidades.
- Tabelas/colunas: `fato_vendas.DATA_VENDA`, `RECEITA`, `QTD_VENDA_ESTOQUE`.
- Excecoes: comparacoes nao sazonais podem ser exploratorias se rotuladas.
- Risco se errada: numero oficial da queda vira dependente da janela escolhida.
- Impacto no relatorio: -85%, -91,7% e -71,7% precisam de reconciliacao por janela/metodo.
- Teste automatizado correspondente: `test_variacao_percentual_calcula_e_bloqueia_base_zero`.

## 8. Correlacao nao e causalidade

- Nome: Correlacao nao e causalidade.
- Descricao: correlacao preco-volume sinaliza investigacao, nao elasticidade nem efeito causal.
- Formula: `corr(preco_medio_mensal, quantidade_mensal), n_obs >= 8`; limiar legado forte `< -0,4`.
- Justificativa: preco, mix, disponibilidade, sazonalidade e loja podem variar juntos.
- Tabelas/colunas: vendas mensais, `PRECO_UNIT_MEDIO`, `QUANTIDADE_VENDIDA`, `dim_precos.PRECO_EMBALAGEM_0`.
- Excecoes: causalidade exige desenho adicional, fora desta spec.
- Risco se errada: repricing pode ser recomendado com base em relacao espuria.
- Impacto no relatorio: trocar "elasticidade" por "candidato a investigacao de preco".
- Teste automatizado correspondente: `test_correlacao_preco_volume_respeita_minimo_observacoes`.

## 9. Recomendacoes sao triagens

- Nome: Recomendacoes sao triagens quando faltam dados criticos.
- Descricao: listas de promocao, descontinuacao, repricing e compra nao sao decisoes finais sem margem, lead time, estoque confiavel, lote minimo e validacao comercial.
- Formula: recomendacao final = `BLOQUEADA` quando faltar dado critico; recomendacao atual = triagem com nivel de confianca baixo.
- Justificativa: dados criticos estao ausentes ou degradados; compra liquida depende da Spec 04.
- Tabelas/colunas: outputs de `src/07_recomendacoes.py`, projecoes, precos e estoque.
- Excecoes: triagens podem priorizar investigacao manual.
- Risco se errada: a empresa executa acoes operacionais sem evidencia suficiente.
- Impacto no relatorio: sumario executivo deve rotular listas como triagem.
- Teste automatizado correspondente: `test_metric_catalog_covers_minimum_metric_families`.

## Limiares herdados nao validados

- Estoque parado: `VENDA_MEDIA_DIARIA <= ESTOQUE_INICIAL * 0,005`.
- Risco de ruptura legado: `DIAS_COBERTURA < 15` e venda media acima da mediana. Deve ser relido como risco/gap, nao ruptura provada.
- Correlacao forte legada: `< -0,4`.
- Minimo de observacoes para correlacao: `n_obs >= 8`.

Todos esses limiares sao escolhas tecnicas herdadas e NAO VALIDADO com o negocio nesta spec.
