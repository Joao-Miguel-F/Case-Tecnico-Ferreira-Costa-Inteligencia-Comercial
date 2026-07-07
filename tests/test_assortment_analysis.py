# -*- coding: utf-8 -*-
"""Tests for Spec 05 assortment analysis."""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis import assortment_analysis as assort  # noqa: E402


REQUIRED_ASSORTMENT_COLUMNS = {
    "ANO_MES",
    "skus_observados",
    "linhas_venda_diarias",
    "mes_referencia_mix",
    "linhas_referencia_mix",
    "skus_esperados_media",
    "skus_esperados_p05",
    "skus_esperados_p95",
    "status_sortimento_controlado",
    "interpretacao",
}


def vendas_fixture():
    return pd.DataFrame(
        {
            "DATA_VENDA": pd.to_datetime(
                [
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                    "2025-01-02",
                    "2025-01-03",
                    "2025-01-04",
                    "2025-02-02",
                ]
            ),
            "COD_EMPRESA": [1] * 8,
            "CODIGO": [10, 10, 20, 30, 10, 10, 20, 20],
            "QUANTIDADE_VENDIDA": [1.0] * 8,
            "PRECO_UNIT_MEDIO": [10.0] * 8,
        }
    )


def test_sortimento_observado_por_mes():
    observed = assort.observed_monthly_assortment(vendas_fixture())
    jan_2024 = observed[observed["ANO_MES"].eq("2024-01")].iloc[0]

    assert jan_2024["skus_observados"] == 3
    assert jan_2024["linhas_venda_diarias"] == 4
    assert jan_2024["receita"] == 40.0


def test_sortimento_controlado_por_volume_usa_mix_do_ano_anterior():
    result = assort.build_assortment_controlled_by_volume(
        vendas_fixture(),
        iterations=30,
        random_seed=7,
    )
    jan_2024 = result[result["ANO_MES"].eq("2024-01")].iloc[0]
    jan_2025 = result[result["ANO_MES"].eq("2025-01")].iloc[0]

    assert REQUIRED_ASSORTMENT_COLUMNS.issubset(result.columns)
    assert jan_2024["status_sortimento_controlado"] == "DADO AUSENTE"
    assert jan_2025["mes_referencia_mix"] == "2024-01"
    assert jan_2025["linhas_referencia_mix"] == 4
    assert pd.notna(jan_2025["skus_esperados_media"])
    assert jan_2025["status_sortimento_controlado"] in assort.ASSORTMENT_STATUS


def test_queda_de_skus_nao_gera_rotulo_de_ruptura_ou_desabastecimento():
    result = assort.build_assortment_controlled_by_volume(
        vendas_fixture(),
        iterations=20,
        random_seed=11,
    )
    text = result.to_csv(index=False).lower()

    assert "ruptura" not in text
    assert "desabastecimento" not in text
    assert "prova disponibilidade fisica" in text


def test_output_gerado_em_diretorio_temporario(tmp_path):
    processed = tmp_path / "processed"
    outputs = tmp_path / "outputs"
    processed.mkdir()
    vendas_fixture().to_parquet(processed / "fato_vendas.parquet", index=False)

    result = assort.generate_assortment_outputs(
        processed,
        outputs,
        iterations=20,
        random_seed=1,
    )

    output_path = outputs / "sortimento_controlado_por_volume.csv"
    assert output_path.exists()
    assert not result["sortimento_controlado_por_volume"].empty
    assert REQUIRED_ASSORTMENT_COLUMNS.issubset(pd.read_csv(output_path).columns)

