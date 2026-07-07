# Spec 06 — Precificação, projeção e recomendações

> Status: **PLANEJADA** (nenhuma implementação feita nesta fase).
> Base de evidência: [specs/00_current_state.md](00_current_state.md), [src/05_precificacao.py](../src/05_precificacao.py), [src/06_projecao_compras.py](../src/06_projecao_compras.py), [src/07_recomendacoes.py](../src/07_recomendacoes.py).

## Problema

1. **Correlação vendida como elasticidade**: `05_precificacao.py` calcula correlação de Pearson entre preço médio mensal e quantidade ([05_precificacao.py:76-91](../src/05_precificacao.py#L76-L91)) e grava `produtos_elasticidade_negativa_forte.csv`; `07_recomendacoes.py` rotula como "demanda sensivel a preco" ([07_recomendacoes.py:80](../src/07_recomendacoes.py#L80)).
2. **Docstring promete o que o código não faz**: o cabeçalho de `06_projecao_compras.py` afirma que a sugestão desconta "o estoque projetado remanescente... para chegar na sugestao de compra liquida" ([06_projecao_compras.py:13-16](../src/06_projecao_compras.py#L13-L16)), mas o código calcula `sugestao_compra_2026 = demanda_projetada_2026 + estoque_seguranca_30d` ([06_projecao_compras.py:129-131](../src/06_projecao_compras.py#L129-L131)) — o `estoque_inicial_total_referencia` é mergeado e **nunca subtraído**. A sugestão é bruta, mas não é rotulada como bruta.
3. **Venda observada chamada de demanda**: a projeção usa vendas (potencialmente censuradas por indisponibilidade) e nomeia o resultado `demanda_projetada` ([06_projecao_compras.py:97](../src/06_projecao_compras.py#L97)).
4. **Recomendações como decisão**: `07_recomendacoes.py` gera "listas acionaveis" de promoção/descontinuação/repricing sem margem, lead time, lote mínimo, estoque atual confiável ou sazonalidade do fornecedor — todos `DADO AUSENTE`.

## Evidência encontrada no repositório

- [src/05_precificacao.py:94-99](../src/05_precificacao.py#L94-L99): limiar `< −0,4` + receita acima da mediana ⇒ `produtos_elasticidade_negativa_forte.csv` (160 produtos, cf. `resumo_executivo.csv`).
- [src/06_projecao_compras.py:96-98](../src/06_projecao_compras.py#L96-L98): projeção = tendência linear (clip ≥ 0) × índice sazonal por categoria; nomeada `demanda_projetada`.
- [src/06_projecao_compras.py:122-131](../src/06_projecao_compras.py#L122-L131): estoque de referência mergeado e não usado na fórmula da sugestão.
- [src/07_recomendacoes.py:50-66](../src/07_recomendacoes.py#L50-L66): descontinuação por "zero vendas em 24 meses" ou "receita irrisória + estoque parado" — critérios só de venda/estoque inicial, sem margem/custo.
- `resumo_executivo.csv`: 1.961 candidatos a promoção; 224 a descontinuação; 50 + 160 a repricing; demanda projetada 2026 ≈ 1.370.583 vs. média histórica ≈ 2.320.942 (queda de ~41% projetada — projetar tendência de queda estrutural para 2026 é decisão metodológica não discutida no relatório).
- Spec 00, "Riscos analíticos" #4, #5, #6.

## Risco para o negócio

- "Elasticidade" sugere que baixar preço aumenta volume de forma previsível; se a correlação for espúria (sazonalidade, mix, promoções não observadas), o repricing destrói margem sem ganhar volume.
- Comprar `demanda_projetada + segurança` sem descontar estoque disponível (quando ele existir e for confiável) gera excesso de estoque; ao mesmo tempo, projetar para 2026 uma tendência de queda possivelmente causada por falta de dados de compras pode subdimensionar o abastecimento.
- Descontinuar 224 produtos sem margem/lead time/papel estratégico pode cortar itens rentáveis ou de tráfego.

## Arquivos de entrada

- `data/processed/fato_vendas.parquet`, `dim_produto.parquet`, `dim_precos.parquet`, `dim_lojas.parquet`;
- `outputs/tables/compras_coverage_audit.csv` e `gaps_saldo_contabil_estoque.csv` (Spec 04 — para decidir se estoque disponível é confiável);
- `outputs/tables/sortimento_controlado_por_volume.csv` (Spec 05 — para sinalizar censura da venda observada);
- outputs legados de 05/06/07 (conferência e reconciliação).

## Arquivos de saída esperados

- `outputs/tables/produtos_correlacao_preco_volume_negativa.csv` — substitui o conceito de "elasticidade" (o legado `produtos_elasticidade_negativa_forte.csv` é preservado; o novo nome é o oficial).
- `outputs/tables/projecao_venda_observada_2026.csv` — com colunas `demanda_observada_projetada`, `estoque_seguranca`, `compra_bruta_sugerida`, `estoque_a_validar_antes_da_compra`, `flag_nao_calcular_compra_liquida_por_estoque_inconfiavel`.
- `outputs/tables/triagem_possivel_promocao.csv`, `outputs/tables/triagem_possivel_descontinuacao.csv` — cada linha com regra usada, evidência, nível de confiança, dado faltante, risco de decisão, próxima validação necessária.
- `src/analysis/pricing_analysis.py`, `src/analysis/projection_analysis.py`, `src/analysis/recommendation_triage.py`.
- `tests/test_pricing.py`, `tests/test_projection.py`, `tests/test_recommendations.py`.

## Regras de negócio envolvidas

- Correlação preço-volume ⇒ "candidato a investigação de preço"; proibido "demanda sensível a preço"/"elasticidade" sem modelo causal.
- Venda observada ≠ demanda real; se há suspeita de indisponibilidade (Spec 04/05), a venda pode estar censurada e a projeção é **piso do cenário observado**.
- `compra_liquida = max(demanda_projetada + estoque_seguranca − estoque_disponivel, 0)` **somente** se estoque disponível for confiável; a Spec 04 já indica que não é (gap ~2,7×, 74% eventos negativos) ⇒ esperar `flag_nao_calcular_compra_liquida_por_estoque_inconfiavel = True` de forma generalizada.
- Recomendação sem margem/lead time/lote mínimo/fornecedor = triagem, nunca decisão final.
- Produtos com poucos pontos (o filtro atual é `n_obs ≥ 8` meses×loja) = dados insuficientes, não sinal.

## Métricas afetadas

- Correlação preço-volume (mantida como exploratória, renomeada);
- Dispersão de preço entre lojas (mantida — é descritiva e tem lastro);
- Demanda projetada 2026 → renomeada venda observada projetada;
- Sugestão de compra → separada em bruta vs. líquida (líquida bloqueada);
- Contadores do `resumo_executivo.csv` (1.961/224/50/160) — reclassificados como triagens.

## Mudanças propostas

1. `pricing_analysis.py`: recalcular correlação com o mesmo método (rastreável ao legado), gravar com nome novo e vocabulário de candidato a investigação; opcionalmente modelo exploratório `log(qtd+1) ~ log(preco) + efeitos fixos produto/loja/mês`, claramente rotulado observacional (decisão de incluir depende de custo/benefício — registrar).
2. `projection_analysis.py`: manter a mecânica tendência×sazonalidade como **cenário observado**, corrigindo a nomenclatura; adicionar as colunas de segurança/flag exigidas; documentar a decisão metodológica de projetar tendência de queda (com alternativa de cenário-piso/estável se fizer sentido — sem inventar demanda).
3. `recommendation_triage.py`: reconstruir promoção/descontinuação/repricing como triagens com os 6 campos obrigatórios (regra, evidência, confiança, dado faltante, risco, próxima validação).
4. Reconciliar contagens novas vs. legadas (ex.: os 224 candidatos a descontinuação devem ser reproduzíveis antes de virar triagem).

## Testes necessários

`tests/test_pricing.py`, `tests/test_projection.py`, `tests/test_recommendations.py` devem validar:
- `produtos_correlacao_preco_volume_negativa.csv` gerado; nenhum output **novo** com "elasticidade" no nome;
- correlação correta em fixture; produtos com poucos pontos marcados como dados insuficientes;
- `projecao_venda_observada_2026.csv` gerado; nenhuma coluna nova chama venda observada de "demanda real";
- compra líquida ausente/nula quando a flag de estoque inconfiável está ativa; flag presente quando aplicável;
- triagens geradas com regra, evidência, nível de confiança, dado faltante, risco e próxima validação preenchidos;
- vocabulário de triagem (nenhum "descontinuar"/"reduzir preço" imperativo sem qualificador exploratório).

## Critérios de aceite

- Elasticidade rebaixada para correlação exploratória em todos os artefatos novos;
- projeção rotulada como cenário observado; compra líquida bloqueada enquanto estoque for inconfiável (decisão vinda do `compras_coverage_audit.csv`);
- todas as recomendações convertidas em triagens com os 6 campos;
- `pytest tests/test_pricing.py tests/test_projection.py tests/test_recommendations.py` passa.

## O que não será feito

- Não será estimada elasticidade causal (impossível sem variação exógena de preço/promoções — `DADO AUSENTE`).
- Não será calculada compra líquida final (bloqueada por estoque inconfiável, salvo reversão da Spec 04).
- Não serão apagados os outputs legados de 05/06/07 (preservação de evidência; descomissionamento é decisão da Spec 08).
- Não será recomendada descontinuação/promoção/repricing como decisão final (faltam margem, estoque atual, idade de estoque, lead time, lote mínimo, fornecedor, substitutos, papel estratégico — todos `DADO AUSENTE`).

## Dúvidas ou bloqueios

- `BLOQUEADO` (externo) — Compra líquida sugerida: depende de estoque disponível confiável, que exige dados fora do repo (inventário/estoque final real).
- `DADO AUSENTE` — Margem/custo por produto: impede priorização financeira das triagens.
- `NÃO VALIDADO` — Vale incluir o modelo com efeitos fixos ou a correlação exploratória basta? Decidir na implementação com custo/benefício registrado.
- `NÃO VALIDADO` — A tendência de queda projetada para 2026 (−41% vs. média histórica) é artefato da base incompleta de compras? A resposta depende das Specs 04/05 e condiciona o texto da projeção.
