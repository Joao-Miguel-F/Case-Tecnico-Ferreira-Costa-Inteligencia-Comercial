# Spec/Fase 00 — Discovery do repositório (estado atual)

> Documento de diagnóstico inicial. **Nenhum código do pipeline foi alterado nesta fase.**
> Regras de marcação usadas ao longo do documento:
> - `NÃO VALIDADO` — afirmação plausível, mas ainda não confirmada com evidência reexecutável nesta fase.
> - `DADO AUSENTE` — a informação depende de um dado/arquivo que não está no repositório ou não pôde ser lido.
> - `BLOQUEADO` — não é possível concluir agora por dependência técnica (ex.: bibliotecas não instaladas).
>
> Data do discovery: 2026-07-06. Branch: `main`. Último commit: `7a71b96 final`.

---

## Objetivo de negócio aparente

Analisar 24 meses (jan/2024 – dez/2025) de vendas, compras e estoque de uma **rede de varejo de materiais de construção, reforma, decoração e eletroeletrônicos**, com **11 lojas** em 5 estados do Nordeste (PE, BA, SE, PB, RN), para apoiar decisões de **sortimento, precificação e compras para 2026**.

Fonte da leitura: [README.md](../README.md) e [reports/relatorio_final.md](../reports/relatorio_final.md).

O achado central declarado pelo projeto é uma **queda estrutural de vendas** ao longo do período, que o relatório associa a uma **contração da reposição de estoque (compras)**. Os números-título usados para essa queda **não são idênticos entre os documentos** (ver seção "Riscos analíticos" e "Perguntas em aberto").

---

## Estrutura atual do repositório

```
.
├── .gitignore
├── README.md
├── SDD.MD                     # prompt/spec de Spec Driven Development (este trabalho)
├── requirements.txt           # pandas, numpy, matplotlib, pyarrow, openpyxl
├── data/
│   ├── raw/                    # 9 arquivos brutos (CSV/XLSX/DOCX)
│   └── processed/             # 11 arquivos .parquet gerados pelo pipeline
├── src/                       # 7 scripts numerados 01..07 (.py)
├── outputs/
│   ├── figures/               # 9 arquivos .png
│   └── tables/                # 30 arquivos .csv
└── reports/
    └── relatorio_final.md     # relatório final narrativo
```

Observações:
- **Não existe** pasta `specs/` além do que este discovery cria, nem pasta `tests/`, nem `docs/`, nem `Makefile`, nem `pyproject.toml` (todos previstos em specs futuras do `SDD.MD`, ainda não criados).
- `.gitignore` ignora `__pycache__/`, `*.pyc`, `.DS_Store`, `.ipynb_checkpoints/`, `.venv/`, `venv/`.
- **Nenhum notebook** (`.ipynb`) foi encontrado.

---

## Scripts existentes

Pasta [src/](../src/), todos em Python, cabeçalho `# -*- coding: utf-8 -*-`, sem `if __name__ == "__main__"` (executam no import/topo do módulo):

| Script | Responsabilidade declarada | Lê de | Escreve em |
|---|---|---|---|
| [01_etl.py](../src/01_etl.py) | Leitura das bases brutas, tratamento de encoding/separador/decimal, checagem de integridade referencial, cálculo de `RECEITA` e `QTD_VENDA_ESTOQUE`, gravação em Parquet | `data/raw` | `data/processed/*.parquet`, `outputs/tables/checks_integridade.csv` |
| [02_estoque_projetado.py](../src/02_estoque_projetado.py) | Saldo acumulado (estoque inicial + compras − vendas) por produto/loja/dia; rupturas (saldo negativo); produtos sem movimentação | `data/processed` | `estoque_diario.parquet`, `estoque_final_projetado.parquet`, `rupturas_estoque.csv`, `produtos_sem_movimentacao.csv` |
| [03_analise_vendas.py](../src/03_analise_vendas.py) | Ranking de produtos, análise por categoria (NIVEL_1), por loja/estado, sazonalidade mensal e heatmap por categoria | `data/processed` | rankings, `vendas_por_*`, `vendas_mensais.csv`, `sazonalidade_por_categoria_mes.csv`, `produtos_sem_nenhuma_venda.csv`, 5 figuras |
| [04_analise_estoque.py](../src/04_analise_estoque.py) | Dias de cobertura (estoque inicial / venda média diária), estoque parado, risco de ruptura, matriz giro×cobertura | `data/processed` | `cobertura_estoque_completa.csv`, `produtos_estoque_parado.csv`, `produtos_risco_ruptura.csv`, `cobertura_estoque.parquet`, 1 figura |
| [05_precificacao.py](../src/05_precificacao.py) | Dispersão de preço entre lojas; correlação preço × volume ("elasticidade aproximada") | `data/processed` | `dispersao_preco_entre_lojas.csv`, `correlacao_preco_volume.csv`, `produtos_elasticidade_negativa_forte.csv`, `produtos_correlacao_positiva_preco_volume.csv`, 2 figuras |
| [06_projecao_compras.py](../src/06_projecao_compras.py) | Projeção de demanda 2026 (tendência linear por produto + índice sazonal por categoria), estoque de segurança 30d, sugestão de compra | `data/processed` | `projecao_demanda_mensal_2026.csv`, `projecao_compras_2026.csv`, 1 figura |
| [07_recomendacoes.py](../src/07_recomendacoes.py) | Consolida candidatos a promoção, descontinuação, repricing; resumo executivo | `outputs/tables`, `data/processed` | `rec_candidatos_promocao.csv`, `rec_candidatos_descontinuacao.csv`, `rec_repricing_padronizacao.csv`, `rec_repricing_elasticidade.csv`, `resumo_executivo.csv` |

**Divergência importante:** o [reports/relatorio_final.md](../reports/relatorio_final.md) menciona uma etapa **"3b — Investigação de causa-raiz"** e afirma que o pipeline é "executável em sequência (`01_` a `08_`)". **Não existe** script `3b` nem script `08` em `src/`. Ver "Riscos analíticos". `NÃO VALIDADO`.

---

## Ordem atual de execução

Conforme [README.md](../README.md):

```bash
pip install -r requirements.txt
cd src
python 01_etl.py
python 02_estoque_projetado.py
python 03_analise_vendas.py
python 04_analise_estoque.py
python 05_precificacao.py
python 06_projecao_compras.py
python 07_recomendacoes.py
```

Notas:
- Os scripts usam **caminhos relativos** (`../data/raw`, `../data/processed`, `../outputs/...`) e portanto **precisam ser executados de dentro de `src/`**. Rodar da raiz quebra os caminhos. (Risco de reprodutibilidade.)
- Há **dependência sequencial**: 03→04 gera `cobertura_estoque.parquet` consumido por 06; 07 lê CSVs produzidos por 03/04/05/06. Não há orquestrador (`Makefile`/`make run`).
- **Reprodução VALIDADA em cópia isolada (2026-07-06):** com as dependências instaladas em uma `.venv` (pandas 3.0.3, numpy 2.5.1, matplotlib 3.11.0, pyarrow 24.0.0, openpyxl 3.1.5), o pipeline `01→07` foi reexecutado numa **cópia isolada** (scratchpad, sem tocar no repo). Os 7 scripts rodaram **sem erro (exit 0)** e a comparação célula a célula mostrou que **os 27 CSVs de `outputs/tables` e os 11 Parquet de `data/processed` reproduzem de forma idêntica** (tolerância 1e-6) os arquivos commitados. Conclusão: o pipeline é reprodutível do zero e o risco de drift de versão (pandas 3.x/numpy 2.x) **não se materializou** para este código. Ainda assim não reexecutei sobre o repo real (outputs commitados preservados).

---

## Bases disponíveis

Pasta [data/raw/](../data/raw/). Contagens de linha e integridade conferidas em [outputs/tables/checks_integridade.csv](../outputs/tables/checks_integridade.csv) e no README.

| Arquivo | Tipo | Sep. campo | Decimal | Encoding | Linhas (declarado) |
|---|---|---|---|---|---|
| `fato_vendas_1.csv` | fato | `,` | `.` | utf-8 | 1.090.390 |
| `fato_compras_2.csv` | fato | `,` | `.` | utf-8 | 1.393 |
| `fato_estoque_inicial_2.csv` | fato | `;` | `,` | utf-8 | 25.330 |
| `dim_produto_1.csv` | dimensão | `;` | `,` | **latin1/cp1252** | 2.731 |
| `dimensao_lojas_2.csv` | dimensão | `;` | — | utf-8 | 11 |
| `dimensao_precos_2.csv` | dimensão | `;` | `,` | utf-8 | 28.560 |
| `dimensao_voltagem_2.csv` | dimensão | `;` | — | utf-8 | ~67 pares (contados na inspeção) |
| `Descr_unidades_medida_2.csv` | dicionário | `;` | — | utf-8 (aparência ASCII, sem acentos) | ~51 unidades (contadas na inspeção) |
| `Descritivo_bases_de_dados_2.xlsx` | dicionário de dados | — | — | — | `DADO AUSENTE` nesta fase (não lido — sem biblioteca para XLSX) |
| `Estudo_de_caso_1.docx` | enunciado do case | — | — | — | `DADO AUSENTE` nesta fase (não lido — formato DOCX) |

Bases processadas em [data/processed/](../data/processed/) (11 Parquet): `dim_produto`, `dim_lojas`, `dim_voltagem`, `dim_unidades`, `dim_precos`, `fato_estoque_inicial`, `fato_compras`, `fato_vendas`, `estoque_diario`, `estoque_final_projetado`, `cobertura_estoque`.

O conteúdo detalhado de `Descritivo_bases_de_dados_2.xlsx` (dicionário coluna a coluna) **não foi lido** nesta fase — marcado `DADO AUSENTE`; deve ser inspecionado na Spec 01/02.

---

## Grão aparente de cada tabela

Baseado na inspeção dos cabeçalhos e amostras dos arquivos brutos. Grão **aparente** — a unicidade de chave **não foi testada** nesta fase (`NÃO VALIDADO`).

| Tabela | Colunas observadas | Grão aparente |
|---|---|---|
| `fato_vendas_1.csv` | `<índice sem nome>`, `DATA_VENDA`, `COD_EMPRESA`, `CODIGO`, `DIGITO`, `EMBALAGEM`, `QUANTIDADE_VENDIDA`, `CONVERSAO_VENDA_PARA_ARMAZENAGEM`, `UNIDADE_DA_VENDA`, `PRECO_UNIT_MEDIO` | linha de venda por produto × loja × dia × embalagem (possivelmente já agregada por dia; **não há ID de transação/pedido**) `NÃO VALIDADO` |
| `fato_compras_2.csv` | `<índice sem nome>`, `DATA_ENTRADA`, `COD_EMPRESA`, `CODIGO`, `EMBALAGEM_FORNECEDOR`, `QUANTIDADE_COMPRA`, `UNIDADE_ESTOQUE`, `PRECO_UNIT_UNIDADE_COMPRA` | entrada de compra por produto × loja × data × embalagem do fornecedor |
| `fato_estoque_inicial_2.csv` | `COD_EMPRESA`, `CODIGO`, `ESTOQUE_INICIAL` | posição de estoque por produto × loja (1 valor inicial) |
| `dim_produto_1.csv` | `CODIGO`, `DIGITO`, `DESCRICAO`, `NIVEL_1`, `NIVEL_2`, `NIVEL_3`, `EMBALAGEM_FORNECEDOR`, `EMBALAGEM_COMPRA`, `CONVERSAO_COMPRA_ARMAZENAGEM`, `UNIDADE_ESTOQUE`, `EMBALAGEM_VENDA_0/1/2`, `CD_VOLTAGEM` | produto (`CODIGO`) — o ETL faz `drop_duplicates(subset=["CODIGO"])`, o que indica duplicidades no bruto `NÃO VALIDADO` |
| `dimensao_lojas_2.csv` | `COD_EMPRESA`, `CD_CIDADE`, `CD_ESTADO` | loja (`COD_EMPRESA`) |
| `dimensao_precos_2.csv` | `CODIGO`, `COD_EMPRESA`, `CATEGORIA`, `PRECO_EMBALAGEM_0`, `PERC_DESCTO_ADICIONAL_EMBALAGEM_0`, `PRECO_EMBALAGEM_1`, `PRECO_EMBALAGEM_2` | preço por produto × loja (× tipo de embalagem, em colunas) |
| `dimensao_voltagem_2.csv` | `CD_VOLTAGEM`, `CD_EMPRESA` | voltagem disponível por loja (par voltagem × loja) |
| `Descr_unidades_medida_2.csv` | `COD_UNIDADE`, `DESCRICAO`, `COD_IBGE` | unidade de medida (`COD_UNIDADE`) |

---

## Chaves aparentes

Inferidas do uso no ETL/joins ([01_etl.py](../src/01_etl.py), [03_analise_vendas.py](../src/03_analise_vendas.py)). Unicidade/integridade **não retestada** aqui além do que já está em `checks_integridade.csv`.

- `dim_produto`: PK aparente `CODIGO`. (Existe também `DIGITO`; não é usado como parte da chave nos joins — possível chave composta `CODIGO+DIGITO` no negócio, `NÃO VALIDADO`.)
- `dim_lojas`: PK aparente `COD_EMPRESA`. Valores observados: `1..9`, `92`, `93` (11 lojas, com "buracos" na numeração).
- `dim_precos`: chave composta aparente `CODIGO + COD_EMPRESA`.
- `dim_voltagem`: chave composta `CD_VOLTAGEM + CD_EMPRESA`.
- `fato_vendas` → FKs `CODIGO`→`dim_produto`, `COD_EMPRESA`→`dim_lojas`.
- `fato_compras` → FKs `CODIGO`→`dim_produto`, `COD_EMPRESA`→`dim_lojas`.
- `fato_estoque_inicial` → chave/grão `CODIGO + COD_EMPRESA`; FKs para as dimensões.
- Integridade referencial vendas/compras/estoque×dimensões: **0% de órfãos** conforme `checks_integridade.csv` (evidência validada e commitada).
- **Inconsistência de nomenclatura de chave:** `dimensao_voltagem` usa `CD_EMPRESA`, enquanto todas as demais bases usam `COD_EMPRESA`.

---

## Outputs existentes

### Tabelas — [outputs/tables/](../outputs/tables/) (30 CSV)
`checks_integridade.csv`, `ranking_produtos_completo.csv`, `top20_produtos_receita.csv`, `bottom20_produtos_receita.csv`, `top20_produtos_quantidade.csv`, `produtos_sem_nenhuma_venda.csv`, `vendas_por_categoria_nivel1.csv`, `vendas_por_loja.csv`, `vendas_por_estado.csv`, `vendas_mensais.csv`, `sazonalidade_por_categoria_mes.csv`, `rupturas_estoque.csv`, `produtos_sem_movimentacao.csv`, `cobertura_estoque_completa.csv`, `produtos_estoque_parado.csv`, `produtos_risco_ruptura.csv`, `dispersao_preco_entre_lojas.csv`, `correlacao_preco_volume.csv`, `produtos_elasticidade_negativa_forte.csv`, `produtos_correlacao_positiva_preco_volume.csv`, `projecao_demanda_mensal_2026.csv`, `projecao_compras_2026.csv`, `rec_candidatos_promocao.csv`, `rec_candidatos_descontinuacao.csv`, `rec_repricing_padronizacao.csv`, `rec_repricing_elasticidade.csv`, `resumo_executivo.csv`.

### Figuras — [outputs/figures/](../outputs/figures/) (9 PNG)
`receita_por_categoria.png`, `top15_produtos_receita.png`, `receita_por_loja.png`, `sazonalidade_mensal.png`, `heatmap_sazonalidade_categoria.png`, `matriz_giro_cobertura.png`, `dispersao_preco_lojas.png`, `distribuicao_correlacao_preco_volume.png`, `projecao_demanda_2026.png`.

### Relatório
[reports/relatorio_final.md](../reports/relatorio_final.md).

**Outputs citados no relatório mas SEM script/tabela correspondente no repo** (`NÃO VALIDADO` / possível `DADO AUSENTE`): não há tabela de same-store YoY, YoY por categoria, YoY por loja, "SKUs distintos comprados por mês" (74→14), "SKUs distintos vendidos por mês" (2.490→1.212) nem a "correlação 0,49" entre SKUs comprados e vendidos — números centrais da Seção 2 do relatório. Nenhum dos 7 scripts existentes produz esses artefatos.

---

## Principais KPIs usados

Extraídos diretamente do código dos scripts:

- **Receita** = `QUANTIDADE_VENDIDA × PRECO_UNIT_MEDIO` (01_etl).
- **Quantidade vendida em unidade de estoque** = `QUANTIDADE_VENDIDA × CONVERSAO_VENDA_PARA_ARMAZENAGEM` (01_etl).
- **Ranking de produtos**: receita, qtd vendida (unid. estoque), nº de transações (`count`), lojas distintas.
- **Receita por categoria (NIVEL_1) / por loja / por estado**; `pct_receita`.
- **Sazonalidade mensal** (receita e quantidade por `ANO_MES`) e heatmap relativo por categoria×mês.
- **Saldo de estoque projetado** = cumsum(estoque_inicial + compras − vendas) por produto/loja (02).
- **Dias de cobertura** = `ESTOQUE_INICIAL / VENDA_MEDIA_DIARIA` (04).
- **Estoque parado**: `VENDA_MEDIA_DIARIA ≤ ESTOQUE_INICIAL × 0,005` (04).
- **Risco de ruptura**: `DIAS_COBERTURA < 15` e `VENDA_MEDIA_DIARIA > mediana` (04).
- **Dispersão de preço entre lojas**: `amplitude_pct`, `cv_pct` sobre `PRECO_EMBALAGEM_0` (05).
- **Correlação preço × volume** por produto (mensal, por loja), `n_obs ≥ 8`, limiar forte `< −0,4` (05).
- **Projeção de demanda 2026** = tendência linear por produto × índice sazonal por categoria (06).
- **Estoque de segurança 30d** = `venda_media_diaria_2026 × 30`; **sugestão de compra** = `demanda_projetada_2026 + estoque_seguranca_30d` (06).
- **Contadores do resumo executivo** (07): candidatos a promoção/descontinuação/repricing etc.

Valores herdados em [resumo_executivo.csv](../outputs/tables/resumo_executivo.csv): 2.731 produtos cadastrados; 2 sem nenhuma venda; 8.757 combinações produto×loja com estoque parado; 2.931 com risco de ruptura; 1.961 candidatos a promoção; 224 a descontinuação; 50 a repricing por padronização; 160 por "elasticidade"; demanda projetada 2026 ≈ 1.370.583 vs. média histórica ≈ 2.320.942.

---

## Principais hipóteses do relatório

Do [reports/relatorio_final.md](../reports/relatorio_final.md), Seção 2 (5 hipóteses concorrentes para a queda de vendas):

- **H1** — Queda causada por fechamento de lojas → relatório marca **Rejeitada**.
- **H2** — Queda concentrada em poucas categorias → relatório marca **Rejeitada** (22 de 23 categorias caem >30%).
- **H3** — Queda concentrada em poucas lojas → relatório marca **Rejeitada** (10 de 11 lojas caem >30%; Loja 9/Salvador cresce +73%).
- **H4** — Sortimento efetivamente vendido está encolhendo → relatório marca **Confirmada** (SKUs vendidos/mês 2.490→1.212).
- **H5** — Reposição/compras encolhendo "mata de fome" o sortimento → relatório marca **Confirmada e explicação mais provável** (SKUs comprados/mês 74→14; correlação 0,49).

Nota: o `SDD.MD` (Spec 07) exige uma matriz H1–H10 mais ampla e um vocabulário de status controlado; o relatório atual cobre apenas H1–H5 e usa status livres.

---

## Conclusões descritivas (do relatório atual)

- Concentração de receita: **D – Eletros = 41%** da receita (R$ 197,6M/24 meses); Eletros+Eletrônicos ≈ 51% da receita com ~11% dos SKUs.
- Loja **93 (Alhandra/PB)** lidera receita (R$ 153,3M) com baixa quantidade → mix de alto ticket; PB concentra 39% da receita com 2 lojas.
- Sazonalidade: **novembro é pico** (Black Friday); nov/24 ≈ R$ 47,2M.
- Top produtos: dois splits 9.000 BTUs e massa corrida PVA 25kg lideram receita.
- Estoque: **8.757** combinações produto×loja com estoque parado; **2.931** com risco de ruptura.
- Preço: amplitudes de preço entre lojas de **até 258%** para o mesmo item.

Essas conclusões descritivas em geral **têm output/figura correspondente** no repo (ainda que os valores não tenham sido reexecutados nesta fase — `NÃO VALIDADO` quanto à reprodução, mas rastreáveis a arquivos).

## Conclusões diagnósticas (do relatório atual)

- A queda de vendas é **ampla e transversal** (quase todas as categorias e lojas), não concentrada → afasta explicações pontuais (H2/H3).
- O **sortimento vendido encolheu** aproximadamente na mesma proporção da receita (H4) → interpretado como assinatura de problema de disponibilidade, não de demanda.
- A base `fato_compras` é reconhecidamente **incompleta**: `estoque_inicial + compras (~1,74M)` << `vendido (~4,64M)`, gap de ~2,7×; **74% dos eventos** de movimentação têm saldo projetado negativo (interpretado como base incompleta, não estoque físico negativo).

## Conclusões causais (do relatório atual)

- Cadeia causal proposta: **reposição (compras) encolhe → menos SKUs disponíveis → sortimento vendido encolhe → transações e receita caem**.
- O relatório **atenua** essa causalidade: reconhece dois cenários não excludentes (queda operacional real de compras vs. captura incompleta de dados) e recomenda validar com Operações/TI antes de agir.
- Ainda assim, o Sumário Executivo afirma que "os dados são consistentes com lojas progressivamente ficando sem itens para vender" e a Seção 8 lista recomendações acionáveis (descontinuação, repricing, promoção) — **linguagem mais forte do que a evidência sustenta**, segundo os princípios do `SDD.MD`. Ver "Riscos analíticos".

---

## Riscos técnicos visíveis

1. **Dependências: RESOLVIDO + reprodução VALIDADA em 2026-07-06** — `pandas/numpy/pyarrow/matplotlib/openpyxl` e `pytest` instalados numa `.venv` isolada (Python 3.14.6). O `requirements.txt` pede `pandas>=2.0`/`numpy>=1.24` e o pip resolveu **pandas 3.0.3 / numpy 2.5.1** (majors acima dos idiomas de pandas 2.x usados no código). O risco de drift foi **testado**: reexecução completa em cópia isolada reproduziu **todos os 38 outputs de forma idêntica** (ver seção "Ordem atual de execução"). Portanto o risco **não se concretizou** hoje. Recomendação de baixo risco remanescente: **congelar as versões exatas provadas** num lockfile (ex.: `requirements.lock` via `pip freeze`) para blindar reprodutibilidade futura — trabalho da Spec 08, não desta fase.
2. **Caminhos relativos frágeis** — scripts assumem execução dentro de `src/` (`../data/...`). Sem `Makefile`/entrypoint; fácil de quebrar.
3. **Sem entrypoint/orquestração** — nenhum `if __name__ == "__main__"`, nenhum `Makefile`, nenhum `pyproject.toml`; ordem de execução só documentada em prosa no README.
4. **Scripts fazem trabalho no nível de módulo** — dificultam import/teste unitário (relevante para as specs de teste seguintes).
5. **Referência a scripts inexistentes** — o relatório cita etapas `3b` e `08` e "01_ a 08_"; só existem `01..07`. Reprodutibilidade comprometida.
6. **`fato_vendas` é grande (1,09M linhas)** e reprocessado várias vezes a partir de Parquet; sem cache/particionamento — custo de execução relevante, mas gerenciável.
7. **`Descritivo_bases_de_dados_2.xlsx` e `Estudo_de_caso_1.docx` não são legíveis** sem bibliotecas extras (`openpyxl` já está no requirements; docx não). Dicionário de dados oficial ainda não incorporado ao código. `DADO AUSENTE` nesta fase.

## Riscos analíticos visíveis

1. **Números-título da queda divergem entre documentos** — README (spoiler): "~85%" entre nov/24 (R$47,2M) e dez/25 (R$3,9M); os dados de `vendas_mensais.csv` dão **−91,7%** para esse mesmo par; o relatório usa **−71,7%** (1T24→4T25, métrica diferente). Três números distintos para "a queda". `NÃO VALIDADO` — precisa de definição única e reconciliação.
2. **Núcleo diagnóstico (Seção 2) não é reproduzível** — same-store YoY, YoY por categoria/loja, "SKUs comprados/mês 74→14", "SKUs vendidos/mês 2.490→1.212" e "correlação 0,49" **não têm script nem tabela** no repositório. Conclusões causais apoiadas em números sem lastro reexecutável. Risco alto de "hipótese vendida como conclusão".
3. **"Ruptura" a partir de saldo negativo** — `02_estoque_projetado.py` grava `rupturas_estoque.csv` e `04` grava `produtos_risco_ruptura.csv` a partir de saldo negativo/cobertura, apesar de a base de compras ser reconhecidamente incompleta. Nomear isso "ruptura" contraria o princípio "saldo negativo não prova ruptura física".
4. **"Elasticidade" para o que é só correlação** — outputs `produtos_elasticidade_negativa_forte.csv`, `rec_repricing_elasticidade.csv` e o texto do `07` ("demanda sensível a preço") tratam correlação preço×volume como elasticidade. Contraria o princípio "correlação não é causalidade".
5. **Recomendações como decisão, não triagem** — descontinuação/promoção/repricing são apresentadas como listas acionáveis sem margem, lead time, lote mínimo, estoque atual confiável, sazonalidade etc.
6. **Projeção usa venda observada como demanda** — `06` projeta a partir de vendas (potencialmente censuradas por ruptura) e chama de "demanda projetada"; a "sugestão de compra" é bruta (não desconta estoque), mas não é rotulada como bruta/piso.
7. **Comparações temporais e sazonalidade** — o comparativo 1T24×4T25 mistura trimestres com sazonalidade diferente; o pico de novembro (Black Friday) pode inflar recortes. Requer tratamento explícito de sazonalidade.
8. **Estoque de segurança/cobertura sobre base incompleta** — cobertura usa apenas estoque inicial + venda média (sem entradas), o que é uma escolha defensável, mas a matriz giro×cobertura ainda pode induzir leitura de "ruptura real".

---

## Problemas de encoding, parsing e formatação visíveis

- `dim_produto_1.csv` em **latin1/cp1252** (contém NBSP `0xA0`); demais bases em UTF-8. Ler `dim_produto` como UTF-8 corrompe registros (documentado no ETL e no relatório). Tratado no código.
- **Mistura de convenções** entre bases: `;`+decimal `,` (dimensões/estoque) vs. `,`+decimal `.` (vendas/compras). Tratado por base no ETL.
- **Coluna de índice sem nome** (`Unnamed`) em `fato_vendas` e `fato_compras` — descartada no ETL.
- `fato_estoque_inicial.ESTOQUE_INICIAL` vem como **string com vírgula decimal** apesar de serem inteiros ("0", "50").
- **Strings vazias / espaços** em `dim_produto` (`EMBALAGEM_VENDA_0` = `" "`) e trailing spaces em `Descr_unidades_medida` (`"PECA (PC) "`, `"PE'"`); `COD_IBGE` vazio na linha `EB;EMBALAGEM ESPECIAL;`.
- `Descr_unidades_medida_2.csv` aparenta estar **sem acentuação** (DUZIA, GARRAFAO, PECA) — pode ser perda de acentos na origem. `NÃO VALIDADO`.
- Valores tipo `NA`/`N/A`/`-`/`null`/`None`: **não observados** na amostra inspecionada; `NÃO VALIDADO` para a base completa.

## Problemas de unidade de medida visíveis

- **Compras não convertidas para unidade de armazenagem:** `02_estoque_projetado.py` soma `QUANTIDADE_COMPRA` **crua**, sem aplicar `CONVERSAO_COMPRA_ARMAZENAGEM` (que existe em `dim_produto`), enquanto as **vendas são convertidas** (`QTD_VENDA_ESTOQUE`). Risco de comparar entradas e saídas em unidades diferentes. (Nas amostras a conversão aparece `1,000000`, mas isso **não foi verificado** para todos os produtos — `NÃO VALIDADO`.)
- **Ambiguidade da unidade de `QUANTIDADE_COMPRA`** — `EMBALAGEM_FORNECEDOR` como `"CX-40-UN"` com `QUANTIDADE_COMPRA=120` e `UNIDADE_ESTOQUE="UN"`: não está claro se 120 é em caixas ou em unidades. `NÃO VALIDADO`.
- **Estoque inicial** em `UNIDADE_ESTOQUE`, vendas convertidas para armazenagem, compras não convertidas → a conta `estoque_inicial + compras − vendas` pode misturar unidades.

## Problemas de qualidade de dados visíveis

- **Cobertura de compras muito baixa**: `estoque_inicial + compras (~1,74M)` vs. `vendido (~4,64M)` — gap ~2,7× (principal limitação declarada).
- **74% dos eventos** de movimentação com saldo projetado negativo (sintoma da base incompleta).
- **Apenas 1.393 registros de compra** para 2.731 produtos × 11 lojas × 24 meses — implausível como universo completo de reposição.
- **Duplicidades no bruto de `dim_produto`** sugeridas pelo `drop_duplicates(subset=["CODIGO"])` no ETL — não quantificadas. `NÃO VALIDADO`.
- **Inconsistência de nomenclatura** `CD_EMPRESA` (voltagem) vs. `COD_EMPRESA` (demais).
- **Integridade referencial 100%** (ponto positivo, validado em `checks_integridade.csv`).
- **Números do relatório não reconciliados** com os CSVs (ver Riscos analíticos #1 e #2).

---

## Pontos que ainda precisam ser validados

- `VALIDADO (2026-07-06)` — Pipeline reexecutado do zero em cópia isolada (venv, pandas 3.0.3/numpy 2.5.1): 7 scripts com exit 0 e os 27 CSVs + 11 Parquet reproduzem de forma idêntica (tol. 1e-6) os commitados. Reprodutibilidade e compatibilidade com pandas 3.x/numpy 2.x confirmadas.
- `NÃO VALIDADO` — Unicidade real das chaves (`dim_produto.CODIGO`, `dim_precos[CODIGO,COD_EMPRESA]`, grão de `fato_vendas` e `fato_estoque_inicial`).
- `NÃO VALIDADO` — Se `CONVERSAO_COMPRA_ARMAZENAGEM` é sempre 1,0; caso não, impacto no saldo de estoque e na cobertura.
- `NÃO VALIDADO` — Definição/valor único da "queda de vendas" (−71,7% vs. −85% vs. −91,7%) e sua reconciliação com `vendas_mensais.csv`.
- `NÃO VALIDADO` — Origem dos números da Seção 2 (SKUs comprados/vendidos por mês, correlação 0,49, same-store, YoY por categoria/loja) — não há script/tabela.
- `DADO AUSENTE` — Conteúdo do dicionário oficial `Descritivo_bases_de_dados_2.xlsx` e do enunciado `Estudo_de_caso_1.docx`.
- `NÃO VALIDADO` — Presença de nulos/sentinelas (`NA`, `-`, `null`) e de datas fora do período nas bases completas.
- `NÃO VALIDADO` — Quantificação de duplicidades e de valores negativos/zerados em quantidade e preço.

## Perguntas em aberto

1. Qual é o número **oficial** da queda de vendas e sobre qual janela/base ele é definido? Por que README, `vendas_mensais.csv` e relatório divergem?
2. `fato_compras` é o universo real de entradas ou uma extração parcial? Faltam transferências/ajustes/devoluções? (Muda todo o diagnóstico causal.)
3. `QUANTIDADE_COMPRA` está em unidade do fornecedor ou de armazenagem? A conversão de compra deve ser aplicada?
4. Onde estão (ou como reproduzir) os cálculos da Seção 2 do relatório (SKUs comprados/vendidos por mês, correlação 0,49, YoY por categoria/loja, same-store)?
5. O saldo de estoque negativo deve ser tratado como gap contábil (e não ruptura física)? Como o relatório/dashboard devem nomeá-lo?
6. A correlação preço×volume deve ser rebaixada para "candidato a investigação de preço" em nome de arquivos e no texto?
7. Existe informação de margem, lead time, lote mínimo, estoque atual confiável, fornecedor — necessária para transformar recomendações em decisões? (Hoje `DADO AUSENTE`.)
8. `dim_produto.DIGITO` faz parte da chave de negócio do produto?
9. Qual o grão real de `fato_vendas` (linha de item, cupom, ou agregado diário)?
10. O que explica a Loja 9 (Salvador) crescer +73% enquanto as demais caem? (afirmação do relatório, `NÃO VALIDADO`).

---

## Conclusão do discovery

O repositório contém um pipeline funcional em 7 scripts, outputs e um relatório coerente em narrativa, **mas** com dois problemas estruturais que condicionam as próximas specs: (a) **o ambiente atual não consegue reproduzir nem testar** (dependências ausentes), e (b) **as conclusões causais/diagnósticas centrais do relatório não têm lastro reexecutável** no código commitado, além de divergências numéricas entre README, CSVs e relatório. As próximas specs devem priorizar ingestão/contratos (Spec 01/02) e a reconstrução auditável das métricas e do diagnóstico (Spec 03/04/05) antes de reescrever o relatório (Spec 07) e construir o dashboard (Spec 09).

**Nenhuma spec além desta (Spec 00) foi implementada. Nenhum código do pipeline foi alterado.**
