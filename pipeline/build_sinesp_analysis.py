"""Gera análises derivadas de Sinesp, SIM e população feminina.

O script não altera o painel. As saídas ficam em ``data/gold/integrado``.

Rodar: ``python pipeline/build_sinesp_analysis.py``.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SILVER = ROOT / "data" / "silver"
DESTINO = ROOT / "data" / "gold" / "integrado"
RELATORIO = ROOT / "docs" / "RELATORIO_ANALISES_SINESP.md"

SINESP = SILVER / "sinesp_vde_ocorrencias.parquet"
SIM = SILVER / "sim_mulheres_agressao.parquet"
POPULACAO = SILVER / "populacao_feminina_municipio.parquet"

RAZAO_UF = DESTINO / "razao_sim_sinesp_uf_2019_2024.csv"
TENTATIVAS = DESTINO / "tentativa_feminicidio_2019_2026.csv"
MUNICIPIOS = DESTINO / "taxa_municipal_feminicidio_sc_2019_2024.csv"
SERIE_MENSAL = DESTINO / "sinesp_serie_mensal_2019_2026.csv"
SAZONALIDADE = DESTINO / "sinesp_sazonalidade_mes_2019_2025.csv"
HOMICIDIOS = DESTINO / "homicidio_doloso_feminicidio_2019_2026.csv"
RESUMO = DESTINO / "resumo_analises_sinesp.json"

FONTE_SINESP = (
    "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/"
    "estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-"
    "gestores-estaduais-sinesp-vde-2022-e-2023"
)

EVENTO_FEMINICIDIO = "Feminicídio"
EVENTO_TENTATIVA = "Tentativa de feminicídio"
EVENTO_HOMICIDIO = "Homicídio doloso"
EVENTOS = [EVENTO_FEMINICIDIO, EVENTO_TENTATIVA, EVENTO_HOMICIDIO]
MESES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def _formatar_inteiro(valor: int | float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def _formatar_decimal(valor: int | float, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def _normalizar_nome(valor: object) -> str:
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = texto.encode("ascii", "ignore").decode("ascii").upper()
    return re.sub(r"[^A-Z0-9]+", " ", texto).strip()


def _carregar() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ausentes = [str(p) for p in [SINESP, SIM, POPULACAO] if not p.exists()]
    if ausentes:
        raise FileNotFoundError(f"Arquivos ausentes: {ausentes}")
    sinesp = pd.read_parquet(
        SINESP,
        columns=[
            "ano",
            "mes",
            "sigla_uf",
            "municipio",
            "evento",
            "abrangencia",
            "vitimas_feminino",
            "vitimas_masculino",
            "vitimas_nao_informado",
            "total_vitimas",
            "situacao_dado",
        ],
    )
    sinesp = sinesp.loc[
        sinesp["abrangencia"].eq("Estadual")
        & sinesp["evento"].astype(str).str.casefold().isin(
            {evento.casefold() for evento in EVENTOS}
        )
    ].copy()
    for coluna in [
        "vitimas_feminino",
        "vitimas_masculino",
        "vitimas_nao_informado",
        "total_vitimas",
    ]:
        sinesp[coluna] = sinesp[coluna].fillna(0)
    sim = pd.read_parquet(
        SIM, columns=["ano", "sigla_uf", "id_municipio", "situacao_dado"]
    )
    populacao = pd.read_parquet(POPULACAO)
    return sinesp, sim, populacao


def _agregar_eventos(sinesp: pd.DataFrame) -> pd.DataFrame:
    medidas = {
        "vitimas_feminino": "sum",
        "vitimas_masculino": "sum",
        "vitimas_nao_informado": "sum",
        "total_vitimas": "sum",
    }
    uf = (
        sinesp.groupby(["ano", "mes", "sigla_uf", "evento"], as_index=False)
        .agg(medidas)
        .assign(
            nivel_territorial="uf",
            id_territorio=lambda x: x.sigla_uf,
            territorio=lambda x: x.sigla_uf,
        )
    )
    brasil = (
        sinesp.groupby(["ano", "mes", "evento"], as_index=False)
        .agg(medidas)
        .assign(
            nivel_territorial="brasil",
            id_territorio="BR",
            territorio="Brasil",
            sigla_uf="",
        )
    )
    resultado = pd.concat([brasil, uf], ignore_index=True)
    for coluna in medidas:
        resultado[coluna] = resultado[coluna].round().astype("int64")
    return resultado


def _anual(mensal: pd.DataFrame) -> pd.DataFrame:
    chaves = [
        "ano",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "sigla_uf",
        "evento",
    ]
    anual = (
        mensal.groupby(chaves, as_index=False)
        .agg(
            vitimas_feminino=("vitimas_feminino", "sum"),
            vitimas_masculino=("vitimas_masculino", "sum"),
            vitimas_nao_informado=("vitimas_nao_informado", "sum"),
            total_vitimas=("total_vitimas", "sum"),
            meses_informados=("mes", "nunique"),
        )
    )
    anual["situacao_dado"] = "consolidado_publicacao"
    anual.loc[anual["ano"].eq(2026), "situacao_dado"] = "parcial"
    return anual


def _selecionar_evento(anual: pd.DataFrame, evento: str, prefixo: str) -> pd.DataFrame:
    chaves = [
        "ano",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "sigla_uf",
    ]
    colunas = chaves + [
        "vitimas_feminino",
        "vitimas_masculino",
        "vitimas_nao_informado",
        "total_vitimas",
        "meses_informados",
        "situacao_dado",
    ]
    resultado = anual.loc[
        anual["evento"].astype(str).str.casefold().eq(evento.casefold()), colunas
    ].copy()
    return resultado.rename(
        columns={
            "vitimas_feminino": f"{prefixo}_vitimas_femininas",
            "vitimas_masculino": f"{prefixo}_vitimas_masculinas",
            "vitimas_nao_informado": f"{prefixo}_vitimas_sexo_nao_informado",
            "total_vitimas": f"{prefixo}_total_vitimas",
            "meses_informados": f"{prefixo}_meses_informados",
            "situacao_dado": f"{prefixo}_situacao_dado",
        }
    )


def _populacao_territorial(populacao: pd.DataFrame) -> pd.DataFrame:
    uf = (
        populacao.groupby(["ano", "sigla_uf"], as_index=False)
        .agg(populacao_feminina=("populacao_feminina", "sum"))
        .assign(
            nivel_territorial="uf",
            id_territorio=lambda x: x.sigla_uf,
        )
    )
    brasil = (
        populacao.groupby("ano", as_index=False)
        .agg(populacao_feminina=("populacao_feminina", "sum"))
        .assign(nivel_territorial="brasil", id_territorio="BR")
    )
    return pd.concat(
        [
            brasil[["ano", "nivel_territorial", "id_territorio", "populacao_feminina"]],
            uf[["ano", "nivel_territorial", "id_territorio", "populacao_feminina"]],
        ],
        ignore_index=True,
    )


def _razao_sim_sinesp(
    anual: pd.DataFrame, sim: pd.DataFrame, populacao: pd.DataFrame
) -> pd.DataFrame:
    fem = _selecionar_evento(anual, EVENTO_FEMINICIDIO, "sinesp_feminicidio")
    fem = fem.loc[fem["ano"].between(2019, 2024)].copy()
    sim_recorte = sim.loc[sim["ano"].between(2019, 2024)].copy()
    sim_uf = (
        sim_recorte.groupby(["ano", "sigla_uf"], as_index=False)
        .size()
        .rename(columns={"size": "sim_obitos_mulheres_agressao"})
        .assign(nivel_territorial="uf", id_territorio=lambda x: x.sigla_uf)
    )
    sim_br = (
        sim_recorte.groupby("ano", as_index=False)
        .size()
        .rename(columns={"size": "sim_obitos_mulheres_agressao"})
        .assign(nivel_territorial="brasil", id_territorio="BR")
    )
    sim_agregado = pd.concat(
        [
            sim_br[["ano", "nivel_territorial", "id_territorio", "sim_obitos_mulheres_agressao"]],
            sim_uf[["ano", "nivel_territorial", "id_territorio", "sim_obitos_mulheres_agressao"]],
        ],
        ignore_index=True,
    )
    chaves = ["ano", "nivel_territorial", "id_territorio"]
    resultado = fem.merge(sim_agregado, on=chaves, how="inner", validate="one_to_one")
    resultado = resultado.merge(
        _populacao_territorial(populacao), on=chaves, how="left", validate="one_to_one"
    )
    resultado["razao_feminicidios_total_sobre_sim"] = (
        resultado["sinesp_feminicidio_total_vitimas"]
        .div(resultado["sim_obitos_mulheres_agressao"])
        .round(4)
    )
    resultado["razao_feminicidios_mulheres_sobre_sim"] = (
        resultado["sinesp_feminicidio_vitimas_femininas"]
        .div(resultado["sim_obitos_mulheres_agressao"])
        .round(4)
    )
    resultado["taxa_sim_100mil_mulheres"] = (
        resultado["sim_obitos_mulheres_agressao"]
        .div(resultado["populacao_feminina"])
        .mul(100_000)
        .round(2)
    )
    resultado["taxa_sinesp_feminicidio_100mil_mulheres"] = (
        resultado["sinesp_feminicidio_total_vitimas"]
        .div(resultado["populacao_feminina"])
        .mul(100_000)
        .round(2)
    )
    resultado["ranking_uf_razao_ano"] = pd.NA
    ufs = resultado["nivel_territorial"].eq("uf")
    resultado.loc[ufs, "ranking_uf_razao_ano"] = (
        resultado.loc[ufs]
        .groupby("ano")["razao_feminicidios_total_sobre_sim"]
        .rank(method="min", ascending=False)
        .astype("Int64")
    )
    resultado["sim_base_territorial"] = "residencia_da_vitima"
    resultado["sinesp_base_territorial"] = "municipio_do_fato"
    resultado["tipo_leitura"] = "indicador_contextual_de_classificacao"
    resultado["comparacao_direta"] = False
    colunas = [
        "ano",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "sigla_uf",
        "populacao_feminina",
        "sim_obitos_mulheres_agressao",
        "sinesp_feminicidio_total_vitimas",
        "sinesp_feminicidio_vitimas_femininas",
        "razao_feminicidios_total_sobre_sim",
        "razao_feminicidios_mulheres_sobre_sim",
        "taxa_sim_100mil_mulheres",
        "taxa_sinesp_feminicidio_100mil_mulheres",
        "ranking_uf_razao_ano",
        "sim_base_territorial",
        "sinesp_base_territorial",
        "tipo_leitura",
        "comparacao_direta",
    ]
    resultado = resultado[colunas].sort_values(
        ["ano", "nivel_territorial", "id_territorio"]
    )
    if len(resultado) != 6 * 28:
        raise ValueError(f"Razão UF com {len(resultado)} linhas, esperado 168")
    if resultado.duplicated(chaves).any():
        raise ValueError("Razão UF possui chave duplicada")
    return resultado.reset_index(drop=True)


def _tentativas_consumados(anual: pd.DataFrame) -> pd.DataFrame:
    chaves = [
        "ano",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "sigla_uf",
    ]
    fem = _selecionar_evento(anual, EVENTO_FEMINICIDIO, "feminicidio")
    tentativa = _selecionar_evento(anual, EVENTO_TENTATIVA, "tentativa_feminicidio")
    resultado = fem.merge(tentativa, on=chaves, how="outer", validate="one_to_one")
    medidas = [
        "feminicidio_vitimas_femininas",
        "feminicidio_vitimas_masculinas",
        "feminicidio_vitimas_sexo_nao_informado",
        "feminicidio_total_vitimas",
        "tentativa_feminicidio_vitimas_femininas",
        "tentativa_feminicidio_vitimas_masculinas",
        "tentativa_feminicidio_vitimas_sexo_nao_informado",
        "tentativa_feminicidio_total_vitimas",
    ]
    resultado[medidas] = resultado[medidas].fillna(0).astype("int64")
    resultado["tentativas_por_feminicidio"] = (
        resultado["tentativa_feminicidio_total_vitimas"]
        .div(resultado["feminicidio_total_vitimas"].where(resultado["feminicidio_total_vitimas"].ne(0)))
        .round(2)
    )
    resultado["cobertura_completa_ano"] = resultado[
        ["feminicidio_meses_informados", "tentativa_feminicidio_meses_informados"]
    ].min(axis=1).eq(12)
    resultado["leitura"] = "registros_classificados_pela_seguranca_publica"
    resultado["nao_interpretar_como"] = "mortes_evitadas"
    resultado = resultado.sort_values(["ano", "nivel_territorial", "id_territorio"])
    if len(resultado) != 8 * 28:
        raise ValueError(f"Tentativas com {len(resultado)} linhas, esperado 224")
    return resultado.reset_index(drop=True)


def _municipios_sc(
    sinesp: pd.DataFrame, populacao: pd.DataFrame
) -> tuple[pd.DataFrame, int]:
    pop = populacao.loc[
        populacao["sigla_uf"].eq("SC") & populacao["ano"].between(2019, 2024)
    ].copy()
    cadastro = pop[["id_municipio", "municipio"]].drop_duplicates()
    cadastro["chave_nome"] = cadastro["municipio"].map(_normalizar_nome)
    if len(cadastro) != 295 or cadastro["chave_nome"].duplicated().any():
        raise ValueError("Cadastro municipal de SC inválido")
    mapa = cadastro.set_index("chave_nome")["id_municipio"].to_dict()

    fem = sinesp.loc[
        sinesp["evento"].astype(str).str.casefold().eq(EVENTO_FEMINICIDIO.casefold())
        & sinesp["sigla_uf"].eq("SC")
        & sinesp["ano"].between(2019, 2024)
    ].copy()
    fem["chave_nome"] = fem["municipio"].map(_normalizar_nome)
    nao_informado = int(
        fem.loc[fem["chave_nome"].eq("NAO INFORMADO"), "total_vitimas"].sum()
    )
    fem["id_municipio"] = fem["chave_nome"].map(mapa)
    sem_mapa = sorted(
        fem.loc[
            fem["id_municipio"].isna() & fem["chave_nome"].ne("NAO INFORMADO"),
            "municipio",
        ].dropna().unique()
    )
    if sem_mapa:
        raise ValueError(f"Municípios sem correspondência: {sem_mapa}")
    agregado = (
        fem.dropna(subset=["id_municipio"])
        .groupby("id_municipio", as_index=False)
        .agg(
            feminicidios_total=("total_vitimas", "sum"),
            feminicidios_vitimas_femininas=("vitimas_feminino", "sum"),
            meses_com_linha=("mes", "size"),
        )
    )
    denominador = (
        pop.groupby(["id_municipio", "municipio"], as_index=False)
        .agg(
            populacao_feminina_anos_pessoa=("populacao_feminina", "sum"),
            populacao_feminina_media=("populacao_feminina", "mean"),
            anos_populacao=("ano", "nunique"),
        )
    )
    resultado = denominador.merge(
        agregado, on="id_municipio", how="left", validate="one_to_one"
    )
    resultado[["feminicidios_total", "feminicidios_vitimas_femininas"]] = (
        resultado[["feminicidios_total", "feminicidios_vitimas_femininas"]]
        .fillna(0)
        .round()
        .astype("int64")
    )
    resultado["periodo_inicio"] = 2019
    resultado["periodo_fim"] = 2024
    resultado["anos_periodo"] = 6
    resultado["taxa_feminicidio_100mil_mulheres_ano"] = (
        resultado["feminicidios_total"]
        .div(resultado["populacao_feminina_anos_pessoa"])
        .mul(100_000)
        .round(2)
    )
    resultado["media_anual_feminicidios"] = (
        resultado["feminicidios_total"].div(6).round(2)
    )
    resultado["dado_suficiente"] = resultado["feminicidios_total"].ge(5)
    resultado["ranking_taxa_apenas_dado_suficiente"] = pd.NA
    suficiente = resultado["dado_suficiente"]
    resultado.loc[suficiente, "ranking_taxa_apenas_dado_suficiente"] = (
        resultado.loc[suficiente, "taxa_feminicidio_100mil_mulheres_ano"]
        .rank(method="min", ascending=False)
        .astype("Int64")
    )
    resultado["base_territorial_sinesp"] = "municipio_do_fato"
    resultado["formula_taxa"] = (
        "soma_feminicidios_2019_2024_dividida_pela_soma_populacao_feminina_2019_2024_vezes_100mil"
    )
    colunas = [
        "id_municipio",
        "municipio",
        "periodo_inicio",
        "periodo_fim",
        "anos_periodo",
        "anos_populacao",
        "populacao_feminina_anos_pessoa",
        "populacao_feminina_media",
        "feminicidios_total",
        "feminicidios_vitimas_femininas",
        "media_anual_feminicidios",
        "taxa_feminicidio_100mil_mulheres_ano",
        "dado_suficiente",
        "ranking_taxa_apenas_dado_suficiente",
        "base_territorial_sinesp",
        "formula_taxa",
    ]
    resultado = resultado[colunas].sort_values(
        ["feminicidios_total", "taxa_feminicidio_100mil_mulheres_ano", "municipio"],
        ascending=[False, False, True],
    )
    if len(resultado) != 295:
        raise ValueError(f"Tabela municipal com {len(resultado)} linhas, esperado 295")
    return resultado.reset_index(drop=True), nao_informado


def _serie_mensal(mensal: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    recorte = mensal.loc[mensal["id_territorio"].isin(["BR", "SC"])].copy()
    chaves = [
        "ano",
        "mes",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "sigla_uf",
    ]
    medidas = {}
    for evento, prefixo in [
        (EVENTO_FEMINICIDIO, "feminicidio"),
        (EVENTO_TENTATIVA, "tentativa_feminicidio"),
        (EVENTO_HOMICIDIO, "homicidio_doloso"),
    ]:
        base = recorte.loc[
            recorte["evento"].astype(str).str.casefold().eq(evento.casefold()),
            chaves + ["vitimas_feminino", "total_vitimas"],
        ].rename(
            columns={
                "vitimas_feminino": f"{prefixo}_vitimas_femininas",
                "total_vitimas": f"{prefixo}_total_vitimas",
            }
        )
        medidas[prefixo] = base
    serie = medidas["feminicidio"]
    serie = serie.merge(medidas["tentativa_feminicidio"], on=chaves, validate="one_to_one")
    serie = serie.merge(medidas["homicidio_doloso"], on=chaves, validate="one_to_one")
    serie["homicidio_doloso_mais_feminicidio_vitimas_femininas"] = (
        serie["homicidio_doloso_vitimas_femininas"]
        + serie["feminicidio_vitimas_femininas"]
    )
    serie["data_referencia"] = pd.to_datetime(
        {"year": serie["ano"], "month": serie["mes"], "day": 1}
    ).dt.strftime("%Y-%m-%d")
    serie["nome_mes"] = serie["mes"].map(MESES)
    serie["situacao_dado"] = "consolidado_publicacao"
    serie.loc[serie["ano"].eq(2026), "situacao_dado"] = "parcial"
    serie = serie.sort_values(["id_territorio", "ano", "mes"]).reset_index(drop=True)
    for coluna in [
        "feminicidio_total_vitimas",
        "tentativa_feminicidio_total_vitimas",
        "homicidio_doloso_mais_feminicidio_vitimas_femininas",
    ]:
        serie[f"{coluna}_soma_movel_12m"] = (
            serie.groupby("id_territorio")[coluna]
            .transform(lambda x: x.rolling(12, min_periods=12).sum())
            .round()
            .astype("Int64")
        )
    if len(serie) != 2 * 92:
        raise ValueError(f"Série mensal com {len(serie)} linhas, esperado 184")

    completos = serie.loc[serie["ano"].between(2019, 2025)].copy()
    metricas = [
        "feminicidio_total_vitimas",
        "tentativa_feminicidio_total_vitimas",
        "homicidio_doloso_mais_feminicidio_vitimas_femininas",
    ]
    sazonal = (
        completos.groupby(["id_territorio", "territorio", "mes", "nome_mes"], as_index=False)
        .agg(
            anos_observados=("ano", "nunique"),
            feminicidio_media_mensal=("feminicidio_total_vitimas", "mean"),
            feminicidio_mediana_mensal=("feminicidio_total_vitimas", "median"),
            tentativa_media_mensal=("tentativa_feminicidio_total_vitimas", "mean"),
            tentativa_mediana_mensal=("tentativa_feminicidio_total_vitimas", "median"),
            mortes_classificadas_media_mensal=(
                "homicidio_doloso_mais_feminicidio_vitimas_femininas",
                "mean",
            ),
        )
    )
    medias_gerais = completos.groupby("id_territorio")[metricas].mean()
    for id_territorio in sazonal["id_territorio"].unique():
        alvo = sazonal["id_territorio"].eq(id_territorio)
        geral = medias_gerais.loc[id_territorio]
        sazonal.loc[alvo, "feminicidio_indice_sazonal"] = (
            sazonal.loc[alvo, "feminicidio_media_mensal"]
            .div(geral["feminicidio_total_vitimas"])
            .mul(100)
        )
        sazonal.loc[alvo, "tentativa_indice_sazonal"] = (
            sazonal.loc[alvo, "tentativa_media_mensal"]
            .div(geral["tentativa_feminicidio_total_vitimas"])
            .mul(100)
        )
        sazonal.loc[alvo, "mortes_classificadas_indice_sazonal"] = (
            sazonal.loc[alvo, "mortes_classificadas_media_mensal"]
            .div(geral["homicidio_doloso_mais_feminicidio_vitimas_femininas"])
            .mul(100)
        )
    numericas = sazonal.select_dtypes(include="number").columns.difference(
        ["mes", "anos_observados"]
    )
    sazonal[numericas] = sazonal[numericas].round(2)
    sazonal = sazonal.sort_values(["id_territorio", "mes"]).reset_index(drop=True)
    if len(sazonal) != 24:
        raise ValueError(f"Sazonalidade com {len(sazonal)} linhas, esperado 24")
    return serie, sazonal


def _homicidio_feminicidio(anual: pd.DataFrame) -> pd.DataFrame:
    chaves = [
        "ano",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "sigla_uf",
    ]
    fem = _selecionar_evento(anual, EVENTO_FEMINICIDIO, "feminicidio")
    hom = _selecionar_evento(anual, EVENTO_HOMICIDIO, "homicidio_doloso")
    resultado = hom.merge(fem, on=chaves, how="inner", validate="one_to_one")
    resultado["homicidio_doloso_mais_feminicidio_vitimas_femininas"] = (
        resultado["homicidio_doloso_vitimas_femininas"]
        + resultado["feminicidio_vitimas_femininas"]
    )
    resultado["soma_metodologicamente_permitida"] = True
    resultado["motivo"] = (
        "definicao_sinesp_de_homicidio_doloso_exclui_feminicidio"
    )
    resultado["rotulo_recomendado"] = (
        "mulheres_vitimas_de_homicidio_doloso_ou_feminicidio"
    )
    resultado["fonte_metodologia"] = FONTE_SINESP
    resultado = resultado.sort_values(["ano", "nivel_territorial", "id_territorio"])
    if len(resultado) != 8 * 28:
        raise ValueError(f"Homicídios com {len(resultado)} linhas, esperado 224")
    return resultado.reset_index(drop=True)


def _controle(
    razao: pd.DataFrame,
    tentativas: pd.DataFrame,
    municipios: pd.DataFrame,
    serie: pd.DataFrame,
    sazonalidade: pd.DataFrame,
    homicidios: pd.DataFrame,
    nao_informado: int,
) -> dict:
    def valor(dados: pd.DataFrame, ano: int, id_territorio: str, coluna: str) -> float:
        recorte = dados.loc[
            dados["ano"].eq(ano) & dados["id_territorio"].eq(id_territorio), coluna
        ]
        if len(recorte) != 1:
            raise ValueError(f"Controle não único: {ano}, {id_territorio}, {coluna}")
        return float(recorte.iloc[0])

    return {
        "gerado_em": date.today().isoformat(),
        "linhas": {
            "razao_uf": len(razao),
            "tentativas": len(tentativas),
            "municipios": len(municipios),
            "serie_mensal": len(serie),
            "sazonalidade": len(sazonalidade),
            "homicidios": len(homicidios),
        },
        "controles": {
            "razao_brasil_2019": valor(
                razao, 2019, "BR", "razao_feminicidios_total_sobre_sim"
            ),
            "razao_brasil_2024": valor(
                razao, 2024, "BR", "razao_feminicidios_total_sobre_sim"
            ),
            "razao_sc_2019": valor(
                razao, 2019, "SC", "razao_feminicidios_total_sobre_sim"
            ),
            "razao_sc_2024": valor(
                razao, 2024, "SC", "razao_feminicidios_total_sobre_sim"
            ),
            "tentativas_brasil_2019": int(
                valor(tentativas, 2019, "BR", "tentativa_feminicidio_total_vitimas")
            ),
            "tentativas_brasil_2025": int(
                valor(tentativas, 2025, "BR", "tentativa_feminicidio_total_vitimas")
            ),
            "feminicidios_sc_2019_2024": int(municipios["feminicidios_total"].sum()),
            "sinesp_sc_nao_informado_2019_2024": nao_informado,
            "soma_homicidio_doloso_feminicidio_permitida": bool(
                homicidios["soma_metodologicamente_permitida"].all()
            ),
        },
        "fonte_metodologia_sinesp": FONTE_SINESP,
    }


def _relatorio(
    razao: pd.DataFrame,
    tentativas: pd.DataFrame,
    municipios: pd.DataFrame,
    sazonalidade: pd.DataFrame,
    homicidios: pd.DataFrame,
) -> str:
    def linha(dados: pd.DataFrame, ano: int, id_territorio: str) -> pd.Series:
        return dados.loc[
            dados["ano"].eq(ano) & dados["id_territorio"].eq(id_territorio)
        ].iloc[0]

    br19 = linha(razao, 2019, "BR")
    br24 = linha(razao, 2024, "BR")
    sc19 = linha(razao, 2019, "SC")
    sc24 = linha(razao, 2024, "SC")
    br_t19 = linha(tentativas, 2019, "BR")
    br_t25 = linha(tentativas, 2025, "BR")
    sc_t25 = linha(tentativas, 2025, "SC")
    top_municipios = municipios.loc[municipios["dado_suficiente"]].head(5)
    lista_municipios = ", ".join(
        f"{r.municipio} ({int(r.feminicidios_total)})" for r in top_municipios.itertuples()
    )
    picos = {}
    for territorio in ["BR", "SC"]:
        base = sazonalidade.loc[sazonalidade["id_territorio"].eq(territorio)]
        picos[territorio] = base.loc[base["feminicidio_indice_sazonal"].idxmax()]
    soma_ok = bool(homicidios["soma_metodologicamente_permitida"].all())

    return f"""# Análises do Sinesp integradas ao SIM

Atualizado em {date.today().isoformat()}.

O painel não foi alterado nem publicado nesta etapa.

## Razão entre Sinesp e SIM

1. No Brasil, a razão entre feminicídios publicados pelo Sinesp e mortes de mulheres por agressão no SIM passou de {_formatar_decimal(br19.razao_feminicidios_total_sobre_sim)} em 2019 para {_formatar_decimal(br24.razao_feminicidios_total_sobre_sim)} em 2024.
2. Em Santa Catarina, a razão passou de {_formatar_decimal(sc19.razao_feminicidios_total_sobre_sim)} para {_formatar_decimal(sc24.razao_feminicidios_total_sobre_sim)}.
3. A tabela inclui as 27 UFs, Brasil, valores absolutos, taxas e ranking anual.
4. A razão deve ser lida como indicador contextual. O SIM usa residência da vítima e o Sinesp usa município do fato.

## Tentativas e feminicídios consumados

1. O Brasil registrou {_formatar_inteiro(br_t19.tentativa_feminicidio_total_vitimas)} tentativas em 2019 e {_formatar_inteiro(br_t25.tentativa_feminicidio_total_vitimas)} em 2025.
2. Santa Catarina registrou {_formatar_inteiro(sc_t25.tentativa_feminicidio_total_vitimas)} tentativas e {_formatar_inteiro(sc_t25.feminicidio_total_vitimas)} feminicídios em 2025, razão de {_formatar_decimal(sc_t25.tentativas_por_feminicidio)} tentativas por feminicídio.
3. O indicador representa registros classificados pela segurança pública. Ele não deve ser descrito como número de mortes evitadas.

## Taxas municipais plurianuais

1. A taxa usa feminicídios de 2019 a 2024 divididos pela soma da população feminina dos mesmos seis anos.
2. A tabela contém os 295 municípios de Santa Catarina.
3. Municípios com menos de cinco vítimas não recebem ranking de taxa.
4. Os cinco maiores números absolutos entre os municípios com dado suficiente são: {lista_municipios}.

## Sazonalidade

1. A série mensal cobre 2019 a 2025 completos e janeiro a agosto de 2026.
2. O maior índice sazonal de feminicídio do Brasil ocorre em {picos['BR'].nome_mes}, com índice {_formatar_decimal(picos['BR'].feminicidio_indice_sazonal, 1)}.
3. Em Santa Catarina, o maior índice ocorre em {picos['SC'].nome_mes}, com índice {_formatar_decimal(picos['SC'].feminicidio_indice_sazonal, 1)}.
4. O índice compara a média de cada mês com a média mensal geral de 2019 a 2025. Ele descreve a série e não identifica causas.
5. Em Santa Catarina, os números mensais são pequenos e o índice pode variar muito com poucos casos.

## Homicídio doloso e feminicídio

1. A documentação oficial define homicídio doloso com exclusão explícita de feminicídio.
2. A soma das duas categorias é metodologicamente permitida no conjunto atual: {"sim" if soma_ok else "não"}.
3. O rótulo recomendado é “mulheres vítimas de homicídio doloso ou feminicídio”. Os dois componentes devem permanecer visíveis.
4. A soma não inclui todas as mortes violentas intencionais. Latrocínio, lesão corporal seguida de morte e outras categorias permanecem separadas.

Fonte metodológica oficial: {FONTE_SINESP}

## Arquivos produzidos

1. `data/gold/integrado/razao_sim_sinesp_uf_2019_2024.csv`
2. `data/gold/integrado/tentativa_feminicidio_2019_2026.csv`
3. `data/gold/integrado/taxa_municipal_feminicidio_sc_2019_2024.csv`
4. `data/gold/integrado/sinesp_serie_mensal_2019_2026.csv`
5. `data/gold/integrado/sinesp_sazonalidade_mes_2019_2025.csv`
6. `data/gold/integrado/homicidio_doloso_feminicidio_2019_2026.csv`

## Reprodução

Execute `python pipeline/build_sinesp_analysis.py` depois de atualizar as camadas Silver.
"""


def main() -> None:
    sinesp, sim, populacao = _carregar()
    mensal = _agregar_eventos(sinesp)
    anual = _anual(mensal)
    razao = _razao_sim_sinesp(anual, sim, populacao)
    tentativas = _tentativas_consumados(anual)
    municipios, nao_informado = _municipios_sc(sinesp, populacao)
    serie, sazonalidade = _serie_mensal(mensal)
    homicidios = _homicidio_feminicidio(anual)
    resumo = _controle(
        razao,
        tentativas,
        municipios,
        serie,
        sazonalidade,
        homicidios,
        nao_informado,
    )

    DESTINO.mkdir(parents=True, exist_ok=True)
    razao.to_csv(RAZAO_UF, index=False, encoding="utf-8-sig")
    tentativas.to_csv(TENTATIVAS, index=False, encoding="utf-8-sig")
    municipios.to_csv(MUNICIPIOS, index=False, encoding="utf-8-sig")
    serie.to_csv(SERIE_MENSAL, index=False, encoding="utf-8-sig")
    sazonalidade.to_csv(SAZONALIDADE, index=False, encoding="utf-8-sig")
    homicidios.to_csv(HOMICIDIOS, index=False, encoding="utf-8-sig")
    RESUMO.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    RELATORIO.write_text(
        _relatorio(razao, tentativas, municipios, sazonalidade, homicidios),
        encoding="utf-8",
    )

    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(f"Relatório: {RELATORIO}")


if __name__ == "__main__":
    main()
