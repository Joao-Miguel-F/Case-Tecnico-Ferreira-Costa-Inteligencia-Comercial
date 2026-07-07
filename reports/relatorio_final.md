# Relatorio final 

Periodo analisado: jan/2024 a dez/2025. Escopo: 11 lojas, 2.731 SKUs cadastrados, 1.090.390 linhas diarias de venda, 1.393 registros de compra e 25.330 posicoes de estoque inicial.

Este relatorio substitui a versao anterior com uma camada explicita de validacao de hipoteses. As conclusoes abaixo distinguem fato validado, evidencia descritiva, associacao exploratoria, hipotese plausivel, conclusao nao comprovada e conclusao bloqueada por dados ausentes.

## 1. Sumario executivo

As vendas observadas cairam fortemente ao longo do periodo. A receita de 2024-11 foi R$ 47,2 milhoes e a de 2025-12 foi R$ 3,9 milhoes em `sortimento_controlado_por_volume.csv`; essa comparacao entre meses extremos indica queda de 91,7%. Outras janelas, como 1T24 contra 4T25, produzem percentuais diferentes. Portanto, qualquer numero de queda precisa declarar a janela usada.

O que os dados sustentam com maior seguranca: a base de vendas tem grao validado, a queda aparece em lojas e categorias, o sortimento vendido observado diminuiu e a base de compras entregue e incompleta para explicar entradas de estoque.

O que os dados nao sustentam: causalidade entre compras e queda de vendas, comprovacao operacional de indisponibilidade, estimativa de procura total sem censura, compra liquida, ordem operacional de compra ou acao automatica de descontinuacao.

## 2. O que foi validado com maior confianca

- A base de vendas e consistente para analises descritivas: grão produto x loja x dia x embalagem, sem duplicatas no contrato, com receita calculada como `QUANTIDADE_VENDIDA * PRECO_UNIT_MEDIO`.
- A base de compras esta incompleta para reconstruir entradas: compras aparecem em 7 de 11 lojas e 329 de 2.731 produtos; entradas conhecidas cobrem 37,4% das vendas observadas em unidade de estoque.
- A cobertura de compras foi classificada como `não confiável para análise causal` no periodo total.
- O gap contabil e material: 14.570 de 28.721 pares produto-loja tem gap maior que zero.

## 3. O que e evidencia descritiva

- Todas as 11 lojas tiveram queda anual observada em 2025 contra 2024, de -30,6% a -66,5%.
- Em 2025, 130 de 132 pares loja-mes sao comparaveis YoY.
- O sortimento vendido observado caiu de 2.490 SKUs em 2024-11 para 1.212 SKUs em 2025-12.
- Em 2025-12, o controle por volume esperava media de 1.849,5 SKUs, e foram observados 1.212.
- A analise mensal de categorias em 2025 teve 206 linhas de queda generalizada, 23 de queda concentrada, 38 de crescimento e 9 de comportamento atipico.

## 4. O que permanece hipotese

- A causa operacional da queda de vendas permanece aberta.
- A reducao de sortimento vendido pode ser compativel com menor disponibilidade, menor procura, mudanca de mix, preco, campanhas, concorrencia, substituicao de SKUs ou falha de captura.
- A relacao entre preco e volume e uma associacao exploratoria em 160 produtos, util para investigacao comercial.
- As triagens de compra, promocao, repricing e descontinuacao ajudam a priorizar revisao, mas nao fecham uma acao operacional automatica.

## 5. O que foi rejeitado ou nao comprovado

- H1 foi rejeitada como explicacao principal: os dados de venda nao mostram fechamento amplo de lojas.
- H3 foi rejeitada como explicacao concentrada em poucas lojas: todas as lojas caem no agregado anual observado.
- H5 ficou invalida por limitacao de dados: a cobertura baixa de compras bloqueia conclusoes causais.
- H9 e H10 ficaram invalidas por limitacao de dados: compra e descontinuacao estao em formato de triagem, com dados criticos ausentes.

## 6. Qualidade e cobertura dos dados

O `data_quality_report.csv` registra 66 checks `PASS`, 8 `WARN` e 7 `FAIL`. Os `FAIL` mais relevantes sao: 132 compras sem preco unitario, cobertura de compras por lojas e produtos, pares vendidos sem estoque inicial nem compra, venda maior que entradas conhecidas e saldos projetados contabeis negativos.

Os principais itens `DADO AUSENTE` sao transferencias, ajustes, devolucoes, estoque final real, calendario operacional de lojas, disponibilidade fisica por SKU-loja-dia, pedidos perdidos, margem, lead time, lote minimo, fornecedor, campanhas e concorrencia.

Os principais itens `NÃO VALIDADO` sao o universo completo de compras, a semantica operacional de estoque inicial zero, a janela que gerou a afirmacao antiga de Loja 9 com crescimento positivo e os limiares comerciais herdados.

Os principais itens `BLOQUEADO` sao causalidade compras-vendas, compra liquida, ordem operacional de compra, acao automatica de promocao/descontinuacao e estimativa de procura total sem censura.

## 7. Diagnostico de vendas

A queda de vendas observadas e robusta como fenomeno descritivo, mas seu percentual depende da janela. A comparacao 2024-11 contra 2025-12 mostra R$ 47,2 milhoes contra R$ 3,9 milhoes. Essa janela e extrema porque novembro carrega sazonalidade forte; por isso, a leitura correta e: houve queda grande, mas o numero oficial deve sempre carregar metodo e periodo.

Como nao existe ID de cupom ou pedido, contagens de linhas devem ser chamadas de linhas diarias de venda, nao transacoes.

## 8. Diagnostico de lojas

A queda aparece distribuida nas 11 lojas. Em 2025 contra 2024, a menor queda anual observada foi na loja 9 (-30,6%) e a maior na loja 93 (-66,5%). A afirmacao antiga de crescimento de +73% para loja 9 nao se reproduziu nos outputs auditaveis atuais e fica `NÃO VALIDADO`.

Dias com venda medem dias com ao menos uma linha observada. Essa metrica nao substitui calendario de abertura, reforma, fechamento temporario ou horario de operacao.

## 9. Diagnostico de categorias

A analise de categorias sugere queda ampla, com alguns periodos em que categorias especificas concentram parte da perda. Portanto, a hipotese de poucas categorias explicarem tudo nao se sustenta em sua forma forte, mas ha concentracoes pontuais que merecem leitura por periodo.

Categorias de alta receita continuam importantes para priorizacao, mas a matriz de hipoteses nao autoriza atribuir a queda total a um grupo pequeno de categorias.

## 10. Diagnostico de sortimento

O sortimento vendido observado encolheu. A queda de 2.490 SKUs em 2024-11 para 1.212 em 2025-12 e descritiva e rastreavel. O controle por volume reforca que 2025-12 ficou abaixo do esperado para o volume de linhas observado.

Essa conclusao deve ficar restrita ao que foi medido: SKUs que apareceram em vendas. Ela nao mede disponibilidade fisica, procura nao atendida nem decisao de mix.

## 11. Compras, estoque e gap contabil

As entradas conhecidas somam 1.738.060,621 unidades de estoque contra 4.641.883,61 unidades vendidas observadas. A diferenca de 2.903.822,989 unidades mostra lacuna contabil relevante.

Esse resultado bloqueia conclusoes causais sobre reposicao. Ele indica que as entradas disponiveis no dado nao reconciliam as saidas observadas. As causas possiveis incluem compras nao capturadas, transferencias, ajustes, devolucoes, inventario final ausente, mudanca de sistema ou processo operacional nao documentado.

## 12. Precificacao como correlacao exploratoria

Foram identificados 160 produtos com correlacao negativa entre preco medio e volume vendido, seguindo minimo de observacoes e filtro de receita. Essa lista serve para investigacao comercial.

A interpretacao permitida e associacao observacional. Para transformar isso em orientacao de preco seriam necessarios margem, concorrencia, campanhas, disponibilidade por periodo e teste controlado.

## 13. Projecao como venda observada

`projecao_venda_observada_2026.csv` projeta 1.370.582,76 unidades de venda observada para 2026, contra media anual historica observada de 2.320.941,8. A compra bruta sugerida soma 1.483.220 unidades.

Compra liquida esta bloqueada em 2.729 produtos porque falta estoque atual confiavel e parametros comerciais. A projecao e um cenario baseado no historico observado, nao uma estimativa de potencial total de mercado.

## 14. Recomendacoes como triagens

Os outputs da Spec 06 devem ser lidos como triagens:

- `triagem_repricing.csv`: 210 linhas, confianca baixa e acao automatica bloqueada.
- `triagem_compras.csv`: 2.729 linhas, todas bloqueadas.
- `triagem_promocao.csv`: 1.961 linhas, confianca baixa e acao automatica bloqueada.
- `triagem_descontinuacao.csv`: 224 linhas, todas bloqueadas.

Essas listas ajudam a ordenar investigacao. Elas nao substituem validacao de margem, estoque atual, idade do estoque, lead time, lote minimo, fornecedor, sazonalidade, substitutos, garantias, devolucoes e papel estrategico do SKU.

## 15. Dados adicionais necessarios

- Base completa de entradas: compras, transferencias, ajustes, devolucoes e inventario final.
- Estoque operacional por SKU, loja e data.
- Calendario operacional das lojas.
- Pedidos perdidos, indisponibilidade registrada operacionalmente ou outra medida de procura nao atendida.
- Margem, custo, fornecedor, lead time, lote minimo e politica de nivel de servico.
- Campanhas, concorrencia, precos de mercado e mudancas de politica comercial.
- Mapeamento de substitutos e papel estrategico de cada SKU.

## 16. Conclusao honesta

A Spec 07 conclui que a queda de vendas observadas e real como fato descritivo, ampla por lojas e categorias, acompanhada por estreitamento do sortimento vendido e por uma lacuna contabil relevante entre entradas conhecidas e saidas observadas.

Mas a conclusao causal central fica bloqueada: a base de compras e insuficiente para explicar por que as vendas cairam. O proximo passo correto nao e executar automaticamente compras ou descontinuacoes, e sim completar a evidencia operacional que falta. Com esses dados adicionais, as triagens atuais podem virar uma fila objetiva de validacao comercial.
