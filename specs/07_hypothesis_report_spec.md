# Spec 07 — Hipóteses e relatório final

> Status: **PLANEJADA** (nenhuma implementação feita nesta fase).
> Base de evidência: [specs/00_current_state.md](00_current_state.md), [reports/relatorio_final.md](../reports/relatorio_final.md), [README.md](../README.md).

## Problema

O relatório atual ([reports/relatorio_final.md](../reports/relatorio_final.md)) tira conclusões mais fortes do que a evidência sustenta:

1. Avalia apenas 5 hipóteses (H1–H5) com status livres ("Rejeitada", "Confirmada", "Confirmada e explicação mais provável") — o SDD.MD exige matriz H1–H10 com vocabulário controlado de 6 status.
2. Os números que sustentam H4 e H5 (SKUs vendidos 2.490→1.212; SKUs comprados 74→14; correlação 0,49; same-store YoY; Loja 9 +73%) **não têm script nem tabela** no repo (Spec 00, "Riscos analíticos" #2).
3. O Sumário Executivo afirma que "os dados são consistentes com lojas progressivamente ficando sem itens para vender" e a Seção 8 lista recomendações acionáveis — linguagem causal/decisória sobre base de compras reconhecidamente incompleta.
4. O relatório cita etapas "3b" e pipeline "01_ a 08_" que não existem (só há `01..07` em `src/`).
5. Os números-título da queda divergem entre documentos (−71,7% no relatório, ~−85% no README, −91,7% implícito em `vendas_mensais.csv`).

## Evidência encontrada no repositório

- Spec 00, "Principais hipóteses do relatório": H1–H3 "Rejeitada", H4 "Confirmada", H5 "Confirmada e explicação mais provável".
- Spec 00, "Conclusões causais": cadeia compras→sortimento→receita proposta com atenuações, mas com sumário executivo e recomendações mais fortes que as ressalvas.
- Spec 00, "Outputs existentes": nenhuma tabela de same-store/YoY/SKUs-mês no repo.
- Spec 00, "Riscos analíticos" #1: três números distintos para a queda.
- Spec 00, "Scripts existentes": referência a `3b` e `08_` inexistentes (`NÃO VALIDADO`).

## Risco para o negócio

- Decisões de compras/sortimento 2026 tomadas sobre uma cadeia causal não comprovada; se a queda de compras for artefato de extração (H6), o negócio "conserta" o problema errado.
- Números-título divergentes minam a confiança de qualquer leitor executivo no trabalho inteiro.
- Recomendações acionáveis sem dados de margem/lead time transferem risco de decisão para quem lê o relatório sem os avisos.

## Arquivos de entrada

Todos os outputs validados das Specs 02–06 (esta spec só roda depois deles):

- `outputs/tables/data_quality_report.csv` (Spec 02);
- `docs/metric_catalog.md`, `docs/business_rules.md` (Spec 03);
- `outputs/tables/compras_coverage_audit.csv`, `gaps_saldo_contabil_estoque.csv`, `docs/known_limitations.md` (Spec 04);
- `outputs/tables/vendas_same_store_yoy.csv`, `vendas_categorias_yoy.csv`, `sortimento_controlado_por_volume.csv` (Spec 05);
- `outputs/tables/produtos_correlacao_preco_volume_negativa.csv`, `projecao_venda_observada_2026.csv`, `triagem_possivel_promocao.csv`, `triagem_possivel_descontinuacao.csv` (Spec 06);
- `reports/relatorio_final.md` atual (base a reescrever).

## Arquivos de saída esperados

- `docs/hypothesis_validation_matrix.md` — por hipótese: evidência usada, teste executado, resultado, status, nível de confiança, riscos, dados ausentes, conclusão permitida, conclusão proibida.
- `outputs/tables/hypothesis_status.csv` — a mesma matriz em formato tabular.
- `reports/relatorio_final.md` — **reescrito** com as 17 seções do SDD.MD (seção 14). O relatório atual deve ser preservado (ex.: cópia `reports/relatorio_final_v1_original.md` ou via histórico git — decidir e documentar; princípio "não sobrescreva arquivos importantes sem necessidade" vs. entregável que manda reescrever).
- `tests/test_hypothesis_report.py`.

## Regras de negócio envolvidas

- Status permitidos (únicos): `Confirmada descritivamente`, `Parcialmente suportada`, `Exploratória`, `Não comprovada`, `Rejeitada`, `Inválida por limitação de dados`.
- Hipóteses mínimas H1–H10 (SDD.MD seção 14): fechamento de lojas; concentração em categorias; concentração em lojas; encolhimento de sortimento; compras causaram queda; base de compras incompleta; queda por demanda real; preço explica parte; compra acionável; descontinuação acionável.
- Se cobertura de compras for baixa (Spec 04), é proibido afirmar que compras causaram a queda — apenas que os registros disponíveis caíram/são incompletos.
- Linguagem obrigatória: gap contábil (não "ruptura comprovada"); correlação exploratória (não "elasticidade"); triagem (não decisão final); venda observada (não demanda real).
- Toda afirmação numérica do relatório deve apontar para um arquivo em `outputs/tables/` ou `docs/`.

## Métricas afetadas

- Número oficial da queda de vendas (definido na Spec 03, reconciliado aqui no texto);
- Status de H1–H5 atuais — esperado rebaixamento: H4/H5 de "Confirmada" para vocabulário controlado condicionado aos resultados das Specs 04/05; H1–H3 reavaliadas com same-store/dias com venda;
- Todos os KPIs citados no sumário executivo.

## Mudanças propostas

1. Construir a matriz H1–H10 preenchida exclusivamente com resultados das Specs 02–06 (nenhum número sem arquivo de origem).
2. Reescrever `reports/relatorio_final.md` com as 17 seções obrigatórias, aplicando as trocas de linguagem exemplificadas no SDD.MD (seção 14, "Linguagem obrigatória").
3. Corrigir as referências a scripts inexistentes (`3b`, `08_`) e unificar o número da queda.
4. Preservar a versão original do relatório de forma documentada.
5. Gerar `hypothesis_status.csv` consumível pelo dashboard (Spec 09).

## Testes necessários

`tests/test_hypothesis_report.py` deve validar:
- `docs/hypothesis_validation_matrix.md`, `outputs/tables/hypothesis_status.csv` e `reports/relatorio_final.md` existem;
- `hypothesis_status.csv` tem colunas obrigatórias e status apenas na lista permitida;
- H1–H10 presentes, cada uma com conclusão permitida e conclusão proibida;
- relatório contém seções de limitações, qualidade dos dados e hipóteses;
- relatório não usa "ruptura comprovada", nem "elasticidade" (quando só houver correlação), nem trata triagem como decisão final;
- relatório não afirma que compras causaram a queda se a cobertura (Spec 04) for insuficiente.

## Critérios de aceite

- Matriz H1–H10 completa com vocabulário controlado;
- relatório reescrito com as 17 seções e linguagem rigorosa;
- cada número do relatório rastreável a um output commitado;
- divergência −71,7%/−85%/−91,7% explicada no próprio relatório;
- `pytest tests/test_hypothesis_report.py` passa.

## O que não será feito

- Não serão geradas novas análises (usa apenas o que as Specs 02–06 produziram); se um insumo faltar, a hipótese correspondente recebe `Inválida por limitação de dados` ou `Não comprovada` — não se inventa evidência.
- Não será deletado o relatório original.
- Não será construído dashboard (Spec 09).
- Não serão emitidas recomendações finais de compra/promoção/descontinuação (permanecem triagens).

## Dúvidas ou bloqueios

- **Dependência dura**: esta spec é bloqueada até as Specs 02–06 estarem concluídas ou formalmente bloqueadas.
- `NÃO VALIDADO` — Como preservar o relatório original: cópia versionada no repo vs. apenas histórico git. Proposta: cópia explícita, pois o SDD.MD pede auditabilidade para leitores fora do git.
- `DADO AUSENTE` — H9/H10 (acionabilidade de compra/descontinuação) provavelmente terminarão `Inválida por limitação de dados` por falta de margem/lead time/estoque confiável — a confirmar com os resultados reais.
- `NÃO VALIDADO` — Alguma conclusão descritiva do relatório atual (concentração de receita, sazonalidade de novembro, dispersão de preço) pode mudar após correção de unidades (Spec 04); o texto final depende desses resultados.
