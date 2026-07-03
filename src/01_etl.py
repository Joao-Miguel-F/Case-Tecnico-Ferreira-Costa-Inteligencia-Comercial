# -*- coding: utf-8 -*-
"""
01_etl.py
Etapa 1 - Entendimento e Limpeza dos Dados

Le todas as bases brutas, trata encoding/separadores/decimais, valida
integridade referencial entre as bases e salva versoes limpas em Parquet
(mais rapido e compacto) na pasta data/processed.

Observacoes de qualidade de dados encontradas:
- dim_produto_1.csv esta em encoding Latin-1 (cp1252), nao UTF-8 (contem
  caracteres como NBSP 0xA0). As demais bases sao UTF-8.
- Bases com prefixo "dimensao_"/"dim_" e "fato_estoque_inicial" usam ';' como
  separador de campo e ',' como separador decimal (padrao BR/Excel).
- fato_compras_2.csv e fato_vendas_1.csv usam ',' como separador de campo e
  '.' como separador decimal (padrao "programatico"/US), e trazem uma coluna
  de indice sem nome (unnamed) que e descartada.
"""
import pandas as pd
import numpy as np
import os

RAW = "../data/raw"
OUT = "../data/processed"
os.makedirs(OUT, exist_ok=True)


def log(msg):
    print(f"[ETL] {msg}")


# ---------------------------------------------------------------------------
# 1. dim_produto
# ---------------------------------------------------------------------------
log("Lendo dim_produto (encoding latin-1, sep ';')...")
dim_produto = pd.read_csv(
    f"{RAW}/dim_produto_1.csv", sep=";", encoding="latin1", dtype=str
)
dim_produto.columns = [c.strip().upper() for c in dim_produto.columns]
for c in dim_produto.columns:
    dim_produto[c] = dim_produto[c].astype(str).str.strip().str.replace('"', "", regex=False)
dim_produto["CODIGO"] = pd.to_numeric(dim_produto["CODIGO"], errors="coerce").astype("Int64")
dim_produto["CONVERSAO_COMPRA_ARMAZENAGEM"] = (
    dim_produto["CONVERSAO_COMPRA_ARMAZENAGEM"].str.replace(",", ".", regex=False).astype(float)
)
dim_produto["CD_VOLTAGEM"] = pd.to_numeric(dim_produto["CD_VOLTAGEM"], errors="coerce").astype("Int64")
dim_produto = dim_produto.drop_duplicates(subset=["CODIGO"])
log(f"dim_produto: {dim_produto.shape[0]} produtos unicos")

# ---------------------------------------------------------------------------
# 2. dimensao_lojas
# ---------------------------------------------------------------------------
log("Lendo dimensao_lojas...")
dim_lojas = pd.read_csv(f"{RAW}/dimensao_lojas_2.csv", sep=";", encoding="utf-8", dtype=str)
dim_lojas.columns = [c.strip().upper() for c in dim_lojas.columns]
dim_lojas["COD_EMPRESA"] = pd.to_numeric(dim_lojas["COD_EMPRESA"], errors="coerce").astype("Int64")
dim_lojas["CD_CIDADE"] = dim_lojas["CD_CIDADE"].str.strip().str.title()
dim_lojas["CD_ESTADO"] = dim_lojas["CD_ESTADO"].str.strip()
log(f"dimensao_lojas: {dim_lojas.shape[0]} lojas")

# ---------------------------------------------------------------------------
# 3. dimensao_voltagem
# ---------------------------------------------------------------------------
log("Lendo dimensao_voltagem...")
dim_voltagem = pd.read_csv(f"{RAW}/dimensao_voltagem_2.csv", sep=";", encoding="utf-8", dtype=str)
dim_voltagem.columns = [c.strip().upper() for c in dim_voltagem.columns]
dim_voltagem = dim_voltagem.apply(lambda s: pd.to_numeric(s, errors="coerce").astype("Int64"))

# ---------------------------------------------------------------------------
# 4. Descr_unidades_medida
# ---------------------------------------------------------------------------
log("Lendo unidades de medida...")
dim_unidades = pd.read_csv(f"{RAW}/Descr_unidades_medida_2.csv", sep=";", encoding="utf-8", dtype=str)
dim_unidades.columns = [c.strip().upper() for c in dim_unidades.columns]
dim_unidades = dim_unidades.apply(lambda s: s.str.strip() if s.dtype == "object" else s)

# ---------------------------------------------------------------------------
# 5. dimensao_precos  (decimal com virgula)
# ---------------------------------------------------------------------------
log("Lendo dimensao_precos (decimal ',')...")
dim_precos = pd.read_csv(f"{RAW}/dimensao_precos_2.csv", sep=";", encoding="utf-8", dtype=str)
dim_precos.columns = [c.strip().upper() for c in dim_precos.columns]
dim_precos["CODIGO"] = pd.to_numeric(dim_precos["CODIGO"], errors="coerce").astype("Int64")
dim_precos["COD_EMPRESA"] = pd.to_numeric(dim_precos["COD_EMPRESA"], errors="coerce").astype("Int64")
for c in ["PRECO_EMBALAGEM_0", "PERC_DESCTO_ADICIONAL_EMBALAGEM_0", "PRECO_EMBALAGEM_1", "PRECO_EMBALAGEM_2"]:
    dim_precos[c] = pd.to_numeric(dim_precos[c].str.replace(",", ".", regex=False), errors="coerce")
log(f"dimensao_precos: {dim_precos.shape[0]} linhas (produto x loja)")

# ---------------------------------------------------------------------------
# 6. fato_estoque_inicial (decimal com virgula, mas sao inteiros)
# ---------------------------------------------------------------------------
log("Lendo fato_estoque_inicial...")
estoque_ini = pd.read_csv(f"{RAW}/fato_estoque_inicial_2.csv", sep=";", encoding="utf-8", dtype=str)
estoque_ini.columns = [c.strip().upper() for c in estoque_ini.columns]
estoque_ini["COD_EMPRESA"] = pd.to_numeric(estoque_ini["COD_EMPRESA"], errors="coerce").astype("Int64")
estoque_ini["CODIGO"] = pd.to_numeric(estoque_ini["CODIGO"], errors="coerce").astype("Int64")
estoque_ini["ESTOQUE_INICIAL"] = pd.to_numeric(
    estoque_ini["ESTOQUE_INICIAL"].str.replace(",", ".", regex=False), errors="coerce"
)
log(f"fato_estoque_inicial: {estoque_ini.shape[0]} linhas")

# ---------------------------------------------------------------------------
# 7. fato_compras (decimal com ponto, sep ',')
# ---------------------------------------------------------------------------
log("Lendo fato_compras...")
compras = pd.read_csv(f"{RAW}/fato_compras_2.csv", sep=",", encoding="utf-8")
compras = compras.drop(columns=[c for c in compras.columns if c.startswith("Unnamed")])
compras.columns = [c.strip().upper() for c in compras.columns]
compras["DATA_ENTRADA"] = pd.to_datetime(compras["DATA_ENTRADA"], errors="coerce")
compras["COD_EMPRESA"] = pd.to_numeric(compras["COD_EMPRESA"], errors="coerce").astype("Int64")
compras["CODIGO"] = pd.to_numeric(compras["CODIGO"], errors="coerce").astype("Int64")
log(f"fato_compras: {compras.shape[0]} linhas | periodo {compras['DATA_ENTRADA'].min()} a {compras['DATA_ENTRADA'].max()}")

# ---------------------------------------------------------------------------
# 8. fato_vendas (a maior base - 1M+ linhas, decimal com ponto, sep ',')
# ---------------------------------------------------------------------------
log("Lendo fato_vendas (pode demorar alguns segundos)...")
vendas = pd.read_csv(
    f"{RAW}/fato_vendas_1.csv",
    sep=",",
    encoding="utf-8",
    dtype={
        "COD_EMPRESA": "Int64",
        "CODIGO": "Int64",
        "DIGITO": "Int64",
        "EMBALAGEM": "Int64",
    },
)
vendas = vendas.drop(columns=[c for c in vendas.columns if c.startswith("Unnamed")])
vendas.columns = [c.strip().upper() for c in vendas.columns]
vendas["DATA_VENDA"] = pd.to_datetime(vendas["DATA_VENDA"], errors="coerce")
log(f"fato_vendas: {vendas.shape[0]} linhas | periodo {vendas['DATA_VENDA'].min()} a {vendas['DATA_VENDA'].max()}")

# ---------------------------------------------------------------------------
# 9. Checks de integridade referencial
# ---------------------------------------------------------------------------
log("Checando integridade referencial...")
prod_ids = set(dim_produto["CODIGO"].dropna())
loja_ids = set(dim_lojas["COD_EMPRESA"].dropna())

vendas_sem_produto = (~vendas["CODIGO"].isin(prod_ids)).sum()
vendas_sem_loja = (~vendas["COD_EMPRESA"].isin(loja_ids)).sum()
compras_sem_produto = (~compras["CODIGO"].isin(prod_ids)).sum()
compras_sem_loja = (~compras["COD_EMPRESA"].isin(loja_ids)).sum()
estoque_sem_produto = (~estoque_ini["CODIGO"].isin(prod_ids)).sum()
estoque_sem_loja = (~estoque_ini["COD_EMPRESA"].isin(loja_ids)).sum()

integridade = pd.DataFrame(
    [
        ["fato_vendas", "CODIGO nao encontrado em dim_produto", vendas_sem_produto, len(vendas)],
        ["fato_vendas", "COD_EMPRESA nao encontrado em dimensao_lojas", vendas_sem_loja, len(vendas)],
        ["fato_compras", "CODIGO nao encontrado em dim_produto", compras_sem_produto, len(compras)],
        ["fato_compras", "COD_EMPRESA nao encontrado em dimensao_lojas", compras_sem_loja, len(compras)],
        ["fato_estoque_inicial", "CODIGO nao encontrado em dim_produto", estoque_sem_produto, len(estoque_ini)],
        ["fato_estoque_inicial", "COD_EMPRESA nao encontrado em dimensao_lojas", estoque_sem_loja, len(estoque_ini)],
    ],
    columns=["base", "check", "linhas_com_problema", "total_linhas"],
)
integridade["pct"] = (integridade["linhas_com_problema"] / integridade["total_linhas"] * 100).round(3)
integridade.to_csv("../outputs/tables/checks_integridade.csv", index=False)
log("Resultado dos checks:")
print(integridade.to_string(index=False))

# Remove linhas de vendas/compras sem produto ou loja validos (ruido)
vendas_clean = vendas[vendas["CODIGO"].isin(prod_ids) & vendas["COD_EMPRESA"].isin(loja_ids)].copy()
compras_clean = compras[compras["CODIGO"].isin(prod_ids) & compras["COD_EMPRESA"].isin(loja_ids)].copy()
estoque_clean = estoque_ini[estoque_ini["CODIGO"].isin(prod_ids) & estoque_ini["COD_EMPRESA"].isin(loja_ids)].copy()

log(f"Vendas removidas por falta de integridade: {len(vendas) - len(vendas_clean)}")
log(f"Compras removidas por falta de integridade: {len(compras) - len(compras_clean)}")

# ---------------------------------------------------------------------------
# 10. Receita de vendas (quantidade x preco medio)
# ---------------------------------------------------------------------------
vendas_clean["RECEITA"] = vendas_clean["QUANTIDADE_VENDIDA"] * vendas_clean["PRECO_UNIT_MEDIO"]
# Quantidade convertida para unidade de estoque (para bater com estoque/compras)
vendas_clean["QTD_VENDA_ESTOQUE"] = (
    vendas_clean["QUANTIDADE_VENDIDA"] * vendas_clean["CONVERSAO_VENDA_PARA_ARMAZENAGEM"]
)

# ---------------------------------------------------------------------------
# 11. Salvar bases limpas em parquet
# ---------------------------------------------------------------------------
log("Salvando bases limpas em Parquet...")
dim_produto.to_parquet(f"{OUT}/dim_produto.parquet", index=False)
dim_lojas.to_parquet(f"{OUT}/dim_lojas.parquet", index=False)
dim_voltagem.to_parquet(f"{OUT}/dim_voltagem.parquet", index=False)
dim_unidades.to_parquet(f"{OUT}/dim_unidades.parquet", index=False)
dim_precos.to_parquet(f"{OUT}/dim_precos.parquet", index=False)
estoque_clean.to_parquet(f"{OUT}/fato_estoque_inicial.parquet", index=False)
compras_clean.to_parquet(f"{OUT}/fato_compras.parquet", index=False)
vendas_clean.to_parquet(f"{OUT}/fato_vendas.parquet", index=False)

log("ETL concluido com sucesso.")
