# Matriz de validacao de hipoteses - Spec 07

Status: Spec 07 implementada. Esta matriz usa apenas contratos, regras e outputs ja consolidados nas Specs 00 a 06. Ela nao reexecuta analises antigas, nao cria dashboard, nao altera dados brutos e nao altera scripts legados.

## Como ler

- `Confirmada descritivamente`: o dado observado sustenta a afirmacao descritiva, sem implicar causa.
- `Parcialmente suportada`: ha evidencia em parte da hipotese, mas a formulacao forte nao e sustentada integralmente.
- `Exploratória`: ha sinal ou plausibilidade, mas falta desenho ou dado para conclusao forte.
- `Não comprovada`: a evidencia disponivel nao sustenta a hipotese.
- `Rejeitada`: os outputs disponiveis contrariam a hipotese em sua forma principal.
- `Inválida por limitação de dados`: a pergunta exige dados ausentes ou contaminados por baixa cobertura.

## Matriz H1-H10

| ID | Hipotese | Evidencia usada | Teste executado | Resultado | Status | Confianca | Conclusao permitida | Conclusao proibida |
|---|---|---|---|---|---|---|---|---|
| H1 | Queda causada por fechamento de lojas | `vendas_same_store_yoy.csv`; `sales_store_category_assortment.md` | Contagem de lojas com venda e comparabilidade YoY | Em 2025, 130/132 loja-mes sao comparaveis e 11 lojas tem venda observada em todos os meses | Rejeitada | Media | A queda nao e explicada por fechamento amplo observado nas vendas | A queda foi causada por fechamento de lojas |
| H2 | Queda concentrada em poucas categorias | `vendas_categorias_yoy.csv` | Classificacao YoY por categoria/periodo | Em 2025 mensal, 206 linhas sao queda generalizada, 23 queda concentrada, 38 crescimento e 9 comportamento atipico | Parcialmente suportada | Media | A queda e ampla, com concentracoes pontuais por periodo | Poucas categorias explicam a queda total |
| H3 | Queda concentrada em poucas lojas | `vendas_same_store_yoy.csv` | Agregacao anual por loja, 2025 vs 2024 | As 11 lojas caem no ano, de -30,6% a -66,5%; Loja 9 +73% ficou NAO VALIDADO | Rejeitada | Media | A queda aparece distribuida entre lojas, com intensidades diferentes | Uma ou poucas lojas causaram a queda |
| H4 | Sortimento vendido encolheu | `sortimento_controlado_por_volume.csv` | SKUs observados e controle por volume | 2.490 SKUs em 2024-11 vs 1.212 em 2025-12; 2025-12 ficou abaixo do esperado pelo controle de volume | Confirmada descritivamente | Media | O sortimento vendido observado encolheu | O encolhimento prova indisponibilidade fisica |
| H5 | Compras/reposicao causaram queda de vendas | `compras_coverage_audit.csv`; `gaps_saldo_contabil_estoque.csv` | Cobertura das entradas conhecidas e classificacao causal | Entradas conhecidas cobrem 37,4% das vendas; periodo total nao confiavel para analise causal | Inválida por limitação de dados | Baixa | A base de entradas nao permite testar causalidade | Compras/reposicao causaram a queda |
| H6 | Base de compras esta incompleta | `data_quality_report.csv`; `compras_coverage_audit.csv` | Cobertura por loja/produto e entradas vs saidas | Compras em 7/11 lojas e 329/2.731 produtos; 98,7% dos pares com venda sem compra registrada | Confirmada descritivamente | Alta | A base de compras nao representa entradas completas | Incompletude prova reducao operacional real |
| H7 | Queda pode ser demanda real e nao ruptura | Regras de negocio; catalogo de metricas; outputs de sortimento e cobertura | Revisao de dados ausentes para procura nao atendida e disponibilidade fisica | Nao ha disponibilidade fisica, pedidos perdidos ou trafego; explicacoes alternativas seguem plausiveis | Exploratória | Baixa | Menor procura permanece possibilidade nao descartada | Venda observada mede demanda real |
| H8 | Preco explica parte da queda | `produtos_correlacao_preco_volume_negativa.csv` | Correlacao preco-volume com minimo de observacoes | 160 produtos com correlacao negativa forte como associacao exploratoria | Exploratória | Baixa | Preco e candidato a investigacao comercial em parte do sortimento | Correlacao observada prova efeito causal ou elasticidade |
| H9 | Recomendacoes de compra sao acionaveis | `triagem_compras.csv`; `projecao_venda_observada_2026.csv` | Status de compra liquida e dados criticos | 2.729 linhas de triagem de compras estao BLOQUEADO/BLOQUEADO; compra liquida bloqueada em 2.729 produtos | Inválida por limitação de dados | Baixa | A lista prioriza investigacao de compra bruta | A lista e pedido final de compra |
| H10 | Recomendacoes de descontinuacao sao acionaveis | `triagem_descontinuacao.csv`; `triagem_promocao.csv` | Status das triagens comerciais | 224 candidatos a descontinuacao estao BLOQUEADO/BLOQUEADO; promocao tem 1.961 linhas de baixa confianca e bloqueadas para acao automatica | Inválida por limitação de dados | Baixa | A lista prioriza revisao comercial | A lista autoriza acao final automatica |

## Evidencias-chave

- Vendas: grão validado produto x loja x dia x embalagem; receita e quantidade em unidade de armazenagem validadas.
- Lojas: em 2025, todas as 11 lojas aparecem com venda observada em todos os meses; isso nao substitui calendario operacional.
- Categorias: a queda aparece majoritariamente generalizada, mas ha concentracoes pontuais em alguns periodos.
- Sortimento: queda de SKUs vendidos e controle por volume sustentam estreitamento observado, nao disponibilidade fisica.
- Compras e estoque: entradas conhecidas cobrem 37,4% das saidas observadas e o periodo total foi classificado como nao confiavel para analise causal.
- Preco: correlacao negativa em 160 produtos e apenas associacao exploratoria.
- Triagens: compra, promocao, repricing e descontinuacao sao listas de priorizacao; todas dependem de validacoes adicionais.

## Dados ausentes, nao validados e bloqueios

- `DADO AUSENTE`: transferencias, ajustes, devolucoes, estoque final real, disponibilidade fisica por SKU-loja-dia, pedidos perdidos, calendario operacional, margem, lead time, lote minimo, fornecedor, campanhas, concorrencia, papel estrategico do SKU.
- `NÃO VALIDADO`: universo completo de compras; semantica operacional do estoque inicial zero; janela que produziu Loja 9 +73%; valor antigo de 14 SKUs comprados no segundo semestre de 2025; limiares comerciais herdados.
- `BLOQUEADO`: causalidade compras -> vendas; compra liquida; pedido final de compra; acao automatica de promocao ou descontinuacao; estimativa de procura total sem censura.
