# -*- coding: utf-8 -*-
"""
04_analise_estoque.py
Etapa 4 - Analise de Estoque e Cobertura

IMPORTANTE - LIMITACAO DE DADOS IDENTIFICADA:
A soma de (estoque_inicial + compras) e MUITO menor que o total vendido no
periodo (vendas totais ~= 4,64M unidades vs. estoque_inicial + compras
~= 1,74M unidades). Isso indica que a base fato_compras nao contem o
universo completo de reposicoes de estoque no periodo (apenas 1.393
registros de compra para 2.731 produtos x 11 lojas x 24 meses). Por isso,
os indicadores de "estoque projetado" (saldo acumulado) devem ser lidos
como indicativos direcionais, e a analise de cobertura aqui prioriza a
venda media diaria observada e o estoque inicial declarado, que sao os
dados mais confiaveis disponiveis, deixando claro essa limitacao no
relatorio final.

- Dias de cobertura de estoque por produto/loja (baseado em estoque inicial
  e venda media diaria - abordagem robusta a base de compras incompleta)
- Produtos com estoque parado (alta cobertura, baixa venda)
- Produtos com risco de ruptura (baixa cobertura, alta venda)
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROC = "../data/processed"
FIG = "../outputs/figures"
TAB = "../outputs/tables"

print("[ESTOQUE-COBERTURA] Carregando bases...")
vendas = pd.read_parquet(f"{PROC}/fato_vendas.parquet")
estoque_ini = pd.read_parquet(f"{PROC}/fato_estoque_inicial.parquet")
dim_produto = pd.read_parquet(f"{PROC}/dim_produto.parquet")
dim_lojas = pd.read_parquet(f"{PROC}/dim_lojas.parquet")

n_dias_periodo = (vendas["DATA_VENDA"].max() - vendas["DATA_VENDA"].min()).days + 1
print(f"[ESTOQUE-COBERTURA] Periodo de {n_dias_periodo} dias")

# Venda media diaria por produto/loja (unidade de estoque)
venda_media = (
    vendas.groupby(["COD_EMPRESA", "CODIGO"])["QTD_VENDA_ESTOQUE"]
    .sum()
    .reset_index()
    .rename(columns={"QTD_VENDA_ESTOQUE": "QTD_VENDIDA_TOTAL"})
)
venda_media["VENDA_MEDIA_DIARIA"] = venda_media["QTD_VENDIDA_TOTAL"] / n_dias_periodo

cobertura = estoque_ini.merge(venda_media, on=["COD_EMPRESA", "CODIGO"], how="left")
cobertura["QTD_VENDIDA_TOTAL"] = cobertura["QTD_VENDIDA_TOTAL"].fillna(0)
cobertura["VENDA_MEDIA_DIARIA"] = cobertura["VENDA_MEDIA_DIARIA"].fillna(0)

cobertura["DIAS_COBERTURA_ESTOQUE_INICIAL"] = np.where(
    cobertura["VENDA_MEDIA_DIARIA"] > 0,
    cobertura["ESTOQUE_INICIAL"] / cobertura["VENDA_MEDIA_DIARIA"],
    np.inf,
)

cobertura = cobertura.merge(dim_produto[["CODIGO", "DESCRICAO", "NIVEL_1"]], on="CODIGO", how="left")
cobertura = cobertura.merge(dim_lojas, on="COD_EMPRESA", how="left")

# ---------------------------------------------------------------------------
# Produtos com estoque parado: estoque inicial alto, giro nenhum ou muito baixo
# ---------------------------------------------------------------------------
print("[ESTOQUE-COBERTURA] Produtos com estoque parado...")
parado = cobertura[
    (cobertura["ESTOQUE_INICIAL"] > 0)
    & (cobertura["VENDA_MEDIA_DIARIA"] <= cobertura["ESTOQUE_INICIAL"] * 0.005)  # vende <0.5%/dia do estoque
].copy()
parado = parado.sort_values("ESTOQUE_INICIAL", ascending=False)
parado.to_csv(f"{TAB}/produtos_estoque_parado.csv", index=False)
print(f"[ESTOQUE-COBERTURA] {len(parado)} combinacoes produto/loja com estoque parado (baixissimo giro)")

# ---------------------------------------------------------------------------
# Produtos com risco de ruptura: baixa cobertura (< 15 dias) e alta venda
# ---------------------------------------------------------------------------
print("[ESTOQUE-COBERTURA] Produtos com risco de ruptura...")
mediana_venda = cobertura.loc[cobertura["VENDA_MEDIA_DIARIA"] > 0, "VENDA_MEDIA_DIARIA"].median()
risco_ruptura = cobertura[
    (cobertura["DIAS_COBERTURA_ESTOQUE_INICIAL"] < 15)
    & (cobertura["VENDA_MEDIA_DIARIA"] > mediana_venda)
].copy()
risco_ruptura = risco_ruptura.sort_values("DIAS_COBERTURA_ESTOQUE_INICIAL")
risco_ruptura.to_csv(f"{TAB}/produtos_risco_ruptura.csv", index=False)
print(f"[ESTOQUE-COBERTURA] {len(risco_ruptura)} combinacoes produto/loja com risco de ruptura (cobertura<15 dias e venda acima da mediana)")

cobertura.to_parquet(f"{PROC}/cobertura_estoque.parquet", index=False)
cobertura_finite = cobertura.replace([np.inf], np.nan)
cobertura_finite.to_csv(f"{TAB}/cobertura_estoque_completa.csv", index=False)

# ---------------------------------------------------------------------------
# Grafico: matriz giro x cobertura (scatter) por produto (agregado loja)
# ---------------------------------------------------------------------------
print("[ESTOQUE-COBERTURA] Grafico matriz de giro...")
agg_prod = (
    cobertura.groupby(["CODIGO", "DESCRICAO"])
    .agg(estoque_inicial=("ESTOQUE_INICIAL", "sum"), venda_media_diaria=("VENDA_MEDIA_DIARIA", "sum"))
    .reset_index()
)
agg_prod["dias_cobertura"] = np.where(
    agg_prod["venda_media_diaria"] > 0, agg_prod["estoque_inicial"] / agg_prod["venda_media_diaria"], np.nan
)
plot_df = agg_prod[(agg_prod["venda_media_diaria"] > 0) & (agg_prod["dias_cobertura"] < 400)]

fig, ax = plt.subplots(figsize=(9, 6))
ax.scatter(plot_df["venda_media_diaria"], plot_df["dias_cobertura"], alpha=0.35, s=18, color="#0891b2")
ax.axhline(15, color="red", linestyle="--", linewidth=1, label="15 dias de cobertura")
ax.axhline(180, color="orange", linestyle="--", linewidth=1, label="180 dias de cobertura")
ax.set_xscale("log")
ax.set_xlabel("Venda media diaria (unid. estoque, escala log)")
ax.set_ylabel("Dias de cobertura (estoque inicial / venda media diaria)")
ax.set_title("Matriz Giro x Cobertura de Estoque (por produto, somando lojas)", fontsize=12, fontweight="bold")
ax.legend()
plt.tight_layout()
plt.savefig(f"{FIG}/matriz_giro_cobertura.png")
plt.close()

print("[ESTOQUE-COBERTURA] Concluido.")
