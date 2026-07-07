# Vendas, lojas, categorias e sortimento - Spec 05

Status: Spec 05 implementada em 2026-07-07.

Esta etapa criou analises auditaveis de vendas, lojas, categorias e sortimento
observado. Ela nao altera scripts legados, nao regrava dados brutos, nao cria
dashboard e nao altera `reports/relatorio_final.md`.

## Entradas usadas

- `data/processed/fato_vendas.parquet`
- `data/processed/dim_lojas.parquet`
- `data/processed/dim_produto.parquet`
- `outputs/tables/data_quality_report.csv`
- `outputs/tables/compras_coverage_audit.csv`

Premissas herdadas: `fato_vendas` tem grao produto x loja x dia x embalagem,
sem duplicatas; nao existe ID de cupom/pedido; contagens de linhas sao
`linhas de venda diarias`; `RECEITA` e `QTD_VENDA_ESTOQUE` ja foram validadas.

## Outputs gerados

### `outputs/tables/vendas_same_store_yoy.csv`

Grao: loja x mes.

Principais campos:

- `receita`, `qtd_vendida_estoque`, `linhas_venda_diarias`,
  `skus_vendidos`, `dias_com_venda`;
- valores do mesmo mes do ano anterior com sufixo `_ano_anterior`;
- variacoes YoY de receita, quantidade em estoque, linhas e dias com venda;
- `loja_comparavel_yoy`;
- `status_loja_mes`;
- `interpretacao_dias_com_venda`.

Definicao de loja comparavel: loja com ao menos uma linha de venda diaria no mes
atual e no mesmo mes do ano anterior. A flag nao prova abertura operacional da
loja; ela apenas define se a comparacao YoY tem observacao dos dois lados.

Resultado observado em 2025: 130 de 132 pares loja-mes sao comparaveis. Os dois
pares nao comparaveis sao loja 9 em 2025-01 e 2025-02, pois nao havia venda nos
mesmos meses de 2024.

Dias com venda: `count_distinct(DATA_VENDA)` por loja x mes, contando dias em que
houve ao menos uma linha de venda. Ausencia de venda nao e tratada como prova de
fechamento operacional.

Resultado anual por loja: a afirmacao antiga de que a loja 9 cresceu +73% nao se
reproduz neste calculo anual 2025 vs 2024. A loja 9 cai cerca de -30,6% em
receita anual observada. Essa divergencia fica `NAO VALIDADO` ate a janela e o
metodo usados no relatorio antigo serem explicitados.

### `outputs/tables/vendas_categorias_yoy.csv`

Grao: categoria (`NIVEL_1`) x periodo, com duas periodicidades:

- `mes`: mes contra mesmo mes do ano anterior;
- `trimestre`: trimestre contra mesmo trimestre do ano anterior.

Classificacoes permitidas:

- `dados insuficientes`: falta base YoY, base zero ou periodo atual sem receita;
- `crescimento`: receita YoY positiva;
- `queda concentrada`: categoria em queda que responde por pelo menos 10% da
  queda de receita do periodo;
- `queda generalizada`: categoria em queda, mas sem concentrar sozinha a perda;
- `comportamento atipico`: variacao da categoria diverge muito da variacao total
  do periodo.

Resultado mensal de 2025:

- `queda generalizada`: 206 linhas;
- `crescimento`: 38 linhas;
- `queda concentrada`: 23 linhas;
- `comportamento atipico`: 9 linhas.

As categorias de 2024 ficam como `dados insuficientes` porque nao ha 2023 na
base contratada.

### `outputs/tables/sortimento_controlado_por_volume.csv`

Grao: mes.

Campos principais:

- `skus_observados`;
- `linhas_venda_diarias`;
- `qtd_vendida_estoque`;
- `mes_referencia_mix`;
- `linhas_referencia_mix`;
- `skus_esperados_media`;
- `skus_esperados_p05`, `skus_esperados_p50`, `skus_esperados_p95`;
- `status_sortimento_controlado`.

Metodo: para cada mes de 2025, o controle usa o mix de linhas do mesmo mes de
2024 como distribuicao de referencia. O numero de linhas de venda diarias do mes
atual vira o tamanho da amostra. Foram usadas 120 iteracoes de bootstrap com
semente fixa para estimar o sortimento esperado e seus percentis.

Interpretacao: queda de SKUs vendidos e evidencia descritiva de sortimento
observado menor. Ela nao prova, por si so, demanda real menor, ruptura fisica ou
desabastecimento. A classificacao indica se o numero de SKUs observados ficou
abaixo/acima do esperado dado o volume de linhas e o mix historico.

Resultados relevantes:

- 2024-11: 2.490 SKUs observados e 71.525 linhas de venda diarias.
- 2025-12: 1.212 SKUs observados e 12.258 linhas de venda diarias.
- Controle de 2025-12 contra mix de 2024-12: media esperada de 1.849,5 SKUs,
  p05 de 1.827,0 e p95 de 1.875,1.
- 2025-12 ficou como `estreitamento_alem_do_esperado`.

Status nos 24 meses:

- `DADO AUSENTE`: 12 meses de 2024, pois falta referencia de 2023;
- `ampliacao_alem_do_esperado`: 4 meses;
- `dentro_do_esperado`: 1 mes;
- `estreitamento_alem_do_esperado`: 7 meses.

## Numeros citados no relatorio antigo

- SKUs vendidos por mes: reproduzido como 2.490 em 2024-11 e 1.212 em 2025-12.
- SKUs comprados por mes: usando `fato_compras`, janeiro/2024 tem 74 SKUs
  distintos comprados e dezembro/2025 tem 5. O valor "14" citado anteriormente
  nao se reproduz para dezembro/2025 nesta extracao. `NAO VALIDADO`.
- Correlacao mensal entre SKUs vendidos e SKUs comprados: 0,4934, reproduzindo
  aproximadamente a correlacao 0,49 citada. Esta correlacao e apenas descritiva.
  A Spec 04 classifica compras como base de baixa cobertura e nao confiavel para
  analise causal.

## Itens remanescentes

- `DADO AUSENTE`: calendario oficial de abertura/fechamento de lojas.
- `DADO AUSENTE`: ID de cupom, pedido ou transacao.
- `DADO AUSENTE`: disponibilidade fisica, estoque final real, transferencias,
  ajustes e devolucoes.
- `NAO VALIDADO`: janela/metodo que gerou a afirmacao antiga de loja 9 +73%.
- `NAO VALIDADO`: valor antigo "14 SKUs comprados por mes"; no dado atual,
  dezembro/2025 tem 5 SKUs distintos comprados e 9 linhas de compra.
- `BLOQUEADO`: conclusao causal de que compras causaram queda de vendas ou
  sortimento, pela baixa cobertura da base de compras documentada na Spec 04.

## Testes

Arquivos criados:

- `tests/test_sales_analysis.py`
- `tests/test_assortment_analysis.py`

Os testes validam YoY contra mesmo mes do ano anterior, lojas comparaveis,
dias com venda, classificacoes de categorias, controle de sortimento por volume,
geracao dos CSVs e consistencia dos totais mensais com `vendas_mensais.csv`.

