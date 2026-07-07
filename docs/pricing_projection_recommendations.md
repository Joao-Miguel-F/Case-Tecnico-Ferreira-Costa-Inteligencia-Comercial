# Precificacao, projecao e triagens - Spec 06

Status: Spec 06 implementada em 2026-07-07.

Esta camada cria artefatos auditaveis para associacao preco-volume, projecao de
venda observada e triagens de repricing, compras, promocao e descontinuacao.
Ela nao altera scripts legados, nao regrava dados brutos, nao cria dashboard e
nao altera `reports/relatorio_final.md`.

## Entradas usadas

- `data/processed/fato_vendas.parquet`
- `data/processed/dim_produto.parquet`
- `data/processed/fato_estoque_inicial.parquet`
- `outputs/tables/compras_coverage_audit.csv`
- `outputs/tables/gaps_saldo_contabil_estoque.csv`
- `outputs/tables/sortimento_controlado_por_volume.csv`
- outputs legados de candidatos comerciais apenas como insumo de triagem

## Correlação preço-volume

Arquivo gerado:

```text
outputs/tables/produtos_correlacao_preco_volume_negativa.csv
```

Regra:

```text
correlacao_preco_volume = corr(preco_medio_mensal, quantidade_mensal)
min_obs_exigido = 8 observacoes produto-loja-mes
limiar de triagem = correlacao_preco_volume < -0,4 e receita acima da mediana
```

Interpretação permitida: associação exploratória para investigação comercial.
Interpretação bloqueada: efeito causal de preço sobre volume.

Produtos com menos de 8 observações, menos de 3 preços mensais distintos ou sem
volume observado suficiente ficam como `DADO AUSENTE` na função de cálculo e não
entram no output de candidatos negativos.

## Projeção de venda observada

Arquivo gerado:

```text
outputs/tables/projecao_venda_observada_2026.csv
```

Regra:

```text
venda_observada_projetada_2026 =
  tendencia linear por produto sobre venda observada historica
  x indice sazonal por categoria

compra_bruta_sugerida =
  venda_observada_projetada_2026 + estoque_seguranca_30d
```

Compra líquida ou pedido final ficam `BLOQUEADO`, porque a Spec 04 classificou a
cobertura de entradas como baixa para análise causal e o projeto não possui
estoque atual disponível confiável, lead time, lote mínimo, margem e fornecedor.

Limitação: a projeção usa venda observada. Ela pode estar limitada por
disponibilidade, mix, sazonalidade e cobertura parcial das entradas conhecidas.
Portanto, o output não mede potencial total de venda e não deve ser usado como
pedido final de compra.

## Triagens

Arquivos gerados:

```text
outputs/tables/triagem_repricing.csv
outputs/tables/triagem_compras.csv
outputs/tables/triagem_promocao.csv
outputs/tables/triagem_descontinuacao.csv
outputs/tables/triagem_possivel_promocao.csv
outputs/tables/triagem_possivel_descontinuacao.csv
```

Todas as triagens possuem:

- `tipo_triagem`
- `nivel_confianca`
- `status_decisao_final`
- `regra_usada`
- `evidencia`
- `dado_faltante`
- `limitacao`
- `risco_decisao`
- `proxima_validacao_necessaria`
- `acao_recomendada`

Níveis adotados:

- `Baixa`: a linha pode priorizar investigação, mas faltam dados críticos.
- `BLOQUEADO`: a linha não sustenta decisão final com os dados atuais.

## Dados ausentes e bloqueios

- `DADO AUSENTE`: margem, estoque atual confiável, lead time, lote mínimo,
  fornecedor, política comercial por loja, concorrência, campanhas, substitutos,
  devoluções, garantias e papel estratégico do SKU.
- `NÃO VALIDADO`: limiares herdados de correlação, estoque de segurança de 30
  dias e interpretação operacional dos zeros de estoque inicial.
- `BLOQUEADO`: compra líquida final, pedido final de compra e decisão final de
  promoção ou descontinuação.

## Testes

Arquivos criados:

- `tests/test_pricing.py`
- `tests/test_projection.py`
- `tests/test_recommendations.py`

Os testes validam nomes e colunas dos outputs, cálculo da correlação, mínimo de
observações, nomenclatura de venda observada, bloqueio de compra líquida quando
faltam dados críticos e presença de evidência, confiança e limitação nas
triagens.
