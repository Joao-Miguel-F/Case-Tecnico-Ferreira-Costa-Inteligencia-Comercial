# Spec 01 — Ingestão, encoding e parsing

> Status: **IMPLEMENTADA / CONSOLIDADA** (entregáveis, outputs e testes confirmados na consolidação de 2026-07-07).
> Nota: o corpo abaixo preserva a especificação original; o resultado consolidado está em [docs/data_formatting_and_encoding.md](../docs/data_formatting_and_encoding.md).
> Base de evidência: [specs/00_current_state.md](00_current_state.md) e leitura direta de [src/01_etl.py](../src/01_etl.py).

## Problema

A leitura das 8 bases brutas está inteiramente embutida em [src/01_etl.py](../src/01_etl.py), com decisões de encoding, separador, decimal e tipo tomadas **caso a caso e de forma implícita** (não documentadas fora de comentários), sem função centralizada de leitura, sem auditoria de ingestão persistida e sem testes. Especificamente:

1. Cada base tem sua própria combinação de `sep`/`encoding`/`decimal` hardcoded (ex.: `dim_produto` em `latin1` + `;`, `fato_vendas` em `utf-8` + `,`), sem validação de que o encoding escolhido é de fato o correto.
2. Números com vírgula decimal são convertidos via `str.replace(",", ".")` pontual ([01_etl.py:43-45](../src/01_etl.py#L43-L45), [01_etl.py:97-99](../src/01_etl.py#L97-L99)) com `errors="coerce"` — nulos criados pela coerção **não são contados nem logados**.
3. `CODIGO`, `COD_EMPRESA`, `DIGITO` são convertidos para `Int64`; se existirem códigos com zeros à esquerda significativos, eles são perdidos silenciosamente (`NÃO VALIDADO` — nas amostras os códigos parecem numéricos puros).
4. Linhas descartadas por integridade referencial ([01_etl.py:165-170](../src/01_etl.py#L165-L170)) são logadas só no stdout; hoje o descarte é 0 (evidência: `checks_integridade.csv`), mas não há registro persistente por arquivo.
5. Não existe `outputs/tables/ingestion_audit.csv`, `docs/data_formatting_and_encoding.md`, `src/io.py` nem `tests/test_ingestion.py`.
6. O dicionário oficial `data/raw/Descritivo_bases_de_dados_2.xlsx` e o enunciado `data/raw/Estudo_de_caso_1.docx` **nunca foram incorporados** à ingestão (`DADO AUSENTE` na Spec 00) — as decisões de parsing não foram conferidas contra o dicionário.

## Evidência encontrada no repositório

- [src/01_etl.py:36-47](../src/01_etl.py#L36-L47): `dim_produto_1.csv` lido com `encoding="latin1"`, `dtype=str`, `drop_duplicates(subset=["CODIGO"])` (duplicidades no bruto não quantificadas).
- [src/01_etl.py:106-107](../src/01_etl.py#L106-L107) e [129](../src/01_etl.py#L129): colunas `Unnamed` (índice sem nome) descartadas em `fato_compras` e `fato_vendas`.
- [src/01_etl.py:97-99](../src/01_etl.py#L97-L99): `ESTOQUE_INICIAL` chega como string com vírgula decimal apesar de conter inteiros.
- Spec 00, seção "Problemas de encoding, parsing e formatação visíveis": NBSP `0xA0` em `dim_produto`; strings vazias `" "` em `EMBALAGEM_VENDA_0`; trailing spaces em `Descr_unidades_medida` (`"PECA (PC) "`); `COD_IBGE` vazio na linha `EB;EMBALAGEM ESPECIAL;`; `Descr_unidades_medida` aparentemente sem acentos (`NÃO VALIDADO`).
- Spec 00, tabela "Bases disponíveis": mistura de convenções `;`+decimal `,` (dimensões/estoque) vs. `,`+decimal `.` (fatos vendas/compras).
- Sentinelas `NA`/`N/A`/`-`/`null`/`None`: não observadas na amostra; `NÃO VALIDADO` para as bases completas.

## Risco para o negócio

- Encoding errado corrompe descrições de produto e categorias (`NIVEL_1..3`), contaminando rankings, análises de categoria e o relatório final.
- Coerções numéricas silenciosas podem transformar valores válidos em nulos (ou zeros) sem que ninguém perceba, distorcendo receita, quantidades e estoque.
- Sem auditoria de ingestão, nenhuma conclusão downstream é auditável: não é possível provar quantas linhas entraram, quantas foram descartadas e por quê.
- Perda de zeros à esquerda em códigos quebraria joins com sistemas externos do varejista.

## Arquivos de entrada

Todos em `data/raw/` (nomes reais, conforme Spec 00):

- `fato_vendas_1.csv` (1.090.390 linhas, `,` + decimal `.`, utf-8)
- `fato_compras_2.csv` (1.393 linhas, `,` + decimal `.`, utf-8)
- `fato_estoque_inicial_2.csv` (25.330 linhas, `;` + decimal `,`, utf-8)
- `dim_produto_1.csv` (2.731 linhas, `;` + decimal `,`, **latin1/cp1252**)
- `dimensao_lojas_2.csv` (11 linhas, `;`, utf-8)
- `dimensao_precos_2.csv` (28.560 linhas, `;` + decimal `,`, utf-8)
- `dimensao_voltagem_2.csv` (~67 pares, `;`, utf-8)
- `Descr_unidades_medida_2.csv` (~51 unidades, `;`, utf-8)
- `Descritivo_bases_de_dados_2.xlsx` (dicionário de dados — leitura via `openpyxl`, para conferir decisões de parsing)
- `Estudo_de_caso_1.docx` (enunciado — `BLOQUEADO` para leitura programática: nenhuma lib docx em `requirements.txt`; se necessário, ler manualmente e transcrever o essencial para docs)

## Arquivos de saída esperados

- `src/io.py` — funções centralizadas de leitura (encoding, separador, decimal, datas, moeda, códigos como string quando necessário, logging, erros claros).
- `docs/data_formatting_and_encoding.md` — documentação de todas as decisões de parsing por arquivo.
- `outputs/tables/ingestion_audit.csv` — uma linha por arquivo bruto com as colunas exigidas pelo SDD.MD (seção 8): nome, caminho, encodings testados/usados, separador, linhas/colunas lidas, colunas esperadas/ausentes/extras, erros de parsing, colunas convertidas (data/número/moeda), nulos antes/depois, zeros criados, registros descartados e motivo, status final.
- `tests/test_ingestion.py`.

## Regras de negócio envolvidas

- Códigos (`CODIGO`, `COD_EMPRESA`, `DIGITO`, `CD_VOLTAGEM`, `COD_UNIDADE`) são identificadores, não medidas: nunca somar; preservar como estão (decisão string vs. int deve ser tomada após validar existência de zeros à esquerda — ver Dúvidas).
- `dim_produto` deve ter 1 linha por produto após deduplicação **documentada** (hoje o `drop_duplicates` é silencioso).
- Nulo criado por coerção ≠ zero: nenhuma coerção pode criar zeros implícitos.
- Nenhuma transformação de encoding, número, data, moeda ou categoria pode ficar implícita (princípio 39 do SDD.MD... — seção 8, "Nenhuma transformação... deve ficar implícita").

## Métricas afetadas

Todas as métricas downstream, pois derivam das bases ingeridas — em particular:
- `RECEITA = QUANTIDADE_VENDIDA × PRECO_UNIT_MEDIO` ([01_etl.py:175](../src/01_etl.py#L175));
- `QTD_VENDA_ESTOQUE = QUANTIDADE_VENDIDA × CONVERSAO_VENDA_PARA_ARMAZENAGEM` ([01_etl.py:177-179](../src/01_etl.py#L177-L179));
- saldo de estoque projetado, cobertura, dispersão de preço, correlação preço×volume, projeção 2026.

## Mudanças propostas

1. Criar `src/io.py` com função central `read_raw(nome_logico)` (nome final a definir na implementação) que encapsula, por arquivo: encoding com fallback testado (`utf-8` → `latin1`/`cp1252`), separador, decimal, parse de datas, dtypes, limpeza de espaços/NBSP, tratamento de `Unnamed`, sentinelas (`NA`, `N/A`, `-`, `null`, `None`, string vazia) e contagem de nulos antes/depois.
2. Gerar `outputs/tables/ingestion_audit.csv` a partir dessas leituras (novo script ou função de auditoria chamada pelos testes — sem alterar `01_etl.py` nesta spec; a substituição da leitura inline pelo `src/io.py` dentro do `01_etl.py` fica condicionada a reproduzir os Parquet atuais byte-idêntico ou com diffs justificados).
3. Ler `Descritivo_bases_de_dados_2.xlsx` (openpyxl já está no `requirements.txt`) e confrontar cada decisão de parsing com o dicionário; registrar divergências em `docs/data_formatting_and_encoding.md`.
4. Validar explicitamente na base completa (não só amostra): sentinelas, zeros à esquerda em códigos, duplicidades de `dim_produto`, valores monetários com `R$` (não observados até agora — `NÃO VALIDADO`), datas fora de jan/2024–dez/2025.

## Testes necessários

`tests/test_ingestion.py` deve validar (conforme SDD.MD seção 8):
- `src/io.py` existe e expõe as funções principais de leitura;
- os 8 CSVs brutos são lidos sem erro;
- `outputs/tables/ingestion_audit.csv` é gerado e tem as colunas obrigatórias;
- encoding e separador usados ficam registrados por arquivo;
- número de linhas lidas > 0 e igual às contagens conhecidas (1.090.390 vendas; 1.393 compras; 25.330 estoque; 2.731 produtos; 11 lojas; 28.560 preços);
- erros de parsing são registrados; nulos antes/depois são contados;
- códigos não perdem zeros à esquerda (teste com fixture sintética, já que a existência real é `NÃO VALIDADO`);
- decimal brasileiro (`1.234,56`) e datas BR/ISO são convertidos corretamente (fixtures sintéticas);
- `dim_produto` lido como utf-8 corrompe / lido como latin1 não corrompe (prova do encoding).

## Critérios de aceite

- `src/io.py`, `docs/data_formatting_and_encoding.md` e `outputs/tables/ingestion_audit.csv` existem;
- toda transformação de encoding/número/data/moeda está documentada e logada;
- nenhuma decisão de parsing permanece implícita;
- contagens de linhas batem com as declaradas na Spec 00 ou a diferença está explicada no audit;
- `pytest tests/test_ingestion.py` passa;
- os Parquet de `data/processed/` **não são alterados** por esta spec (ou qualquer diff é documentado).

## O que não será feito

- Não será reescrito `01_etl.py` além do mínimo (idealmente nada nesta spec — `io.py` nasce em paralelo e a troca da leitura inline é decisão registrada à parte).
- Não serão criados schemas/pandera (Spec 02), métricas (Spec 03) nem análises (Specs 04–06).
- Não será tocado `reports/relatorio_final.md` nem criado dashboard.
- Não serão apagados nem regravados os arquivos brutos de `data/raw/`.

## Dúvidas ou bloqueios

- `NÃO VALIDADO` — Existem códigos com zeros à esquerda nas bases reais? (Define se `CODIGO` deve virar string; hoje é `Int64`.)
- `NÃO VALIDADO` — `Descr_unidades_medida_2.csv` perdeu acentos na origem ou é assim mesmo?
- `DADO AUSENTE` — Conteúdo do `Descritivo_bases_de_dados_2.xlsx` ainda não foi lido; pode alterar decisões de tipo/chave.
- `BLOQUEADO` — `Estudo_de_caso_1.docx` sem biblioteca de leitura no `requirements.txt`; decidir entre adicionar `python-docx` (mudança de dependência) ou transcrição manual.
- `NÃO VALIDADO` — `dim_produto.DIGITO` participa da chave de negócio? (Pergunta 8 da Spec 00.)
