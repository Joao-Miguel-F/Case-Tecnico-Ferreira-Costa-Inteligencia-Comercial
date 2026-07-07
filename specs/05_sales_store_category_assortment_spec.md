# Spec 05 — Vendas, lojas, categorias e sortimento

> Status: **IMPLEMENTADA / CONSOLIDADA** (entregáveis, outputs e testes confirmados na consolidação de 2026-07-07).
> Nota: o corpo abaixo preserva a especificação original; o resultado consolidado está em [docs/sales_store_category_assortment.md](../docs/sales_store_category_assortment.md).
> Base de evidência: [specs/00_current_state.md](00_current_state.md), [src/03_analise_vendas.py](../src/03_analise_vendas.py), [reports/relatorio_final.md](../reports/relatorio_final.md).

## Problema

O núcleo diagnóstico do relatório (Seção 2) **não é reproduzível**: same-store YoY, YoY por categoria, YoY por loja, "SKUs distintos vendidos por mês caíram de 2.490 para 1.212", "SKUs comprados por mês de 74 para 14" e a "correlação 0,49" entre SKUs comprados e vendidos **não têm script nem tabela** no repositório. Além disso:

1. As análises existentes em `03_analise_vendas.py` são agregados simples (ranking, categoria, loja/estado, sazonalidade) — não há comparação mês contra mesmo mês do ano anterior, nem identificação de lojas comparáveis, nem dias com venda por loja/mês.
2. A conclusão do relatório de que H4 ("sortimento vendido encolheu") está "Confirmada" ignora que a queda de SKUs vendidos pode ser consequência mecânica da queda de volume — não há análise de sortimento controlada por volume.
3. A afirmação de que a Loja 9 (Salvador) cresce +73% enquanto as demais caem é `NÃO VALIDADO` (sem tabela YoY por loja no repo).

## Evidência encontrada no repositório

- Spec 00, "Outputs existentes": lista dos 30 CSVs — nenhum contém same-store, YoY, SKUs/mês ou a correlação 0,49.
- Spec 00, "Riscos analíticos" #2: números centrais da Seção 2 sem lastro reexecutável.
- Outputs existentes de vendas: `vendas_mensais.csv`, `vendas_por_categoria_nivel1.csv`, `vendas_por_loja.csv`, `vendas_por_estado.csv`, `sazonalidade_por_categoria_mes.csv`, `ranking_produtos_completo.csv` — todos agregados do período inteiro ou mensais simples, sem YoY.
- Spec 00, "Principais hipóteses": H1 (fechamento de lojas) marcada "Rejeitada" pelo relatório sem análise de dias com venda/mês (o próprio SDD.MD alerta: presença de venda em algum mês não prova loja aberta o mês todo).
- `fato_vendas` não tem ID de transação (Spec 00, grão aparente) — "volume de transações" precisará ser proxy (linhas de venda ou dias×loja), limitação a documentar.

## Risco para o negócio

- As decisões de 2026 (sortimento, compras) apoiam-se em números que ninguém consegue recalcular; se estiverem errados, todo o plano herda o erro.
- Rejeitar H1 (fechamento de lojas) sem medir dias com venda pode esconder fechamentos parciais/temporários.
- Confirmar H4 sem controle de volume pode transformar um sintoma (menos volume ⇒ menos SKUs) em causa ("desabastecimento"), direcionando capital de compras para o problema errado.

## Arquivos de entrada

- `data/processed/fato_vendas.parquet` (com `RECEITA`, `QTD_VENDA_ESTOQUE`, `DATA_VENDA`);
- `data/processed/fato_compras.parquet` (para SKUs comprados/mês e correlação com SKUs vendidos);
- `data/processed/dim_produto.parquet` (`NIVEL_1` para categorias), `dim_lojas.parquet` (loja/cidade/estado);
- `outputs/tables/vendas_mensais.csv` (conferência de consistência com os novos cálculos).

## Arquivos de saída esperados

- `outputs/tables/vendas_same_store_yoy.csv` — por loja×mês: receita, quantidade, ticket médio, SKUs vendidos, dias com venda, variação vs. mesmo mês do ano anterior, flag de loja comparável/nova/incompleta.
- `outputs/tables/vendas_categorias_yoy.csv` — por categoria (`NIVEL_1`)×mês e ×trimestre vs. mesmo período do ano anterior, com classificação {queda generalizada, queda concentrada, crescimento, comportamento atípico, dados insuficientes}.
- `outputs/tables/sortimento_controlado_por_volume.csv` — SKUs observados/mês, linhas de venda/mês, SKUs esperados dado o volume (reamostragem do mix histórico), percentis/IC, flag de estreitamento além do esperado.
- `src/analysis/sales_analysis.py`, `src/analysis/assortment_analysis.py`.
- `tests/test_sales_analysis.py`, `tests/test_assortment_analysis.py`.

## Regras de negócio envolvidas

- YoY compara mês contra **mesmo mês** do ano anterior (jan/25 vs. jan/24); com 24 meses de dados (2024–2025), só há 12 pares YoY.
- Loja comparável = com venda em ambos os períodos comparados; lojas novas/incompletas marcadas, não descartadas silenciosamente.
- Ausência/presença de venda não prova fechamento/abertura operacional — medir dias com venda, meses sem venda, quedas abruptas.
- Loja atípica (candidata: Loja 9) segmentada, não escondida.
- Queda de SKUs vendidos só sustenta hipótese de estreitamento real se exceder o esperado dado o volume (pergunta central do SDD.MD seção 12).
- Novembro é pico sazonal (Black Friday) — não comparar períodos de sazonalidade diferente sem alerta.

## Métricas afetadas

- Receita/quantidade/ticket por loja e categoria (agora com variação YoY);
- SKUs vendidos por mês (nova série oficial — hoje o número 2.490→1.212 não tem fonte);
- Dias com venda por loja/mês (nova);
- Same-store sales YoY (nova);
- SKUs esperados dado o volume + intervalo (nova);
- Status das hipóteses H1–H4 do relatório (insumo direto da Spec 07).

## Mudanças propostas

1. Implementar `src/analysis/sales_analysis.py`: séries mensais por loja e categoria, YoY mês-contra-mesmo-mês, trimestre-contra-mesmo-trimestre, dias com venda, flags de comparabilidade e atipicidade.
2. Implementar `src/analysis/assortment_analysis.py`: SKUs distintos/mês, linhas/mês, reamostragem do mix histórico (ex.: bootstrap de linhas do período-base no volume do mês final) para estimar SKUs esperados com percentis.
3. Reproduzir (ou refutar) os números da Seção 2 do relatório: 2.490→1.212 SKUs vendidos/mês, 74→14 SKUs comprados/mês, correlação 0,49, Loja 9 +73% — cada um vira valor recalculado e rastreável.
4. Conferir consistência das novas séries mensais com `vendas_mensais.csv` (mesmos totais).

## Testes necessários

`tests/test_sales_analysis.py` e `tests/test_assortment_analysis.py` devem validar:
- os 3 CSVs de saída são gerados com colunas obrigatórias;
- YoY compara mês contra mesmo mês do ano anterior (fixture com 24 meses sintéticos);
- lojas comparáveis identificadas corretamente; lojas novas/incompletas flagadas;
- dias com venda calculados corretamente;
- classificação de categorias pertence às 5 classes esperadas;
- sortimento observado correto; sortimento esperado gerado com percentis/IC;
- queda de SKUs **não** gera automaticamente rótulo de ruptura/desabastecimento (vocabulário do output);
- totais mensais novos batem com `vendas_mensais.csv` (tolerância numérica).

## Critérios de aceite

- Todos os números da Seção 2 do relatório ou são reproduzidos com script rastreável ou são formalmente marcados como não reproduzidos;
- same-store YoY, YoY de categorias e sortimento controlado por volume existem como outputs;
- a resposta à pergunta "a queda de SKUs excede o esperado dado o volume?" está calculada com incerteza (percentis/IC);
- `pytest tests/test_sales_analysis.py tests/test_assortment_analysis.py` passa.

## O que não será feito

- Não será alterado `03_analise_vendas.py` nem regravados seus outputs (novas análises nascem em `src/analysis/`).
- Não será concluída causa da queda (demanda vs. disponibilidade) — isso é da Spec 07, com os insumos daqui e da Spec 04.
- Não será analisada margem/lucratividade (`DADO AUSENTE` — não há custo).
- Não será feito dashboard nem figura nova além das necessárias aos outputs (figuras são camada de apresentação, Spec 09).

## Dúvidas ou bloqueios

- `NÃO VALIDADO` — Sem ID de transação, o proxy de volume será linhas de venda; validar se a Seção 2 do relatório usou o mesmo proxy (não documentado).
- `NÃO VALIDADO` — Loja 9 +73%: pode não se reproduzir; se não, o relatório precisará ser corrigido (Spec 07).
- `DADO AUSENTE` — Calendário oficial de abertura/fechamento de lojas não existe no repo; conclusões sobre fechamento permanecerão inferenciais.
- Dependência: grão de `fato_vendas` validado na Spec 02 (duplicidade mudaria SKUs/mês e volumes) e unidades da Spec 04 para quantidades em unidade de estoque.
