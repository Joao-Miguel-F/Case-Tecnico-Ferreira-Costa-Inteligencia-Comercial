# -*- coding: utf-8 -*-
"""
07_recomendacoes.py
Etapa 7 - Recomendacoes

Consolida as analises anteriores em 4 listas acionaveis:
1. Candidatos a promocao (estoque parado + giro baixo, mas com relevancia)
2. Candidatos a descontinuacao (vendas muito baixas/nulas e estoque parado)
3. Sugestoes de repricing (alta dispersao de preco entre lojas OU
   elasticidade negativa forte sugerindo espaco para ajuste)
4. Plano de compras sugerido (ja gerado na etapa 6, aqui so resumimos)
"""
import pandas as pd
import numpy as np

TAB = "../outputs/tables"
PROC = "../data/processed"

print("[RECS] Carregando resultados das etapas anteriores...")
rank_produto = pd.read_csv(f"{TAB}/ranking_produtos_completo.csv")
parado = pd.read_csv(f"{TAB}/produtos_estoque_parado.csv")
risco_ruptura = pd.read_csv(f"{TAB}/produtos_risco_ruptura.csv")
dispersao = pd.read_csv(f"{TAB}/dispersao_preco_entre_lojas.csv")
elastico = pd.read_csv(f"{TAB}/produtos_elasticidade_negativa_forte.csv")
sem_venda = pd.read_csv(f"{TAB}/produtos_sem_nenhuma_venda.csv")
proj_2026 = pd.read_csv(f"{TAB}/projecao_compras_2026.csv")

# ---------------------------------------------------------------------------
# 1. Candidatos a PROMOCAO
#    Estoque parado (baixo giro) mas produto ainda relevante (teve alguma
#    venda, esta em categoria com boa demanda geral) -> "dar um empurrao"
# ---------------------------------------------------------------------------
print("[RECS] Candidatos a promocao...")
parado_agg = (
    parado.groupby(["CODIGO", "DESCRICAO", "NIVEL_1"])
    .agg(estoque_parado_total=("ESTOQUE_INICIAL", "sum"), lojas_com_estoque_parado=("COD_EMPRESA", "nunique"))
    .reset_index()
)
promocao = parado_agg.merge(rank_produto[["CODIGO", "receita", "qtd_vendida"]], on="CODIGO", how="left")
promocao["receita"] = promocao["receita"].fillna(0)
promocao = promocao[promocao["receita"] > 0]  # teve alguma venda, nao e caso de descontinuacao
promocao = promocao.sort_values("estoque_parado_total", ascending=False)
promocao.to_csv(f"{TAB}/rec_candidatos_promocao.csv", index=False)
print(f"[RECS] {len(promocao)} produtos candidatos a promocao (estoque parado + alguma venda)")

# ---------------------------------------------------------------------------
# 2. Candidatos a DESCONTINUACAO
#    Zero venda no periodo OU (estoque parado extenso e receita irrisoria)
# ---------------------------------------------------------------------------
print("[RECS] Candidatos a descontinuacao...")
zero_venda_ids = set(sem_venda["CODIGO"])
baixissima_receita = rank_produto[rank_produto["receita"] > 0].nsmallest(int(len(rank_produto) * 0.1), "receita")
descontinuar_baixa_receita = baixissima_receita.merge(
    parado_agg[["CODIGO", "estoque_parado_total"]], on="CODIGO", how="inner"
)
descontinuar = pd.concat(
    [
        sem_venda.assign(motivo="Zero vendas em 24 meses")[["CODIGO", "DESCRICAO", "NIVEL_1", "motivo"]],
        descontinuar_baixa_receita.assign(motivo="Receita irrisoria + estoque parado")[
            ["CODIGO", "DESCRICAO", "NIVEL_1", "motivo"]
        ],
    ],
    ignore_index=True,
).drop_duplicates(subset=["CODIGO"])
descontinuar = descontinuar.merge(rank_produto[["CODIGO", "receita", "qtd_vendida"]], on="CODIGO", how="left")
descontinuar.to_csv(f"{TAB}/rec_candidatos_descontinuacao.csv", index=False)
print(f"[RECS] {len(descontinuar)} produtos candidatos a descontinuacao")

# ---------------------------------------------------------------------------
# 3. Sugestoes de REPRICING
#    a) alta dispersao de preco entre lojas -> padronizar
#    b) elasticidade negativa forte -> avaliar reducao de preco para ganhar volume
# ---------------------------------------------------------------------------
print("[RECS] Sugestoes de repricing...")
repricing_padronizacao = dispersao.sort_values("amplitude_pct", ascending=False).head(50).copy()
repricing_padronizacao["tipo_recomendacao"] = "Padronizar preco entre lojas (alta dispersao)"
repricing_padronizacao.to_csv(f"{TAB}/rec_repricing_padronizacao.csv", index=False)

repricing_elasticidade = elastico.copy()
repricing_elasticidade["tipo_recomendacao"] = "Avaliar reducao de preco (demanda sensivel a preco)"
repricing_elasticidade.to_csv(f"{TAB}/rec_repricing_elasticidade.csv", index=False)
print(f"[RECS] {len(repricing_padronizacao)} produtos p/ padronizacao de preco, {len(repricing_elasticidade)} p/ avaliacao de reducao de preco")

# ---------------------------------------------------------------------------
# 4. Resumo executivo em numeros
# ---------------------------------------------------------------------------
print("[RECS] Montando resumo executivo...")
resumo = {
    "total_produtos_cadastrados": int(rank_produto.shape[0] + len(sem_venda)),
    "produtos_sem_nenhuma_venda": int(len(sem_venda)),
    "combinacoes_produto_loja_estoque_parado": int(parado.shape[0]),
    "combinacoes_produto_loja_risco_ruptura": int(risco_ruptura.shape[0]),
    "produtos_candidatos_promocao": int(len(promocao)),
    "produtos_candidatos_descontinuacao": int(len(descontinuar)),
    "produtos_candidatos_repricing_padronizacao": int(len(repricing_padronizacao)),
    "produtos_candidatos_repricing_elasticidade": int(len(repricing_elasticidade)),
    "demanda_total_projetada_2026": float(proj_2026["demanda_projetada_2026"].sum()),
    "demanda_media_anual_historica": float(proj_2026["venda_media_anual_historica"].sum()),
}
resumo_df = pd.DataFrame([resumo]).T.reset_index()
resumo_df.columns = ["indicador", "valor"]
resumo_df.to_csv(f"{TAB}/resumo_executivo.csv", index=False)
print(resumo_df.to_string(index=False))
print("[RECS] Concluido.")
