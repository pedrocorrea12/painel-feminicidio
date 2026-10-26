"""Gera indicadores de cor ou raça para SIM e SINAN com Censo 2022.

As taxas anuais do SIM usam o denominador fixo do Censo 2022. O resultado
municipal de Santa Catarina agrega 2019 a 2024 e anualiza o denominador.
O SINAN recebe um indice de representacao, nunca uma taxa de pessoas unicas.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SILVER = ROOT / "data" / "silver"
IBGE = ROOT / "data" / "gold" / "ibge"
DESTINO = ROOT / "data" / "gold" / "raca"

SIM = SILVER / "sim_mulheres_agressao.parquet"
SINAN = SILVER / "sinan_viol_mulheres_interpessoal.parquet"
POPULACAO = SILVER / "populacao_feminina_municipio.parquet"
CENSO_UF = IBGE / "censo2022_mulheres_cor_raca_uf.csv"
CENSO_MUNICIPIOS = IBGE / "censo2022_mulheres_cor_raca_municipios_sc.csv"

SIM_UF_ANO = DESTINO / "sim_raca_uf_ano_2019_2024.csv"
SIM_MUNICIPIOS = DESTINO / "sim_raca_municipios_sc_2019_2024.csv"
SINAN_UF = DESTINO / "sinan_raca_uf_2024.csv"
SINAN_MUNICIPIOS = DESTINO / "sinan_raca_municipios_sc_2019_2024.csv"
RESUMO = DESTINO / "resumo_raca.json"

RACAS = {
    "1": "Branca",
    "2": "Preta",
    "3": "Amarela",
    "4": "Parda",
    "5": "Indígena",
}
ORDEM_RACAS = ["Branca", "Preta", "Parda", "Negra", "Amarela", "Indígena"]
CENSO_COLUNAS = {
    "Branca": "brancas",
    "Preta": "pretas",
    "Parda": "pardas",
    "Negra": "negras",
    "Amarela": "amarelas",
    "Indígena": "indigenas",
}


def _verificar_arquivos() -> None:
    caminhos = [SIM, SINAN, POPULACAO, CENSO_UF, CENSO_MUNICIPIOS]
    ausentes = [str(c.relative_to(ROOT)) for c in caminhos if not c.exists()]
    if ausentes:
        raise FileNotFoundError(f"Arquivos ausentes: {ausentes}")


def _censo_uf_longo() -> pd.DataFrame:
    censo = pd.read_csv(CENSO_UF, dtype={"sigla_uf": "string"})
    linhas = []
    for raca, coluna in CENSO_COLUNAS.items():
        parte = censo[["sigla_uf", "mulheres_total", "mulheres_identificadas", coluna]].copy()
        parte = parte.rename(columns={coluna: "populacao_feminina_raca"})
        parte["raca"] = raca
        linhas.append(parte)
    longo = pd.concat(linhas, ignore_index=True)
    longo["populacao_feminina_raca"] = longo["populacao_feminina_raca"].astype("int64")
    return longo


def _censo_municipal_longo() -> pd.DataFrame:
    censo = pd.read_csv(CENSO_MUNICIPIOS, dtype={"id_municipio": "string"})
    censo["id_municipio"] = censo["id_municipio"].str.zfill(7)
    cadastro = (
        pd.read_parquet(POPULACAO, columns=["id_municipio", "municipio", "sigla_uf"])
        .loc[lambda x: x.sigla_uf.eq("SC"), ["id_municipio", "municipio"]]
        .drop_duplicates()
    )
    censo = censo.drop(columns="municipio").merge(
        cadastro, on="id_municipio", how="left", validate="one_to_one"
    )
    if censo["municipio"].isna().any() or len(censo) != 295:
        raise ValueError("Cadastro do Censo municipal de Santa Catarina invalido")
    linhas = []
    for raca, coluna in CENSO_COLUNAS.items():
        parte = censo[
            ["id_municipio", "municipio", "mulheres_total", "identificadas", coluna]
        ].copy()
        parte = parte.rename(
            columns={"identificadas": "mulheres_identificadas", coluna: "populacao_feminina_raca"}
        )
        parte["raca"] = raca
        linhas.append(parte)
    longo = pd.concat(linhas, ignore_index=True)
    longo["populacao_feminina_raca"] = longo["populacao_feminina_raca"].astype("int64")
    return longo


def _adicionar_negra(dados: pd.DataFrame, chaves: list[str], valor: str) -> pd.DataFrame:
    identificadas = dados.loc[dados["raca"].isin(RACAS.values())].copy()
    negra = (
        identificadas.loc[identificadas["raca"].isin(["Preta", "Parda"])]
        .groupby(chaves, as_index=False)[valor]
        .sum()
    )
    negra["raca"] = "Negra"
    return pd.concat([identificadas, negra], ignore_index=True)


def _metricas_representacao(dados: pd.DataFrame, valor: str) -> pd.DataFrame:
    dados = dados.copy()
    dados["percentual_raca_entre_informadas"] = (
        dados[valor]
        .div(dados["registros_raca_informada"].where(dados["registros_raca_informada"].ne(0)))
        .mul(100)
        .round(2)
    )
    dados["percentual_raca_populacao_censo"] = (
        dados["populacao_feminina_raca"]
        .div(dados["mulheres_identificadas"].where(dados["mulheres_identificadas"].ne(0)))
        .mul(100)
        .round(2)
    )
    dados["indice_representacao"] = (
        dados["percentual_raca_entre_informadas"]
        .div(dados["percentual_raca_populacao_censo"].where(dados["percentual_raca_populacao_censo"].ne(0)))
        .round(3)
    )
    dados["percentual_raca_nao_informada"] = (
        dados["registros_raca_nao_informada"]
        .div(dados["registros_total"].where(dados["registros_total"].ne(0)))
        .mul(100)
        .round(2)
    )
    return dados


def _sim_uf_ano(censo: pd.DataFrame) -> pd.DataFrame:
    sim = pd.read_parquet(
        SIM, columns=["ano", "RACACOR", "sigla_uf", "situacao_dado"]
    )
    sim = sim.loc[
        sim["ano"].between(2019, 2024) & sim["situacao_dado"].eq("definitivo")
    ].copy()
    sim["codigo_raca"] = sim["RACACOR"].fillna("").astype(str).str.strip()
    sim["raca"] = sim["codigo_raca"].map(RACAS).fillna("Não informada")
    sim_uf = sim.loc[sim["sigla_uf"].notna()].copy()
    sim_br = sim.copy()
    sim_br["sigla_uf"] = "BR"
    base = pd.concat([sim_uf, sim_br], ignore_index=True)

    totais = (
        base.groupby(["ano", "sigla_uf"], as_index=False)
        .agg(
            registros_total=("ano", "size"),
            registros_raca_informada=("raca", lambda x: int(x.ne("Não informada").sum())),
            registros_raca_nao_informada=("raca", lambda x: int(x.eq("Não informada").sum())),
        )
    )
    contagens = (
        base.loc[base["raca"].ne("Não informada")]
        .groupby(["ano", "sigla_uf", "raca"], as_index=False)
        .size()
        .rename(columns={"size": "obitos_mulheres_agressao"})
    )
    contagens = _adicionar_negra(
        contagens, ["ano", "sigla_uf"], "obitos_mulheres_agressao"
    )
    grade = (
        totais[["ano", "sigla_uf"]]
        .drop_duplicates()
        .merge(pd.DataFrame({"raca": ORDEM_RACAS}), how="cross")
    )
    resultado = grade.merge(
        contagens, on=["ano", "sigla_uf", "raca"], how="left", validate="one_to_one"
    )
    resultado["obitos_mulheres_agressao"] = (
        resultado["obitos_mulheres_agressao"].fillna(0).astype("int64")
    )
    resultado = resultado.merge(
        totais, on=["ano", "sigla_uf"], how="left", validate="many_to_one"
    ).merge(censo, on=["sigla_uf", "raca"], how="left", validate="many_to_one")
    if resultado["populacao_feminina_raca"].isna().any():
        raise ValueError("SIM por UF sem denominador do Censo")
    resultado = _metricas_representacao(resultado, "obitos_mulheres_agressao")
    resultado["taxa_100mil_mulheres_censo2022"] = (
        resultado["obitos_mulheres_agressao"]
        .div(resultado["populacao_feminina_raca"])
        .mul(100_000)
        .round(3)
    )
    resultado["denominador_ano"] = 2022
    resultado["base_territorial"] = "residencia_da_vitima"
    resultado["dado_suficiente"] = resultado["obitos_mulheres_agressao"].ge(5)
    return resultado.sort_values(["ano", "sigla_uf", "raca"]).reset_index(drop=True)


def _sim_municipios(censo: pd.DataFrame) -> pd.DataFrame:
    sim = pd.read_parquet(
        SIM, columns=["ano", "RACACOR", "id_municipio", "sigla_uf", "situacao_dado"]
    )
    sim = sim.loc[
        sim["ano"].between(2019, 2024)
        & sim["sigla_uf"].eq("SC")
        & sim["situacao_dado"].eq("definitivo")
    ].copy()
    sim["id_municipio"] = sim["id_municipio"].fillna("").astype(str).str.strip()
    sim["raca"] = sim["RACACOR"].fillna("").astype(str).str.strip().map(RACAS).fillna("Não informada")
    totais = (
        sim.groupby("id_municipio", as_index=False)
        .agg(
            registros_total=("ano", "size"),
            registros_raca_informada=("raca", lambda x: int(x.ne("Não informada").sum())),
            registros_raca_nao_informada=("raca", lambda x: int(x.eq("Não informada").sum())),
        )
    )
    contagens = (
        sim.loc[sim["raca"].ne("Não informada")]
        .groupby(["id_municipio", "raca"], as_index=False)
        .size()
        .rename(columns={"size": "obitos_mulheres_agressao"})
    )
    contagens = _adicionar_negra(contagens, ["id_municipio"], "obitos_mulheres_agressao")
    resultado = censo.merge(
        contagens, on=["id_municipio", "raca"], how="left", validate="one_to_one"
    ).merge(totais, on="id_municipio", how="left", validate="many_to_one")
    colunas_contagem = [
        "obitos_mulheres_agressao", "registros_total", "registros_raca_informada",
        "registros_raca_nao_informada",
    ]
    resultado[colunas_contagem] = resultado[colunas_contagem].fillna(0).astype("int64")
    resultado = _metricas_representacao(resultado, "obitos_mulheres_agressao")
    resultado["taxa_anual_media_100mil_mulheres_censo2022"] = (
        resultado["obitos_mulheres_agressao"]
        .div(resultado["populacao_feminina_raca"].mul(6))
        .mul(100_000)
        .round(3)
    )
    resultado["periodo_inicio"] = 2019
    resultado["periodo_fim"] = 2024
    resultado["anos_periodo"] = 6
    resultado["denominador_ano"] = 2022
    resultado["base_territorial"] = "residencia_da_vitima"
    resultado["dado_suficiente"] = resultado["obitos_mulheres_agressao"].ge(5)
    return resultado.sort_values(["id_municipio", "raca"]).reset_index(drop=True)


def _sinan_uf_2024(censo: pd.DataFrame) -> pd.DataFrame:
    sinan = pd.read_parquet(SINAN, columns=["ano", "SG_UF", "CS_RACA"])
    sinan = sinan.loc[sinan["ano"].eq(2024)].copy()
    sinan["raca"] = sinan["CS_RACA"].fillna("").astype(str).str.strip().map(RACAS).fillna("Não informada")
    sinan_br = sinan.copy()
    sinan_br["sigla_uf"] = "BR"
    mapa_uf = (
        pd.read_parquet(POPULACAO, columns=["id_municipio", "sigla_uf"])
        .assign(codigo_uf=lambda x: x.id_municipio.astype(str).str[:2])
        [["codigo_uf", "sigla_uf"]]
        .drop_duplicates()
    )
    sinan = sinan.merge(
        mapa_uf, left_on="SG_UF", right_on="codigo_uf", how="left", validate="many_to_one"
    )
    sinan = sinan.loc[sinan["sigla_uf"].notna()].copy()
    base = pd.concat([sinan, sinan_br], ignore_index=True)
    totais = (
        base.groupby("sigla_uf", as_index=False)
        .agg(
            registros_total=("ano", "size"),
            registros_raca_informada=("raca", lambda x: int(x.ne("Não informada").sum())),
            registros_raca_nao_informada=("raca", lambda x: int(x.eq("Não informada").sum())),
        )
    )
    contagens = (
        base.loc[base["raca"].ne("Não informada")]
        .groupby(["sigla_uf", "raca"], as_index=False)
        .size()
        .rename(columns={"size": "notificacoes"})
    )
    contagens = _adicionar_negra(contagens, ["sigla_uf"], "notificacoes")
    grade = totais[["sigla_uf"]].merge(pd.DataFrame({"raca": ORDEM_RACAS}), how="cross")
    resultado = grade.merge(
        contagens, on=["sigla_uf", "raca"], how="left", validate="one_to_one"
    )
    resultado["notificacoes"] = resultado["notificacoes"].fillna(0).astype("int64")
    resultado = resultado.merge(totais, on="sigla_uf", validate="many_to_one").merge(
        censo, on=["sigla_uf", "raca"], validate="many_to_one"
    )
    resultado = _metricas_representacao(resultado, "notificacoes")
    resultado["ano"] = 2024
    resultado["unidade"] = "notificacoes"
    resultado["nao_interpretar_como"] = "pessoas_unicas"
    return resultado.sort_values(["sigla_uf", "raca"]).reset_index(drop=True)


def _sinan_municipios(censo: pd.DataFrame) -> pd.DataFrame:
    sinan = pd.read_parquet(SINAN, columns=["ano", "SG_UF", "id_municipio", "CS_RACA"])
    sinan = sinan.loc[sinan["ano"].between(2019, 2024) & sinan["SG_UF"].eq("42")].copy()
    sinan["id_municipio"] = sinan["id_municipio"].fillna("").astype(str).str.strip()
    sinan["raca"] = sinan["CS_RACA"].fillna("").astype(str).str.strip().map(RACAS).fillna("Não informada")
    totais = (
        sinan.groupby("id_municipio", as_index=False)
        .agg(
            registros_total=("ano", "size"),
            registros_raca_informada=("raca", lambda x: int(x.ne("Não informada").sum())),
            registros_raca_nao_informada=("raca", lambda x: int(x.eq("Não informada").sum())),
        )
    )
    contagens = (
        sinan.loc[sinan["raca"].ne("Não informada")]
        .groupby(["id_municipio", "raca"], as_index=False)
        .size()
        .rename(columns={"size": "notificacoes"})
    )
    contagens = _adicionar_negra(contagens, ["id_municipio"], "notificacoes")
    resultado = censo.merge(
        contagens, on=["id_municipio", "raca"], how="left", validate="one_to_one"
    ).merge(totais, on="id_municipio", how="left", validate="many_to_one")
    colunas = ["notificacoes", "registros_total", "registros_raca_informada", "registros_raca_nao_informada"]
    resultado[colunas] = resultado[colunas].fillna(0).astype("int64")
    resultado = _metricas_representacao(resultado, "notificacoes")
    resultado["periodo_inicio"] = 2019
    resultado["periodo_fim"] = 2024
    resultado["unidade"] = "notificacoes"
    resultado["nao_interpretar_como"] = "pessoas_unicas"
    resultado["dado_suficiente"] = resultado["notificacoes"].ge(20)
    return resultado.sort_values(["id_municipio", "raca"]).reset_index(drop=True)


def main() -> None:
    _verificar_arquivos()
    censo_uf = _censo_uf_longo()
    censo_municipal = _censo_municipal_longo()
    sim_uf = _sim_uf_ano(censo_uf)
    sim_municipios = _sim_municipios(censo_municipal)
    sinan_uf = _sinan_uf_2024(censo_uf)
    sinan_municipios = _sinan_municipios(censo_municipal)

    if len(sim_uf) != 6 * 28 * len(ORDEM_RACAS):
        raise ValueError("Quantidade inesperada de linhas no SIM por UF e ano")
    if len(sim_municipios) != 295 * len(ORDEM_RACAS):
        raise ValueError("Quantidade inesperada de linhas no SIM municipal")
    if len(sinan_uf) != 28 * len(ORDEM_RACAS):
        raise ValueError("Quantidade inesperada de linhas no SINAN por UF")
    if len(sinan_municipios) != 295 * len(ORDEM_RACAS):
        raise ValueError("Quantidade inesperada de linhas no SINAN municipal")

    controle_sim_br = int(
        sim_uf.loc[
            sim_uf.sigla_uf.eq("BR") & sim_uf.raca.eq("Branca"),
            "registros_total",
        ].sum()
    )
    controle_sim_sc = int(
        sim_municipios.loc[sim_municipios.raca.eq("Branca"), "registros_total"].sum()
    )
    if controle_sim_br != 22_691 or controle_sim_sc != 580:
        raise ValueError(f"Controles do SIM divergentes: BR={controle_sim_br}, SC={controle_sim_sc}")

    DESTINO.mkdir(parents=True, exist_ok=True)
    sim_uf.to_csv(SIM_UF_ANO, index=False, encoding="utf-8-sig")
    sim_municipios.to_csv(SIM_MUNICIPIOS, index=False, encoding="utf-8-sig")
    sinan_uf.to_csv(SINAN_UF, index=False, encoding="utf-8-sig")
    sinan_municipios.to_csv(SINAN_MUNICIPIOS, index=False, encoding="utf-8-sig")

    resumo = {
        "gerado_em": date.today().isoformat(),
        "periodo_sim": [2019, 2024],
        "denominador": "Censo 2022, mulheres por cor ou raça",
        "controles": {
            "sim_obitos_brasil_2019_2024": controle_sim_br,
            "sim_obitos_sc_2019_2024": controle_sim_sc,
            "sinan_notificacoes_brasil_2024": int(
                sinan_uf.loc[sinan_uf.sigla_uf.eq("BR"), "registros_total"].iloc[0]
            ),
            "sinan_notificacoes_sc_2024": int(
                sinan_uf.loc[sinan_uf.sigla_uf.eq("SC"), "registros_total"].iloc[0]
            ),
        },
        "regras": [
            "Negra corresponde a preta mais parda.",
            "A parcela sem cor ou raça informada permanece visível.",
            "As taxas municipais do SIM são médias anuais do período 2019 a 2024.",
            "O SINAN mede notificações e não pessoas únicas.",
        ],
    }
    RESUMO.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
