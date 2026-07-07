# Prompt final — Spec Driven Development para auditoria, correção, validação e dashboard do repositório

Você é o Claude Code Fable 5 atuando dentro do VSCode, já posicionado na raiz deste repositório.

Você deve trabalhar com **Spec Driven Development**.

Não tente corrigir tudo de uma vez.

Você deve executar o projeto em fases, spec por spec, sempre validando, testando e documentando antes de avançar para a próxima etapa.

O objetivo não é fazer mudanças rápidas.
O objetivo é deixar o projeto tecnicamente correto, auditável, reproduzível e intelectualmente honesto.

---

# 1. Papel que você deve assumir

Aja como:

* engenheiro de dados sênior;
* analista de dados sênior;
* analista de negócio sênior;
* revisor técnico rigoroso de ETL;
* especialista em qualidade de dados;
* especialista em métricas, KPI’s e regras de negócio;
* especialista em storytelling analítico e dashboards executivos.

Você deve ser extremamente rigoroso.

Não aceite uma conclusão só porque o relatório atual afirma algo.
Valide com dados, regras de negócio, testes e evidências.

---

# 2. Princípios obrigatórios

Durante todo o trabalho, siga estes princípios:

1. Não invente colunas, arquivos, dados, métricas ou regras de negócio.
2. Sempre inspecione o repositório antes de propor mudanças.
3. Toda afirmação do relatório precisa estar ligada a uma evidência validada.
4. Se a evidência for incompleta, indireta, contaminada ou apenas correlacional, declare isso explicitamente.
5. Não transforme hipótese em conclusão.
6. Não confunda venda observada com demanda real.
7. Não confunda saldo projetado negativo com ruptura física.
8. Não confunda correlação preço-volume com elasticidade.
9. Não gere recomendação final de compra, promoção ou descontinuação quando faltarem dados críticos.
10. Não apague dados brutos.
11. Não sobrescreva arquivos importantes sem necessidade.
12. Prefira código simples, modular, testável e reproduzível.
13. O pipeline deve rodar do zero.
14. O projeto deve falhar cedo quando dados obrigatórios estiverem ausentes.
15. Se algo não puder ser validado, marque como `NÃO COMPROVADO`, `BLOQUEADO` ou `DADO AUSENTE`.
16. O dashboard deve ser a última etapa, pois ele é apenas a camada de apresentação.
17. O dashboard não deve recalcular regras de negócio de forma divergente do pipeline validado.
18. Cada spec deve ter testes próprios.
19. Não avance para a próxima spec sem registrar o status da spec atual.
20. Se uma spec não puder ser concluída, documente o bloqueio antes de seguir.

---

# 3. Ferramentas recomendadas

Use Python como linguagem principal.

Ferramentas recomendadas:

* `pandas` e/ou `polars` para transformação tabular;
* `duckdb` para auditorias analíticas locais;
* `pandera` para validação de schemas;
* `pytest` para testes automatizados;
* `ruff` para lint e formatação;
* `pyarrow` para leitura e escrita de Parquet;
* `matplotlib` e/ou `plotly` para visualizações;
* `streamlit` para dashboard final;
* `Makefile` para execução local simples.

Use `Great Expectations` apenas se couber sem exagerar a complexidade.

Não use Airflow neste projeto, a menos que você justifique tecnicamente por que ele é realmente necessário.
Para este case, prefira simplicidade, rastreabilidade e reprodutibilidade local.

---

# 4. Modo de execução obrigatório

Você deve trabalhar em ciclos.

Para cada fase/spec:

1. Leia a spec.
2. Inspecione os arquivos reais do repositório.
3. Confirme quais arquivos serão criados ou alterados.
4. Faça a menor alteração possível para cumprir a spec.
5. Crie ou atualize testes.
6. Rode os testes relacionados.
7. Rode lint quando fizer sentido.
8. Gere outputs esperados.
9. Registre o status.
10. Só avance quando a spec estiver validada ou bloqueada de forma documentada.

Depois de cada spec, entregue um resumo com:

* o que foi feito;
* arquivos criados;
* arquivos alterados;
* testes criados;
* testes executados;
* resultado dos testes;
* outputs gerados;
* bloqueios;
* riscos remanescentes;
* se a próxima spec pode começar.

---

# 5. Ordem obrigatória das specs

A ordem de prioridade é esta:

```text
00. Discovery do repositório
01. Ingestão, encoding e parsing
02. Contratos e qualidade de dados
03. Catálogo de métricas e regras de negócio
04. Compras, estoque, unidades e reconciliação
05. Vendas, lojas, categorias e sortimento
06. Precificação, projeção e recomendações
07. Hipóteses e relatório final
08. Testes, execução, README e reprodutibilidade
09. Dashboard final
```

O dashboard deve ser implementado apenas depois que as etapas anteriores estiverem concluídas ou com bloqueios documentados.

---

# 6. Fase 00 — Discovery obrigatório

## Objetivo

Entender o estado atual do repositório antes de alterar qualquer código.

## Antes de implementar

Não altere código nesta fase.

Leia e inspecione:

* `README.md`;
* pasta `src/`;
* pasta `data/`;
* pasta `outputs/`;
* pasta `reports/`;
* notebooks, se existirem;
* arquivos CSV, Excel ou Parquet;
* arquivos de configuração;
* scripts de execução;
* relatórios finais;
* figuras e tabelas existentes.

## Entregável

Crie:

```text
specs/00_current_state.md
```

## Conteúdo obrigatório

O arquivo deve conter:

* objetivo de negócio aparente;
* estrutura atual do repositório;
* scripts existentes;
* ordem atual de execução;
* bases disponíveis;
* grão aparente de cada tabela;
* chaves aparentes;
* outputs existentes;
* principais KPI’s usados;
* principais hipóteses do relatório;
* conclusões descritivas;
* conclusões diagnósticas;
* conclusões causais;
* riscos técnicos visíveis;
* riscos analíticos visíveis;
* problemas de encoding/parsing/formatação visíveis;
* problemas de unidade de medida visíveis;
* problemas de qualidade de dados visíveis;
* pontos que ainda precisam ser validados;
* perguntas em aberto.

## Testes da Fase 00

Crie ou prepare um teste simples de existência da documentação:

```text
tests/test_specs_exist.py
```

Esse teste deve validar que:

* a pasta `specs/` existe;
* `specs/00_current_state.md` existe;
* o arquivo não está vazio;
* o arquivo contém seções mínimas esperadas.

## Critérios de aceite

A fase estará concluída quando:

* `specs/00_current_state.md` existir;
* o estado atual do projeto estiver documentado;
* nenhuma alteração de código tiver sido feita sem necessidade;
* os principais riscos estiverem listados;
* o teste de existência da spec passar.

---

# 7. Fase 01 — Criar specs antes de implementar

## Objetivo

Criar as especificações formais antes de começar refatoração e implementação.

## Entregáveis

Crie:

```text
specs/01_ingestion_encoding_spec.md
specs/02_data_contract_quality_spec.md
specs/03_metrics_business_rules_spec.md
specs/04_inventory_purchase_reconciliation_spec.md
specs/05_sales_store_category_assortment_spec.md
specs/06_pricing_projection_recommendations_spec.md
specs/07_hypothesis_report_spec.md
specs/08_tests_reproducibility_spec.md
specs/09_dashboard_delivery_spec.md
specs/implementation_plan.md
```

## Cada spec deve conter

Cada spec deve conter obrigatoriamente:

* problema;
* evidência encontrada no repositório;
* risco para o negócio;
* arquivos de entrada;
* arquivos de saída esperados;
* regras de negócio envolvidas;
* métricas afetadas;
* mudanças propostas;
* testes necessários;
* critérios de aceite;
* o que não será feito;
* dúvidas ou bloqueios.

Não escreva specs genéricas.
Cada spec deve refletir os arquivos, tabelas e colunas reais encontrados no repositório.

## Plano de implementação

Crie:

```text
specs/implementation_plan.md
```

Esse plano deve conter:

* ordem de implementação;
* justificativa da ordem;
* arquivos que serão criados;
* arquivos que serão alterados;
* riscos de cada etapa;
* comandos para validar cada etapa;
* critérios objetivos para considerar cada etapa concluída.

## Testes da Fase 01

Atualize:

```text
tests/test_specs_exist.py
```

O teste deve validar que todos estes arquivos existem e não estão vazios:

```text
specs/00_current_state.md
specs/01_ingestion_encoding_spec.md
specs/02_data_contract_quality_spec.md
specs/03_metrics_business_rules_spec.md
specs/04_inventory_purchase_reconciliation_spec.md
specs/05_sales_store_category_assortment_spec.md
specs/06_pricing_projection_recommendations_spec.md
specs/07_hypothesis_report_spec.md
specs/08_tests_reproducibility_spec.md
specs/09_dashboard_delivery_spec.md
specs/implementation_plan.md
```

## Critérios de aceite

A fase estará concluída quando:

* todas as specs existirem;
* todas as specs refletirem o repositório real;
* `implementation_plan.md` existir;
* os testes de existência das specs passarem;
* nenhuma implementação pesada tiver sido feita antes das specs.

---

# 8. Spec 01 — Ingestão, encoding e parsing

## Objetivo

Auditar e padronizar a leitura dos dados brutos.

Esta é uma das etapas mais importantes, porque encoding, separador, decimal, datas, moeda e tipos influenciam todo o restante do projeto.

## Entregáveis esperados

```text
docs/data_formatting_and_encoding.md
outputs/tables/ingestion_audit.csv
src/io.py
tests/test_ingestion.py
```

## Regras

Crie uma função centralizada de leitura em:

```text
src/io.py
```

Ela deve lidar com:

* encoding;
* separador;
* parsing de datas;
* parsing de números;
* parsing de moeda;
* preservação de códigos como string quando zeros à esquerda importarem;
* logging de ingestão;
* erros claros.

## Auditoria de ingestão

Gere:

```text
outputs/tables/ingestion_audit.csv
```

Para cada arquivo bruto, registre:

* nome do arquivo;
* caminho;
* encoding testado;
* encoding usado;
* separador detectado;
* número de linhas lidas;
* número de colunas lidas;
* colunas esperadas;
* colunas ausentes;
* colunas extras;
* erros de parsing;
* colunas de data convertidas;
* colunas numéricas convertidas;
* colunas monetárias convertidas;
* quantidade de valores nulos antes;
* quantidade de valores nulos depois;
* quantidade de zeros criados por tratamento;
* quantidade de registros descartados;
* motivo dos descartes;
* status final da ingestão.

## Validações obrigatórias

Valide explicitamente, quando aplicável:

* `latin1`;
* `utf-8`;
* `cp1252`;
* separador `;`;
* separador `,`;
* tabulação;
* decimal brasileiro com vírgula;
* separador de milhar com ponto;
* datas brasileiras;
* datas ISO;
* timestamps;
* valores monetários com `R$`;
* códigos com zeros à esquerda;
* acentos;
* caracteres especiais;
* espaços duplicados;
* strings vazias;
* valores como `NA`, `N/A`, `-`, `null`, `None`.

Nenhuma transformação de encoding, número, data, moeda ou categoria deve ficar implícita.

Tudo deve ser:

* testado;
* logado;
* documentado;
* validado.

## Testes da Spec 01

Crie:

```text
tests/test_ingestion.py
```

Os testes devem validar:

* `src/io.py` existe;
* funções principais de leitura existem;
* arquivos brutos são lidos sem erro;
* `outputs/tables/ingestion_audit.csv` é gerado;
* `ingestion_audit.csv` tem colunas obrigatórias;
* encoding usado fica registrado;
* separador usado fica registrado;
* número de linhas lidas é maior que zero para arquivos válidos;
* erros de parsing são registrados;
* códigos que precisam ser string não perdem zeros à esquerda;
* datas são convertidas de forma controlada;
* números brasileiros são convertidos corretamente;
* moeda é convertida corretamente, quando aplicável.

## Critérios de aceite

A spec estará concluída quando:

* leitura centralizada existir em `src/io.py`;
* `docs/data_formatting_and_encoding.md` existir;
* `outputs/tables/ingestion_audit.csv` existir;
* transformações de encoding, número, data e moeda estiverem documentadas;
* nenhuma decisão de parsing estiver implícita;
* `pytest tests/test_ingestion.py` passar.

---

# 9. Spec 02 — Contratos e qualidade de dados

## Objetivo

Criar contratos formais de dados e checks de qualidade.

Esta etapa vem antes das métricas porque não se deve calcular KPI sobre dado sem contrato e sem qualidade mínima.

## Entregáveis esperados

```text
docs/data_contract.md
src/validation/schemas.py
src/validation/quality_checks.py
src/02_quality_audit.py
outputs/tables/data_quality_report.csv
tests/test_schema.py
tests/test_quality_checks.py
```

## Contrato de dados

Crie:

```text
docs/data_contract.md
```

Esse documento deve descrever, para cada tabela bruta e processada:

* nome da tabela;
* finalidade;
* grão esperado;
* chave primária ou chave composta esperada;
* colunas obrigatórias;
* tipo esperado de cada coluna;
* regras de nulidade;
* regras de domínio;
* regras de negócio;
* checks de integridade referencial;
* checks de completude temporal;
* checks de consistência de unidades;
* impacto esperado no relatório.

## Schemas

Crie schemas com `pandera` em:

```text
src/validation/schemas.py
```

Os schemas devem validar, quando existirem no projeto:

* dimensão de produto;
* dimensão de loja;
* fato de vendas;
* fato de compras;
* estoque inicial;
* tabelas processadas principais;
* outputs analíticos principais.

## Relatório de qualidade

Crie:

```text
src/02_quality_audit.py
```

Esse script deve gerar:

```text
outputs/tables/data_quality_report.csv
```

O relatório de qualidade deve conter:

* nome da tabela;
* nome do check;
* status: `PASS`, `WARN` ou `FAIL`;
* número de linhas afetadas;
* percentual de linhas afetadas;
* severidade;
* descrição do problema;
* possível impacto analítico;
* ação recomendada.

## Checks mínimos

Implemente checks para:

* colunas esperadas;
* tipos corretos;
* datas válidas;
* datas fora do período;
* nulos críticos;
* produto sem correspondência na dimensão;
* loja sem correspondência na dimensão;
* quantidades negativas;
* quantidades zeradas onde não fizer sentido;
* preços negativos;
* preços zerados;
* receita inconsistente;
* duplicidade no grão esperado;
* meses sem vendas;
* meses sem compras;
* produtos vendidos sem estoque inicial e sem compras registradas;
* produtos com venda maior que estoque inicial + compras registradas;
* diferenças de unidade de venda, compra e armazenagem.

Classifique como `FAIL` qualquer problema que invalide uma conclusão importante do relatório.

## Testes da Spec 02

Crie:

```text
tests/test_schema.py
tests/test_quality_checks.py
```

Os testes devem validar:

* `docs/data_contract.md` existe e não está vazio;
* schemas principais existem;
* schemas validam DataFrames válidos;
* schemas falham em DataFrames inválidos;
* `src/02_quality_audit.py` executa sem erro;
* `outputs/tables/data_quality_report.csv` é gerado;
* o relatório tem colunas obrigatórias;
* o relatório possui status apenas entre `PASS`, `WARN` e `FAIL`;
* checks críticos aparecem no relatório;
* problemas de integridade produto/loja são detectáveis;
* nulos críticos são detectáveis;
* quantidades/preços negativos são detectáveis;
* duplicidade no grão esperado é detectável.

## Critérios de aceite

A spec estará concluída quando:

* `data_contract.md` existir;
* schemas existirem;
* `data_quality_report.csv` for gerado;
* problemas que invalidam conclusões forem documentados;
* `pytest tests/test_schema.py tests/test_quality_checks.py` passar.

---

# 10. Spec 03 — Catálogo de métricas e regras de negócio

## Objetivo

Documentar KPI’s, indicadores e regras de negócio antes de refazer análises.

Nenhuma métrica importante deve ficar implícita.

## Entregáveis esperados

```text
docs/metric_catalog.md
docs/business_rules.md
src/metrics.py
tests/test_metrics.py
```

## Catálogo de métricas

Crie:

```text
docs/metric_catalog.md
```

Para cada métrica, documente:

* nome;
* objetivo de negócio;
* fórmula exata;
* tabela de origem;
* colunas usadas;
* grão;
* filtros;
* unidade;
* periodicidade;
* limitações;
* nível de confiança;
* arquivo de output;
* seção do relatório;
* tipo: descritiva, diagnóstica, preditiva ou recomendação.

## Métricas mínimas

### Vendas

* receita bruta;
* quantidade vendida;
* quantidade vendida em unidade de armazenagem;
* ticket médio;
* preço médio vendido;
* número de vendas ou pedidos;
* linhas de venda;
* SKUs vendidos;
* receita por loja;
* receita por categoria;
* receita same-store YoY;
* variação mensal;
* variação YoY;
* dias com venda por loja/mês.

### Compras e estoque

* estoque inicial;
* compras registradas;
* compras em unidade de armazenagem;
* estoque inicial + compras;
* vendas acumuladas;
* saldo projetado;
* gap contábil de estoque;
* cobertura de compras;
* cobertura em dias;
* produtos vendidos sem compra registrada;
* produtos vendidos acima das entradas conhecidas.

### Precificação

* preço médio mensal;
* variação de preço;
* dispersão de preço por loja;
* correlação preço-volume;
* candidatos a investigação de preço.

### Projeção e recomendação

* venda observada projetada;
* demanda potencial, se estimada;
* estoque de segurança;
* compra bruta sugerida;
* compra líquida sugerida, apenas se estoque disponível for confiável;
* candidatos a promoção;
* candidatos a descontinuação;
* candidatos a repricing;
* nível de confiança da recomendação.

## Regras de negócio

Crie:

```text
docs/business_rules.md
```

Cada regra deve conter:

* nome;
* descrição;
* fórmula;
* justificativa;
* tabela ou tabelas afetadas;
* colunas usadas;
* exceções;
* risco se a regra estiver errada;
* impacto no relatório;
* teste automatizado correspondente.

## Regras mínimas

Documente estas regras:

1. Toda análise de estoque deve usar unidade comum de armazenagem.
2. Venda observada não é demanda real.
3. Saldo negativo não prova ruptura física.
4. Nulo de estoque não é automaticamente estoque zero.
5. Preço de compra nulo não pode entrar no CMV sem regra explícita.
6. Loja atípica deve ser segmentada, não escondida.
7. Comparações temporais devem respeitar sazonalidade.
8. Correlação não é causalidade.
9. Recomendações são triagens quando faltam dados críticos.

## Código de métricas

Crie ou refatore:

```text
src/metrics.py
```

As métricas principais devem ser funções reutilizáveis e testáveis.

## Testes da Spec 03

Crie:

```text
tests/test_metrics.py
```

Os testes devem validar:

* `docs/metric_catalog.md` existe;
* `docs/business_rules.md` existe;
* métricas principais estão documentadas;
* regras mínimas estão documentadas;
* `src/metrics.py` existe;
* funções principais de métricas existem;
* receita é calculada corretamente;
* quantidade é calculada corretamente;
* preço médio é calculado corretamente;
* ticket médio é calculado corretamente;
* variação percentual é calculada corretamente;
* cobertura de compras é calculada corretamente;
* gap contábil é calculado corretamente;
* funções lidam com divisão por zero;
* funções lidam com dados vazios de forma controlada;
* fórmulas testadas batem com o catálogo de métricas.

## Critérios de aceite

A spec estará concluída quando:

* métricas estiverem documentadas;
* regras de negócio estiverem documentadas;
* funções de métricas existirem;
* testes das métricas passarem;
* nenhuma métrica crítica estiver implícita.

---

# 11. Spec 04 — Compras, estoque, unidades e reconciliação

## Objetivo

Corrigir e validar a lógica de compras, estoque, unidades e gaps.

Esta é uma das specs mais importantes, porque erros aqui podem destruir as conclusões do relatório.

## Entregáveis esperados

```text
outputs/tables/compras_coverage_audit.csv
outputs/tables/gaps_saldo_contabil_estoque.csv
src/analysis/inventory_reconciliation.py
tests/test_units.py
tests/test_reconciliation.py
```

## Regras obrigatórias

Vendas em unidade de estoque:

```text
QTD_VENDA_ESTOQUE = QUANTIDADE_VENDIDA × CONVERSAO_VENDA_PARA_ARMAZENAGEM
```

Compras em unidade de estoque:

```text
QTD_COMPRA_ESTOQUE = QUANTIDADE_COMPRA × CONVERSAO_COMPRA_ARMAZENAGEM
```

Se `QUANTIDADE_COMPRA` já estiver em unidade de armazenagem, documente explicitamente em:

```text
docs/known_limitations.md
```

Não deixe conversão implícita.

## Gap contábil

Não chame saldo negativo automaticamente de ruptura.

Use:

```text
gap_entrada = max(vendas_acumuladas - estoque_inicial - compras_acumuladas, 0)
```

Interprete gap como possível:

* ruptura;
* transferência não capturada;
* compra ausente;
* ajuste de inventário ausente;
* devolução não modelada;
* falha de extração;
* erro de unidade;
* estoque inicial incompleto;
* erro de data.

## Auditoria de cobertura de compras

Gere:

```text
outputs/tables/compras_coverage_audit.csv
```

Esse arquivo deve medir:

* total vendido em unidade de estoque;
* estoque inicial em unidade de estoque;
* compras registradas em unidade de estoque;
* estoque inicial + compras;
* diferença entre saídas e entradas conhecidas;
* percentual de cobertura;
* percentual de eventos com saldo negativo;
* percentual de SKUs com venda mas sem compra;
* percentual de SKUs com venda mas sem estoque inicial suficiente;
* cobertura por mês;
* cobertura por loja;
* cobertura por categoria;
* cobertura por produto.

Classificação:

* `OK`;
* `suspeito`;
* `crítico`;
* `não confiável para análise causal`.

Se a cobertura for baixa, o relatório não pode concluir que houve queda real de reposição.
Ele só pode dizer que os registros disponíveis de compras caíram ou são incompletos.

## Testes da Spec 04

Crie:

```text
tests/test_units.py
tests/test_reconciliation.py
```

Os testes devem validar:

* conversão de venda para unidade de estoque;
* conversão de compra para unidade de estoque;
* nenhuma análise de estoque usa unidade de venda misturada com unidade de compra;
* compras usam `QTD_COMPRA_ESTOQUE` quando conversão existir;
* vendas usam `QTD_VENDA_ESTOQUE` quando conversão existir;
* gap contábil é calculado corretamente;
* gap nunca fica negativo;
* saldo negativo não é classificado automaticamente como ruptura física;
* `compras_coverage_audit.csv` é gerado;
* `gaps_saldo_contabil_estoque.csv` é gerado;
* outputs possuem colunas obrigatórias;
* classificação de confiabilidade pertence às categorias esperadas;
* casos sem compras registradas são tratados como limitação, não como prova causal.

## Critérios de aceite

A spec estará concluída quando:

* unidades estiverem tratadas explicitamente;
* gaps não forem chamados de ruptura física;
* cobertura de compras estiver auditada;
* outputs forem gerados;
* testes de unidade e reconciliação passarem.

---

# 12. Spec 05 — Vendas, lojas, categorias e sortimento

## Objetivo

Validar o que pode estar correto nas análises comerciais.

Esta etapa só deve ocorrer depois de qualidade, métricas, regras de negócio e unidades estarem minimamente validadas.

## Entregáveis esperados

```text
outputs/tables/vendas_same_store_yoy.csv
outputs/tables/vendas_categorias_yoy.csv
outputs/tables/sortimento_controlado_por_volume.csv
src/analysis/sales_analysis.py
src/analysis/assortment_analysis.py
tests/test_sales_analysis.py
tests/test_assortment_analysis.py
```

## Análise de lojas

A análise deve:

* comparar mês contra mesmo mês do ano anterior;
* considerar lojas comparáveis;
* medir receita;
* medir quantidade;
* medir ticket médio;
* medir SKUs vendidos;
* medir dias com venda;
* indicar lojas novas ou com histórico incompleto.

Não conclua que não houve fechamento de loja apenas porque houve venda em algum mês.

Verifique:

* dias com venda por mês;
* meses sem venda;
* queda abrupta de dias com venda;
* lojas que aparecem;
* lojas que desaparecem;
* lojas com comportamento incompatível com operação normal.

## Análise de categorias

A análise deve:

* comparar mês contra mesmo mês do ano anterior;
* comparar trimestre contra mesmo trimestre do ano anterior;
* classificar categorias em:

  * queda generalizada;
  * queda concentrada;
  * crescimento;
  * comportamento atípico;
  * dados insuficientes.

Evite comparar períodos com sazonalidade diferente sem alerta.

## Análise de sortimento

A queda de SKUs vendidos não prova desabastecimento se o volume de transações também caiu.

Implemente:

* SKUs distintos por mês;
* volume de transações ou linhas por mês;
* amostragem ou reamostragem para estimar SKUs esperados dado o volume;
* comparação entre sortimento observado e esperado;
* percentis ou intervalo de confiança.

Pergunta central:

```text
Dado o volume de vendas do mês final, quantos SKUs esperaríamos vender se o mix histórico continuasse igual?
```

Se o sortimento observado for muito menor que o esperado, isso fortalece a hipótese de estreitamento real do sortimento.

Se não for, a queda de SKUs pode ser apenas consequência da queda de volume.

## Testes da Spec 05

Crie:

```text
tests/test_sales_analysis.py
tests/test_assortment_analysis.py
```

Os testes devem validar:

* `vendas_same_store_yoy.csv` é gerado;
* `vendas_categorias_yoy.csv` é gerado;
* `sortimento_controlado_por_volume.csv` é gerado;
* same-store compara mês contra mesmo mês do ano anterior;
* lojas comparáveis são identificadas corretamente;
* lojas novas ou incompletas são marcadas;
* dias com venda são calculados corretamente;
* variação YoY é calculada corretamente;
* categorias são classificadas corretamente;
* sortimento observado é calculado corretamente;
* sortimento esperado por amostragem é calculado;
* percentis ou intervalo de confiança são gerados;
* queda de SKUs não é automaticamente interpretada como ruptura.

## Critérios de aceite

A spec estará concluída quando:

* análises YoY forem criadas;
* same-store estiver implementado;
* queda de SKUs estiver controlada por volume;
* outputs forem gerados;
* testes passarem;
* conclusões de sortimento forem tratadas como evidência, não prova automática de ruptura.

---

# 13. Spec 06 — Precificação, projeção e recomendações

## Objetivo

Corrigir linguagem e lógica de preço, projeção e recomendação.

Esta etapa deve impedir que correlação seja vendida como causalidade e que triagens sejam vendidas como decisões finais.

## Entregáveis esperados

```text
outputs/tables/produtos_correlacao_preco_volume_negativa.csv
outputs/tables/projecao_venda_observada_2026.csv
outputs/tables/triagem_possivel_promocao.csv
outputs/tables/triagem_possivel_descontinuacao.csv
src/analysis/pricing_analysis.py
src/analysis/projection_analysis.py
src/analysis/recommendation_triage.py
tests/test_pricing.py
tests/test_projection.py
tests/test_recommendations.py
```

## Precificação

Se o método calcula apenas correlação entre preço médio e quantidade vendida, não chame de elasticidade.

Use linguagem:

```text
candidato a investigação de preço
```

Não use:

```text
produto com demanda sensível a preço
```

Se possível, implemente modelo exploratório melhor, mas sem afirmar causalidade:

```text
log(qtd + 1) ~ log(preco) + efeitos fixos de produto + efeitos fixos de loja + efeitos fixos de mês
```

Deixe claro que:

* é observacional;
* não prova causalidade;
* não controla promoções se a base não tiver promoção;
* não controla estoque real se a base de estoque for incompleta.

## Projeção

Separe:

* venda observada;
* demanda inferida;
* demanda potencial;
* compra bruta sugerida;
* compra líquida sugerida.

Se houver suspeita de ruptura, venda observada pode estar censurada.

Se estoque disponível não for confiável, não gere compra líquida como decisão final.

Use:

```text
compra_liquida_sugerida = max(demanda_projetada + estoque_seguranca - estoque_disponivel, 0)
```

apenas quando estoque disponível for confiável.

Caso contrário, gere:

* `demanda_observada_projetada`;
* `estoque_seguranca`;
* `compra_bruta_sugerida`;
* `estoque_a_validar_antes_da_compra`;
* `flag_nao_calcular_compra_liquida_por_estoque_inconfiavel`.

## Recomendações

Transforme recomendações em triagens.

Cada triagem deve ter:

* regra usada;
* evidência;
* nível de confiança;
* dado faltante;
* risco de decisão;
* próxima validação necessária.

Não recomende descontinuação final sem dados de:

* margem;
* estoque atual;
* idade do estoque;
* lead time;
* lote mínimo;
* fornecedor;
* sazonalidade;
* produto substituto;
* papel estratégico do SKU;
* custo de armazenagem;
* devoluções;
* garantias;
* campanhas comerciais.

## Testes da Spec 06

Crie:

```text
tests/test_pricing.py
tests/test_projection.py
tests/test_recommendations.py
```

Os testes devem validar:

* arquivo de correlação preço-volume é gerado;
* nenhum output novo usa “elasticidade” no nome se só houver correlação;
* correlação preço-volume é calculada corretamente;
* produtos com poucos pontos são tratados como dados insuficientes;
* projeção de venda observada é gerada;
* venda observada não é chamada de demanda real;
* compra líquida só é calculada quando estoque disponível for confiável;
* flag de impossibilidade de compra líquida existe quando aplicável;
* triagens de promoção são geradas;
* triagens de descontinuação são geradas;
* triagens possuem nível de confiança;
* triagens possuem dados faltantes;
* triagens possuem risco de decisão;
* triagens não usam linguagem de decisão final.

## Critérios de aceite

A spec estará concluída quando:

* elasticidade for rebaixada para correlação exploratória;
* projeção for tratada como cenário observado;
* recomendações forem tratadas como triagem;
* compra líquida não for calculada se estoque for inconfiável;
* outputs forem gerados;
* testes passarem.

---

# 14. Spec 07 — Hipóteses e relatório final

## Objetivo

Reescrever hipóteses e relatório com rigor analítico.

Esta etapa só deve ocorrer depois das análises principais terem sido validadas.

## Entregáveis esperados

```text
docs/hypothesis_validation_matrix.md
outputs/tables/hypothesis_status.csv
reports/relatorio_final.md
tests/test_hypothesis_report.py
```

## Matriz de hipóteses

Crie:

```text
docs/hypothesis_validation_matrix.md
outputs/tables/hypothesis_status.csv
```

A matriz deve conter:

* hipótese;
* evidência usada;
* teste executado;
* resultado;
* status;
* nível de confiança;
* riscos;
* dados ausentes;
* conclusão permitida;
* conclusão proibida.

## Status permitidos

Use apenas:

* `Confirmada descritivamente`;
* `Parcialmente suportada`;
* `Exploratória`;
* `Não comprovada`;
* `Rejeitada`;
* `Inválida por limitação de dados`.

## Hipóteses mínimas

A matriz deve avaliar:

* H1: queda causada por fechamento de lojas;
* H2: queda concentrada em poucas categorias;
* H3: queda concentrada em poucas lojas;
* H4: sortimento vendido encolheu;
* H5: compras/reposição causaram queda de vendas;
* H6: base de compras está incompleta;
* H7: queda pode ser demanda real e não ruptura;
* H8: preço explica parte da queda;
* H9: recomendações de compra são acionáveis;
* H10: recomendações de descontinuação são acionáveis.

## Relatório final

Reescreva:

```text
reports/relatorio_final.md
```

O relatório deve conter:

1. Sumário executivo.
2. O que foi validado com alta confiança.
3. O que foi validado apenas como evidência descritiva.
4. O que permanece hipótese.
5. O que foi rejeitado.
6. Principais limitações dos dados.
7. Qualidade e cobertura das bases.
8. Diagnóstico de vendas.
9. Diagnóstico de lojas.
10. Diagnóstico de categorias.
11. Diagnóstico de sortimento.
12. Diagnóstico de compras e estoque.
13. Precificação: correlação, não causalidade.
14. Projeção: cenário observado, não demanda real.
15. Recomendações como triagem.
16. Próximos dados necessários.
17. Conclusão honesta.

## Linguagem obrigatória

Troque afirmações fortes por linguagem rigorosa.

Exemplo 1:

De:

```text
A reposição de estoque matou o sortimento vendável.
```

Para:

```text
Os registros disponíveis de compras caíram e não explicam as saídas observadas. Porém, como a base de compras é incompleta, isso não prova queda real de reposição operacional. A hipótese de desabastecimento é plausível, mas precisa de validação com entradas completas, transferências, ajustes de estoque e estoque final.
```

Exemplo 2:

De:

```text
As lojas ficaram sem itens para vender.
```

Para:

```text
A queda de sortimento vendido é compatível com indisponibilidade, mas também pode ser explicada por queda de volume, alteração de mix, falha de captura, substituição de SKUs ou redução real de demanda. A análise controlada por volume deve indicar se o estreitamento do sortimento excede o esperado.
```

Exemplo 3:

De:

```text
Produto com elasticidade negativa forte.
```

Para:

```text
Produto com correlação negativa entre preço médio e volume vendido, candidato a investigação comercial.
```

## Testes da Spec 07

Crie:

```text
tests/test_hypothesis_report.py
```

Os testes devem validar:

* `docs/hypothesis_validation_matrix.md` existe;
* `outputs/tables/hypothesis_status.csv` existe;
* `reports/relatorio_final.md` existe;
* `hypothesis_status.csv` tem colunas obrigatórias;
* status das hipóteses pertence à lista permitida;
* hipóteses mínimas H1 a H10 existem;
* cada hipótese tem conclusão permitida;
* cada hipótese tem conclusão proibida;
* relatório contém seção de limitações;
* relatório contém seção de qualidade dos dados;
* relatório contém seção de hipóteses;
* relatório não usa “ruptura comprovada” sem evidência;
* relatório não usa “elasticidade” quando só houver correlação;
* relatório não trata recomendações exploratórias como decisão final;
* relatório não afirma que compras causaram queda se cobertura for insuficiente.

## Critérios de aceite

A spec estará concluída quando:

* relatório estiver reescrito com rigor;
* hipóteses estiverem classificadas;
* limitações estiverem explícitas;
* conclusões permitidas e proibidas estiverem documentadas;
* testes passarem.

---

# 15. Spec 08 — Testes, execução, README e reprodutibilidade

## Objetivo

Garantir que o projeto rode, teste e seja auditável de ponta a ponta.

Esta spec consolida os testes criados nas specs anteriores.

## Entregáveis esperados

```text
tests/test_specs_exist.py
tests/test_ingestion.py
tests/test_schema.py
tests/test_quality_checks.py
tests/test_metrics.py
tests/test_units.py
tests/test_reconciliation.py
tests/test_sales_analysis.py
tests/test_assortment_analysis.py
tests/test_pricing.py
tests/test_projection.py
tests/test_recommendations.py
tests/test_hypothesis_report.py
tests/test_outputs.py
pyproject.toml
Makefile
README.md
```

## Makefile

Crie ou atualize:

```text
Makefile
```

Com comandos:

```bash
make install
make lint
make test
make run
make audit
make report
make all
```

Comportamento esperado:

* `make install` instala dependências;
* `make lint` roda `ruff`;
* `make test` roda `pytest`;
* `make run` executa o pipeline completo;
* `make audit` gera relatórios de qualidade;
* `make report` reconstrói tabelas e relatório final, se aplicável;
* `make all` roda lint, testes, pipeline e auditoria.

## Pyproject

Crie ou atualize:

```text
pyproject.toml
```

Inclua:

* dependências;
* configuração do pytest;
* configuração do ruff;
* paths do projeto;
* versão mínima do Python.

## README

Atualize:

```text
README.md
```

O README deve explicar:

* objetivo do projeto;
* estrutura do repositório;
* bases usadas;
* limitações principais;
* como instalar dependências;
* como rodar pipeline;
* como rodar testes;
* como rodar auditoria;
* como interpretar outputs;
* quais conclusões são confiáveis;
* quais conclusões são apenas hipóteses;
* quais dados adicionais seriam necessários;
* como abrir o dashboard quando ele for implementado.

## Testes da Spec 08

Crie:

```text
tests/test_outputs.py
```

Esse teste deve validar:

* outputs principais existem;
* outputs principais não estão vazios sem justificativa;
* outputs têm colunas obrigatórias;
* `ingestion_audit.csv` existe;
* `data_quality_report.csv` existe;
* `compras_coverage_audit.csv` existe;
* `hypothesis_status.csv` existe;
* specs existem;
* docs existem;
* relatório final existe;
* Makefile existe;
* pyproject existe;
* README existe.

Também rode:

```bash
make lint
make test
make run
make audit
```

Se algum comando falhar por motivo real, documente:

* comando;
* erro;
* causa provável;
* impacto;
* próximo passo.

## Critérios de aceite

A spec estará concluída quando:

* `make test` passar ou bloqueios reais estiverem documentados;
* `make lint` passar ou pendências estiverem documentadas;
* pipeline rodar do zero ou bloqueios reais estiverem documentados;
* README estiver atualizado;
* outputs principais forem validados;
* documentação estiver completa.

---

# 16. Spec 09 — Dashboard final e camada de apresentação

## Objetivo

Criar o dashboard final apenas depois que ingestão, tratamento, métricas, regras de negócio, validações, hipóteses, relatório, testes e reprodutibilidade estiverem implementados ou com bloqueios documentados.

O dashboard é camada de apresentação.

Ele não deve executar ETL pesado.
Ele não deve redefinir regras de negócio.
Ele não deve calcular métricas de forma diferente dos scripts validados.
Ele não deve transformar hipóteses em conclusões.

## Ferramentas recomendadas

Use:

* `Streamlit` como primeira opção;
* `Plotly` para gráficos interativos;
* `pandas` ou `polars` apenas para leitura e preparação leve dos outputs já validados.

Não use Dash, Power BI, Tableau ou outra ferramenta a menos que haja justificativa clara.

## Entregáveis esperados

Estrutura recomendada:

```text
dashboard/
  app.py
  pages/
  components/
  assets/
```

Ou, se a simplicidade for melhor:

```text
app.py
```

Também atualize:

```text
README.md
Makefile
tests/test_dashboard.py
```

Adicione comando:

```bash
make dashboard
```

## Fonte de dados do dashboard

O dashboard deve consumir preferencialmente arquivos já validados em:

```text
outputs/tables/
outputs/figures/
docs/
reports/
```

O dashboard não deve ler diretamente os dados brutos, exceto se houver uma seção específica de auditoria de ingestão.

## Regras obrigatórias do dashboard

1. O dashboard deve usar somente métricas documentadas em `docs/metric_catalog.md`.
2. O dashboard deve respeitar as regras de negócio em `docs/business_rules.md`.
3. O dashboard deve exibir limitações dos dados quando um indicador tiver baixa confiança.
4. O dashboard deve diferenciar:

   * fato validado;
   * evidência descritiva;
   * hipótese;
   * recomendação exploratória;
   * conclusão não comprovada.
5. O dashboard não deve chamar gap contábil de ruptura física.
6. O dashboard não deve chamar correlação preço-volume de elasticidade.
7. O dashboard não deve apresentar compra líquida sugerida se o estoque disponível for inconfiável.
8. O dashboard não deve apresentar recomendações de promoção, repricing ou descontinuação como decisões finais.
9. O dashboard deve deixar claro quando uma análise é uma triagem.
10. O dashboard deve contar uma história clara sobre desempenho do negócio, gargalos, riscos e oportunidades, sem exagerar causalidade.
11. O dashboard deve conter tooltips explicativos nos KPI’s, gráficos, filtros e indicadores principais.
12. Os tooltips devem explicar:

    * fórmula do KPI;
    * interpretação;
    * unidade;
    * nível de confiança;
    * limitação relevante;
    * fonte do dado.

## Estrutura recomendada do dashboard

### Página 1 — Sumário executivo

Mostrar:

* receita total;
* variação mensal;
* variação YoY, se disponível;
* quantidade vendida;
* SKUs vendidos;
* lojas ativas comparáveis;
* status geral das hipóteses;
* principais alertas de qualidade de dados.

Separar visualmente:

* indicadores confiáveis;
* indicadores exploratórios;
* indicadores bloqueados por dados insuficientes.

Incluir tooltips em todos os KPI’s principais.

### Página 2 — Qualidade dos dados

Mostrar:

* status dos checks;
* tabela de `data_quality_report.csv`;
* problemas críticos;
* impacto analítico;
* bases com maior risco;
* cobertura da base de compras;
* auditoria de encoding/parsing.

Essa página deve deixar claro se o projeto pode ou não sustentar conclusões causais.

### Página 3 — Vendas

Mostrar:

* evolução mensal de receita;
* evolução mensal de quantidade;
* ticket médio;
* preço médio;
* variação YoY;
* sazonalidade;
* principais produtos.

### Página 4 — Lojas

Mostrar:

* receita por loja;
* same-store sales YoY;
* dias com venda por loja/mês;
* lojas novas ou incompletas;
* lojas com comportamento atípico.

Não concluir fechamento operacional apenas por ausência ou presença de vendas sem evidência adicional.

### Página 5 — Categorias

Mostrar:

* receita por categoria;
* variação YoY por categoria;
* categorias em queda;
* categorias em crescimento;
* categorias com dados insuficientes.

### Página 6 — Sortimento

Mostrar:

* SKUs vendidos por mês;
* linhas/transações por mês;
* SKUs observados vs SKUs esperados controlando volume;
* interpretação da queda de sortimento.

Deixar claro se a queda de SKUs excede ou não o esperado dado o volume.

### Página 7 — Compras, estoque e gap contábil

Mostrar:

* compras registradas;
* estoque inicial;
* vendas em unidade de armazenagem;
* cobertura de compras;
* gaps contábeis;
* classificação de confiabilidade para análise causal.

Nunca chamar automaticamente gap contábil de ruptura física.

### Página 8 — Precificação

Mostrar:

* preço médio;
* dispersão de preço por loja;
* correlação preço-volume;
* candidatos a investigação de preço.

Usar linguagem:

```text
correlação exploratória
```

Não usar:

```text
elasticidade comprovada
```

### Página 9 — Projeção e triagens

Mostrar:

* projeção de venda observada;
* cenário-piso;
* compra bruta sugerida;
* flag de impossibilidade de compra líquida, quando aplicável;
* triagens de promoção;
* triagens de descontinuação;
* triagens de repricing.

Toda recomendação deve mostrar:

* regra usada;
* evidência;
* nível de confiança;
* dado faltante;
* risco da decisão;
* próxima validação necessária.

### Página 10 — Hipóteses e conclusão

Mostrar:

* matriz de hipóteses;
* status de cada hipótese;
* evidência usada;
* conclusão permitida;
* conclusão proibida;
* próximos dados necessários.

### Página 10 — Glossário

Mostrar:

* dicionário de termos técnicos para usuários sem conhecimento técnico aprofundado
* guia de leitura dos KPIs
* fórmulas e regras de negócio 
* Dicionário de dados simplificado para explicar bases e colunas 
* FAQ do dashboard perguntas frequentes com respostas evitando Overconfidence sempre falando de hipóteses e olhando tudo como um cenário de teste. Sem dar certezas absolutas
* lista de todas as tecnologias usadas sejam bibliotecas, linguagens etc


## Design e experiência do usuário

O dashboard deve seguir estes princípios:

* espaço de respiro entre blocos;
* fundo neutro;
* cores de destaque apenas para alertas, KPI’s ou diferenças importantes;
* evitar poluição visual;
* títulos explicativos;
* subtítulos com interpretação de negócio;
* notas de limitação próximas aos gráficos;
* tooltips em KPI’s, gráficos, filtros e indicadores;
* filtros globais quando fizer sentido:

  * período;
  * loja;
  * categoria;
  * produto;
  * nível de confiança;
  * status da hipótese;
* tabelas com busca, ordenação e download quando fizer sentido;
* visualizações interativas;
* storytelling claro.

O dashboard deve responder:

1. O que aconteceu?
2. Onde aconteceu?
3. O que os dados permitem afirmar?
4. O que ainda é hipótese?
5. Quais decisões podem ser tomadas agora?
6. Quais decisões exigem mais dados?

## Testes da Spec 09

Crie:

```text
tests/test_dashboard.py
```

Os testes devem validar:

* arquivo principal do dashboard existe;
* comando `make dashboard` existe no Makefile;
* dashboard importa sem erro;
* dashboard não lê dados brutos diretamente, salvo seção específica de auditoria;
* dashboard consome outputs validados;
* dashboard contém referências às principais páginas/seções;
* dashboard contém tooltips ou help texts nos principais KPI’s;
* dashboard não usa linguagem proibida como “ruptura comprovada” sem evidência;
* dashboard não usa “elasticidade comprovada” se só houver correlação;
* dashboard não apresenta recomendações exploratórias como decisão final;
* README explica como abrir o dashboard.

## Critérios de aceite

A spec estará concluída quando:

* `make dashboard` executar o dashboard;
* dashboard rodar sem recalcular o ETL completo;
* dashboard consumir outputs validados;
* dashboard não possuir métricas divergentes do catálogo;
* dashboard exibir limitações e níveis de confiança;
* dashboard possuir tooltips explicativos;
* dashboard não transformar hipótese em conclusão;
* dashboard não apresentar recomendações exploratórias como decisão final;
* README explicar como abrir e usar o dashboard;
* testes do dashboard passarem ou bloqueios reais estiverem documentados.

---

# 17. Entrega final esperada

Ao concluir todas as fases, entregue um resumo final com:

1. specs criadas;
2. specs implementadas;
3. arquivos criados;
4. arquivos alterados;
5. principais bugs corrigidos;
6. principais melhorias de engenharia de dados;
7. principais melhorias de análise de negócio;
8. principais conclusões rebaixadas;
9. hipóteses mantidas;
10. hipóteses rejeitadas ou não comprovadas;
11. comandos para rodar;
12. comandos para testar;
13. comandos para auditar;
14. comando para abrir o dashboard;
15. riscos remanescentes;
16. dados adicionais necessários.

Se alguma etapa não puder ser feita, documente:

* o que não pôde ser feito;
* por que não pôde ser feito;
* qual seria a validação correta;
* impacto nas conclusões;
* impacto no dashboard, se houver.

Não esconda limitações.

O objetivo final é que qualquer pessoa consiga:

1. entender os dados;
2. entender as regras de negócio;
3. rodar o pipeline;
4. validar os testes;
5. auditar a qualidade dos dados;
6. interpretar as hipóteses;
7. abrir o dashboard;
8. saber exatamente o que é conclusão confiável e o que ainda é hipótese.
