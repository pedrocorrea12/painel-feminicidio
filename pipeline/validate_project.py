"""Valida estrutura, Gold e arquivos essenciais do projeto."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    obrigatorios = [
        ROOT / "data" / "silver" / "populacao_feminina_municipio.parquet",
        ROOT / "data" / "silver" / "indicadores_territorio_ano.parquet",
        ROOT / "data" / "gold" / "painel.json",
        ROOT / "dashboard" / "dist" / "data" / "painel.json",
        ROOT / "dashboard" / "dist" / "index.html",
        ROOT / "dashboard" / "dist" / "styles.css",
        ROOT / "dashboard" / "dist" / "app.js",
    ]
    ausentes = [str(p.relative_to(ROOT)) for p in obrigatorios if not p.exists()]
    if ausentes:
        raise FileNotFoundError(f"Arquivos ausentes: {ausentes}")
    gold = ROOT / "data" / "gold" / "painel.json"
    site_gold = ROOT / "dashboard" / "dist" / "data" / "painel.json"
    assert gold.read_bytes() == site_gold.read_bytes()
    dados = json.loads(gold.read_text(encoding="utf-8"))
    assert dados["controle"]["sc_2024"] == 9647
    assert dados["controle"]["sc_parceiro_2024"] == 2918
    assert dados["controle"]["florianopolis_parceiro_2024"] == 120
    assert dados["controle"]["pop_feminina_sc_2024"] == 4071859
    assert dados["controle"]["taxa_sc_2024"] == 236.92
    assert len(dados["municipios_sc_2024"]) == 295

    silver = pd.read_parquet(ROOT / "data" / "silver" / "indicadores_territorio_ano.parquet")
    assert len(silver) == 55980
    assert not silver.duplicated(["ano", "nivel_territorial", "id_territorio"]).any()
    assert silver.groupby("nivel_territorial").size().to_dict() == {
        "brasil": 10,
        "municipio": 55700,
        "uf": 270,
    }
    brasil24 = silver.loc[
        silver.ano.eq(2024)
        & silver.nivel_territorial.eq("brasil")
        & silver.id_territorio.eq("BR")
    ].iloc[0]
    assert brasil24.populacao_feminina == 108921464
    assert brasil24.notificacoes == 289220
    assert brasil24.taxa_notificacoes_100mil == 265.53
    print("Projeto validado: Silvers, Gold, taxas e dimensão municipal OK.")


if __name__ == "__main__":
    main()

