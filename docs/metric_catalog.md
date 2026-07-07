# Catalogo de metricas - Spec 03

Status: Spec 03. Este catalogo documenta formulas e limites de uso. Ele nao executa analises novas, nao recalcula outputs e nao corrige os scripts legados.

Fontes: `SDD.MD` secao 10, `specs/03_metrics_business_rules_spec.md`, `docs/data_contract.md`, `outputs/tables/data_quality_report.csv` e `specs/00_current_state.md` secao "Principais KPIs usados".

## Premissas obrigatorias

- Periodo contratado: jan/2024 a dez/2025.
- Grao validado de `fato_vendas`: produto x loja x dia x embalagem, 0 duplicatas em 1.090.390 linhas.
- Nao existe ID de cupom/pedido/transacao. Qualquer contagem herdada como "numero de vendas" deve ser chamada de linhas de venda diarias.
- `RECEITA = QUANTIDADE_VENDIDA * PRECO_UNIT_MEDIO` e `QTD_VENDA_ESTOQUE = QUANTIDADE_VENDIDA * CONVERSAO_VENDA_PARA_ARMAZENAGEM` estao validadas pela Spec 02.
- `QUANTIDADE_COMPRA` esta em embalagem de compra do fornecedor; compras em unidade comum usam `QUANTIDADE_COMPRA * CONVERSAO_COMPRA_ARMAZENAGEM`.
- Saldo negativo e venda acima das entradas conhecidas sao gap contabil, nunca prova de ruptura fisica.
- Metricas de custo, margem e CMV ficam BLOQUEADAS enquanto 132 compras (9,5%) nao tiverem `PRECO_UNIT_UNIDADE_COMPRA` ou regra explicita de imputacao.
- Cobertura de compras e conclusoes causais sobre reposicao tem confianca baixa: compras cobrem 7/11 lojas e 329/2.731 produtos.
- Preco 0 em `PRECO_EMBALAGEM_1/2` significa sem preco valido para analises de preco.
- Correlacao preco-volume nao e elasticidade; use "candidato a investigacao de preco".

## Formula IDs do codigo

As formulas abaixo devem bater com `src/metrics.py::FORMULAS`.

| Formula ID | Formula documentada |
|---|---|
| receita_bruta | `sum(QUANTIDADE_VENDIDA * PRECO_UNIT_MEDIO)` |
| quantidade_vendida | `sum(QUANTIDADE_VENDIDA)` |
| quantidade_vendida_armazenagem | `sum(QUANTIDADE_VENDIDA * CONVERSAO_VENDA_PARA_ARMAZENAGEM)` |
| linhas_venda_diarias | `count(fato_vendas rows)` |
| ticket_medio_linha | `receita_bruta / linhas_venda_diarias` |
| preco_medio_vendido | `receita_bruta / quantidade_vendida` |
| variacao_percentual | `(valor_atual - valor_base) / valor_base` |
| compras_armazenagem | `sum(QUANTIDADE_COMPRA * CONVERSAO_COMPRA_ARMAZENAGEM)` |
| entradas_conhecidas | `estoque_inicial + compras_armazenagem` |
| saldo_projetado | `estoque_inicial + compras_armazenagem - vendas_armazenagem` |
| gap_contabil_estoque | `max(vendas_armazenagem - estoque_inicial - compras_armazenagem, 0)` |
| cobertura_dias | `estoque_inicial / venda_media_diaria` |
| cobertura_compras_lojas | `lojas_com_compra / total_lojas` |
| cobertura_compras_produtos | `produtos_com_compra / total_produtos` |
| preco_valido | `PRECO_EMBALAGEM_n > 0` |
| correlacao_preco_volume | `corr(preco_medio_mensal, quantidade_mensal), n_obs >= 8` |

## Vendas

| Metrica | Objetivo de negocio | Formula exata | Origem e colunas | Grao | Filtros | Unidade e periodicidade | Limitacoes | Confianca | Output | Relatorio | Tipo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Receita bruta | Medir valor vendido observado. | `sum(QUANTIDADE_VENDIDA * PRECO_UNIT_MEDIO)` | `fato_vendas`: `QUANTIDADE_VENDIDA`, `PRECO_UNIT_MEDIO`; processado tambem tem `RECEITA`. | Produto x loja x dia x embalagem; agregavel. | Periodo valido 2024-2025; preco > 0 ja validado. | BRL; diaria, mensal, anual. | Receita observada, nao margem. | Alta | `outputs/tables/vendas_mensais.csv`, rankings de vendas. | Secoes de vendas e resumo executivo. | Descritiva |
| Quantidade vendida | Medir volume na unidade de venda original. | `sum(QUANTIDADE_VENDIDA)` | `fato_vendas`: `QUANTIDADE_VENDIDA`. | Produto x loja x dia x embalagem. | Quantidade > 0 validada. | Unidade de venda; diaria/mensal. | Mistura unidades se agregada entre embalagens/produtos. | Alta no grao; Media em agregacoes amplas | Outputs de vendas e sazonalidade. | Secoes de vendas/sazonalidade. | Descritiva |
| Quantidade vendida em unidade de armazenagem | Comparar vendas com estoque/compras em unidade comum. | `sum(QUANTIDADE_VENDIDA * CONVERSAO_VENDA_PARA_ARMAZENAGEM)` | `fato_vendas`: `QUANTIDADE_VENDIDA`, `CONVERSAO_VENDA_PARA_ARMAZENAGEM`; processado `QTD_VENDA_ESTOQUE`. | Produto x loja x dia x embalagem. | Conversao > 0; 3.725 linhas com possivel conversao faltante ficam WARN. | Unidade de estoque; diaria/mensal. | Depende da conversao cadastrada. | Alta com WARN pontual | `fato_vendas.parquet`, outputs de estoque. | Estoque, giro e rankings. | Descritiva |
| Ticket medio por linha diaria | Proxy de valor medio por linha agregada. | `receita_bruta / linhas_venda_diarias` | `fato_vendas`: receita calculada e contagem de linhas. | Linha diaria agregada, nao cupom. | Denominador zero -> indefinido. | BRL por linha; mensal/anual. | Nao e ticket medio de cupom; nao ha ID de transacao. | Baixa como ticket; Alta como receita/linha | Rankings legados. | Sumario/rankings quando citado. | Descritiva |
| Preco medio vendido | Preco medio ponderado pelo volume vendido. | `receita_bruta / quantidade_vendida` | `fato_vendas`: `QUANTIDADE_VENDIDA`, `PRECO_UNIT_MEDIO`. | Produto/loja/periodo agregado. | Denominador zero -> indefinido. | BRL por unidade de venda; mensal. | `PRECO_UNIT_MEDIO` ja e media diaria; agregacao deve ser ponderada. | Alta | Analises de preco/vendas. | Precificacao. | Descritiva |
| Numero de vendas/pedidos | Contar cupons ou pedidos reais. | `DADO AUSENTE`: requer ID de pedido/cupom inexistente. | Nenhuma coluna disponivel. | Nao disponivel. | Nao aplicavel. | Pedidos/cupons. | BLOQUEADA; nao substituir por count sem renomear. | BLOQUEADA | Nenhum output confiavel. | Qualquer mencao a "transacoes". | Descritiva |
| Linhas de venda diarias | Contar registros agregados de venda. | `count(fato_vendas rows)` | `fato_vendas`: linhas no grao validado. | Produto x loja x dia x embalagem. | Nenhum alem do periodo. | Linhas; diaria/mensal. | Nao e numero de cupons/pedidos. | Alta | Rankings legados com `count`. | Transacoes legadas devem ser renomeadas. | Descritiva |
| SKUs vendidos | Medir sortimento com venda observada. | `count_distinct(CODIGO com venda)` | `fato_vendas`: `CODIGO`. | Produto por periodo/loja/categoria. | Somente vendas observadas. | SKUs; mensal/anual. | Nao mede disponibilidade nem demanda. Numeros do relatorio sem script ficam NAO VALIDADO. | Media | Citado no relatorio; output direto nao identificado para todos os recortes. | H4/sortimento vendido. | Diagnostica |
| Receita por loja | Comparar desempenho entre lojas. | `sum(RECEITA) group by COD_EMPRESA` | `fato_vendas`, `dim_lojas`: `COD_EMPRESA`, `CD_CIDADE`, `CD_ESTADO`. | Loja x periodo. | 0 orfaos de loja. | BRL; mensal/anual. | Loja 9/Salvador atipica deve ser segmentada. | Alta | `receita_por_loja.csv` ou equivalente legado. | Analise por loja/estado. | Descritiva |
| Receita por categoria | Comparar familias mercadologicas. | `sum(RECEITA) group by NIVEL_1` | `fato_vendas` + `dim_produto`: `CODIGO`, `NIVEL_1`. | Categoria x periodo. | 0 orfaos de produto. | BRL; mensal/anual. | Hierarquia cadastral; nao reconcilia `dim_precos.CATEGORIA` nesta spec. | Alta | `receita_por_categoria.csv` ou equivalente legado. | Analise por categoria. | Descritiva |
| Receita same-store YoY | Comparar lojas comparaveis ano contra ano. | `(receita_periodo_atual_same_store - receita_periodo_base_same_store) / receita_periodo_base_same_store` | `fato_vendas`, `dim_lojas`. | Loja comparavel x mes/ano. | Apenas lojas presentes nos dois periodos; sazonalidade igual. | Percentual; YoY. | Citada sem script/output reprodutivel. Definicao de same-store ainda NAO VALIDADA. | NAO VALIDADO | Nenhum output reprodutivel identificado. | H2/H3 quando usado. | Diagnostica |
| Variacao mensal | Medir mudanca sequencial. | `(valor_mes - valor_mes_anterior) / valor_mes_anterior` | Serie mensal de receita/quantidade. | Mes. | Base zero -> indefinido; destacar novembro/Black Friday. | Percentual mensal. | Pode confundir sazonalidade com tendencia. | Media | `vendas_mensais.csv`. | Queda de vendas. | Diagnostica |
| Variacao YoY | Medir mudanca contra mesmo periodo do ano anterior. | `(valor_periodo_ano_atual - valor_periodo_ano_anterior) / valor_periodo_ano_anterior` | Serie mensal/trimestral/anual de vendas. | Mes ou periodo sazonalmente comparavel. | Mes contra mesmo mes; trimestre contra mesmo trimestre. | Percentual YoY. | Numero oficial da "queda" precisa declarar janela; -85%, -91,7% e -71,7% eram janelas diferentes. | Media | `vendas_mensais.csv`; relatorio. | Queda de vendas. | Diagnostica |
| Dias com venda por loja/mes | Medir atividade operacional por loja. | `count_distinct(DATA_VENDA) group by COD_EMPRESA, ANO_MES` | `fato_vendas`: `DATA_VENDA`, `COD_EMPRESA`. | Loja x mes. | Dias com pelo menos uma linha de venda. | Dias; mensal. | Nao distingue loja fechada de ausencia de venda sem calendario operacional. | Media | Nao existe output legado dedicado. | Operacao/same-store. | Diagnostica |

## Compras e estoque

| Metrica | Objetivo de negocio | Formula exata | Origem e colunas | Grao | Filtros | Unidade e periodicidade | Limitacoes | Confianca | Output | Relatorio | Tipo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Estoque inicial | Base conhecida de posicao inicial. | `sum(ESTOQUE_INICIAL)` | `fato_estoque_inicial`: `ESTOQUE_INICIAL`. | Produto x loja. | Zero explicito mantido; nulo nao deve virar zero. | Unidade de estoque; posicao inicial. | 47,6% zeros explicitos; sem confirmacao de inventario. | Media | `fato_estoque_inicial.parquet`, cobertura. | Estoque/cobertura. | Descritiva |
| Compras registradas | Medir entradas registradas no dado disponivel. | `sum(QUANTIDADE_COMPRA)` | `fato_compras`: `QUANTIDADE_COMPRA`. | Produto x loja x data x embalagem fornecedor. | Quantidade > 0 validada. | Embalagem de compra; diaria/mensal. | Cobertura estrutural baixa; nao usar como universo completo. | Baixa | Outputs de compras legados. | H5/reposicao. | Descritiva |
| Compras em unidade de armazenagem | Comparar compras com vendas/estoque. | `sum(QUANTIDADE_COMPRA * CONVERSAO_COMPRA_ARMAZENAGEM)` | `fato_compras` + `dim_produto`: `QUANTIDADE_COMPRA`, `CONVERSAO_COMPRA_ARMAZENAGEM`. | Produto x loja x data x embalagem fornecedor. | Join por `CODIGO`; conversao > 0. | Unidade de estoque; diaria/mensal. | Pipeline legado ainda nao aplica esta conversao; correcao e Spec 04. | Media como formula; Baixa como cobertura | Nao recalculado nesta spec. | Estoque/reconciliacao. | Descritiva |
| Estoque inicial + compras | Medir entradas conhecidas. | `estoque_inicial + compras_armazenagem` | `fato_estoque_inicial`, `fato_compras`, `dim_produto`. | Produto x loja/periodo. | Compras convertidas. | Unidade de estoque. | Entradas incompletas: faltam transferencias, ajustes, compras nao capturadas. | Baixa | Estoque projetado legado, com ressalva. | H5/estoque. | Diagnostica |
| Vendas acumuladas | Comparar saidas conhecidas. | `sum(QTD_VENDA_ESTOQUE) acumulado por produto x loja` | `fato_vendas.parquet`: `QTD_VENDA_ESTOQUE`. | Produto x loja x data. | Periodo ordenado. | Unidade de estoque; diaria acumulada. | Venda observada nao e demanda real. | Alta | `estoque_diario.parquet`. | Estoque/giro. | Descritiva |
| Saldo projetado | Saldo contabil conhecido pelo dado disponivel. | `estoque_inicial + compras_armazenagem - vendas_armazenagem` | Estoque, compras convertidas, vendas convertidas. | Produto x loja x data/periodo. | Nunca interpretar negativo como ruptura. | Unidade de estoque. | Baixa cobertura de entradas; legado mistura unidade de compra. | Baixa | `estoque_diario.parquet`, `estoque_final_projetado.parquet`. | Estoque. | Diagnostica |
| Gap contabil de estoque | Quantificar venda acima das entradas conhecidas. | `max(vendas_armazenagem - estoque_inicial - compras_armazenagem, 0)` | Estoque, compras convertidas, vendas convertidas. | Produto x loja/periodo. | Gap negativo vira 0. | Unidade de estoque. | Mede lacuna contabil, nao ruptura fisica. | Alta como gap; BLOQUEADA como ruptura | Quality report; novo nome para outputs de ruptura legados. | Estoque e riscos. | Diagnostica |
| Cobertura de compras | Medir completude da base de compras. | `lojas_com_compra / total_lojas`; `produtos_com_compra / total_produtos` | `fato_compras`, `dim_lojas`, `dim_produto`. | Loja/produto no periodo completo. | Alguma compra no periodo. | Percentual; periodo 2024-2025. | Nao mede valor comprado, so cobertura. | Alta | `data_quality_report.csv`. | Limitacoes/H5. | Diagnostica |
| Cobertura em dias | Estimar dias cobertos pelo estoque inicial. | `estoque_inicial / venda_media_diaria` | `cobertura_estoque.parquet`, vendas e estoque. | Produto x loja. | Denominador zero -> indefinido. | Dias. | 47,6% estoque inicial zero; venda observada pode estar censurada. | Baixa | `cobertura_estoque.parquet`. | Estoque parado/risco. | Diagnostica |
| Produtos vendidos sem compra registrada | Evidenciar entradas faltantes. | `count_distinct(CODIGO, COD_EMPRESA com venda > 0 e compras_armazenagem = 0)` | `fato_vendas`, `fato_compras`. | Produto x loja. | Periodo completo. | Pares produto x loja. | Pode haver estoque inicial ou transferencias; nao e ruptura. | Alta como indicador de lacuna | `data_quality_report.csv`. | Limitacoes de reposicao. | Diagnostica |
| Produtos vendidos acima das entradas conhecidas | Medir desbalanco contabil. | `vendas_armazenagem > estoque_inicial + compras_armazenagem` | Vendas, estoque, compras. | Produto x loja. | Entradas conhecidas convertidas. | Pares/proporcao; periodo. | Gap contabil generalizado; nao causalidade. | Alta como gap | `data_quality_report.csv`. | Limitacoes de estoque. | Diagnostica |
| Custo, CMV e margem | Medir rentabilidade. | `BLOQUEADA`: requer preco de compra completo ou imputacao aprovada. | `fato_compras.PRECO_UNIT_UNIDADE_COMPRA`. | Produto/loja/periodo. | 132 nulos impedem CMV confiavel. | BRL. | Sem regra explicita, nao calcular. | BLOQUEADA | Nenhum output confiavel. | Recomendacoes financeiras. | Diagnostica |

## Precificacao

| Metrica | Objetivo de negocio | Formula exata | Origem e colunas | Grao | Filtros | Unidade e periodicidade | Limitacoes | Confianca | Output | Relatorio | Tipo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Preco medio mensal | Acompanhar preco praticado vendido. | `sum(RECEITA) / sum(QUANTIDADE_VENDIDA)` por mes | `fato_vendas`: `PRECO_UNIT_MEDIO`, `QUANTIDADE_VENDIDA`. | Produto/loja/mes. | Quantidade > 0. | BRL por unidade de venda; mensal. | Media ponderada de medias diarias. | Alta | Analises de precificacao. | Precificacao. | Descritiva |
| Variacao de preco | Medir alteracao de preco entre periodos. | `(preco_atual - preco_base) / preco_base` | Preco medio mensal ou `dim_precos`. | Produto/loja/mes. | Base zero/invalida -> indefinido. | Percentual. | Usar mesma embalagem e tratar preco 0 como invalido. | Media | Outputs de precos. | Precificacao. | Diagnostica |
| Dispersao de preco por loja | Detectar variacao de tabela entre lojas. | `amplitude_pct = (max(PRECO_EMBALAGEM_0)-min(PRECO_EMBALAGEM_0))/min(PRECO_EMBALAGEM_0)`; `cv_pct = std/mean` | `dim_precos`: `PRECO_EMBALAGEM_0`, `COD_EMPRESA`, `CODIGO`. | Produto entre lojas. | Precos validos > 0. | Percentual; posicao cadastral. | `dim_precos` nao tem aba no dicionario oficial; categoria a reconciliar na Spec 05. | Media | `dispersao_precos.csv` ou equivalente. | Precificacao. | Diagnostica |
| Correlacao preco-volume | Sinalizar associacao para investigacao. | `corr(preco_medio_mensal, quantidade_mensal), n_obs >= 8` | Vendas agregadas por produto/loja/mes. | Produto ou produto x loja mensal. | Minimo 8 observacoes; limiar legado forte `< -0,4`. | Coeficiente de correlacao. | Nao e elasticidade; nao prova causalidade. | Baixa | `produtos_elasticidade_negativa_forte.csv` legado. | Repricing. | Diagnostica |
| Candidatos a investigacao de preco | Priorizar itens para revisar preco. | `correlacao_preco_volume < -0,4` e `n_obs >= 8`, com linguagem de triagem | Saida de correlacao e dispersao. | Produto/produto x loja. | Nao chamar de elasticidade. | Lista de candidatos. | Precisa validacao comercial, margem e concorrencia. | Baixa | `rec_repricing_elasticidade.csv` legado, renomeacao conceitual. | Recomendacoes. | Recomendacao |

## Projecao e recomendacao

| Metrica | Objetivo de negocio | Formula exata | Origem e colunas | Grao | Filtros | Unidade e periodicidade | Limitacoes | Confianca | Output | Relatorio | Tipo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Venda observada projetada | Projetar venda observada futura. | `tendencia linear por produto * indice sazonal por categoria` | Vendas mensais e categoria `NIVEL_1`. | Produto x mes futuro. | Historico 2024-2025. | Unidade de estoque ou BRL conforme serie. | Projeta venda observada, nao demanda real. | Baixa | `projecao_demanda_2026.csv` legado, com ressalva de nome. | Projecao 2026. | Preditiva |
| Demanda potencial | Estimar demanda sem censura de disponibilidade. | `DADO AUSENTE`: requer disponibilidade/ruptura real ou modelo causal. | Nao ha estoque atual confiavel, ruptura fisica nem pedidos perdidos. | Nao disponivel. | Nao aplicavel. | Unidades. | BLOQUEADA nesta spec. | BLOQUEADA | Nenhum. | Planejamento. | Preditiva |
| Estoque de seguranca | Criar colchao bruto para triagem. | `venda_media_diaria_2026 * 30` | Projecao legada de venda observada. | Produto. | Horizonte legado 30 dias; limiar nao validado com negocio. | Unidade de estoque. | Sem lead time, nivel de servico ou variabilidade real. | Baixa | `sugestao_compras_2026.csv` legado. | Compras 2026. | Recomendacao |
| Compra bruta sugerida | Triar necessidade bruta antes de estoque confiavel. | `venda_observada_projetada + estoque_seguranca_30d` | Projecao e estoque de seguranca. | Produto. | Nao desconta estoque atual. | Unidade de estoque. | E sugestao bruta/piso, nao pedido final. | Baixa | `sugestao_compras_2026.csv`. | Recomendacoes. | Recomendacao |
| Compra liquida sugerida | Recomendar compra descontando disponibilidade. | `BLOQUEADA`: `compra_bruta - estoque_disponivel_confiavel` | Requer estoque atual confiavel. | Produto x loja. | Somente apos reconciliacao Spec 04. | Unidade de estoque. | Estoque disponivel confiavel ausente. | BLOQUEADA | Nenhum confiavel. | Recomendacoes. | Recomendacao |
| Candidatos a promocao | Triar itens para acao comercial. | Regra legada de recomendacao + validacao de margem/estoque antes de acao | Outputs do script 07. | Produto. | Nao executar sem dados criticos. | Lista. | Margem, estoque atual e plano comercial ausentes. | Baixa | `rec_promocao.csv` legado. | Recomendacoes. | Recomendacao |
| Candidatos a descontinuacao | Triar itens para revisar sortimento. | Regra legada de recomendacao + validacao de margem, cobertura e papel de categoria | Outputs do script 07. | Produto. | Nao acionar automaticamente. | Lista. | Demanda real, margem e papel estrategico ausentes. | Baixa | `rec_descontinuacao.csv` legado. | Recomendacoes. | Recomendacao |
| Candidatos a repricing | Triar itens para revisar preco. | Dispersao ou correlacao forte, sempre como investigacao | `dim_precos`, correlacao preco-volume. | Produto/produto x loja. | Precos validos; correlacao nao causal. | Lista. | Margem/concorrencia ausentes; nao e elasticidade. | Baixa | `rec_repricing_*.csv` legado. | Recomendacoes. | Recomendacao |
| Nivel de confianca da recomendacao | Explicitar risco de uso operacional. | `Alta/Media/Baixa/BLOQUEADA` conforme dados criticos presentes | Catalogo, quality report e regras. | Recomendacao. | Baixa se faltar margem, lead time, estoque atual ou demanda real. | Classe. | Nao substitui aprovacao de negocio. | Alta como classificacao; baixa para recomendacoes atuais | Resumo executivo legado deve ser relido como triagem. | Recomendacoes. | Recomendacao |

## Itens bloqueados ou nao validados

- `BLOQUEADA`: numero real de pedidos/cupons, demanda potencial, compra liquida sugerida, custo/CMV/margem.
- `DADO AUSENTE`: ID de transacao, pedidos perdidos, estoque atual confiavel, lead time, lote minimo, margem, regra de imputacao de preco de compra.
- `NAO VALIDADO`: numero oficial unico da queda de vendas; same-store YoY reprodutivel; SKUs vendidos/comprados por mes citados no relatorio; correlacao compras-vendas 0,49; limiares legados 0,005, 15 dias, -0,4 e n_obs >= 8 com o negocio.
