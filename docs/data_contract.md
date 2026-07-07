# Contrato de dados — Spec 02

> Gerado na Spec 02 (2026-07-07). Código executável do contrato:
> [src/validation/schemas.py](../src/validation/schemas.py) (pandera) e
> [src/validation/quality_checks.py](../src/validation/quality_checks.py).
> Auditoria: `python src/02_quality_audit.py` → [outputs/tables/data_quality_report.csv](../outputs/tables/data_quality_report.csv).
> Fontes: dicionário oficial `data/raw/Descritivo_bases_de_dados_2.xlsx` (lido na Spec 01),
> [docs/data_formatting_and_encoding.md](data_formatting_and_encoding.md) e inspeção
> empírica das bases completas em 2026-07-07.
> Divergência entre este documento e `schemas.py` é bug.

## Decisão de dependência (obrigatória da Spec 02)

`pandera` **não estava** no `requirements.txt`. Foi testado e instalado neste ambiente:

- **pandera==0.32.1** (congelado em `requirements.txt`), validado com pandas 3.0.3,
  numpy 2.5.1, Python 3.14.6 em 2026-07-07 (schema aceita DataFrame válido e rejeita
  inválido com `SchemaErrors`/failure cases — smoke test executado antes da adoção).
- API usada: `pandera.pandas` (obrigatória a partir da série 0.32).
- Nenhum outro pacote foi adicionado. Great Expectations descartado (simplicidade).

## Convenções do contrato

- **Tipos**: são os produzidos por [src/io.py](../src/io.py) (Spec 01): códigos `Int64`;
  numéricos decimal-US `float64`; numéricos decimal-BR `Float64`; datas `datetime64`
  (resolução não fixada); texto sem dtype fixado (nulidade/domínio são checados; o
  dtype físico de string varia entre versões do pandas).
- **Período contratado**: 2024-01-01 a 2025-12-31 (100% das datas dentro — validado).
- **Status dos checks**: `PASS` (0 afetados ou informativo), `WARN` (degrada, não
  invalida), `FAIL` (invalida ou torna não comprovável conclusão importante do relatório).
- A Spec 02 **mede e reporta**; nenhum check corrige, imputa ou descarta dados.

## Unicidade validada (grão real, testado em 2026-07-07 nas bases completas)

Resposta ao `NÃO VALIDADO` da Spec 00 — agora com número:

| Tabela | Chave/grão testado | Duplicatas | Veredito |
|---|---|---|---|
| `dim_produto` | `CODIGO` | **0** em 2.731 | chave confirmada (`DIGITO` é dígito verificador, fora da chave) |
| `dim_lojas` | `COD_EMPRESA` | **0** em 11 | chave confirmada |
| `dim_precos` | `CODIGO + COD_EMPRESA` | **0** em 28.560 | chave confirmada |
| `dim_voltagem` | `CD_VOLTAGEM + CD_EMPRESA` | **0** em 67 | chave confirmada |
| `dim_unidades` | `COD_UNIDADE` | **0** em 51 | chave confirmada |
| `fato_estoque_inicial` | `CODIGO + COD_EMPRESA` | **0** em 25.330 | grão confirmado |
| `fato_vendas` | `CODIGO + COD_EMPRESA + DATA_VENDA + EMBALAGEM` | **0** em 1.090.390 | **grão diário agregado CONFIRMADO** (pergunta 9 da Spec 00 respondida) |
| `fato_compras` | `CODIGO + COD_EMPRESA + DATA_ENTRADA + EMBALAGEM_FORNECEDOR` | **0** em 1.393 | grão confirmado (único até sem `EMBALAGEM_FORNECEDOR`) |

Consequência: o `drop_duplicates` do ETL legado é no-op; receita/quantidade **não**
estão infladas por duplicidade de grão (risco da Spec 02 afastado com evidência).

---

## Tabelas brutas

### 1. `fato_vendas` (`data/raw/fato_vendas_1.csv`, 1.090.390 linhas)

- **Finalidade**: fatos de venda para receita, quantidade, sortimento e preço praticado.
- **Grão**: produto × loja × dia × embalagem (**agregado diário** — `PRECO_UNIT_MEDIO`
  é "preço unitário médio do dia", dicionário oficial; não há ID de transação, logo
  contagem de linhas ≠ contagem de cupons/pedidos).
- **Chave composta**: `CODIGO + COD_EMPRESA + DATA_VENDA + EMBALAGEM` (0 duplicatas).
- **Colunas obrigatórias/tipos/nulidade/domínio**:

| Coluna | Tipo | Nulidade | Domínio / regra |
|---|---|---|---|
| `DATA_VENDA` | datetime | não nulo | 2024-01-02 a 2025-12-31 (dentro do período) |
| `COD_EMPRESA` | Int64 | não nulo | FK → `dim_lojas` (0 órfãos) |
| `CODIGO` | Int64 | não nulo | FK → `dim_produto` (0 órfãos) |
| `DIGITO` | Int64 | não nulo | dígito verificador; consistente com `dim_produto` (0 divergências) |
| `EMBALAGEM` | Int64 | não nulo | 0=padrão, 1/2=preço especial (dicionário); observado: só 0 (1.090.090) e 1 (300) |
| `QUANTIDADE_VENDIDA` | float64 | não nulo | > 0 (0 zeros, 0 negativos) — em **embalagem vendida** |
| `CONVERSAO_VENDA_PARA_ARMAZENAGEM` | float64 | não nulo | > 0; ≠ 1 em 1.815 linhas (0,17%) |
| `UNIDADE_DA_VENDA` | texto | não nulo | domínio de `dim_unidades.COD_UNIDADE` (0 fora) |
| `PRECO_UNIT_MEDIO` | float64 | não nulo | > 0 (0 zeros/negativos); média **diária** |

- **Regras de negócio**: venda em unidade de armazenagem = `QUANTIDADE_VENDIDA ×
  CONVERSAO_VENDA_PARA_ARMAZENAGEM`; venda observada ≠ demanda real.
- **Integridade referencial**: produto, loja e unidade — 0 órfãos (validado).
- **Completude temporal**: 24/24 meses com vendas.
- **Consistência de unidades**: 5.539 linhas (0,51%) com `UNIDADE_DA_VENDA` ≠
  `UNIDADE_ESTOQUE` do produto; destas, **3.725 com conversão = 1** (`WARN` —
  possível conversão faltante; validar com o negócio).
- **Impacto no relatório**: receita/quantidade/sortimento saem daqui; grão validado
  afasta o risco de inflação por duplicidade. A linha "n° de transações = count"
  do legado deve ser lida como "linhas de venda diárias", não cupons.

### 2. `fato_compras` (`data/raw/fato_compras_2.csv`, 1.393 linhas)

- **Finalidade**: entradas de compra (única fonte de reposição disponível).
- **Grão**: produto × loja × data de entrada × embalagem do fornecedor (0 duplicatas).
- **Chave composta**: `CODIGO + COD_EMPRESA + DATA_ENTRADA + EMBALAGEM_FORNECEDOR`.
- **Colunas**:

| Coluna | Tipo | Nulidade | Domínio / regra |
|---|---|---|---|
| `DATA_ENTRADA` | datetime | não nulo | 2024-01-03 a 2025-12-17 (dentro do período) |
| `COD_EMPRESA` | Int64 | não nulo | FK → `dim_lojas` (0 órfãos) |
| `CODIGO` | Int64 | não nulo | FK → `dim_produto` (0 órfãos) |
| `EMBALAGEM_FORNECEDOR` | texto | 1 nulo (`WARN`) | descrição da embalagem de compra |
| `QUANTIDADE_COMPRA` | float64 | não nulo | > 0; em **EMBALAGEM DE COMPRA do fornecedor** (dicionário) — exige `CONVERSAO_COMPRA_ARMAZENAGEM` para unidade de estoque |
| `UNIDADE_ESTOQUE` | texto | não nulo | domínio de `dim_unidades` (0 fora); idêntica à do cadastro (0 divergências) |
| `PRECO_UNIT_UNIDADE_COMPRA` | float64 | **132 nulos (9,5%) — `FAIL`** | > 0 quando presente; preço por embalagem de compra |

- **Regras de negócio**: compra em unidade de armazenagem = `QUANTIDADE_COMPRA ×
  CONVERSAO_COMPRA_ARMAZENAGEM`. **Nulo de preço de compra não pode entrar em
  custo/CMV sem regra explícita** (nulo crítico).
- **Completude temporal**: 24/24 meses com compras (mas volume mensal cai de ~111
  para 9 registros — medido, interpretação é Spec 04/05).
- **Cobertura (`FAIL` — invalida conclusão causal do relatório)**: só **7 de 11
  lojas** têm alguma compra (faltam lojas 1, 4, 8, 9) e só **329 de 2.731 produtos**;
  1.393 registros em 24 meses é implausível como universo de reposição.
- **Consistência de unidades**: no dado atual, **0 das 1.393 linhas** são de produtos
  com conversão ≠ 1 — o erro de unidade do `02_estoque_projetado.py` (que soma
  `QUANTIDADE_COMPRA` crua) **não se materializa no dado atual**, mas é risco
  latente para novas extrações (`WARN`; correção do uso é Spec 04).
- **Impacto no relatório**: a conclusão central "compras encolheram → sortimento caiu"
  fica **não comprovável** com esta base (limitação estrutural, não bug).

### 3. `fato_estoque_inicial` (`data/raw/fato_estoque_inicial_2.csv`, 25.330 linhas)

- **Finalidade**: posição inicial de estoque por produto × loja.
- **Grão/chave**: `CODIGO + COD_EMPRESA` (0 duplicatas); 2.731 produtos × 11 lojas
  (não é o produto cartesiano completo: 25.330 < 30.041).
- **Colunas**:

| Coluna | Tipo | Nulidade | Domínio / regra |
|---|---|---|---|
| `COD_EMPRESA` | Int64 | não nulo | FK → `dim_lojas` (0 órfãos) |
| `CODIGO` | Int64 | não nulo | FK → `dim_produto` (0 órfãos) |
| `ESTOQUE_INICIAL` | Float64 | não nulo | ≥ 0; já em **unidade de estoque** (dicionário) — sem conversão |

- **Regra de negócio**: **nulo de estoque não é estoque zero** — aqui não há nulos,
  mas **12.052 pares (47,6%) têm zero explícito** (`WARN`: confirmar com o negócio
  se é posição real ou falta de inventário; nenhum check imputa nada).
- **Impacto no relatório**: base do saldo projetado e da "cobertura em dias"; o zero
  em massa pode transformar "sem inventário" em "ruptura" indevidamente.

### 4. `dim_produto` (`data/raw/dim_produto_1.csv`, 2.731 linhas)

- **Finalidade**: cadastro de produtos, hierarquia (NIVEL_1/2/3), embalagens e conversões.
- **Grão/chave**: `CODIGO` (0 duplicatas). `DIGITO` = dígito verificador (fora da chave).
- **Colunas**:

| Coluna | Tipo | Nulidade | Domínio / regra |
|---|---|---|---|
| `CODIGO` | Int64 | não nulo, único | ≥ 1 |
| `DIGITO` | Int64 | não nulo | dígito verificador |
| `DESCRICAO` | texto | não nulo | 2.033 linhas com espaços internos duplicados (herdado; normalização estética não é escopo) |
| `NIVEL_1/2/3` | texto | não nulo | hierarquia mercadológica |
| `EMBALAGEM_FORNECEDOR` | texto | 59 nulos (estrutural) | |
| `EMBALAGEM_COMPRA` | texto | não nulo | |
| `CONVERSAO_COMPRA_ARMAZENAGEM` | Float64 | não nulo | > 0; **≠ 1 em 226 produtos (8,3%)** — embalagem de compra ≠ unidade de estoque (`WARN` de unidade) |
| `UNIDADE_ESTOQUE` | texto | não nulo | domínio de `dim_unidades` (0 fora) |
| `EMBALAGEM_VENDA_0` | texto | não nulo | embalagem padrão |
| `EMBALAGEM_VENDA_1/2` | texto | 1.793/1.854 nulos (estrutural) | embalagens especiais opcionais |
| `CD_VOLTAGEM` | Int64 | **48 nulos (`WARN`)** | 0 = "sem voltagem" (dicionário); demais no domínio de `dim_voltagem` (0 fora) |

- **Decisão de contrato (CD_VOLTAGEM)**: **vazio ≠ 0**. O dicionário define 0 como
  "sem voltagem"; o vazio não está definido, logo é **dado faltante** (`WARN`, medir
  e completar cadastro) — não é equiparado a 0 nem imputado.
- **Impacto no relatório**: hierarquia alimenta os rankings por categoria; conversão
  de compra é o coração da reconciliação de estoque (Spec 04).

### 5. `dim_lojas` (`data/raw/dimensao_lojas_2.csv`, 11 linhas)

- **Grão/chave**: `COD_EMPRESA` (0 duplicatas). Valores: 1–9, 92, 93 (buracos na
  numeração são herdados da origem).
- **Colunas**: `COD_EMPRESA` Int64 não nulo único ≥ 1; `CD_CIDADE`, `CD_ESTADO`
  texto não nulo.
- **Impacto no relatório**: base do same-store e das análises por loja/estado.

### 6. `dim_precos` (`data/raw/dimensao_precos_2.csv`, 28.560 linhas)

- **`DADO AUSENTE`**: única base **sem aba no dicionário oficial** — o contrato
  desta tabela é inteiramente empírico (inspeção do arquivo).
- **Grão/chave**: `CODIGO + COD_EMPRESA` (0 duplicatas); 2.731 produtos × 11 lojas
  (também não cartesiano completo).
- **Colunas**:

| Coluna | Tipo | Nulidade | Domínio / regra |
|---|---|---|---|
| `CODIGO` | Int64 | não nulo | FK → `dim_produto` (0 órfãos) |
| `COD_EMPRESA` | Int64 | não nulo | FK → `dim_lojas` (0 órfãos) |
| `CATEGORIA` | texto | não nulo | rótulo comercial (difere de NIVEL_1? — a reconciliar na Spec 05) |
| `PRECO_EMBALAGEM_0` | Float64 | não nulo | > 0 (0 zeros) — preço da embalagem padrão |
| `PERC_DESCTO_ADICIONAL_EMBALAGEM_0` | Float64 | não nulo | ≥ 0 (22.577 zeros = sem desconto; legítimo) |
| `PRECO_EMBALAGEM_1` | Float64 | 19.142 nulos (estrutural) | ≥ 0; **364 zeros (`WARN`)** em embalagem cadastrada |
| `PRECO_EMBALAGEM_2` | Float64 | 19.785 nulos (estrutural) | ≥ 0; **600 zeros (`WARN`)** |

- **Regra de negócio**: preço 0 em embalagem especial cadastrada deve ser tratado
  como "sem preço válido" nas análises de preço (regra explícita, não silenciosa).
- **Impacto no relatório**: dispersão de preço entre lojas e correlação preço-volume
  usam esta tabela; zeros distorcem amplitude/CV se não forem tratados.

### 7. `dim_voltagem` (`data/raw/dimensao_voltagem_2.csv`, 67 linhas)

- **Grão/chave**: `CD_VOLTAGEM + CD_EMPRESA` (0 duplicatas).
- **Colunas**: `CD_VOLTAGEM` Int64 ≥ 0 não nulo; `CD_EMPRESA` Int64 não nulo,
  FK → `dim_lojas.COD_EMPRESA` (0 órfãos).
- **Nota de nomenclatura**: usa `CD_EMPRESA` enquanto todas as demais usam
  `COD_EMPRESA` (herdado da origem; o contrato registra, não renomeia).
- **Impacto no relatório**: nenhum uso analítico atual; domínio de voltagem.

### 8. `dim_unidades` (`data/raw/Descr_unidades_medida_2.csv`, 51 linhas)

- **Grão/chave**: `COD_UNIDADE` (0 duplicatas) — alfanumérico, sempre string.
- **Colunas**: `COD_UNIDADE` texto não nulo único; `DESCRICAO` texto não nulo
  (acentuação possivelmente perdida na origem — `NÃO VALIDADO`, herdado da Spec 01);
  `COD_IBGE` texto, **1 nulo** na linha `EB` (`WARN` baixa).
- **Impacto no relatório**: dá nome às unidades; sem uso em métrica numérica.

---

## Tabelas processadas (data/processed/*.parquet — geradas pelo pipeline legado)

Os schemas descrevem o que os Parquet **contêm**, sem endossar o cálculo que os
gerou; os problemas de método (unidade de compra, interpretação de saldo) estão
medidos no quality report e serão corrigidos na Spec 04.

### `fato_vendas.parquet` (1.090.390 linhas)

- Bruto + 2 colunas derivadas. Grão idêntico ao bruto (0 duplicatas — validado).
- `RECEITA` float64 ≥ 0 = `QUANTIDADE_VENDIDA × PRECO_UNIT_MEDIO` — **0 divergências**
  (tolerância R$ 0,01; check `receita_consistente` PASS).
- `QTD_VENDA_ESTOQUE` float64 > 0 = `QUANTIDADE_VENDIDA × CONVERSAO_VENDA_PARA_ARMAZENAGEM`
  — **0 divergências** (validado).

### `dim_*.parquet` e `fato_compras.parquet` / `fato_estoque_inicial.parquet`

- Espelhos dos brutos após o parsing do ETL legado (mesmas contagens de linhas:
  2.731 / 11 / 67 / 51 / 28.560 / 1.393 / 25.330). Valem as regras de negócio,
  nulidade e domínio das brutas; os **dtypes físicos divergem** em alguns casos
  (ex.: `dim_produto.parquet` tem `DIGITO` como string e
  `CONVERSAO_COMPRA_ARMAZENAGEM` como `float64`, enquanto o contrato bruto usa
  `Int64`/`Float64`) — divergência herdada do parsing do ETL legado, registrada
  aqui e não corrigida nesta spec.

### `estoque_diario.parquet` (1.116.540 linhas)

- **Grão**: produto × loja × data de evento. Colunas: `QTD_COMPRA` ≥ 0, `QTD_VENDA` ≥ 0,
  `VARIACAO`, `SALDO_ESTOQUE` (cumsum).
- **`FAIL` medido**: `SALDO_ESTOQUE < 0` em **829.285 linhas (74,3%)**.
- **Regra de interpretação obrigatória**: saldo negativo é **gap contábil**
  (base de compras incompleta + `QUANTIDADE_COMPRA` somada sem conversão), **não
  ruptura física**. O relatório atual chama de ruptura — conclusão invalidada.

### `estoque_final_projetado.parquet` (28.721 linhas)

- **Grão**: produto × loja. **`FAIL` medido**: `ESTOQUE_FINAL_PROJETADO < 0` em
  **17.919 linhas (62,4%)**. Mesma regra de interpretação acima.

### `cobertura_estoque.parquet` (25.330 linhas)

- **Grão**: produto × loja (0 duplicatas). `DIAS_COBERTURA_ESTOQUE_INICIAL` deriva
  de `ESTOQUE_INICIAL / VENDA_MEDIA_DIARIA` — herda o `WARN` dos 47,6% de estoque
  inicial zero (cobertura 0 dias pode ser "sem inventário", não ruptura iminente).

---

## Checks de integridade referencial (resultado consolidado)

0 órfãos em todas as combinações: vendas/compras/estoque/preços × produto;
vendas/compras/estoque/preços/voltagem × loja; vendas/compras × unidades.
(Confirma e amplia o `checks_integridade.csv` legado.)

## Checks de completude temporal

- Vendas: 24/24 meses. Compras: 24/24 meses (volume mensal declinante — medido).
- Completude por loja/dia ("dias com venda") é escopo da Spec 05.

## Checks de consistência de unidades

| Check | Resultado | Status |
|---|---|---|
| Venda: unidade ≠ armazenagem com conversão = 1 | 3.725 linhas (0,34%) | WARN |
| Produto: embalagem de compra ≠ armazenagem (conversão ≠ 1) | 226 produtos (8,3%) | WARN |
| Compras existentes que exigiriam conversão ≠ 1 | 0 de 1.393 | PASS (risco latente) |
| `UNIDADE_ESTOQUE` da compra ≠ cadastro | 0 | PASS |

## Impacto consolidado no relatório atual

| Conclusão do relatório | Sustentação após os checks |
|---|---|
| Receita/quantidade/queda de vendas (descritivo) | Sustentada no grão: sem duplicidade, receita consistente, 0 órfãos |
| "Rupturas" por saldo negativo | **Invalidada como ruptura física** — 74% de saldo negativo é gap contábil sob base de compras incompleta (7/11 lojas, 329/2.731 produtos) |
| "Compras caíram → sortimento caiu" (causal) | **Não comprovável** — cobertura de compras FAIL |
| Análises de custo/CMV | **Bloqueadas** sem regra explícita para os 9,5% de compras sem preço |
| Cobertura em dias / estoque parado | Degradada — 47,6% de estoque inicial igual a 0 sem confirmação de inventário |

## Pendências e itens não resolvidos nesta spec

| Item | Status |
|---|---|
| Descrição oficial de `dimensao_precos` | `DADO AUSENTE` (sem aba no dicionário) — contrato empírico |
| Semântica do zero em `ESTOQUE_INICIAL` (47,6%) | `NÃO VALIDADO` — exige confirmação do negócio |
| Semântica do vazio em `CD_VOLTAGEM` (48) | Decisão de contrato: dado faltante (≠ 0); completar cadastro |
| Universo real de entradas (transferências, ajustes, devoluções) | `DADO AUSENTE` — sem ele, conclusões causais de reposição seguem bloqueadas |
| `Estudo_de_caso_1.docx` | `BLOQUEADO` (herdado da Spec 01 — sem lib DOCX) |
| Correção do uso de `QUANTIDADE_COMPRA`/saldo | Escopo da **Spec 04** (aqui apenas medido) |
| Reconciliação `CATEGORIA` (dim_precos) × `NIVEL_1` (dim_produto) | Escopo da **Spec 05** |
