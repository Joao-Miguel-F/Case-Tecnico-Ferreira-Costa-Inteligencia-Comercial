# Reconciliação de compras, estoque e unidades - Spec 04

Status: Spec 04 implementada em 2026-07-07.

Esta documentação descreve a nova camada de reconciliação criada em
`src/inventory_reconciliation.py`. Ela não altera os scripts legados
`src/01_etl.py` a `src/07_recomendacoes.py`, não regrava dados brutos e não
altera `reports/relatorio_final.md`.

## Objetivo

Corrigir a comparação entre compras, vendas e estoque usando uma unidade comum
de armazenagem, e reinterpretar saldo projetado negativo como gap contábil.

Saldo negativo nos dados disponíveis não é evidência física operacional. Ele
mede que as saídas observadas excedem as entradas conhecidas na base atual.

## Fórmulas usadas

Vendas em unidade de armazenagem:

```text
QTD_VENDA_ESTOQUE = QUANTIDADE_VENDIDA * CONVERSAO_VENDA_PARA_ARMAZENAGEM
```

Compras em unidade de armazenagem:

```text
QTD_COMPRA_ESTOQUE = QUANTIDADE_COMPRA * CONVERSAO_COMPRA_ARMAZENAGEM
```

Entradas conhecidas:

```text
ENTRADAS_CONHECIDAS_ESTOQUE = ESTOQUE_INICIAL + COMPRAS_REGISTRADAS_ESTOQUE
```

Saldo projetado contábil:

```text
SALDO_PROJETADO_CONTABIL = ESTOQUE_INICIAL + COMPRAS_REGISTRADAS_ESTOQUE - VENDAS_ESTOQUE
```

Gap contábil:

```text
GAP_CONTABIL_ESTOQUE = max(VENDAS_ESTOQUE - ESTOQUE_INICIAL - COMPRAS_REGISTRADAS_ESTOQUE, 0)
```

## Conversão de compras

`QUANTIDADE_COMPRA` está em embalagem de compra do fornecedor, conforme o
dicionário oficial lido na Spec 01. Por isso, a reconciliação sempre multiplica
`QUANTIDADE_COMPRA` por `CONVERSAO_COMPRA_ARMAZENAGEM` antes de comparar com
vendas ou estoque.

Diagnóstico herdado e preservado:

| Item | Resultado |
|---|---:|
| Linhas de compra no dado atual | 1.393 |
| Linhas de compra com conversão diferente de 1 | 0 |
| Produtos cadastrados com conversão diferente de 1 | 226 |

Conclusão: o erro de unidade não muda o dado atual de compras, mas era um risco
latente. A fórmula nova está correta para cargas futuras em que compras envolvam
produtos com conversão diferente de 1.

## Outputs gerados

### `outputs/tables/compras_coverage_audit.csv`

Audita a cobertura das entradas conhecidas contra as saídas observadas em cinco
níveis:

- período total;
- mês;
- loja;
- categoria;
- produto.

Colunas principais:

- `total_vendido_estoque`;
- `estoque_inicial_estoque`;
- `compras_registradas_estoque`;
- `entradas_conhecidas_estoque`;
- `diferenca_saidas_entradas`;
- `pct_cobertura_entradas`;
- `pct_eventos_saldo_projetado_negativo`;
- `pct_skus_venda_sem_compra`;
- `pct_skus_venda_sem_estoque_inicial_suficiente`;
- `classificacao_confiabilidade`.

Classificações permitidas:

- `OK`;
- `suspeito`;
- `crítico`;
- `não confiável para análise causal`.

Resumo do período total:

| Métrica | Valor |
|---|---:|
| Vendas em unidade de estoque | 4.641.883,61 |
| Estoque inicial conhecido | 1.392.769,841 |
| Compras registradas convertidas | 345.290,78 |
| Entradas conhecidas | 1.738.060,621 |
| Diferença saídas - entradas conhecidas | 2.903.822,989 |
| Cobertura das entradas conhecidas | 37,4% |
| Eventos com saldo projetado negativo | 74,3% |
| Pares produto-loja com venda sem compra registrada | 21.118 de 21.387 |
| Classificação | não confiável para análise causal |

### `outputs/tables/gaps_saldo_contabil_estoque.csv`

Reconciliação por produto x loja. O arquivo contém 28.721 pares produto-loja e
14.570 pares com gap contábil maior que zero.

Colunas principais:

- `COD_EMPRESA`;
- `CODIGO`;
- `DESCRICAO`;
- `NIVEL_1`;
- `ESTOQUE_INICIAL`;
- `COMPRAS_REGISTRADAS_ESTOQUE`;
- `VENDAS_ESTOQUE`;
- `ENTRADAS_CONHECIDAS_ESTOQUE`;
- `SALDO_PROJETADO_CONTABIL`;
- `GAP_CONTABIL_ESTOQUE`;
- `VENDA_SEM_COMPRA_REGISTRADA`;
- `INTERPRETACAO_SALDO_NEGATIVO`;
- `POSSIVEIS_CAUSAS_GAP`.

O campo `POSSIVEIS_CAUSAS_GAP` lista causas compatíveis com a lacuna contábil,
sem transformar a lacuna em conclusão física.

## Limitações remanescentes

- `DADO AUSENTE`: transferências entre lojas, ajustes de inventário, devoluções,
  estoque final físico e inventário operacional.
- `NÃO VALIDADO`: se `fato_compras` representa o universo completo das entradas
  ou apenas uma extração parcial.
- `NÃO VALIDADO`: semântica operacional dos zeros explícitos em
  `ESTOQUE_INICIAL`.
- `BLOQUEADO`: decompor o gap contábil por causa real sem novas bases de entrada
  e movimentações de estoque.
- `BLOQUEADO`: métricas de CMV, margem e compra líquida enquanto persistirem
  preços de compra nulos e ausência de estoque disponível confiável.

## Decisão de linguagem

Os novos outputs usam `gap contábil`, `saldo projetado contábil` e
`entradas conhecidas`. Eles não classificam saldo negativo como evidência física.

## Testes

Arquivo criado:

```text
tests/test_inventory_reconciliation.py
```

Os testes validam:

- conversão de vendas para unidade de armazenagem;
- conversão de compras para unidade de armazenagem;
- rejeição de divergência em `QTD_VENDA_ESTOQUE`;
- cálculo de gap contábil com corte inferior em zero;
- geração dos dois CSVs;
- colunas obrigatórias;
- classificações permitidas;
- caso sem compra registrada tratado como limitação, não como prova causal.
