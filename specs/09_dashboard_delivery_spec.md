# Spec 09 — Dashboard final e camada de apresentação

> Status: **PLANEJADA** (nenhuma implementação feita nesta fase). **Última etapa do projeto**, por decisão do SDD.MD (o dashboard é só apresentação).
> Base de evidência: [specs/00_current_state.md](00_current_state.md) e SDD.MD (seção 16).

## Problema

Não existe camada de apresentação interativa: hoje o consumo é via 30 CSVs em `outputs/tables/`, 9 PNGs estáticos em `outputs/figures/` e um relatório markdown. Não há como um usuário de negócio explorar vendas/lojas/categorias/hipóteses com filtros, nem distinguir visualmente o que é fato validado do que é hipótese — distinção que é o coração deste projeto. Qualquer dashboard construído **antes** das Specs 01–08 herdaria os problemas atuais (elasticidade, "ruptura", recomendações como decisão), por isso ele é deliberadamente a última spec.

## Evidência encontrada no repositório

- Spec 00, "Estrutura atual": nenhum arquivo de dashboard (`app.py`, `dashboard/`, streamlit) existe.
- [requirements.txt](../requirements.txt): não inclui `streamlit` nem `plotly` (mudança de dependência necessária).
- Os insumos que o dashboard exibirá ainda não existem (serão criados nas Specs 01–07): `ingestion_audit.csv`, `data_quality_report.csv`, `compras_coverage_audit.csv`, `vendas_same_store_yoy.csv`, `sortimento_controlado_por_volume.csv`, `hypothesis_status.csv`, triagens.
- Outputs legados que podem alimentar páginas descritivas já existem: `vendas_mensais.csv`, `vendas_por_categoria_nivel1.csv`, `vendas_por_loja.csv`, `dispersao_preco_entre_lojas.csv` etc.

## Risco para o negócio

- Dashboard construído sobre outputs não validados institucionalizaria os erros atuais com aparência de autoridade (pior que o relatório, pois vira ferramenta do dia a dia).
- Dashboard que recalcula métricas por conta própria pode divergir do pipeline validado e criar "duas verdades".
- Sem distinção visual entre fato validado/evidência/hipótese/triagem, o usuário executivo tomará triagem por decisão.

## Arquivos de entrada

Somente artefatos validados (o dashboard **não lê `data/raw/`**, exceto seção específica de auditoria de ingestão, se existir):

- `outputs/tables/*.csv` (validados pelas Specs 02–07, incluindo `hypothesis_status.csv`, `data_quality_report.csv`, `compras_coverage_audit.csv`, triagens, YoY, sortimento);
- `outputs/figures/*.png` (quando fizer sentido reusar);
- `docs/metric_catalog.md`, `docs/business_rules.md`, `docs/known_limitations.md` (fonte dos tooltips);
- `reports/relatorio_final.md` (texto de conclusões).

## Arquivos de saída esperados

- `dashboard/app.py` (+ `dashboard/pages/`, `dashboard/components/`, `dashboard/assets/` se a estrutura multipage compensar; senão `app.py` na raiz — decidir na implementação, com simplicidade como critério).
- `tests/test_dashboard.py`.
- `Makefile` atualizado com `make dashboard`.
- `README.md` atualizado (como abrir e usar o dashboard).

## Regras de negócio envolvidas

Regras obrigatórias do SDD.MD (seção 16), todas verificáveis:

1. Usar somente métricas do `docs/metric_catalog.md`; nenhum recálculo divergente do pipeline.
2. Exibir limitações e nível de confiança junto aos indicadores.
3. Diferenciar visualmente: fato validado / evidência descritiva / hipótese / recomendação exploratória / não comprovada.
4. Nunca chamar gap contábil de ruptura física; nunca chamar correlação de elasticidade.
5. Não exibir compra líquida sugerida se o estoque disponível for inconfiável (respeitar a flag da Spec 06).
6. Triagens sempre com regra, evidência, confiança, dado faltante, risco e próxima validação.
7. Tooltips nos KPIs/gráficos/filtros com fórmula, interpretação, unidade, confiança, limitação e fonte.

## Métricas afetadas

Nenhuma métrica nova é criada. O dashboard **apresenta**: receita e variações (mensal/YoY), quantidade, ticket, SKUs vendidos, lojas comparáveis, status de hipóteses, checks de qualidade, cobertura de compras, gaps contábeis, preço médio/dispersão/correlação exploratória, projeção observada e triagens — todas vindas dos outputs validados.

## Mudanças propostas

1. Implementar Streamlit + Plotly com as 10 páginas do SDD.MD: Sumário executivo; Qualidade dos dados; Vendas; Lojas; Categorias; Sortimento; Compras/estoque/gap contábil; Precificação; Projeção e triagens; Hipóteses e conclusão.
2. Leitura leve de CSVs/Parquet validados (pandas), com cache do Streamlit; zero ETL pesado.
3. Componente padrão de "selo epistêmico" (fato validado/evidência/hipótese/triagem/bloqueado) aplicado a todo KPI e gráfico.
4. Tooltips gerados a partir do catálogo de métricas (fonte única, sem duplicar fórmulas em texto livre).
5. Adicionar `streamlit`/`plotly` ao `pyproject.toml` e o alvo `make dashboard`.
6. Design conforme SDD.MD: fundo neutro, respiro, cor só para alerta/destaque, títulos com interpretação de negócio, filtros globais (período, loja, categoria, produto, confiança, status de hipótese) onde fizer sentido.

## Testes necessários

`tests/test_dashboard.py` deve validar:
- arquivo principal existe; `make dashboard` existe no Makefile;
- o app importa sem erro (smoke test sem servidor);
- não lê `data/raw/` fora da seção de auditoria (inspeção de código/paths);
- consome os outputs validados esperados;
- contém referências às 10 páginas/seções;
- contém tooltips/help texts nos KPIs principais;
- não contém linguagem proibida ("ruptura comprovada", "elasticidade comprovada", recomendações como decisão final);
- README explica como abrir o dashboard.

## Critérios de aceite

- `make dashboard` sobe o app; app roda sem executar ETL completo;
- toda métrica exibida tem correspondência no catálogo (auditável);
- limitações, níveis de confiança e selos epistêmicos visíveis;
- compra líquida ausente enquanto a flag de estoque inconfiável estiver ativa;
- `pytest tests/test_dashboard.py` passa (ou bloqueios reais documentados);
- README atualizado.

## O que não será feito

- Nenhum recálculo de regra de negócio no dashboard.
- Nenhuma leitura de dados brutos fora da (eventual) página de auditoria de ingestão.
- Não será usado Dash/Power BI/Tableau (SDD.MD: Streamlit primeira opção, sem justificativa para trocar).
- Nenhuma "conclusão causal" nova: o dashboard repete o status epistêmico da matriz de hipóteses, nunca o endurece.
- Não será publicado/hospedado externamente (execução local via `make dashboard`; deploy fica fora do escopo).

## Dúvidas ou bloqueios

- **Dependência dura**: bloqueada até Specs 01–08 concluídas ou bloqueadas com registro. É a última etapa por definição.
- `NÃO VALIDADO` — Estrutura multipage (`dashboard/pages/`) vs. `app.py` único: decidir na implementação pelo critério de simplicidade (10 páginas sugerem multipage, mas avaliar).
- `NÃO VALIDADO` — Desempenho da leitura de `fato_vendas`-derivados no Streamlit; se necessário, pré-agregar nos scripts validados (nunca no dashboard).
- `DADO AUSENTE` — Identidade visual/branding do cliente não existe no repo; usar padrão neutro do SDD.MD.
