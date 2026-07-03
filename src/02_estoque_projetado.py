# -*- coding: utf-8 -*-
"""
02_estoque_projetado.py
Etapa 2 - Construcao do Estoque Projetado

Para cada produto x loja: estoque_final = estoque_inicial + compras - vendas
Calculado de forma acumulada ao longo do tempo (24 meses), tudo na unidade
de estoque (UNIDADE_ESTOQUE), para permitir comparacao direta.

Saidas:
- data/processed/estoque_diario.parquet -> saldo projetado por produto/loja/dia
  (apenas nos dias em que houve movimentacao, para nao gerar 1 linha por dia
  para cada produto/loja - calculamos o saldo acumulado e o ultimo valor vale
  ate a proxima movimentacao)
- outputs/tables/rupturas_estoque.csv -> ocorrencias de estoque negativo
- outputs/tables/produtos_sem_movimentacao.csv -> produto/loja com estoque
  inicial > 0 e nenhuma venda no periodo
"""
import pandas as pd
import numpy as np

PROC = "../data/processed"

print("[ESTOQUE] Carregando bases...")
estoque_ini = pd.read_parquet(f"{PROC}/fato_estoque_inicial.parquet")
compras = pd.read_parquet(f"{PROC}/fato_compras.parquet")
vendas = pd.read_parquet(f"{PROC}/fato_vendas.parquet")

# --- Agrega movimentacoes diarias por produto x loja x dia ---------------
print("[ESTOQUE] Agregando compras diarias...")
compras_diarias = (
    compras.groupby(["COD_EMPRESA", "CODIGO", "DATA_ENTRADA"])["QUANTIDADE_COMPRA"]
    .sum()
    .reset_index()
    .rename(columns={"DATA_ENTRADA": "DATA", "QUANTIDADE_COMPRA": "QTD_COMPRA"})
)

print("[ESTOQUE] Agregando vendas diarias (em unidade de estoque)...")
vendas_diarias = (
    vendas.groupby(["COD_EMPRESA", "CODIGO", "DATA_VENDA"])["QTD_VENDA_ESTOQUE"]
    .sum()
    .reset_index()
    .rename(columns={"DATA_VENDA": "DATA", "QTD_VENDA_ESTOQUE": "QTD_VENDA"})
)

print("[ESTOQUE] Unindo movimentacoes...")
mov = pd.merge(
    compras_diarias, vendas_diarias, on=["COD_EMPRESA", "CODIGO", "DATA"], how="outer"
)
mov["QTD_COMPRA"] = mov["QTD_COMPRA"].fillna(0)
mov["QTD_VENDA"] = mov["QTD_VENDA"].fillna(0)
mov["VARIACAO"] = mov["QTD_COMPRA"] - mov["QTD_VENDA"]

# Junta estoque inicial (chave produto/loja) como "movimentacao" na data minima
data_inicio = mov["DATA"].min()
print(f"[ESTOQUE] Data de inicio do periodo: {data_inicio}")

estoque_ini_mov = estoque_ini.copy()
estoque_ini_mov["DATA"] = data_inicio - pd.Timedelta(days=1)
estoque_ini_mov["QTD_COMPRA"] = 0
estoque_ini_mov["QTD_VENDA"] = 0
estoque_ini_mov["VARIACAO"] = estoque_ini_mov["ESTOQUE_INICIAL"]
estoque_ini_mov = estoque_ini_mov[["COD_EMPRESA", "CODIGO", "DATA", "QTD_COMPRA", "QTD_VENDA", "VARIACAO"]]

mov_full = pd.concat([estoque_ini_mov, mov], ignore_index=True)
mov_full = mov_full.sort_values(["COD_EMPRESA", "CODIGO", "DATA"])

print("[ESTOQUE] Calculando saldo acumulado (pode demorar)...")
mov_full["SALDO_ESTOQUE"] = mov_full.groupby(["COD_EMPRESA", "CODIGO"])["VARIACAO"].cumsum()

mov_full.to_parquet(f"{PROC}/estoque_diario.parquet", index=False)
print(f"[ESTOQUE] estoque_diario salvo: {mov_full.shape[0]} linhas")

# --- Rupturas de estoque (saldo negativo) ---------------------------------
print("[ESTOQUE] Identificando rupturas (estoque negativo)...")
rupturas = mov_full[mov_full["SALDO_ESTOQUE"] < 0].copy()
resumo_rupturas = (
    rupturas.groupby(["COD_EMPRESA", "CODIGO"])
    .agg(
        qtd_dias_com_ruptura=("DATA", "nunique"),
        pior_saldo=("SALDO_ESTOQUE", "min"),
        primeira_ruptura=("DATA", "min"),
        ultima_ruptura=("DATA", "max"),
    )
    .reset_index()
    .sort_values("qtd_dias_com_ruptura", ascending=False)
)
resumo_rupturas.to_csv("../outputs/tables/rupturas_estoque.csv", index=False)
print(f"[ESTOQUE] {resumo_rupturas.shape[0]} combinacoes produto/loja tiveram estoque negativo em algum momento")
print(f"[ESTOQUE] Isso representa {rupturas.shape[0]} eventos de movimentacao com saldo negativo")

# --- Produtos com estoque parado (sem nenhuma venda no periodo) ----------
print("[ESTOQUE] Identificando produtos sem movimentacao de venda...")
chaves_com_venda = set(zip(vendas["COD_EMPRESA"], vendas["CODIGO"]))
estoque_ini["TEVE_VENDA"] = estoque_ini.apply(
    lambda r: (r["COD_EMPRESA"], r["CODIGO"]) in chaves_com_venda, axis=1
)
sem_venda = estoque_ini[(~estoque_ini["TEVE_VENDA"]) & (estoque_ini["ESTOQUE_INICIAL"] > 0)].copy()
sem_venda = sem_venda.sort_values("ESTOQUE_INICIAL", ascending=False)
sem_venda.to_csv("../outputs/tables/produtos_sem_movimentacao.csv", index=False)
print(f"[ESTOQUE] {sem_venda.shape[0]} combinacoes produto/loja tem estoque inicial > 0 e nenhuma venda em 24 meses")

# --- Saldo final por produto/loja (ultimo valor no periodo) --------------
saldo_final = mov_full.sort_values("DATA").groupby(["COD_EMPRESA", "CODIGO"]).last().reset_index()
saldo_final = saldo_final[["COD_EMPRESA", "CODIGO", "DATA", "SALDO_ESTOQUE"]].rename(
    columns={"DATA": "DATA_ULTIMO_EVENTO", "SALDO_ESTOQUE": "ESTOQUE_FINAL_PROJETADO"}
)
saldo_final.to_parquet(f"{PROC}/estoque_final_projetado.parquet", index=False)
print("[ESTOQUE] Concluido.")
