# Formatação e encoding das bases brutas — Spec 01

> Gerado na Spec 01 (2026-07-07). Fonte de código: [src/io.py](../src/io.py).
> Auditoria por arquivo: [outputs/tables/ingestion_audit.csv](../outputs/tables/ingestion_audit.csv).
> Evidências levantadas por sondagem programática das **bases completas** (não amostras),
> confrontadas com o dicionário oficial `data/raw/Descritivo_bases_de_dados_2.xlsx`
> (lido integralmente via openpyxl em 2026-07-07).

## 1. O dicionário oficial (Descritivo_bases_de_dados_2.xlsx)

O arquivo tem 7 abas, cada uma com pares `Coluna | Descrição` (sem tipos, sem chaves formais,
sem domínios): `Dim_produtos`, `dim_unidades`, `dim_Voltagem`, `Dim_lojas`, `Fato_compras`,
`dim_estoque_inicial`, `fato_vendas`.

### O que o dicionário revelou (achados relevantes)

| # | Achado | Fonte (aba) | Impacto |
|---|---|---|---|
| 1 | **`QUANTIDADE_COMPRA` = "Quantidade que entrou no estoque na embalagem compra do fornecedor"** — ou seja, está expressa em *embalagem de compra*, **não** em unidade de armazenagem. | `Fato_compras` | `CONVERSAO_COMPRA_ARMAZENAGEM` ("quantas unidades de estoque compõem a Embalagem de Compra", aba `Dim_produtos`) **deve ser aplicada** às compras. O `02_estoque_projetado.py` soma `QUANTIDADE_COMPRA` crua — para 226 produtos a conversão ≠ 1 (12, 6, 24, 20, 10, 4, 2…), logo há **erro de unidade latente** no saldo de estoque. Correção é escopo da Spec 04. |
| 2 | `PRECO_UNIT_UNIDADE_COMPRA` = "Preço unitário por unidade de quantidade de compra" — preço por embalagem de compra, não por unidade de estoque. | `Fato_compras` | CMV/custo por unidade de estoque exigiria dividir pela conversão. Spec 04. |
| 3 | **`DIGITO` é "Dígito Verificador do produto"** — não é parte da chave de negócio. | `Dim_produtos`, `fato_vendas` | Resolve a dúvida da Spec 00 (pergunta 8): chave do produto é `CODIGO`; `DIGITO` é redundância verificável. |
| 4 | `ESTOQUE_INICIAL` está "na unidade de estoque". | `dim_estoque_inicial` | Estoque inicial não precisa de conversão. |
| 5 | `QUANTIDADE_VENDIDA` = "Quantidade da embalagem vendida"; `CONVERSAO_VENDA_PARA_ARMAZENAGEM` converte venda → unidade de estoque (linha a linha na própria base). | `fato_vendas` | Confirma o cálculo `QTD_VENDA_ESTOQUE` do `01_etl.py` como correto. |
| 6 | `EMBALAGEM` em vendas: 0 = Padrão; 1 e 2 = Preço Especial — casa com `PRECO_EMBALAGEM_0/1/2` e `EMBALAGEM_VENDA_0/1/2`. | `fato_vendas`, `Dim_produtos` | Habilita validação cruzada preço praticado × tabela de preço (Spec 05/06). |
| 7 | `CD_VOLTAGEM = 0` significa "sem voltagem" (não é nulo). | `Dim_produtos` | Regra de domínio para a Spec 02. |
| 8 | `PRECO_UNIT_MEDIO` = "preço unitário médio **do dia** da embalagem vendida". | `fato_vendas` | Confirma grão diário agregado de `fato_vendas` (produto × loja × dia × embalagem), sem ID de transação. |
| 9 | **Não existe aba para `dimensao_precos_2.csv`** — o dicionário não descreve `CATEGORIA`, `PRECO_EMBALAGEM_*` nem `PERC_DESCTO_ADICIONAL_EMBALAGEM_0`. | — | `DADO AUSENTE`: colunas esperadas de `dim_precos` vêm da inspeção do arquivo, não do dicionário. |
| 10 | O dicionário **não define tipos, formatos, unidades numéricas nem chaves primárias** — só descrições textuais. | todas | Tipos/chaves continuam decisão empírica documentada (abaixo) + contrato formal na Spec 02. |

### Divergências dicionário × parsing atual do `01_etl.py`

- **Nenhuma divergência de encoding/separador/decimal**: o dicionário é omisso sobre formato físico; as decisões do ETL foram validadas empiricamente (seção 3).
- **Divergência de unidade (não de parsing)**: achado #1 acima — o ETL lê `QUANTIDADE_COMPRA` corretamente, mas o *uso* downstream (02) ignora a conversão de compra. Registrado aqui e na Spec 04; **nada foi alterado nesta spec**.
- `Estudo_de_caso_1.docx`: **`BLOQUEADO`** — sem biblioteca de leitura de DOCX no `requirements.txt`; nenhuma dependência foi adicionada (decisão de menor risco). Se necessário, transcrever manualmente.

## 2. Validações empíricas nas bases completas (2026-07-07)

Método: leitura byte a byte + `dtype=str, na_filter=False` (nenhuma interpretação implícita do pandas), sobre **todas as linhas** dos 8 CSVs.

| Validação | Resultado |
|---|---|
| Zeros à esquerda em códigos (`CODIGO`, `COD_EMPRESA`, `DIGITO`, `EMBALAGEM`, `CD_VOLTAGEM`, `CD_EMPRESA`, `COD_IBGE`) | **0 ocorrências** em todas as bases → converter códigos numéricos para `Int64` **não perde informação** (o `io.py` ainda assim revalida a cada leitura e mantém string se aparecerem). |
| Sentinelas `NA`, `N/A`, `-`, `null`, `None` | **0 ocorrências literais**. O único "nulo" real é a **string vazia** (ver contagens abaixo). |
| String vazia (após strip) | `fato_compras`: 132 em `PRECO_UNIT_UNIDADE_COMPRA` (9,5% das compras **sem preço**) + 1 em `EMBALAGEM_FORNECEDOR`; `dim_produto`: 59 `EMBALAGEM_FORNECEDOR`, 1.793 `EMBALAGEM_VENDA_1`, 1.854 `EMBALAGEM_VENDA_2`, 48 `CD_VOLTAGEM`; `dim_precos`: 19.142 `PRECO_EMBALAGEM_1`, 19.785 `PRECO_EMBALAGEM_2`; `dim_unidades`: 1 `COD_IBGE` (linha `EB`). |
| Valores monetários com `R$` | **0 ocorrências** em qualquer base. Preços vêm como número puro. O helper `parse_currency_brl` existe e é testado (exigência do SDD), mas não é aplicado a nenhuma coluna real. |
| Datas | 100% ISO `YYYY-MM-DD` nas duas colunas de data: `DATA_VENDA` (1.090.390/1.090.390, de 2024-01-02 a 2025-12-31) e `DATA_ENTRADA` (1.393/1.393, de 2024-01-03 a 2025-12-17). **Nenhuma data BR, nenhum timestamp, nenhuma data fora de jan/2024–dez/2025.** |
| Duplicidades em `dim_produto.CODIGO` | **0 duplicatas** no bruto (2.731 códigos distintos em 2.731 linhas) → o `drop_duplicates(subset=["CODIGO"])` do `01_etl.py` é um no-op hoje (defensivo, não mascarador). |
| NBSP (`0xA0`) | 801 bytes em `dim_produto_1.csv` (causa da falha utf-8); 0 nos demais. |
| Bytes 0x80–0x9F (faixa em que latin1 ≠ cp1252) | **0 bytes** em `dim_produto_1.csv` → latin1 e cp1252 produzem texto **idêntico** para este arquivo; a escolha de `latin1` (igual ao legado) é segura. |
| Espaços | `dim_produto.DESCRICAO`: 2.033 linhas com espaços internos duplicados e 3 com trailing; `EMBALAGEM_VENDA_1/2`: valores `" "` (viram NA); `dim_unidades.DESCRICAO`: 1 trailing (`"PECA (PC) "`). |
| Contagens de linhas | Todas batem com a Spec 00: 1.090.390 vendas; 1.393 compras; 25.330 estoque; 2.731 produtos; 11 lojas; 28.560 preços; 67 voltagem×loja; 51 unidades. |
| Coerções numéricas/data que criaram NA | **0** em todas as bases (`nulos_antes == nulos_depois` no audit) — nenhum valor válido foi perdido por conversão. |
| Nulos × encoding (validado em 2026-07-07) | Releitura dos 4 arquivos com nulos sob utf-8, utf-8-sig, latin1 e cp1252: contagem de nulos **idêntica** em todos os encodings que decodificam (133 / 3.754 / 38.927 / 1), inclusive por coluna. Nulos são campos estruturalmente vazios na origem (`;;`); separadores são ASCII e os encodings candidatos são ASCII-compatíveis, logo encoding não cria nem remove nulos. Os 132 preços de compra ausentes são falta real de dado, não artefato de leitura. |
| Nulos × separador (validado em 2026-07-07) | Releitura das 8 bases trocando `;`↔`,`: com o separador **errado**, ou a leitura falha (`ParserError` em fato_estoque_inicial e dim_produto com `,`) ou a tabela **colapsa em 1 coluna** (demais casos). As contagens de nulos sob separador errado mudam (compras 133→0; preços 38.927→20.553; unidades 1→0), mas são **artefatos sem significado**: vazios reais somem porque ficam colados dentro de uma string única (`...;"";""`), e "nulos" fantasmas surgem quando o parser quebra a linha nas vírgulas **decimais** (`"31,395"` → campos residuais vazios). Nenhuma troca de separador recupera dado ausente; os separadores corretos são os que reproduzem a estrutura de colunas do dicionário oficial (9/7/3/14/3/7/2/3 colunas). |

Achados adicionais da sondagem (registrados para specs futuras):

- `fato_compras` tem compras para **apenas 7 das 11 lojas** e **329 dos 2.731 produtos** — reforça a suspeita de base de compras incompleta (Spec 04).
- `CONVERSAO_VENDA_PARA_ARMAZENAGEM` ≠ 1 em 1.815 linhas de venda (0,17%); `CONVERSAO_COMPRA_ARMAZENAGEM` ≠ 1 em 226 produtos (8,3%).

## 3. Decisões de parsing por arquivo (implementadas em `src/io.py`)

Convenções físicas confirmadas (iguais às do `01_etl.py` legado — nenhuma divergência de leitura encontrada):

| Arquivo | Encoding (testado → usado) | Sep. | Decimal | Datas | Observações |
|---|---|---|---|---|---|
| `fato_vendas_1.csv` | utf-8 → **utf-8** | `,` | `.` | `DATA_VENDA` ISO | coluna `Unnamed: 0` (índice exportado) descartada |
| `fato_compras_2.csv` | utf-8 → **utf-8** | `,` | `.` | `DATA_ENTRADA` ISO | `Unnamed: 0` descartada; 132 preços vazios → NA |
| `fato_estoque_inicial_2.csv` | utf-8 → **utf-8** | `;` | `,` | — | `ESTOQUE_INICIAL` string "0","50" com vírgula decimal → float |
| `dim_produto_1.csv` | utf-8 (**falha byte 2486, 0xA0**) → **latin1** | `;` | `,` | — | 801 NBSP; latin1 ≡ cp1252 aqui (0 bytes 0x80–0x9F) |
| `dimensao_lojas_2.csv` | utf-8 → **utf-8** | `;` | — | — | |
| `dimensao_precos_2.csv` | utf-8 → **utf-8** | `;` | `,` | — | sem aba no dicionário oficial (`DADO AUSENTE`) |
| `dimensao_voltagem_2.csv` | utf-8 → **utf-8** | `;` | — | — | usa `CD_EMPRESA` (≠ `COD_EMPRESA` das demais) |
| `Descr_unidades_medida_2.csv` | utf-8 → **utf-8** | `;` | — | — | `COD_UNIDADE`/`COD_IBGE` mantidos string |

Regras gerais do `io.py` (todas explícitas, logadas e testadas):

1. **Encoding**: decodificação estrita dos bytes completos na ordem `utf-8 → latin1 → cp1252`; o primeiro que decodifica é usado; testados e usado ficam no audit.
2. **Separador**: detectado por contagem no cabeçalho entre `;`, `,` e tab; divergência do esperado gera warning.
3. **Leitura crua**: `dtype=str` + `na_filter=False` — o pandas não interpreta nada sozinho.
4. **Texto**: NBSP → espaço, strip nas pontas. **Espaços internos duplicados são preservados** (decisão: normalização de conteúdo é da Spec 02, não da ingestão).
5. **Sentinelas**: `""`, `NA`, `N/A`, `-`, `null`, `None`, `NULL` (comparação exata pós-strip) → `NA`, contadas em `nulos_antes`.
6. **Códigos**: cada leitura revalida zeros à esquerda (`^0\d+$`); se existirem, a coluna **permanece string** com warning; senão vira `Int64`. Hoje: todos viram `Int64`, exceto `COD_UNIDADE`/`COD_IBGE` (alfanuméricos/código externo — sempre string).
7. **Decimal BR**: remoção de ponto de milhar **apenas** quando o padrão `1.234,56` é inequívoco; depois `,` → `.`. Coerções para NA são contadas e entram em `erros_parsing`.
8. **Decimal US**: `to_numeric` com contagem de coerções.
9. **Datas**: formato detectado e aplicado **explicitamente** (`%Y-%m-%d`, `%d/%m/%Y`, com/sem hora); mistura de formatos gera erro claro, nunca inferência silenciosa.
10. **Moeda**: `parse_currency_brl` (remove `R$` + decimal BR) disponível e testado; nenhuma coluna real precisa dele.
11. **Zeros criados**: nenhuma etapa preenche NA com 0 — `zeros_criados = 0` por construção (auditado).
12. **Descartes**: a ingestão **não descarta linhas** (0 em todas as bases); o filtro de integridade referencial do `01_etl.py` é escopo das Specs 02/04.

## 4. Relação com o pipeline legado

- `src/io.py` **não** substitui a leitura inline do `01_etl.py` nesta spec. Os scripts `01`–`07` e os Parquet de `data/processed/` **não foram alterados**.
- Diferenças deliberadas do `io.py` em relação ao legado (relevantes para eventual troca futura, que exigirá prova de equivalência):
  - `io.py` não faz `drop_duplicates` em `dim_produto` (no-op hoje; deduplicação vira check explícito na Spec 02);
  - `io.py` não aplica `str.title()` em `CD_CIDADE` (transformação estética do legado);
  - `io.py` não remove aspas `"` de `dim_produto` (a remoção do legado é no-op no dado atual);
  - `io.py` converte strings vazias em NA e conta; o legado deixa `" "`/`""` como texto em colunas string;
  - `io.py` não filtra linhas por integridade referencial.

## 5. Pendências desta spec

| Item | Status |
|---|---|
| Conteúdo de `Estudo_de_caso_1.docx` | `BLOQUEADO` — sem lib DOCX no requirements; nenhuma dependência adicionada. |
| Descrição oficial de `dimensao_precos_2.csv` | `DADO AUSENTE` — sem aba no dicionário. |
| Acentuação de `Descr_unidades_medida_2.csv` (DUZIA, GARRAFAO, PECA) | `NÃO VALIDADO` — arquivo é ASCII puro; impossível saber se a perda de acentos ocorreu na origem. |
| Tipos/chaves formais por tabela | `DADO AUSENTE` no dicionário — serão formalizados no contrato de dados (Spec 02) com base empírica. |
| Correção da unidade de `QUANTIDADE_COMPRA` no saldo de estoque | Escopo da **Spec 04** (registrado no achado #1). |
