# Spec 04 — Compras, estoque, unidades e reconciliação

> Status: **IMPLEMENTADA / CONSOLIDADA** (entregáveis, outputs e testes confirmados na consolidação de 2026-07-07).
> Nota: o corpo abaixo preserva a especificação original; o resultado consolidado está em [docs/inventory_reconciliation.md](../docs/inventory_reconciliation.md).
> Base de evidência: [specs/00_current_state.md](00_current_state.md), [src/02_estoque_projetado.py](../src/02_estoque_projetado.py), [src/01_etl.py](../src/01_etl.py).

## Problema

O saldo de estoque projetado mistura unidades e rotula gap contábil como "ruptura":

1. **Unidades misturadas**: [02_estoque_projetado.py:31-36](../src/02_estoque_projetado.py#L31-L36) soma `QUANTIDADE_COMPRA` **crua**, sem aplicar `CONVERSAO_COMPRA_ARMAZENAGEM` (coluna existente em `dim_produto`), enquanto as vendas são convertidas para unidade de estoque (`QTD_VENDA_ESTOQUE`). A conta `estoque_inicial + compras − vendas` pode somar caixas com unidades.
2. **"Ruptura" indevida**: [02_estoque_projetado.py:74-90](../src/02_estoque_projetado.py#L74-L90) grava todo saldo negativo em `rupturas_estoque.csv`, apesar de a base de compras ser reconhecidamente incompleta (1.393 registros para 2.731 produtos × 11 lojas × 24 meses; entradas conhecidas ~1,74M vs. vendas ~4,64M — gap ~2,7×; 74% dos eventos com saldo negativo).
3. **Sem auditoria de cobertura**: não existe medição formal de quanto das saídas é explicado pelas entradas conhecidas, por mês/loja/categoria/produto — logo o relatório não tem base para afirmar que "compras caíram" em vez de "registros de compras caíram".

## Evidência encontrada no repositório

- [src/02_estoque_projetado.py:31-36](../src/02_estoque_projetado.py#L31-L36): `compras.groupby(...)["QUANTIDADE_COMPRA"].sum()` — nenhuma conversão aplicada.
- [src/01_etl.py:177-179](../src/01_etl.py#L177-L179): vendas convertidas (`QTD_VENDA_ESTOQUE`), assimetria comprovada.
- `dim_produto` possui `CONVERSAO_COMPRA_ARMAZENAGEM` (lida em [01_etl.py:43-45](../src/01_etl.py#L43-L45)); nas amostras vale `1,000000`, mas isso **não foi verificado para todos os produtos** (`NÃO VALIDADO`).
- Ambiguidade real registrada na Spec 00: `EMBALAGEM_FORNECEDOR="CX-40-UN"` com `QUANTIDADE_COMPRA=120` e `UNIDADE_ESTOQUE="UN"` — 120 caixas ou 120 unidades? `NÃO VALIDADO`.
- [outputs/tables/rupturas_estoque.csv](../outputs/tables/rupturas_estoque.csv) e `produtos_risco_ruptura.csv` existem com essa nomenclatura.
- Spec 00, "Conclusões diagnósticas": gap ~2,7× e 74% de eventos negativos, já reconhecidos pelo próprio relatório como sintoma de base incompleta.

## Risco para o negócio

- Se `CONVERSAO_COMPRA_ARMAZENAGEM ≠ 1` para produtos relevantes, o saldo projetado, a cobertura e o tamanho do gap estão errados — e a magnitude da "falta de compras" muda.
- Chamar gap contábil de "ruptura" leva o negócio a agir (comprar, promover, descontinuar) sobre um artefato de dados: o custo é compra desnecessária ou diagnóstico errado da queda de vendas.
- A cadeia causal do relatório (compras → sortimento → receita) fica sem sustentação quantificada sem a auditoria de cobertura.

## Arquivos de entrada

- `data/processed/fato_compras.parquet`, `fato_vendas.parquet`, `fato_estoque_inicial.parquet`, `dim_produto.parquet` (com `CONVERSAO_COMPRA_ARMAZENAGEM` e `UNIDADE_ESTOQUE`), `dim_lojas.parquet`;
- `data/raw/Descritivo_bases_de_dados_2.xlsx` (para resolver a ambiguidade de unidade de `QUANTIDADE_COMPRA` — `DADO AUSENTE` até a Spec 01 ler o dicionário).

## Arquivos de saída esperados

- `outputs/tables/compras_coverage_audit.csv` — cobertura das entradas conhecidas vs. saídas: total vendido (un. estoque), estoque inicial, compras (un. estoque), entradas totais, diferença, % cobertura, % eventos com saldo negativo, % SKUs com venda sem compra, % SKUs com venda sem estoque inicial suficiente, cobertura por mês/loja/categoria/produto, classificação (`OK`/`suspeito`/`crítico`/`não confiável para análise causal`).
- `outputs/tables/gaps_saldo_contabil_estoque.csv` — gap contábil por produto×loja: `gap_entrada = max(vendas_acumuladas − estoque_inicial − compras_acumuladas, 0)`.
- `src/analysis/inventory_reconciliation.py`.
- `docs/known_limitations.md` — se `QUANTIDADE_COMPRA` já estiver em unidade de armazenagem, documentar explicitamente aqui.
- `tests/test_units.py`, `tests/test_reconciliation.py`.

## Regras de negócio envolvidas

- `QTD_VENDA_ESTOQUE = QUANTIDADE_VENDIDA × CONVERSAO_VENDA_PARA_ARMAZENAGEM` (já aplicada no ETL).
- `QTD_COMPRA_ESTOQUE = QUANTIDADE_COMPRA × CONVERSAO_COMPRA_ARMAZENAGEM` (a aplicar, condicionada à resposta da ambiguidade de unidade).
- `gap_entrada = max(vendas_acumuladas − estoque_inicial − compras_acumuladas, 0)` — nunca negativo.
- Gap contábil admite múltiplas causas (ruptura, transferência não capturada, compra ausente, ajuste de inventário, devolução, falha de extração, erro de unidade, estoque inicial incompleto, erro de data) — nenhuma pode ser afirmada sem evidência adicional.
- Se cobertura de compras for baixa, o relatório só pode afirmar que **os registros disponíveis** de compras caíram/são incompletos.

## Métricas afetadas

- Saldo projetado de estoque (`estoque_diario.parquet`, `estoque_final_projetado.parquet`);
- "Rupturas" (`rupturas_estoque.csv`) → renomeadas/reinterpretadas como gap contábil;
- Cobertura de compras (nova); gap contábil (nova); % SKUs com venda sem compra (nova);
- Indiretamente: risco de ruptura e matriz giro×cobertura (04_analise_estoque) e a sugestão de compra 2026 (06), que herdam o saldo.

## Mudanças propostas

1. Validar na base completa se `CONVERSAO_COMPRA_ARMAZENAGEM == 1.0` para todos os produtos; se não, aplicar a conversão às compras em `src/analysis/inventory_reconciliation.py`; se sim (ou se o dicionário disser que `QUANTIDADE_COMPRA` já está em unidade de estoque), documentar em `docs/known_limitations.md`. Nada implícito.
2. Calcular `gap_entrada` com clip em zero, por produto×loja (e agregações por mês/loja/categoria), gravando `gaps_saldo_contabil_estoque.csv` com vocabulário de **gap contábil**, listando as causas possíveis.
3. Gerar `compras_coverage_audit.csv` com as dimensões e classificações exigidas pelo SDD.MD (seção 11).
4. Não alterar `02_estoque_projetado.py` nesta spec; a nova lógica nasce em `src/analysis/` e a reconciliação com os outputs legados é reportada (diferenças quantificadas). A eventual correção/renomeação dos outputs legados é decisão documentada na Spec 07/08.

## Testes necessários

`tests/test_units.py` e `tests/test_reconciliation.py` devem validar:
- conversão de venda e de compra para unidade de estoque (fixtures com conversão ≠ 1);
- nenhuma análise nova mistura unidade de venda com unidade de compra;
- `gap_entrada` correto e nunca negativo;
- saldo negativo não é classificado automaticamente como ruptura física (vocabulário dos outputs);
- `compras_coverage_audit.csv` e `gaps_saldo_contabil_estoque.csv` gerados com colunas obrigatórias;
- classificação de confiabilidade pertence a {`OK`, `suspeito`, `crítico`, `não confiável para análise causal`};
- caso sem compras registradas tratado como limitação, não como prova causal.

## Critérios de aceite

- A pergunta "conversão de compra é sempre 1?" respondida com número na base completa;
- unidades explícitas em toda a reconciliação nova;
- cobertura de compras auditada por mês/loja/categoria/produto com classificação;
- nenhum output novo usa a palavra "ruptura" para saldo contábil negativo;
- `pytest tests/test_units.py tests/test_reconciliation.py` passa.

## O que não será feito

- Não será alterado `src/02_estoque_projetado.py` nem regravados `rupturas_estoque.csv`/`estoque_diario.parquet` legados (preservação de evidência; a substituição é decidida nas Specs 07/08).
- Não será estimado estoque físico real (impossível sem inventário/transferências — `DADO AUSENTE`).
- Não será concluída causa da queda de compras (só medição de cobertura).

## Dúvidas ou bloqueios

- `NÃO VALIDADO` — `CONVERSAO_COMPRA_ARMAZENAGEM` é 1,0 para todos os 2.731 produtos? (Determinante para o tamanho do gap.)
- `NÃO VALIDADO` — Unidade real de `QUANTIDADE_COMPRA` (caixa do fornecedor vs. unidade de estoque); depende do dicionário xlsx (`DADO AUSENTE` até Spec 01).
- `DADO AUSENTE` — Transferências entre lojas, devoluções, ajustes de inventário e estoque final real não existem no repo: o gap contábil **não poderá** ser decomposto em causas; a spec entrega classificação de confiabilidade, não veredito.
- `NÃO VALIDADO` — `fato_compras` é extração parcial ou universo completo? (Pergunta 2 da Spec 00 — só o dono do dado responde; marcar como bloqueio externo.)
