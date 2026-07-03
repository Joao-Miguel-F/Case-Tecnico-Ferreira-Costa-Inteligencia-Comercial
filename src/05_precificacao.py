# -*- coding: utf-8 -*-
"""
05_precificacao.py
Etapa 5 - Analise de Precificacao

- Compara precos entre lojas para o mesmo produto (dispersao de preco)
- Correlaciona variacao de preco (mensal, por loja) com variacao de volume
- Aponta produtos com maior dispersao de preco entre lojas (oportunidade de
  padronizacao) e produtos com correlacao preco x volume mais forte
  (oportunidade de repricing)
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROC = "../data/processed"
FIG = "../outputs/figures"
TAB = "../outputs/tables"

print("[PRECOS] Carregando bases...")
dim_precos = pd.read_parquet(f"{PROC}/dim_precos.parquet")
dim_produto = pd.read_parquet(f"{PROC}/dim_produto.parquet")
dim_lojas = pd.read_parquet(f"{PROC}/dim_lojas.parquet")
vendas = pd.read_parquet(f"{PROC}/fato_vendas.parquet")

# ---------------------------------------------------------------------------
# 1. Dispersao de preco entre lojas (embalagem padrao - 0)
# ---------------------------------------------------------------------------
print("[PRECOS] Dispersao de preco entre lojas (embalagem padrao)...")
disp = (
    dim_precos.groupby("CODIGO")["PRECO_EMBALAGEM_0"]
    .agg(["mean", "std", "min", "max", "count"])
    .reset_index()
    .rename(columns={"mean": "preco_medio", "std": "preco_desvio", "min": "preco_min", "max": "preco_max", "count": "qtd_lojas"})
)
disp = disp[disp["qtd_lojas"] >= 2]
disp["amplitude_pct"] = ((disp["preco_max"] - disp["preco_min"]) / disp["preco_medio"] * 100).round(2)
disp["cv_pct"] = (disp["preco_desvio"] / disp["preco_medio"] * 100).round(2)
disp = disp.merge(dim_produto[["CODIGO", "DESCRICAO", "NIVEL_1"]], on="CODIGO", how="left")

# junta receita para priorizar produtos relevantes
receita_produto = vendas.groupby("CODIGO")["RECEITA"].sum().reset_index().rename(columns={"RECEITA": "receita_total"})
disp = disp.merge(receita_produto, on="CODIGO", how="left")
disp["receita_total"] = disp["receita_total"].fillna(0)

disp_relevante = disp[disp["receita_total"] > disp["receita_total"].quantile(0.5)].sort_values(
    "amplitude_pct", ascending=False
)
disp_relevante.to_csv(f"{TAB}/dispersao_preco_entre_lojas.csv", index=False)
print(f"[PRECOS] Top 10 produtos (relevantes) com maior dispersao de preco entre lojas:")
print(disp_relevante.head(10)[["CODIGO", "DESCRICAO", "amplitude_pct", "receita_total"]].to_string(index=False))

fig, ax = plt.subplots(figsize=(9, 6))
d = disp_relevante.head(15).iloc[::-1]
ax.barh([desc[:35] for desc in d["DESCRICAO"]], d["amplitude_pct"], color="#dc2626")
ax.set_xlabel("Amplitude de preco entre lojas (%)")
ax.set_title("Top 15 produtos com maior dispersao de preco entre lojas\n(entre os 50% de maior receita)", fontsize=11, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{FIG}/dispersao_preco_lojas.png")
plt.close()

# ---------------------------------------------------------------------------
# 2. Correlacao preco x volume (elasticidade aproximada) por produto
# ---------------------------------------------------------------------------
print("[PRECOS] Calculando correlacao preco x volume por produto (mensal, por loja)...")
vendas["ANO_MES"] = vendas["DATA_VENDA"].dt.to_period("M").astype(str)
mensal_prod_loja = (
    vendas.groupby(["CODIGO", "COD_EMPRESA", "ANO_MES"])
    .agg(qtd=("QTD_VENDA_ESTOQUE", "sum"), receita=("RECEITA", "sum"))
    .reset_index()
)
mensal_prod_loja["preco_medio_mes"] = mensal_prod_loja["receita"] / mensal_prod_loja["qtd"].replace(0, np.nan)

def calc_corr(g):
    if g["preco_medio_mes"].nunique() < 3 or g["qtd"].sum() == 0:
        return pd.Series({"correlacao_preco_volume": np.nan, "n_obs": len(g)})
    c = g["preco_medio_mes"].corr(g["qtd"])
    return pd.Series({"correlacao_preco_volume": c, "n_obs": len(g)})

print("[PRECOS] Agregando (pode levar alguns instantes)...")
corr_por_produto = (
    mensal_prod_loja.groupby("CODIGO").apply(calc_corr).reset_index()
)
corr_por_produto = corr_por_produto[corr_por_produto["n_obs"] >= 8]
corr_por_produto = corr_por_produto.merge(dim_produto[["CODIGO", "DESCRICAO", "NIVEL_1"]], on="CODIGO", how="left")
corr_por_produto = corr_por_produto.merge(receita_produto, on="CODIGO", how="left")
corr_por_produto = corr_por_produto.dropna(subset=["correlacao_preco_volume"])
corr_por_produto = corr_por_produto.sort_values("correlacao_preco_volume")
corr_por_produto.to_csv(f"{TAB}/correlacao_preco_volume.csv", index=False)

# Produtos com correlacao negativa forte (comportamento elastico esperado) e receita relevante
elastico = corr_por_produto[
    (corr_por_produto["correlacao_preco_volume"] < -0.4)
    & (corr_por_produto["receita_total"] > corr_por_produto["receita_total"].quantile(0.5))
].sort_values("correlacao_preco_volume")
elastico.to_csv(f"{TAB}/produtos_elasticidade_negativa_forte.csv", index=False)
print(f"[PRECOS] {len(elastico)} produtos relevantes com correlacao preco-volume fortemente negativa (<-0.4)")

# Produtos com correlacao positiva (contra-intuitivo, indica outros fatores dominando, ou produto Giffen-like / sazonal)
contra_intuitivo = corr_por_produto[
    (corr_por_produto["correlacao_preco_volume"] > 0.4)
    & (corr_por_produto["receita_total"] > corr_por_produto["receita_total"].quantile(0.5))
].sort_values("correlacao_preco_volume", ascending=False)
contra_intuitivo.to_csv(f"{TAB}/produtos_correlacao_positiva_preco_volume.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(corr_por_produto["correlacao_preco_volume"], bins=40, color="#7c3aed", edgecolor="white")
ax.axvline(0, color="black", linewidth=0.8)
ax.set_title("Distribuicao da correlacao preco x volume por produto\n(base mensal por loja)", fontsize=11, fontweight="bold")
ax.set_xlabel("Correlacao (preco medio mensal vs quantidade vendida)")
ax.set_ylabel("Numero de produtos")
plt.tight_layout()
plt.savefig(f"{FIG}/distribuicao_correlacao_preco_volume.png")
plt.close()

print("[PRECOS] Concluido.")
