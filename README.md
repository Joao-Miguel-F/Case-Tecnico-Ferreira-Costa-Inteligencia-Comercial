# Painel Resultados - auditoria analitica de varejo

**Dashboard GitHub Pages:** https://joao-miguel-f.github.io/Case-Tecnico-Ferreira-Costa-Inteligencia-Comercial/

Este repositorio entrega uma auditoria analitica de varejo sobre 24 meses de dados
(jan/2024 a dez/2025), 11 lojas e 2.731 SKUs cadastrados. O projeto organiza
vendas, compras, estoque, precificacao, projecoes e hipoteses em uma trilha
auditavel, com Specs 00-09 concluidas. A porta de entrada recomendada para o
avaliador e o dashboard estatico em `docs/index.html`, publicado via GitHub
Pages e gerado por `src/dashboard_build.py` a partir de outputs validados.

O ponto central da entrega e separar o que o dado permite afirmar do que ainda
precisa de validacao: venda observada nao e demanda real; gap contabil nao e
ruptura fisica comprovada; correlacao preco-volume nao e elasticidade; triagem
nao e decisao final.

## A) Como usar o repositorio

### Dashboard publicado

Quando o GitHub Pages estiver ativo, use o dashboard como primeira leitura:

```text
https://joao-miguel-f.github.io/Case-Tecnico-Ferreira-Costa-Inteligencia-Comercial/
```

Configuracao esperada no GitHub: **Settings -> Pages -> Deploy from a branch ->
Branch: `main` -> folder: `/docs`**. O dashboard e um site estatico em
`docs/` (`docs/index.html`, `docs/assets/`, `docs/data/`) e nao usa CDN.

### Instalacao

Com `make` disponivel:

```bash
make install
```

Equivalente PowerShell nesta maquina Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt pytest ruff
```

O projeto usa Python `>=3.11`, `pytest`, `ruff` e as dependencias declaradas em
`requirements.txt`. Nesta maquina, use sempre `.\.venv\Scripts\python.exe`.
Em ambientes Unix ou Windows com Python global configurado, o comando generico
equivalente para a suite e `python -m pytest tests/`.

### Comandos principais

| Acao | Com `make` | PowerShell equivalente |
|---|---|---|
| Lint | `make lint` | `.\.venv\Scripts\python.exe -m ruff check .` |
| Testes | `make test` | `.\.venv\Scripts\python.exe -m pytest tests/` |
| Pipeline legado | `make run` | ver bloco "Pipeline legado sem make" abaixo |
| Auditorias Specs 01-06 | `make audit` | rodar os scripts de auditoria listados abaixo |
| Validar relatorio/outputs | `make report` | `.\.venv\Scripts\python.exe -m pytest tests/test_hypothesis_report.py tests/test_outputs.py` |
| Suite completa | `make all` | rodar lint, pipeline, auditorias, report e testes |
| Gerar dados do dashboard | `make dashboard-build` | `.\.venv\Scripts\python.exe src/dashboard_build.py` |
| Abrir dashboard local | `make dashboard` | `.\.venv\Scripts\python.exe -m http.server 8000 --directory docs` |
| Testar dashboard | `make dashboard-test` | `.\.venv\Scripts\python.exe -m pytest tests/test_dashboard.py` |

Pipeline legado sem `make`:

```powershell
Push-Location src
..\.venv\Scripts\python.exe 01_etl.py
..\.venv\Scripts\python.exe 02_estoque_projetado.py
..\.venv\Scripts\python.exe 03_analise_vendas.py
..\.venv\Scripts\python.exe 04_analise_estoque.py
..\.venv\Scripts\python.exe 05_precificacao.py
..\.venv\Scripts\python.exe 06_projecao_compras.py
..\.venv\Scripts\python.exe 07_recomendacoes.py
Pop-Location
```

Auditorias sem `make`:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe src/io.py
.\.venv\Scripts\python.exe src/02_quality_audit.py
.\.venv\Scripts\python.exe src/inventory_reconciliation.py
.\.venv\Scripts\python.exe src/analysis/sales_analysis.py
.\.venv\Scripts\python.exe src/analysis/assortment_analysis.py
.\.venv\Scripts\python.exe src/analysis/pricing_analysis.py
.\.venv\Scripts\python.exe src/analysis/projection_analysis.py
.\.venv\Scripts\python.exe src/analysis/recommendation_triage.py
```

Dashboard local:

```powershell
.\.venv\Scripts\python.exe src/dashboard_build.py
.\.venv\Scripts\python.exe -m http.server 8000 --directory docs
```

Depois, acesse http://localhost:8000. Tambem e possivel abrir `docs/index.html`
diretamente, pois os dados estao embarcados em `docs/data/dashboard_data.js`.

### Mapa do repositorio

| Pasta/arquivo | O que contem | Quando usar |
|---|---|---|
| `docs/index.html` | Dashboard estatico da Spec 09 | Primeira leitura do avaliador e apresentacao executiva |
| `docs/assets/` | CSS e JavaScript do painel | Suporte visual do dashboard |
| `docs/data/` | `dashboard_data.json` e `.js` derivados dos outputs | Necessario para GitHub Pages; deve ser commitado |
| `reports/relatorio_final.md` | Relatorio final com conclusoes e limitacoes | Leitura executiva detalhada |
| `outputs/tables/` | CSVs auditaveis das specs e do relatorio | Validar numeros, hipoteses e triagens |
| `docs/*.md` | Contratos, regras, catalogos e notas metodologicas | Auditar metodologia e limites de uso |
| `specs/` | Specs SDD 00-09 e plano de implementacao | Entender o processo de construcao |
| `src/` | Scripts legados e camadas auditaveis novas | Reexecutar pipeline, auditorias e dashboard build |
| `tests/` | Suite automatizada com 243 testes | Validar regressao e linguagem epistemica |
| `Makefile` | Atalhos de execucao local | Usar em ambientes com `make` |
| `pyproject.toml` | Configuracao de pytest/ruff/Python | Conferir padrao de qualidade |
| `data/raw/` | Dados originais fornecidos | Fonte bruta; nao regravar |
| `data/processed/` | Parquets gerados pelo pipeline legado | Base intermediaria para analises |

### Roteiro de leitura sugerido

1. Abra o dashboard GitHub Pages ou `docs/index.html`.
2. Leia `reports/relatorio_final.md`.
3. Confira `outputs/tables/hypothesis_status.csv`.
4. Audite `docs/`, especialmente `data_contract.md`, `business_rules.md`,
   `metric_catalog.md` e os documentos das Specs 04-06.
5. Consulte `tests/`, em especial `tests/test_outputs.py` e
   `tests/test_dashboard.py`, para ver as garantias automatizadas.

## B) Como o processo foi feito

### Spec 00 - discovery do estado atual

A Spec 00 documentou o repositorio antes de qualquer implementacao pesada:
estrutura, scripts legados, bases, graos aparentes, chaves, outputs existentes,
riscos tecnicos e riscos analiticos. O diagnostico inicial ficou em
[`specs/00_current_state.md`](specs/00_current_state.md) e guiou a ordem das
demais specs.

### Spec 01 - ingestao, encoding e parsing

A ingestao foi centralizada em [`src/io.py`](src/io.py), com regras explicitas
para encoding, separador, decimal, datas, moeda, sentinelas e codigos. A
documentacao esta em [`docs/data_formatting_and_encoding.md`](docs/data_formatting_and_encoding.md)
e a trilha auditavel em [`outputs/tables/ingestion_audit.csv`](outputs/tables/ingestion_audit.csv).

### Spec 02 - contratos e qualidade

Foram criados contratos de dados e checks de qualidade para as bases brutas,
processadas e outputs principais. A referencia metodologica esta em
[`docs/data_contract.md`](docs/data_contract.md), o codigo em
[`src/validation/`](src/validation/) e o resultado em
[`outputs/tables/data_quality_report.csv`](outputs/tables/data_quality_report.csv).

### Spec 03 - metricas e regras de negocio

Antes de novas analises, as metricas e regras foram congeladas em
[`docs/metric_catalog.md`](docs/metric_catalog.md) e
[`docs/business_rules.md`](docs/business_rules.md). Essa etapa definiu a
linguagem obrigatoria: venda observada, gap contabil, correlacao, triagem, dado
ausente, nao validado e bloqueado.

### Spec 04 - compras, estoque, unidades e reconciliacao

A reconciliacao passou a comparar vendas, compras e estoque em unidade comum de
armazenagem e a interpretar saldo negativo como gap contabil. O codigo esta em
[`src/inventory_reconciliation.py`](src/inventory_reconciliation.py), a nota em
[`docs/inventory_reconciliation.md`](docs/inventory_reconciliation.md) e os
outputs em [`outputs/tables/compras_coverage_audit.csv`](outputs/tables/compras_coverage_audit.csv)
e [`outputs/tables/gaps_saldo_contabil_estoque.csv`](outputs/tables/gaps_saldo_contabil_estoque.csv).

### Spec 05 - vendas, lojas, categorias e sortimento

A analise auditavel de vendas criou YoY por loja, categorias e controle de
sortimento por volume. A documentacao esta em
[`docs/sales_store_category_assortment.md`](docs/sales_store_category_assortment.md)
e os outputs principais sao
[`vendas_same_store_yoy.csv`](outputs/tables/vendas_same_store_yoy.csv),
[`vendas_categorias_yoy.csv`](outputs/tables/vendas_categorias_yoy.csv) e
[`sortimento_controlado_por_volume.csv`](outputs/tables/sortimento_controlado_por_volume.csv).

### Spec 06 - precificacao, projecao e triagens

A precificacao foi tratada como associacao exploratoria, nao como elasticidade.
A projecao passou a ser de venda observada, e as recomendacoes viraram triagens
com dados faltantes e decisao final bloqueada. A nota esta em
[`docs/pricing_projection_recommendations.md`](docs/pricing_projection_recommendations.md)
e os outputs incluem
[`produtos_correlacao_preco_volume_negativa.csv`](outputs/tables/produtos_correlacao_preco_volume_negativa.csv),
[`projecao_venda_observada_2026.csv`](outputs/tables/projecao_venda_observada_2026.csv)
e os arquivos `triagem_*.csv`.

### Spec 07 - hipoteses e relatorio final

As hipoteses H1-H10 foram classificadas com vocabulario controlado e conclusoes
permitidas/proibidas. A matriz esta em
[`docs/hypothesis_validation_matrix.md`](docs/hypothesis_validation_matrix.md),
o CSV em [`outputs/tables/hypothesis_status.csv`](outputs/tables/hypothesis_status.csv)
e a leitura final em [`reports/relatorio_final.md`](reports/relatorio_final.md).

### Spec 08 - reprodutibilidade

A entrega ganhou `Makefile`, `pyproject.toml`, suite consolidada e README de
execucao. A validacao principal roda com `pytest tests/`, e
[`tests/test_outputs.py`](tests/test_outputs.py) garante a existencia dos
artefatos, colunas obrigatorias e termos epistemicos exigidos.

### Spec 09 - dashboard final

O dashboard final foi implementado como site estatico em `docs/`, compativel com
GitHub Pages. O build em [`src/dashboard_build.py`](src/dashboard_build.py) gera
`docs/data/dashboard_data.json` e `docs/data/dashboard_data.js` a partir de
outputs validados; [`tests/test_dashboard.py`](tests/test_dashboard.py) valida
estrutura, linguagem, selos e fontes.

## Limitacoes honestas

### Fato validado

- O grao de vendas foi validado como produto x loja x dia x embalagem.
- A receita e a quantidade vendida em unidade de armazenagem sao reprodutiveis.
- A queda de vendas observadas aparece distribuida por lojas e categorias.
- O sortimento vendido observado encolheu.
- A base de compras entregue e incompleta para reconstruir todas as entradas.

### Evidencia descritiva

- O gap contabil mostra que entradas conhecidas nao reconciliam as saidas
  observadas.
- A queda de sortimento vendido e compativel com menor disponibilidade, mas
  tambem com menor procura, mix, preco, campanhas, concorrencia ou captura de
  dados.
- A correlacao preco-volume identifica candidatos a investigacao comercial, nao
  efeito causal.
- As listas de compra, promocao, repricing e descontinuacao sao triagem.

### DADO AUSENTE / NAO VALIDADO / BLOQUEADO

- `DADO AUSENTE`: transferencias, ajustes, devolucoes, estoque final real,
  disponibilidade fisica por SKU-loja-dia, pedidos perdidos, calendario
  operacional, margem, custo, fornecedor, lead time, lote minimo, campanhas e
  concorrencia.
- `NAO VALIDADO`: universo completo de compras, semantica operacional dos zeros
  de estoque inicial, alguns limiares comerciais herdados e janelas antigas que
  nao se reproduziram nos outputs auditaveis atuais.
- `BLOQUEADO`: causalidade compras -> queda de vendas, ruptura fisica
  comprovada, demanda real sem censura, compra liquida, pedido final de compra,
  promocao/descontinuacao automatica e recomendacoes financeiras finais.

## Validacao automatizada

Comandos finais esperados nesta entrega:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ --basetemp .pytest-tmp-final
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe src/dashboard_build.py
```

Os testes tambem verificam que o README documenta GitHub Pages, `make dashboard`,
`python -m http.server`, `src/dashboard_build.py`, `docs/index.html`, Spec 09 e
os termos venda observada, gap contabil, correlacao, triagem, dado ausente, nao
validado e bloqueado.
