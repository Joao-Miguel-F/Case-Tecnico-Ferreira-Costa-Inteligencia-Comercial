# Análise de Desempenho de Produtos no Varejo

Estudo de caso: rede de varejo de materiais de construção, reforma e decoração com 11 lojas em 5 estados do Nordeste do Brasil (PE, BA, SE, PB, RN), cobrindo 24 meses de dados (jan/2024–dez/2025).

**➡️ Leia o relatório final com todos os achados e recomendações em [`reports/relatorio_final.md`](reports/relatorio_final.md).**

## Achado principal (spoiler)

A receita mensal caiu ~85% entre novembro/2024 (pico de R$ 47,2M, efeito Black Friday) e dezembro/2025 (R$ 3,9M). Esse é o achado mais crítico do estudo e condiciona todas as demais recomendações — veja a seção 1 do relatório.

## Estrutura do repositório

```
.
├── data/
│   ├── raw/                # Bases originais fornecidas (CSV/XLSX/DOCX), sem alteração
│   └── processed/          # Bases limpas e derivadas, em Parquet (geradas pelo pipeline)
├── src/                    # Pipeline de análise, em ordem de execução
│   ├── 01_etl.py                    # Limpeza, tipagem, checagem de integridade
│   ├── 02_estoque_projetado.py      # Estoque projetado, rupturas, produtos parados
│   ├── 03_analise_vendas.py         # Ranking de produtos, categorias, lojas, sazonalidade
│   ├── 04_analise_estoque.py        # Cobertura de estoque, giro, risco de ruptura
│   ├── 05_precificacao.py           # Dispersão de preço entre lojas, elasticidade
│   ├── 06_projecao_compras.py       # Projeção de demanda e compras para 2026
│   └── 07_recomendacoes.py          # Consolida promoção / descontinuação / repricing
├── outputs/
│   ├── figures/             # Gráficos gerados (PNG)
│   └── tables/               # Tabelas de resultado (CSV) referenciadas no relatório
├── reports/
│   └── relatorio_final.md   # Relatório final com achados e recomendações defendidas
├── requirements.txt
└── README.md
```

## Como reproduzir

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

Cada script lê da pasta `data/raw` (etapa 1) ou `data/processed` (demais etapas) e escreve seus resultados em `data/processed`, `outputs/tables` e `outputs/figures`. Rodar em sequência recria todo o pipeline do zero.

## Bases de dados originais

| Arquivo | Descrição | Linhas |
|---|---|---|
| `fato_vendas_1.csv` | Saídas (vendas) por produto/loja/dia | 1.090.390 |
| `fato_compras_2.csv` | Entradas de estoque (compras) | 1.393 |
| `fato_estoque_inicial_2.csv` | Posição de estoque no início do período | 25.330 |
| `dim_produto_1.csv` | Hierarquia de produto, embalagens, voltagem | 2.731 |
| `dimensao_lojas_2.csv` | Cidade/estado de cada loja | 11 |
| `dimensao_precos_2.csv` | Preços por produto, loja e tipo de embalagem | 28.560 |
| `dimensao_voltagem_2.csv` | Voltagens disponíveis por loja | — |
| `Descr_unidades_medida_2.csv` | Dicionário de unidades de medida | — |
| `Descritivo_bases_de_dados_2.xlsx` | Dicionário de dados de todas as bases | — |
| `Estudo_de_caso_1.docx` | Enunciado original do estudo de caso | — |

Ver `data/raw/Descritivo_bases_de_dados_2.xlsx` para o dicionário de dados completo, coluna a coluna.

## Principais decisões de limpeza de dados

- `dim_produto_1.csv` está em encoding **Latin-1/cp1252** (não UTF-8) — lido com `encoding="latin1"` para evitar perda de registros.
- Bases `dimensao_*` e `fato_estoque_inicial` usam `;` como separador de campo e `,` como decimal (padrão BR/Excel).
- `fato_compras` e `fato_vendas` usam `,` como separador de campo e `.` como decimal.
- 100% de integridade referencial entre `fato_vendas`/`fato_compras`/`fato_estoque_inicial` e as dimensões de produto e loja (nenhuma linha órfã).
- A base `fato_compras` está incompleta frente ao volume vendido no período — ver limitação detalhada na seção 2 do relatório final.
