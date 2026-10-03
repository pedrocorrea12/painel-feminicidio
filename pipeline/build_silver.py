"""Consolida SINAN e populacao feminina em indicadores territoriais anuais."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SINAN = ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal.parquet"
SINAN_PRELIMINAR = ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal_2025_preliminar.parquet"
SIM = ROOT / "data" / "silver" / "sim_mulheres_agressao.parquet"
POPULACAO = ROOT / "data" / "silver" / "populacao_feminina_municipio.parquet"
DESTINO = ROOT / "data" / "silver" / "indicadores_territorio_ano.parquet"
DESTINO_PRELIMINAR = ROOT / "data" / "silver" / "sinan_preliminar_territorio_ano.parquet"

COLUNAS_SINAN = [
    "ano", "SG_UF", "id_municipio", "REL_CONJ", "REL_EXCON",
    "REL_NAMO", "REL_EXNAM", "LOCAL_OCOR",
]


def _metricas(base: pd.DataFrame) -> pd.DataFrame:
    base = base.copy()
    base[["notificacoes", "parceiro", "residencia", "populacao_feminina", "obitos_mulheres_agressao"]] = (
        base[["notificacoes", "parceiro", "residencia", "populacao_feminina", "obitos_mulheres_agressao"]]
        .fillna(0)
        .astype("int64")
    )
    base["percentual_parceiro"] = (
        base["parceiro"].div(base["notificacoes"].where(base["notificacoes"].ne(0))) * 100
    ).fillna(0).round(1)
    base["taxa_notificacoes_100mil"] = (
        base["notificacoes"].div(base["populacao_feminina"]) * 100_000
    ).round(2)
    base["taxa_parceiro_100mil"] = (
        base["parceiro"].div(base["populacao_feminina"]) * 100_000
    ).round(2)
    base["taxa_obitos_mulheres_agressao_100mil"] = (
        base["obitos_mulheres_agressao"].div(base["populacao_feminina"]) * 100_000
    ).round(2)
    base["dado_suficiente"] = (
        base["nivel_territorial"].ne("municipio") | base["notificacoes"].ge(5)
    )
    return base


def construir() -> pd.DataFrame:
    for caminho in (SINAN, SIM, POPULACAO):
        if not caminho.exists():
            raise FileNotFoundError(f"Silver ausente: {caminho}")

    sinan = pd.read_parquet(SINAN, columns=COLUNAS_SINAN)
    sim = pd.read_parquet(SIM, columns=["ano", "id_municipio", "sigla_uf"])
    sim["id_municipio"] = sim["id_municipio"].fillna("").astype(str).str.strip()
    sim["sigla_uf"] = sim["sigla_uf"].fillna("").astype(str).str.strip()
    sinan["id_municipio"] = sinan["id_municipio"].fillna("").astype(str).str.strip()
    sinan["SG_UF"] = sinan["SG_UF"].fillna("").astype(str).str.strip()
    sinan["parceiro"] = (
        sinan[["REL_CONJ", "REL_EXCON", "REL_NAMO", "REL_EXNAM"]]
        .eq("1")
        .any(axis=1)
    )
    sinan["na_residencia"] = sinan["LOCAL_OCOR"].eq("01")

    pop = pd.read_parquet(POPULACAO)
    pop["id_municipio"] = pop["id_municipio"].astype(str)
    anos = sorted(pop["ano"].unique().tolist())
    sinan = sinan.loc[sinan["ano"].isin(anos)].copy()

    mapa_uf = (
        pop.assign(id_uf=pop["id_municipio"].str[:2])[["id_uf", "sigla_uf"]]
        .drop_duplicates()
        .sort_values("id_uf")
    )
    if len(mapa_uf) != 27:
        raise ValueError(f"Esperadas 27 UFs, encontradas {len(mapa_uf)}")

    validos = set(pop["id_municipio"])
    sinan_municipio = sinan.loc[sinan["id_municipio"].isin(validos)]
    agregado_municipio = (
        sinan_municipio.groupby(["ano", "id_municipio"], as_index=False)
        .agg(
            notificacoes=("ano", "size"),
            parceiro=("parceiro", "sum"),
            residencia=("na_residencia", "sum"),
        )
    )
    sim_municipio = (
        sim.loc[sim["id_municipio"].isin(validos)]
        .groupby(["ano", "id_municipio"], as_index=False)
        .size()
        .rename(columns={"size": "obitos_mulheres_agressao"})
    )
    agregado_municipio = agregado_municipio.merge(
        sim_municipio, on=["ano", "id_municipio"], how="outer", validate="one_to_one"
    )
    municipio = pop.merge(
        agregado_municipio,
        on=["ano", "id_municipio"],
        how="left",
        validate="one_to_one",
    ).rename(columns={"municipio": "territorio"})
    municipio.insert(1, "nivel_territorial", "municipio")
    municipio.insert(2, "id_territorio", municipio["id_municipio"])
    municipio = municipio.drop(columns="id_municipio")

    pop_uf = (
        pop.assign(id_uf=pop["id_municipio"].str[:2])
        .groupby(["ano", "id_uf", "sigla_uf"], as_index=False)
        .agg(populacao_feminina=("populacao_feminina", "sum"))
    )
    sinan_uf = (
        sinan.loc[sinan["SG_UF"].isin(set(mapa_uf["id_uf"]))]
        .groupby(["ano", "SG_UF"], as_index=False)
        .agg(
            notificacoes=("ano", "size"),
            parceiro=("parceiro", "sum"),
            residencia=("na_residencia", "sum"),
        )
        .rename(columns={"SG_UF": "id_uf"})
    )
    sim_uf = (
        sim.loc[sim["sigla_uf"].isin(set(mapa_uf["sigla_uf"]))]
        .groupby(["ano", "sigla_uf"], as_index=False)
        .size()
        .rename(columns={"size": "obitos_mulheres_agressao"})
    )
    uf = pop_uf.merge(sinan_uf, on=["ano", "id_uf"], how="left", validate="one_to_one")
    uf = uf.merge(sim_uf, on=["ano", "sigla_uf"], how="left", validate="one_to_one")
    uf["nivel_territorial"] = "uf"
    uf["id_territorio"] = uf["sigla_uf"]
    uf["territorio"] = uf["sigla_uf"]
    uf = uf.drop(columns="id_uf")

    pop_brasil = (
        pop.groupby("ano", as_index=False)
        .agg(populacao_feminina=("populacao_feminina", "sum"))
    )
    sinan_brasil = (
        sinan.groupby("ano", as_index=False)
        .agg(
            notificacoes=("ano", "size"),
            parceiro=("parceiro", "sum"),
            residencia=("na_residencia", "sum"),
        )
    )
    sim_brasil = (
        sim.groupby("ano", as_index=False)
        .size()
        .rename(columns={"size": "obitos_mulheres_agressao"})
    )
    brasil = pop_brasil.merge(sinan_brasil, on="ano", how="left", validate="one_to_one")
    brasil = brasil.merge(sim_brasil, on="ano", how="left", validate="one_to_one")
    brasil["nivel_territorial"] = "brasil"
    brasil["id_territorio"] = "BR"
    brasil["territorio"] = "Brasil"
    brasil["sigla_uf"] = ""

    colunas = [
        "ano", "nivel_territorial", "id_territorio", "territorio", "sigla_uf",
        "populacao_feminina", "notificacoes", "parceiro", "residencia",
        "obitos_mulheres_agressao",
    ]
    consolidado = pd.concat(
        [brasil[colunas], uf[colunas], municipio[colunas]], ignore_index=True
    )
    consolidado = _metricas(consolidado).sort_values(
        ["ano", "nivel_territorial", "id_territorio"]
    ).reset_index(drop=True)

    esperado = len(anos) * (1 + 27 + 5570)
    if len(consolidado) != esperado:
        raise ValueError(f"Linhas inesperadas: {len(consolidado)} != {esperado}")
    if consolidado.duplicated(["ano", "nivel_territorial", "id_territorio"]).any():
        raise ValueError("Chave territorial anual duplicada")
    if consolidado.isna().any().any():
        raise ValueError("Silver consolidada contém valores nulos")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    consolidado.to_parquet(DESTINO, index=False)
    return consolidado


def construir_preliminar() -> pd.DataFrame:
    if not SINAN_PRELIMINAR.exists():
        raise FileNotFoundError(f"Silver preliminar ausente: {SINAN_PRELIMINAR}")
    colunas = ["ano", "SG_UF", "id_municipio", "REL_CONJ", "REL_EXCON", "REL_NAMO", "REL_EXNAM"]
    sinan = pd.read_parquet(SINAN_PRELIMINAR, columns=colunas)
    sinan["id_municipio"] = sinan["id_municipio"].fillna("").astype(str).str.strip()
    sinan["SG_UF"] = sinan["SG_UF"].fillna("").astype(str).str.strip()
    sinan["parceiro"] = sinan[["REL_CONJ", "REL_EXCON", "REL_NAMO", "REL_EXNAM"]].eq("1").any(axis=1)
    municipio = (
        sinan.groupby(["ano", "id_municipio"], as_index=False)
        .agg(notificacoes=("ano", "size"), parceiro=("parceiro", "sum"))
        .assign(nivel_territorial="municipio", id_territorio=lambda x: x.id_municipio)
        .drop(columns="id_municipio")
    )
    uf = (
        sinan.groupby(["ano", "SG_UF"], as_index=False)
        .agg(notificacoes=("ano", "size"), parceiro=("parceiro", "sum"))
        .assign(nivel_territorial="uf", id_territorio=lambda x: x.SG_UF)
        .drop(columns="SG_UF")
    )
    brasil = (
        sinan.groupby("ano", as_index=False)
        .agg(notificacoes=("ano", "size"), parceiro=("parceiro", "sum"))
        .assign(nivel_territorial="brasil", id_territorio="BR")
    )
    resultado = pd.concat([brasil, uf, municipio], ignore_index=True)
    resultado["situacao_dado"] = "preliminar"
    resultado.to_parquet(DESTINO_PRELIMINAR, index=False)
    return resultado


def main() -> None:
    dados = construir()
    preliminar = construir_preliminar()
    print(f"Silver consolidada: {DESTINO}")
    print(f"Linhas: {len(dados)}")
    print(f"Período: {dados.ano.min()}-{dados.ano.max()}")
    print(dados.groupby("nivel_territorial").size().to_string())
    print(f"Silver preliminar: {DESTINO_PRELIMINAR} ({len(preliminar)} linhas)")


if __name__ == "__main__":
    main()
