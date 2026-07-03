# -*- coding: utf-8 -*-
"""
03_analise_vendas.py
Etapa 3 - Analise de Desempenho de Vendas

- Ranking de produtos mais/menos vendidos (quantidade e receita)
- Analise por hierarquia (NIVEL_1)
- Analise por loja / regiao (estado)
- Sazonalidade mensal
"""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

PROC = "../data/processed"
FIG = "../outputs/figures"
TAB = "../outputs/tables"

plt.rcParams["figure.dpi"] = 110
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["font.size"] = 10

print("[VENDAS] Carregando bases...")
vendas = pd.read_parquet(f"{PROC}/fato_vendas.parquet")
dim_produto = pd.read_parquet(f"{PROC}/dim_produto.parquet")
dim_lojas = pd.read_parquet(f"{PROC}/dim_lojas.parquet")

vendas = vendas.merge(dim_produto[["CODIGO", "DESCRICAO", "NIVEL_1", "NIVEL_2", "NIVEL_3"]], on="CODIGO", how="left")
vendas = vendas.merge(dim_lojas, on="COD_EMPRESA", how="left")
vendas["ANO_MES"] = vendas["DATA_VENDA"].dt.to_period("M").astype(str)

def fmt_milhoes(x, pos):
    return f"{x/1e6:.1f}M" if abs(x) >= 1e6 else f"{x/1e3:.0f}K"

# ---------------------------------------------------------------------------
# 1. Ranking de produtos - quantidade e receita
# ---------------------------------------------------------------------------
print("[VENDAS] Ranking de produtos...")
rank_produto = (
    vendas.groupby(["CODIGO", "DESCRICAO", "NIVEL_1"])
    .agg(
        qtd_vendida=("QTD_VENDA_ESTOQUE", "sum"),
        receita=("RECEITA", "sum"),
        qtd_transacoes=("QUANTIDADE_VENDIDA", "count"),
        lojas_distintas=("COD_EMPRESA", "nunique"),
    )
    .reset_index()
    .sort_values("receita", ascending=False)
)
rank_produto.to_csv(f"{TAB}/ranking_produtos_completo.csv", index=False)

top20_receita = rank_produto.head(20)
bottom20_receita = rank_produto[rank_produto["qtd_vendida"] > 0].sort_values("receita").head(20)
top20_receita.to_csv(f"{TAB}/top20_produtos_receita.csv", index=False)
bottom20_receita.to_csv(f"{TAB}/bottom20_produtos_receita.csv", index=False)

top20_qtd = rank_produto.sort_values("qtd_vendida", ascending=False).head(20)
top20_qtd.to_csv(f"{TAB}/top20_produtos_quantidade.csv", index=False)

# Produtos cadastrados sem NENHUMA venda
produtos_sem_venda = dim_produto[~dim_produto["CODIGO"].isin(vendas["CODIGO"].unique())]
produtos_sem_venda.to_csv(f"{TAB}/produtos_sem_nenhuma_venda.csv", index=False)
print(f"[VENDAS] {len(produtos_sem_venda)} de {len(dim_produto)} produtos cadastrados nao tiveram NENHUMA venda em 24 meses")

# Grafico top 15 receita
fig, ax = plt.subplots(figsize=(9, 6))
d = top20_receita.head(15).iloc[::-1]
labels = [f"{desc[:35]}" for desc in d["DESCRICAO"]]
ax.barh(labels, d["receita"], color="#2563eb")
ax.set_title("Top 15 produtos por receita (24 meses)", fontsize=13, fontweight="bold")
ax.set_xlabel("Receita (R$)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhoes))
plt.tight_layout()
plt.savefig(f"{FIG}/top15_produtos_receita.png")
plt.close()

# ---------------------------------------------------------------------------
# 2. Analise por hierarquia NIVEL_1
# ---------------------------------------------------------------------------
print("[VENDAS] Analise por categoria (NIVEL_1)...")
por_categoria = (
    vendas.groupby("NIVEL_1")
    .agg(receita=("RECEITA", "sum"), qtd_vendida=("QTD_VENDA_ESTOQUE", "sum"), qtd_produtos=("CODIGO", "nunique"))
    .reset_index()
    .sort_values("receita", ascending=False)
)
por_categoria["pct_receita"] = (por_categoria["receita"] / por_categoria["receita"].sum() * 100).round(2)
por_categoria.to_csv(f"{TAB}/vendas_por_categoria_nivel1.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 7))
d = por_categoria.sort_values("receita").tail(23)
ax.barh([c[:35] for c in d["NIVEL_1"]], d["receita"], color="#16a34a")
ax.set_title("Receita por categoria (NIVEL_1) - 24 meses", fontsize=13, fontweight="bold")
ax.set_xlabel("Receita (R$)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhoes))
plt.tight_layout()
plt.savefig(f"{FIG}/receita_por_categoria.png")
plt.close()

# ---------------------------------------------------------------------------
# 3. Analise por loja / regiao
# ---------------------------------------------------------------------------
print("[VENDAS] Analise por loja e estado...")
por_loja = (
    vendas.groupby(["COD_EMPRESA", "CD_CIDADE", "CD_ESTADO"])
    .agg(receita=("RECEITA", "sum"), qtd_vendida=("QTD_VENDA_ESTOQUE", "sum"))
    .reset_index()
    .sort_values("receita", ascending=False)
)
por_loja.to_csv(f"{TAB}/vendas_por_loja.csv", index=False)

por_estado = (
    vendas.groupby("CD_ESTADO")
    .agg(receita=("RECEITA", "sum"), qtd_vendida=("QTD_VENDA_ESTOQUE", "sum"), qtd_lojas=("COD_EMPRESA", "nunique"))
    .reset_index()
    .sort_values("receita", ascending=False)
)
por_estado.to_csv(f"{TAB}/vendas_por_estado.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 5))
d = por_loja.sort_values("receita")
labels = [f"{r.CD_CIDADE} (Loja {r.COD_EMPRESA})" for r in d.itertuples()]
ax.barh(labels, d["receita"], color="#ea580c")
ax.set_title("Receita por loja - 24 meses", fontsize=13, fontweight="bold")
ax.set_xlabel("Receita (R$)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhoes))
plt.tight_layout()
plt.savefig(f"{FIG}/receita_por_loja.png")
plt.close()

# ---------------------------------------------------------------------------
# 4. Sazonalidade mensal
# ---------------------------------------------------------------------------
print("[VENDAS] Sazonalidade mensal...")
mensal = (
    vendas.groupby("ANO_MES")
    .agg(receita=("RECEITA", "sum"), qtd_vendida=("QTD_VENDA_ESTOQUE", "sum"))
    .reset_index()
    .sort_values("ANO_MES")
)
mensal.to_csv(f"{TAB}/vendas_mensais.csv", index=False)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(mensal["ANO_MES"], mensal["receita"], marker="o", color="#7c3aed", linewidth=2)
ax.set_title("Evolucao mensal da receita (jan/2024 - dez/2025)", fontsize=13, fontweight="bold")
ax.set_ylabel("Receita (R$)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhoes))
plt.xticks(rotation=60, ha="right")
plt.tight_layout()
plt.savefig(f"{FIG}/sazonalidade_mensal.png")
plt.close()

# Sazonalidade por categoria (heatmap simplificado - top 10 categorias)
top10_cat = por_categoria.head(10)["NIVEL_1"].tolist()
vendas["MES"] = vendas["DATA_VENDA"].dt.month
sazon_cat = (
    vendas[vendas["NIVEL_1"].isin(top10_cat)]
    .groupby(["NIVEL_1", "MES"])["RECEITA"]
    .sum()
    .reset_index()
    .pivot(index="NIVEL_1", columns="MES", values="RECEITA")
    .reindex(top10_cat)
)
sazon_cat.to_csv(f"{TAB}/sazonalidade_por_categoria_mes.csv")

fig, ax = plt.subplots(figsize=(10, 6))
sazon_norm = sazon_cat.div(sazon_cat.max(axis=1), axis=0)  # normaliza 0-1 por linha p/ ver padrao
im = ax.imshow(sazon_norm.values, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(12))
ax.set_xticklabels(["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"])
ax.set_yticks(range(len(sazon_cat.index)))
ax.set_yticklabels([c[:30] for c in sazon_cat.index])
ax.set_title("Sazonalidade relativa por categoria (intensidade de vendas por mes, somando 2024+2025)", fontsize=11, fontweight="bold")
plt.colorbar(im, ax=ax, label="Intensidade relativa (0-1)")
plt.tight_layout()
plt.savefig(f"{FIG}/heatmap_sazonalidade_categoria.png")
plt.close()

print("[VENDAS] Top 5 categorias por receita:")
print(por_categoria.head(5).to_string(index=False))
print("[VENDAS] Concluido.")
