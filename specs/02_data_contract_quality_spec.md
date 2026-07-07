# Spec 02 — Contratos e qualidade de dados

> Status: **IMPLEMENTADA / CONSOLIDADA** (entregáveis, outputs e testes confirmados na consolidação de 2026-07-07).
> Nota: o corpo abaixo preserva a especificação original; o resultado consolidado está em [docs/data_contract.md](../docs/data_contract.md).
> Base de evidência: [specs/00_current_state.md](00_current_state.md), [src/01_etl.py](../src/01_etl.py), [outputs/tables/checks_integridade.csv](../outputs/tables/checks_integridade.csv).

## Problema

O único controle de qualidade existente é o check de integridade referencial do ETL ([01_etl.py:137-160](../src/01_etl.py#L137-L160)), que cobre apenas 6 verificações (órfãos de `CODIGO` e `COD_EMPRESA` nos 3 fatos). Não existe:

- contrato formal de dados (`docs/data_contract.md`) descrevendo grão, chaves, tipos, nulidade e domínio de cada tabela;
- validação de schema (nenhum uso de `pandera` ou equivalente);
- checks de duplicidade no grão, valores negativos/zerados, datas fora do período, completude temporal, consistência de unidades;
- relatório de qualidade persistido (`data_quality_report.csv`).

Consequência direta documentada na Spec 00: o grão real de `fato_vendas` é desconhecido (linha por item? cupom? agregado diário?), a unicidade de `dim_produto.CODIGO` no bruto é desconhecida (o ETL faz `drop_duplicates` sem quantificar), e problemas centrais como "venda maior que estoque inicial + compras" (gap ~2,7×) não são medidos por check formal.

## Evidência encontrada no repositório

- [outputs/tables/checks_integridade.csv](../outputs/tables/checks_integridade.csv): 0% de órfãos em todos os 6 checks — único artefato de qualidade commitado.
- [src/01_etl.py:47](../src/01_etl.py#L47): `drop_duplicates(subset=["CODIGO"])` em `dim_produto` — indica duplicidade no bruto, não quantificada (`NÃO VALIDADO`).
- Spec 00, "Problemas de qualidade de dados visíveis": cobertura de compras `estoque_inicial + compras (~1,74M) << vendido (~4,64M)`; 74% dos eventos de movimentação com saldo projetado negativo; apenas 1.393 registros de compra para 2.731 produtos × 11 lojas × 24 meses.
- Spec 00, "Chaves aparentes": `dimensao_voltagem` usa `CD_EMPRESA` enquanto todas as demais usam `COD_EMPRESA` (inconsistência de nomenclatura).
- Spec 00, "Grão aparente": nenhuma unicidade de chave foi testada (`NÃO VALIDADO` para `dim_produto.CODIGO`, `dim_precos[CODIGO, COD_EMPRESA]`, grão de `fato_vendas` e de `fato_estoque_inicial`).
- `pandera` não está em [requirements.txt](../requirements.txt) (só pandas, numpy, matplotlib, pyarrow, openpyxl).

## Risco para o negócio

- KPI calculado sobre dado sem contrato: se `fato_vendas` tiver duplicidade no grão, receita e quantidades estão infladas — e todo o diagnóstico de queda muda.
- A conclusão causal central do relatório (compras encolheram → sortimento caiu) depende de uma base de compras cuja completude nunca foi formalmente medida; sem check de cobertura, hipótese vira conclusão.
- Duplicidades não quantificadas em `dim_produto` podem duplicar linhas em joins e inflar métricas por categoria.

## Arquivos de entrada

- `data/processed/*.parquet` (11 arquivos: `dim_produto`, `dim_lojas`, `dim_voltagem`, `dim_unidades`, `dim_precos`, `fato_estoque_inicial`, `fato_compras`, `fato_vendas`, `estoque_diario`, `estoque_final_projetado`, `cobertura_estoque`);
- `data/raw/*.csv` (para checks de duplicidade **no bruto**, antes do `drop_duplicates` do ETL);
- `data/raw/Descritivo_bases_de_dados_2.xlsx` (dicionário oficial — fonte primária do contrato; `DADO AUSENTE` até ser lido na Spec 01).

## Arquivos de saída esperados

- `docs/data_contract.md` — contrato por tabela: finalidade, grão, chave, colunas obrigatórias, tipos, nulidade, domínio, regras de negócio, integridade referencial, completude temporal, consistência de unidades, impacto no relatório.
- `src/validation/schemas.py` — schemas `pandera` para `dim_produto`, `dim_lojas`, `dim_precos`, `fato_vendas`, `fato_compras`, `fato_estoque_inicial` e principais processadas.
- `src/validation/quality_checks.py` — funções de check reutilizáveis.
- `src/02_quality_audit.py` — script que roda os checks e grava o relatório. (Nota de nomenclatura: já existe `src/02_estoque_projetado.py`; o prefixo `02_` duplicado é aceito pelo SDD.MD, mas ver Dúvidas.)
- `outputs/tables/data_quality_report.csv` — colunas: tabela, check, status (`PASS`/`WARN`/`FAIL`), linhas afetadas, % afetado, severidade, descrição, impacto analítico, ação recomendada.
- `tests/test_schema.py`, `tests/test_quality_checks.py`.

## Regras de negócio envolvidas

- Grão esperado (a validar): `fato_vendas` = produto × loja × dia × embalagem (`NÃO VALIDADO`); `fato_compras` = produto × loja × data × embalagem_fornecedor; `fato_estoque_inicial` = produto × loja; `dim_precos` = produto × loja.
- Quantidades e preços não podem ser negativos; zeros exigem justificativa.
- Nulo de estoque não é estoque zero.
- Produto vendido sem estoque inicial e sem compra registrada é anomalia a medir (não a esconder).
- Venda acumulada > estoque inicial + compras registradas = gap contábil (check central para a Spec 04).
- Datas devem estar em jan/2024–dez/2025.

## Métricas afetadas

- Receita, quantidade vendida, ticket médio (duplicidade no grão inflaria tudo);
- Saldo projetado de estoque e "rupturas" (dependem da completude de compras);
- Cobertura de compras (métrica nova, definida na Spec 04, mas cujo check nasce aqui);
- Rankings por produto/categoria/loja (dependem de `dim_produto` sem duplicidade).

## Mudanças propostas

1. Escrever `docs/data_contract.md` a partir do dicionário oficial (xlsx) + inspeção real; onde o dicionário divergir do dado, registrar a divergência.
2. Implementar schemas `pandera` (adicionar `pandera` às dependências — mudança de `requirements.txt`/`pyproject.toml` a documentar).
3. Implementar os checks mínimos do SDD.MD (seção 9): colunas, tipos, datas válidas/fora do período, nulos críticos, órfãos produto/loja, quantidades/preços negativos ou zerados, receita inconsistente (`RECEITA ≠ QUANTIDADE_VENDIDA × PRECO_UNIT_MEDIO`), duplicidade no grão, meses sem vendas/compras, produtos vendidos sem estoque inicial nem compras, venda > estoque inicial + compras, diferenças de unidade venda/compra/armazenagem.
4. Classificar como `FAIL` todo problema que invalide conclusão importante do relatório (ex.: se a duplicidade de grão em `fato_vendas` for real).
5. Gerar `outputs/tables/data_quality_report.csv`.

## Testes necessários

`tests/test_schema.py` e `tests/test_quality_checks.py` devem validar:
- `docs/data_contract.md` existe e não está vazio;
- schemas existem, aceitam DataFrames válidos e rejeitam inválidos (fixtures sintéticas);
- `src/02_quality_audit.py` executa sem erro e gera o relatório;
- o relatório tem as colunas obrigatórias e status apenas em {`PASS`, `WARN`, `FAIL`};
- checks críticos aparecem no relatório: órfãos, nulos críticos, negativos, duplicidade de grão, venda > entradas conhecidas;
- o check de duplicidade detecta duplicata plantada em fixture.

## Critérios de aceite

- `data_contract.md` cobre as 8 tabelas brutas + processadas principais;
- unicidade real das chaves respondida com número (quantas duplicatas em `dim_produto` no bruto; grão de `fato_vendas` confirmado ou refutado);
- `data_quality_report.csv` gerado com os checks mínimos;
- problemas que invalidam conclusões do relatório marcados como `FAIL` e listados;
- `pytest tests/test_schema.py tests/test_quality_checks.py` passa.

## O que não será feito

- Não serão corrigidos os problemas encontrados (esta spec **mede**; correções analíticas são das Specs 04–07).
- Não será alterado o ETL existente nem os Parquet commitados.
- Não serão criadas métricas (Spec 03) nem análises novas (Specs 04–06).
- Great Expectations não será usado (pandera + checks próprios bastam; princípio de simplicidade do SDD.MD).

## Dúvidas ou bloqueios

- `DADO AUSENTE` — Dicionário oficial (`Descritivo_bases_de_dados_2.xlsx`) ainda não lido; o contrato começará pelo observado e será reconciliado com o dicionário quando lido (dependência da Spec 01).
- `NÃO VALIDADO` — Grão real de `fato_vendas` (pergunta 9 da Spec 00): sem ID de transação, a unicidade produto×loja×dia×embalagem pode legitimamente não valer.
- Dúvida de nomenclatura: `src/02_quality_audit.py` colide com o prefixo de `src/02_estoque_projetado.py`. O SDD.MD manda criar exatamente `src/02_quality_audit.py`; manter o nome exigido e documentar que o prefixo numérico dos scripts legados não é ordem de execução do novo pipeline.
- `NÃO VALIDADO` — Se `PERC_DESCTO_ADICIONAL_EMBALAGEM_0` e `PRECO_EMBALAGEM_1/2` têm domínio válido (nunca inspecionados a fundo).
