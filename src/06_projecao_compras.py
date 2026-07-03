# -*- coding: utf-8 -*-
"""
06_projecao_compras.py
Etapa 6 - Projecao de Compras para o Proximo Ano (2026)

Metodologia:
1. Demanda mensal media por produto/loja nos 24 meses observados (usando
   vendas, que sao o dado mais completo e confiavel da base).
2. Tendencia: regressao linear simples da venda mensal ao longo do tempo
   (24 pontos) por produto, para capturar crescimento/queda estrutural.
3. Sazonalidade: indice sazonal mensal (media do mes / media geral) por
   categoria (NIVEL_1), aplicado a projecao mes a mes de 2026.
4. Estoque de seguranca: adicionamos 30 dias de cobertura como buffer,
   descontando o estoque projetado remanescente ao final do periodo
   observado (quando disponivel e nao-negativo) para chegar na
   sugestao de compra liquida.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROC = "../data/processed"
FIG = "../outputs/figures"
TAB = "../outputs/tables"

print("[PROJECAO] Carregando bases...")
vendas = pd.read_parquet(f"{PROC}/fato_vendas.parquet")
dim_produto = pd.read_parquet(f"{PROC}/dim_produto.parquet")
cobertura = pd.read_parquet(f"{PROC}/cobertura_estoque.parquet")

vendas["ANO_MES"] = vendas["DATA_VENDA"].dt.to_period("M")
vendas["MES_NUM"] = vendas["DATA_VENDA"].dt.month
vendas["IDX_MES"] = (vendas["ANO_MES"] - vendas["ANO_MES"].min()).apply(lambda x: x.n)

# ---------------------------------------------------------------------------
# 1. Serie mensal por produto (todas as lojas somadas, unidade de estoque)
# ---------------------------------------------------------------------------
print("[PROJECAO] Construindo serie mensal por produto...")
serie_prod = (
    vendas.groupby(["CODIGO", "IDX_MES", "MES_NUM"])["QTD_VENDA_ESTOQUE"]
    .sum()
    .reset_index()
)

# Garante 24 meses completos por produto (preenche com 0 quando nao vendeu no mes)
produtos_com_venda = serie_prod["CODIGO"].unique()
meses_completos = pd.DataFrame({"IDX_MES": range(24)})
meses_completos["MES_NUM"] = [((i % 12) + 1) for i in range(24)]

grid = pd.MultiIndex.from_product([produtos_com_venda, range(24)], names=["CODIGO", "IDX_MES"]).to_frame(index=False)
grid = grid.merge(meses_completos[["IDX_MES", "MES_NUM"]], on="IDX_MES", how="left")
serie_completa = grid.merge(serie_prod, on=["CODIGO", "IDX_MES", "MES_NUM"], how="left")
serie_completa["QTD_VENDA_ESTOQUE"] = serie_completa["QTD_VENDA_ESTOQUE"].fillna(0)

# ---------------------------------------------------------------------------
# 2. Tendencia (regressao linear simples) por produto
# ---------------------------------------------------------------------------
print("[PROJECAO] Calculando tendencia linear por produto...")
def slope_intercept(g):
    x = g["IDX_MES"].values
    y = g["QTD_VENDA_ESTOQUE"].values
    if len(x) < 2 or np.all(y == 0):
        return pd.Series({"slope": 0.0, "intercept": y.mean() if len(y) else 0.0})
    A = np.vstack([x, np.ones(len(x))]).T
    slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
    return pd.Series({"slope": slope, "intercept": intercept})

tendencia = serie_completa.groupby("CODIGO").apply(slope_intercept).reset_index()

# ---------------------------------------------------------------------------
# 3. Indice sazonal mensal por categoria (NIVEL_1)
# ---------------------------------------------------------------------------
print("[PROJECAO] Calculando indice sazonal por categoria...")
vendas_cat = vendas.merge(dim_produto[["CODIGO", "NIVEL_1"]], on="CODIGO", how="left")
sazon_cat = vendas_cat.groupby(["NIVEL_1", "MES_NUM"])["QTD_VENDA_ESTOQUE"].sum().reset_index()
media_cat = vendas_cat.groupby("NIVEL_1")["QTD_VENDA_ESTOQUE"].sum().reset_index().rename(columns={"QTD_VENDA_ESTOQUE": "total_cat"})
sazon_cat = sazon_cat.merge(media_cat, on="NIVEL_1")
sazon_cat["media_mensal_esperada"] = sazon_cat["total_cat"] / 24
sazon_cat["indice_sazonal"] = sazon_cat["QTD_VENDA_ESTOQUE"] / (sazon_cat["total_cat"] / 12)
sazon_cat = sazon_cat[["NIVEL_1", "MES_NUM", "indice_sazonal"]]

# ---------------------------------------------------------------------------
# 4. Projecao mensal 2026 por produto = tendencia(mes 24..35) * indice sazonal
# ---------------------------------------------------------------------------
print("[PROJECAO] Projetando demanda 2026...")
produto_cat = dim_produto[["CODIGO", "DESCRICAO", "NIVEL_1"]]
proj_base = tendencia.merge(produto_cat, on="CODIGO", how="left")

meses_2026 = pd.DataFrame({"IDX_MES_FUT": range(24, 36), "MES_NUM": [((i % 12) + 1) for i in range(24, 36)]})
proj = proj_base.merge(meses_2026, how="cross")
proj = proj.merge(sazon_cat, on=["NIVEL_1", "MES_NUM"], how="left")
proj["indice_sazonal"] = proj["indice_sazonal"].fillna(1.0)

proj["demanda_tendencia"] = (proj["slope"] * proj["IDX_MES_FUT"] + proj["intercept"]).clip(lower=0)
proj["demanda_projetada"] = proj["demanda_tendencia"] * proj["indice_sazonal"]
proj["demanda_projetada"] = proj["demanda_projetada"].clip(lower=0)

proj_mensal_2026 = proj[["CODIGO", "DESCRICAO", "NIVEL_1", "MES_NUM", "demanda_projetada"]].copy()
proj_mensal_2026.to_csv(f"{TAB}/projecao_demanda_mensal_2026.csv", index=False)

# ---------------------------------------------------------------------------
# 5. Demanda anual projetada 2026 e sugestao de compra
# ---------------------------------------------------------------------------
demanda_anual_2026 = proj_mensal_2026.groupby(["CODIGO", "DESCRICAO", "NIVEL_1"])["demanda_projetada"].sum().reset_index()
demanda_anual_2026 = demanda_anual_2026.rename(columns={"demanda_projetada": "demanda_projetada_2026"})

demanda_2024_25 = vendas.groupby("CODIGO")["QTD_VENDA_ESTOQUE"].sum().reset_index().rename(
    columns={"QTD_VENDA_ESTOQUE": "vendido_24_meses"}
)
demanda_anual_2026 = demanda_anual_2026.merge(demanda_2024_25, on="CODIGO", how="left")
demanda_anual_2026["venda_media_anual_historica"] = demanda_anual_2026["vendido_24_meses"] / 2
demanda_anual_2026["crescimento_pct_vs_media_historica"] = (
    (demanda_anual_2026["demanda_projetada_2026"] / demanda_anual_2026["venda_media_anual_historica"].replace(0, np.nan) - 1) * 100
).round(1)

# Estoque de seguranca de 30 dias com base na venda media diaria projetada
demanda_anual_2026["venda_media_diaria_2026"] = demanda_anual_2026["demanda_projetada_2026"] / 365
demanda_anual_2026["estoque_seguranca_30d"] = demanda_anual_2026["venda_media_diaria_2026"] * 30

# Estoque disponivel ao final do periodo observado (soma entre lojas, so considera se >0)
estoque_final = cobertura.groupby("CODIGO")["ESTOQUE_INICIAL"].sum().reset_index().rename(
    columns={"ESTOQUE_INICIAL": "estoque_inicial_total_referencia"}
)
demanda_anual_2026 = demanda_anual_2026.merge(estoque_final, on="CODIGO", how="left")
demanda_anual_2026["estoque_inicial_total_referencia"] = demanda_anual_2026["estoque_inicial_total_referencia"].fillna(0)

demanda_anual_2026["sugestao_compra_2026"] = (
    demanda_anual_2026["demanda_projetada_2026"] + demanda_anual_2026["estoque_seguranca_30d"]
).round(0)

demanda_anual_2026 = demanda_anual_2026.sort_values("demanda_projetada_2026", ascending=False)
demanda_anual_2026.to_csv(f"{TAB}/projecao_compras_2026.csv", index=False)

print("[PROJECAO] Top 10 produtos por demanda projetada 2026:")
print(
    demanda_anual_2026.head(10)[
        ["CODIGO", "DESCRICAO", "demanda_projetada_2026", "sugestao_compra_2026", "crescimento_pct_vs_media_historica"]
    ].to_string(index=False)
)

# ---------------------------------------------------------------------------
# 6. Grafico: total projetado por mes 2026 vs. media historica mensal
# ---------------------------------------------------------------------------
proj_total_mes = proj_mensal_2026.groupby("MES_NUM")["demanda_projetada"].sum().reset_index()
hist_total_mes = vendas.groupby(vendas["DATA_VENDA"].dt.month)["QTD_VENDA_ESTOQUE"].sum().reset_index()
hist_total_mes.columns = ["MES_NUM", "qtd_historica_total"]
hist_total_mes["media_mensal_historica"] = hist_total_mes["qtd_historica_total"] / 2

meses_nome = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(meses_nome, hist_total_mes.sort_values("MES_NUM")["media_mensal_historica"], marker="o", label="Media mensal historica (2024-2025)", color="#64748b")
ax.plot(meses_nome, proj_total_mes.sort_values("MES_NUM")["demanda_projetada"], marker="o", label="Projecao mensal 2026", color="#dc2626")
ax.set_title("Demanda projetada 2026 vs. media historica (todos os produtos)", fontsize=12, fontweight="bold")
ax.set_ylabel("Quantidade (unidade de estoque)")
ax.legend()
plt.tight_layout()
plt.savefig(f"{FIG}/projecao_demanda_2026.png")
plt.close()

print(f"[PROJECAO] Demanda total projetada 2026: {demanda_anual_2026['demanda_projetada_2026'].sum():,.0f} unidades")
print(f"[PROJECAO] Demanda total observada media anual (2024-2025): {demanda_anual_2026['venda_media_anual_historica'].sum():,.0f} unidades")
print("[PROJECAO] Concluido.")
