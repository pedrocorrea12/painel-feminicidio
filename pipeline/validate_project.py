"""Valida estrutura, Gold e arquivos essenciais do projeto."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    obrigatorios = [
        ROOT / "data" / "silver" / "populacao_feminina_municipio.parquet",
        ROOT / "data" / "silver" / "populacao_municipio_ano.parquet",
        ROOT / "data" / "silver" / "populacao_municipio_sexo_ano.parquet",
        ROOT / "data" / "silver" / "populacao_municipio_idade_ano.parquet",
        ROOT / "data" / "silver" / "indicadores_territorio_ano.parquet",
        ROOT / "data" / "silver" / "sim_mulheres_agressao.parquet",
        ROOT / "data" / "silver" / "sim_atlas_mortalidade.parquet",
        ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal_2025_preliminar.parquet",
        ROOT / "data" / "silver" / "sinan_preliminar_territorio_ano.parquet",
        ROOT / "data" / "silver" / "sinan_atlas_violencia.parquet",
        ROOT / "data" / "silver" / "sinesp_feminicidio.parquet",
        ROOT / "data" / "silver" / "sinesp_vde_ocorrencias.parquet",
        ROOT / "data" / "silver" / "rais_vinculos_raca_sexo.parquet",
        ROOT / "data" / "silver" / "rais_movimentacao_mensal.parquet",
        ROOT / "data" / "silver" / "rais_escolaridade_raca_sexo.parquet",
        ROOT / "data" / "gold" / "painel.json",
        ROOT / "data" / "gold" / "integrado" / "historico_integrado_2019_2024.csv",
        ROOT / "data" / "gold" / "integrado" / "monitoramento_atual_2025_2026.csv",
        ROOT / "data" / "gold" / "integrado" / "razao_sim_sinesp_uf_2019_2024.csv",
        ROOT / "data" / "gold" / "integrado" / "tentativa_feminicidio_2019_2026.csv",
        ROOT / "data" / "gold" / "integrado" / "taxa_municipal_feminicidio_sc_2019_2024.csv",
        ROOT / "data" / "gold" / "integrado" / "sinesp_serie_mensal_2019_2026.csv",
        ROOT / "data" / "gold" / "integrado" / "sinesp_sazonalidade_mes_2019_2025.csv",
        ROOT / "data" / "gold" / "integrado" / "homicidio_doloso_feminicidio_2019_2026.csv",
        ROOT / "data" / "gold" / "raca" / "sim_raca_uf_ano_2019_2024.csv",
        ROOT / "data" / "gold" / "raca" / "sim_raca_municipios_sc_2019_2024.csv",
        ROOT / "data" / "gold" / "raca" / "sinan_raca_uf_2024.csv",
        ROOT / "data" / "gold" / "raca" / "sinan_raca_municipios_sc_2019_2024.csv",
        ROOT / "data" / "gold" / "rais" / "emprego_formal_sexo_2019_2025.csv",
        ROOT / "data" / "gold" / "rais" / "emprego_formal_sexo_municipios_sc_2019_2025.csv",
        ROOT / "data" / "gold" / "rais" / "movimentacao_mensal_sexo_2019_2025.csv",
        ROOT / "data" / "gold" / "rais" / "insercao_formal_mulheres_negras_2024_2025.csv",
        ROOT / "data" / "gold" / "rais" / "razao_salarial_raca_2024_2025.csv",
        ROOT / "data" / "gold" / "atlas" / "catalogo_indicadores.csv",
        ROOT / "data" / "gold" / "atlas" / "matriz_disponibilidade_fontes.csv",
        ROOT / "data" / "gold" / "atlas" / "resumo_catalogo.json",
        ROOT / "data" / "gold" / "atlas" / "sim_mortalidade_territorio_ano.csv",
        ROOT / "data" / "gold" / "atlas" / "sim_mortalidade_idade_ano.csv",
        ROOT / "data" / "gold" / "atlas" / "sim_mortalidade_metodologia.json",
        ROOT / "data" / "gold" / "atlas" / "sinan_violencia_territorio_ano.csv",
        ROOT / "data" / "gold" / "atlas" / "sinan_violencia_idade_ano.csv",
        ROOT / "data" / "gold" / "atlas" / "sinan_violencia_metodologia.json",
        ROOT / "data" / "gold" / "atlas" / "sinesp_cobertura_evento_uf_ano.csv",
        ROOT / "data" / "gold" / "atlas" / "sinesp_cobertura_evento_resumo.csv",
        ROOT / "data" / "gold" / "atlas" / "sinesp_prioridade_territorio_ano.csv",
        ROOT / "data" / "gold" / "atlas" / "sinesp_prioridade_mensal.csv",
        ROOT / "data" / "gold" / "atlas" / "sinesp_prioridade_metodologia.json",
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
    assert dados["controle"]["sim_agressao_sc_2024"] == 90
    assert dados["sinan_2025_preliminar"]["brasil"][0]["situacao_dado"] == "preliminar"
    assert dados["sinesp_feminicidio"]["brasil"]
    assert len(dados["sim_raca"]["uf_ano"]) == 1008
    assert len(dados["sim_raca"]["municipios_sc"]) == 1770
    assert len(dados["sinan_raca"]["uf_2024"]) == 168
    assert len(dados["rais"]["sexo_ano"]) == 196
    assert len(dados["rais"]["sexo_municipios_sc"]) == 295
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
    assert brasil24.obitos_mulheres_agressao > 0
    sim = pd.read_parquet(ROOT / "data" / "silver" / "sim_mulheres_agressao.parquet")
    assert sorted(sim.ano.unique().tolist()) == list(range(2015, 2027))
    assert set(sim.loc[sim.ano.between(2015, 2024), "situacao_dado"].unique()) == {
        "definitivo"
    }
    assert set(sim.loc[sim.ano.eq(2025), "situacao_dado"].unique()) == {"preliminar"}
    assert set(sim.loc[sim.ano.eq(2026), "situacao_dado"].unique()) == {"previa"}
    sinesp = pd.read_parquet(ROOT / "data" / "silver" / "sinesp_feminicidio.parquet")
    assert sinesp.vitimas_feminicidio.sum() > 0
    assert sorted(sinesp.ano.unique().tolist()) == list(range(2019, 2027))
    meses_sinesp = sinesp.groupby("ano")["mes"].nunique().to_dict()
    assert all(meses_sinesp[ano] == 12 for ano in range(2019, 2026))
    assert meses_sinesp[2026] == 8

    integrado = ROOT / "data" / "gold" / "integrado"
    historico = pd.read_csv(integrado / "historico_integrado_2019_2024.csv")
    assert len(historico) == 1782
    assert not historico.duplicated(
        ["ano", "nivel_territorial", "id_territorio"]
    ).any()
    assert (
        (
            historico.sinan_notificacoes.div(historico.populacao_feminina).mul(100_000)
            - historico.sinan_taxa_notificacoes_100mil
        ).abs()
        <= 0.011
    ).all()

    razao = pd.read_csv(integrado / "razao_sim_sinesp_uf_2019_2024.csv")
    assert len(razao) == 168
    assert not razao.duplicated(
        ["ano", "nivel_territorial", "id_territorio"]
    ).any()
    assert (
        (
            razao.sinesp_feminicidio_total_vitimas
            .div(razao.sim_obitos_mulheres_agressao)
            .round(4)
            - razao.razao_feminicidios_total_sobre_sim
        ).abs()
        <= 0.0001
    ).all()

    tentativas = pd.read_csv(integrado / "tentativa_feminicidio_2019_2026.csv")
    assert len(tentativas) == 224
    assert int(
        tentativas.loc[
            tentativas.ano.eq(2025) & tentativas.id_territorio.eq("BR"),
            "tentativa_feminicidio_total_vitimas",
        ].iloc[0]
    ) == 4188

    municipios = pd.read_csv(
        integrado / "taxa_municipal_feminicidio_sc_2019_2024.csv"
    )
    assert len(municipios) == 295
    assert municipios.id_municipio.nunique() == 295
    assert municipios.anos_populacao.eq(6).all()
    assert int(municipios.feminicidios_total.sum()) == 335
    assert (
        (
            municipios.feminicidios_total
            .div(municipios.populacao_feminina_anos_pessoa)
            .mul(100_000)
            .round(2)
            - municipios.taxa_feminicidio_100mil_mulheres_ano
        ).abs()
        <= 0.01
    ).all()

    serie = pd.read_csv(integrado / "sinesp_serie_mensal_2019_2026.csv")
    assert len(serie) == 184
    assert not serie.duplicated(["ano", "mes", "id_territorio"]).any()
    sazonalidade = pd.read_csv(integrado / "sinesp_sazonalidade_mes_2019_2025.csv")
    assert len(sazonalidade) == 24
    homicidios = pd.read_csv(
        integrado / "homicidio_doloso_feminicidio_2019_2026.csv"
    )
    assert len(homicidios) == 224
    assert homicidios.soma_metodologicamente_permitida.all()
    assert (
        homicidios.homicidio_doloso_vitimas_femininas
        + homicidios.feminicidio_vitimas_femininas
        == homicidios.homicidio_doloso_mais_feminicidio_vitimas_femininas
    ).all()

    raca = ROOT / "data" / "gold" / "raca"
    sim_raca = pd.read_csv(raca / "sim_raca_uf_ano_2019_2024.csv")
    assert len(sim_raca) == 1008
    assert not sim_raca.duplicated(["ano", "sigla_uf", "raca"]).any()
    assert int(
        sim_raca.loc[
            sim_raca.sigla_uf.eq("BR") & sim_raca.raca.eq("Branca"),
            "registros_total",
        ].sum()
    ) == 22691
    sim_raca_municipios = pd.read_csv(
        raca / "sim_raca_municipios_sc_2019_2024.csv",
        dtype={"id_municipio": "string"},
    )
    assert len(sim_raca_municipios) == 1770
    assert sim_raca_municipios.id_municipio.nunique() == 295
    assert int(
        sim_raca_municipios.loc[
            sim_raca_municipios.raca.eq("Branca"), "registros_total"
        ].sum()
    ) == 580
    sinan_raca = pd.read_csv(raca / "sinan_raca_uf_2024.csv")
    assert len(sinan_raca) == 168
    assert int(
        sinan_raca.loc[
            sinan_raca.sigla_uf.eq("BR") & sinan_raca.raca.eq("Negra"),
            "registros_total",
        ].iloc[0]
    ) == 289220

    rais_silver = pd.read_parquet(
        ROOT / "data" / "silver" / "rais_vinculos_raca_sexo.parquet"
    )
    assert set(rais_silver.cd_sexo.unique()) == {1, 2}
    assert rais_silver.loc[rais_silver.ano.lt(2024), "raca_usavel"].eq(False).all()
    assert rais_silver.loc[rais_silver.ano.ge(2024), "raca_usavel"].eq(True).all()
    rais_uf = rais_silver.loc[rais_silver.nivel_territorial.eq("uf")]
    rais_br = rais_silver.loc[rais_silver.nivel_territorial.eq("brasil")]
    assert rais_uf.groupby("ano").qt_vinculos.sum().eq(
        rais_br.groupby("ano").qt_vinculos.sum()
    ).all()
    rais_sc = rais_uf.loc[rais_uf.sigla_uf.eq("SC")].groupby("ano").qt_vinculos.sum()
    assert int(rais_sc.loc[2019]) == 2319210
    assert int(rais_sc.loc[2025]) == 2949150
    rais_gold = ROOT / "data" / "gold" / "rais"
    emprego = pd.read_csv(rais_gold / "emprego_formal_sexo_2019_2025.csv")
    assert len(emprego) == 196
    assert not emprego.duplicated(["ano", "id_territorio"]).any()
    movimento_rais = pd.read_csv(rais_gold / "movimentacao_mensal_sexo_2019_2025.csv")
    assert (
        movimento_rais.admissoes - movimento_rais.desligamentos
        == movimento_rais.saldo
    ).all()
    insercao = pd.read_csv(
        rais_gold / "insercao_formal_mulheres_negras_2024_2025.csv"
    )
    assert len(insercao) == 56
    assert insercao.ano.isin([2024, 2025]).all()

    atlas = ROOT / "data" / "gold" / "atlas"
    catalogo = pd.read_csv(atlas / "catalogo_indicadores.csv")
    assert len(catalogo) == 48
    assert catalogo.id_indicador.nunique() == 48
    assert catalogo.fonte.nunique() == 6
    assert int(catalogo.fonte.eq("Sinesp VDE").sum()) == 31
    assert int(catalogo.prioridade.eq(1).sum()) == 21
    assert catalogo.loc[catalogo.indicador.eq("População total, por sexo e por idade"), "prontidao"].eq(
        "pronto"
    ).all()
    matriz_atlas = pd.read_csv(atlas / "matriz_disponibilidade_fontes.csv")
    assert len(matriz_atlas) == 6
    assert set(matriz_atlas.fonte) == {"IBGE", "Sinesp VDE", "Censo 2022", "SIM", "SINAN", "RAIS"}

    sim_atlas = pd.read_parquet(ROOT / "data" / "silver" / "sim_atlas_mortalidade.parquet")
    assert len(sim_atlas) == 1101514
    assert sorted(sim_atlas.ano.unique().tolist()) == list(range(2015, 2027))
    assert set(sim_atlas.grupo_causa.unique()) == {"agressao", "suicidio", "acidente_transporte"}
    controle_sim_atlas = (
        sim_atlas.loc[sim_atlas.grupo_causa.eq("agressao") & sim_atlas.sexo.eq("feminino")]
        .groupby("ano")
        .size()
        .to_dict()
    )
    assert controle_sim_atlas == sim.groupby("ano").size().to_dict()
    sim_atlas_territorio = pd.read_csv(atlas / "sim_mortalidade_territorio_ano.csv")
    assert len(sim_atlas_territorio) == 46512
    assert not sim_atlas_territorio.duplicated(
        ["ano", "nivel_territorial", "id_territorio", "grupo_causa", "sexo"]
    ).any()
    assert sim_atlas_territorio.loc[
        sim_atlas_territorio.ano.le(2024)
        & sim_atlas_territorio.sexo.isin(["total", "feminino", "masculino"]),
        "taxa_100mil",
    ].notna().all()
    assert sim_atlas_territorio.loc[
        sim_atlas_territorio.ano.ge(2025), "taxa_100mil"
    ].isna().all()
    sim_atlas_idade = pd.read_csv(atlas / "sim_mortalidade_idade_ano.csv")
    assert len(sim_atlas_idade) == 864
    assert not sim_atlas_idade.duplicated(
        ["ano", "territorio", "grupo_causa", "grupo_etario"]
    ).any()

    sinan_atlas = pd.read_parquet(ROOT / "data" / "silver" / "sinan_atlas_violencia.parquet")
    assert len(sinan_atlas) == 4292317
    assert sorted(sinan_atlas.ano.unique().tolist()) == list(range(2015, 2026))
    assert set(sinan_atlas.natureza_violencia.unique()) == {"interpessoal", "autoprovocada"}
    sinan_mulheres_controle = pd.concat(
        [
            pd.read_parquet(ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal.parquet", columns=["ano"]),
            pd.read_parquet(ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal_2025_preliminar.parquet", columns=["ano"]),
        ],
        ignore_index=True,
    ).groupby("ano").size().to_dict()
    sinan_atlas_controle = (
        sinan_atlas.loc[
            sinan_atlas.sexo.eq("feminino")
            & sinan_atlas.natureza_violencia.eq("interpessoal")
        ]
        .groupby("ano")
        .size()
        .to_dict()
    )
    assert sinan_atlas_controle == sinan_mulheres_controle
    sinan_atlas_territorio = pd.read_csv(
        atlas / "sinan_violencia_territorio_ano.csv",
        dtype={"id_territorio": "string"},
        low_memory=False,
    )
    assert len(sinan_atlas_territorio) == 127908
    assert not sinan_atlas_territorio.duplicated(
        ["ano", "nivel_territorial", "id_territorio", "indicador", "sexo"]
    ).any()
    assert sinan_atlas_territorio.loc[
        sinan_atlas_territorio.ano.eq(2025), "taxa_100mil"
    ].isna().all()
    sinan_atlas_idade = pd.read_csv(atlas / "sinan_violencia_idade_ano.csv")
    assert len(sinan_atlas_idade) == 2376
    assert not sinan_atlas_idade.duplicated(
        ["ano", "territorio", "indicador", "grupo_etario"]
    ).any()

    sinesp_cobertura = pd.read_csv(atlas / "sinesp_cobertura_evento_uf_ano.csv")
    assert len(sinesp_cobertura) == 1944
    assert sinesp_cobertura.indicador.nunique() == 9
    assert sinesp_cobertura.cobertura_mensal_completa.all()
    assert not sinesp_cobertura.duplicated(["indicador", "ano", "sigla_uf"]).any()
    sinesp_resumo = pd.read_csv(atlas / "sinesp_cobertura_evento_resumo.csv")
    assert len(sinesp_resumo) == 9
    assert sinesp_resumo.todos_uf_anos_completos.all()
    assert set(sinesp_resumo.loc[sinesp_resumo.sc_tem_cobertura_municipal, "indicador"]) == {
        "Feminicídio",
        "Tentativa de feminicídio",
        "Homicídio doloso",
        "Tentativa de homicídio",
        "Suicídio",
    }
    sinesp_territorio = pd.read_csv(
        atlas / "sinesp_prioridade_territorio_ano.csv",
        dtype={"id_territorio": "string"},
    )
    assert len(sinesp_territorio) == 56160
    assert sinesp_territorio.indicador.nunique() == 10
    assert not sinesp_territorio.duplicated(
        ["nivel_territorial", "id_territorio", "ano", "indicador", "sexo"]
    ).any()
    assert sinesp_territorio.loc[sinesp_territorio.ano.ge(2025), "taxa_100mil"].isna().all()
    assert sinesp_territorio.loc[
        sinesp_territorio.nivel_territorial.eq("municipio"), "id_territorio"
    ].nunique() == 295
    sinesp_mensal_atlas = pd.read_csv(atlas / "sinesp_prioridade_mensal.csv")
    assert len(sinesp_mensal_atlas) == 7360
    assert not sinesp_mensal_atlas.duplicated(
        ["territorio", "ano", "mes", "indicador", "sexo"]
    ).any()

    conexao = duckdb.connect()
    pop_total = (ROOT / "data" / "silver" / "populacao_municipio_ano.parquet").as_posix()
    pop_sexo = (ROOT / "data" / "silver" / "populacao_municipio_sexo_ano.parquet").as_posix()
    pop_idade = (ROOT / "data" / "silver" / "populacao_municipio_idade_ano.parquet").as_posix()
    assert conexao.execute(f"SELECT count(*) FROM read_parquet('{pop_total}')").fetchone()[0] == 55700
    assert conexao.execute(f"SELECT count(*) FROM read_parquet('{pop_sexo}')").fetchone()[0] == 111400
    assert conexao.execute(f"SELECT count(*) FROM read_parquet('{pop_idade}')").fetchone()[0] == 4511700
    assert conexao.execute(
        f"SELECT sum(populacao) FROM read_parquet('{pop_total}') WHERE ano = 2024"
    ).fetchone()[0] == 212583750
    divergencias = conexao.execute(
        f"""
        WITH s AS (
            SELECT ano, id_municipio, sum(populacao) AS populacao
            FROM read_parquet('{pop_sexo}') GROUP BY ano, id_municipio
        ), i AS (
            SELECT ano, id_municipio, sum(populacao) AS populacao
            FROM read_parquet('{pop_idade}') GROUP BY ano, id_municipio
        )
        SELECT count(*)
        FROM read_parquet('{pop_total}') t
        JOIN s USING (ano, id_municipio)
        JOIN i USING (ano, id_municipio)
        WHERE t.populacao <> s.populacao OR t.populacao <> i.populacao
        """
    ).fetchone()[0]
    conexao.close()
    assert divergencias == 0

    print(
        "Projeto validado: SINAN, SIM, Sinesp, população, raça, RAIS, atlas, Gold, análises e dimensões OK."
    )


if __name__ == "__main__":
    main()

