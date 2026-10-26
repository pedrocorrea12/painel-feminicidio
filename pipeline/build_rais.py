"""Constroi as camadas Silver e Gold da RAIS por sexo e cor ou raca."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "data" / "bronze" / "rais" / "obsref"
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold" / "rais"

ARQ_UF = BRONZE / "rais_br_uf_sexo_raca.csv"
ARQ_MUNICIPIO = BRONZE / "rais_sc_municipio_sexo_raca.csv"
ARQ_ESCOLARIDADE = BRONZE / "rais_br_uf_sexo_raca_escolaridade.csv"
ARQ_MOVIMENTO = BRONZE / "rais_br_uf_mes_sexo_raca_admissoes_desligamentos.csv"
MUNICIPIOS = ROOT / "data" / "bronze" / "ibge" / "municipios_brasil.json"
CENSO_UF = ROOT / "data" / "gold" / "ibge" / "censo2022_mulheres_cor_raca_uf.csv"
CENSO_MUNICIPIOS = ROOT / "data" / "gold" / "ibge" / "censo2022_mulheres_cor_raca_municipios_sc.csv"
POPULACAO = SILVER / "populacao_feminina_municipio.parquet"

SILVER_ESTOQUE = SILVER / "rais_vinculos_raca_sexo.parquet"
SILVER_MOVIMENTO = SILVER / "rais_movimentacao_mensal.parquet"
SILVER_ESCOLARIDADE = SILVER / "rais_escolaridade_raca_sexo.parquet"

GOLD_SEXO = GOLD / "emprego_formal_sexo_2019_2025.csv"
GOLD_SEXO_MUNICIPIOS = GOLD / "emprego_formal_sexo_municipios_sc_2019_2025.csv"
GOLD_MOVIMENTO = GOLD / "movimentacao_mensal_sexo_2019_2025.csv"
GOLD_INSERCAO = GOLD / "insercao_formal_mulheres_negras_2024_2025.csv"
GOLD_SALARIO_RACA = GOLD / "razao_salarial_raca_2024_2025.csv"
GOLD_SALARIO_RACA_MUNICIPIOS = GOLD / "razao_salarial_raca_municipios_sc_2024_2025.csv"
GOLD_ESCOLARIDADE = GOLD / "escolaridade_mulheres_raca_2024_2025.csv"
GOLD_QUALIDADE = GOLD / "qualidade_raca_rais_2024_2025.csv"
GOLD_RESUMO = GOLD / "resumo_rais.json"

RACA_PROJETO = {1: 5, 2: 1, 4: 2, 6: 3, 8: 4, 9: 9, 99: 9}
RACA_ROTULO = {
    1: "Branca",
    2: "Preta",
    3: "Amarela",
    4: "Parda",
    5: "Indígena",
    9: "Não identificada",
}
SEXO_ROTULO = {1: "Masculino", 2: "Feminino"}
ESCOLARIDADE_ROTULO = {
    1: "Analfabeto",
    2: "Até 5 ano incompleto",
    3: "5 ano completo",
    4: "6 a 9 ano incompleto",
    5: "Fundamental completo",
    6: "Médio incompleto",
    7: "Médio completo",
    8: "Superior incompleto",
    9: "Superior completo",
    10: "Mestrado",
    11: "Doutorado",
}


def _verificar_arquivos() -> None:
    caminhos = [
        ARQ_UF, ARQ_MUNICIPIO, ARQ_ESCOLARIDADE, ARQ_MOVIMENTO,
        MUNICIPIOS, CENSO_UF, CENSO_MUNICIPIOS, POPULACAO,
    ]
    ausentes = [str(c.relative_to(ROOT)) for c in caminhos if not c.exists()]
    if ausentes:
        raise FileNotFoundError(f"Arquivos ausentes: {ausentes}")


def _mapa_municipios() -> pd.DataFrame:
    registros = json.loads(MUNICIPIOS.read_text(encoding="utf-8"))
    linhas = []
    for item in registros:
        codigo = str(item.get("id", "")).zfill(7)
        if len(codigo) != 7:
            continue
        linhas.append(
            {
                "id_municipio_6d": codigo[:6],
                "id_municipio": codigo,
            }
        )
    mapa = pd.DataFrame(linhas).drop_duplicates("id_municipio_6d")
    if mapa["id_municipio_6d"].duplicated().any():
        raise ValueError("Mapa municipal com codigo de seis digitos duplicado")
    nomes = (
        pd.read_parquet(POPULACAO, columns=["id_municipio", "municipio", "sigla_uf"])
        .loc[lambda x: x.sigla_uf.eq("SC"), ["id_municipio", "municipio"]]
        .drop_duplicates()
        .rename(columns={"municipio": "municipio_canonico"})
    )
    return mapa.merge(nomes, on="id_municipio", how="left", validate="one_to_one")


def _normalizar_dimensoes(dados: pd.DataFrame) -> pd.DataFrame:
    dados = dados.loc[dados["cd_sexo"].isin([1, 2])].copy()
    dados["cd_raca_original"] = dados["cd_raca"].astype("int16")
    dados["cd_raca"] = dados["cd_raca_original"].map(RACA_PROJETO).astype("int8")
    dados["raca"] = dados["cd_raca"].map(RACA_ROTULO)
    dados["sexo"] = dados["cd_sexo"].map(SEXO_ROTULO)
    dados["raca_negra"] = dados["cd_raca"].isin([2, 4])
    dados["raca_identificada"] = dados["cd_raca"].ne(9)
    dados["raca_usavel"] = dados["ano"].ge(2024)
    return dados


def _silver_estoque(mapa: pd.DataFrame) -> pd.DataFrame:
    uf = pd.read_csv(ARQ_UF)
    uf = _normalizar_dimensoes(uf)
    uf["nivel_territorial"] = uf["sigla_uf"].map(lambda x: "brasil" if x == "BR" else "uf")
    uf["id_territorio"] = uf["sigla_uf"]
    uf["territorio"] = uf["sigla_uf"].map(lambda x: "Brasil" if x == "BR" else x)
    uf["id_municipio"] = pd.Series([None] * len(uf), dtype="string")

    municipio = pd.read_csv(ARQ_MUNICIPIO, dtype={"id_municipio_6d": "string"})
    municipio["id_municipio_6d"] = municipio["id_municipio_6d"].str.zfill(6)
    municipio = municipio.merge(mapa, on="id_municipio_6d", how="left", validate="many_to_one")
    if municipio["id_municipio"].isna().any():
        faltantes = municipio.loc[municipio.id_municipio.isna(), "id_municipio_6d"].unique().tolist()
        raise ValueError(f"Municipios da RAIS sem codigo de sete digitos: {faltantes[:10]}")
    municipio["municipio"] = municipio["municipio_canonico"].fillna(municipio["municipio"])
    municipio = _normalizar_dimensoes(municipio)
    municipio["nivel_territorial"] = "municipio"
    municipio["id_territorio"] = municipio["id_municipio"]
    municipio["territorio"] = municipio["municipio"]
    municipio["sigla_uf"] = "SC"

    colunas = [
        "ano", "nivel_territorial", "id_territorio", "territorio", "sigla_uf",
        "id_municipio", "cd_sexo", "sexo", "cd_raca_original", "cd_raca", "raca",
        "raca_negra", "raca_identificada", "raca_usavel", "qt_vinculos",
        "qt_vinculos_18_64", "qt_com_remuneracao", "vl_rem_dez_soma",
        "vl_rem_dez_media", "vl_rem_dez_mediana",
    ]
    uf["vl_rem_media_ano_media"] = uf.get("vl_rem_media_ano_media")
    municipio["vl_rem_media_ano_media"] = float("nan")
    colunas.append("vl_rem_media_ano_media")
    estoque = pd.concat([uf[colunas], municipio[colunas]], ignore_index=True)
    estoque["id_municipio"] = estoque["id_municipio"].astype("string")
    return estoque.sort_values(
        ["ano", "nivel_territorial", "id_territorio", "cd_sexo", "cd_raca"]
    ).reset_index(drop=True)


def _silver_movimento() -> pd.DataFrame:
    movimento = pd.read_csv(ARQ_MOVIMENTO)
    movimento = _normalizar_dimensoes(movimento)
    movimento["nivel_territorial"] = movimento["sigla_uf"].map(
        lambda x: "brasil" if x == "BR" else "uf"
    )
    movimento["id_territorio"] = movimento["sigla_uf"]
    movimento["territorio"] = movimento["sigla_uf"].map(
        lambda x: "Brasil" if x == "BR" else x
    )
    colunas = [
        "ano", "mes", "nivel_territorial", "id_territorio", "territorio", "sigla_uf",
        "cd_sexo", "sexo", "cd_raca_original", "cd_raca", "raca", "raca_negra",
        "raca_identificada", "raca_usavel", "qt_admissoes", "qt_desligamentos",
        "qt_desligamentos_sem_justa_causa", "saldo",
    ]
    return movimento[colunas].sort_values(
        ["ano", "mes", "nivel_territorial", "id_territorio", "cd_sexo", "cd_raca"]
    ).reset_index(drop=True)


def _silver_escolaridade() -> pd.DataFrame:
    escolaridade = pd.read_csv(ARQ_ESCOLARIDADE)
    escolaridade = escolaridade.loc[escolaridade["cd_escolaridade"].isin(ESCOLARIDADE_ROTULO)].copy()
    escolaridade = _normalizar_dimensoes(escolaridade)
    escolaridade["escolaridade"] = escolaridade["cd_escolaridade"].map(ESCOLARIDADE_ROTULO)
    escolaridade["nivel_territorial"] = escolaridade["sigla_uf"].map(
        lambda x: "brasil" if x == "BR" else "uf"
    )
    escolaridade["id_territorio"] = escolaridade["sigla_uf"]
    escolaridade["territorio"] = escolaridade["sigla_uf"].map(
        lambda x: "Brasil" if x == "BR" else x
    )
    colunas = [
        "ano", "nivel_territorial", "id_territorio", "territorio", "sigla_uf",
        "cd_sexo", "sexo", "cd_raca_original", "cd_raca", "raca", "raca_negra",
        "raca_identificada", "raca_usavel", "cd_escolaridade", "escolaridade",
        "qt_vinculos", "qt_vinculos_18_64", "qt_com_remuneracao",
        "vl_rem_dez_soma", "vl_rem_dez_media", "vl_rem_dez_mediana",
    ]
    return escolaridade[colunas].sort_values(
        ["ano", "nivel_territorial", "id_territorio", "cd_sexo", "cd_raca", "cd_escolaridade"]
    ).reset_index(drop=True)


def _agregar_sexo(estoque: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    base = (
        estoque.groupby(chaves + ["cd_sexo", "sexo"], as_index=False)
        .agg(
            qt_vinculos=("qt_vinculos", "sum"),
            qt_com_remuneracao=("qt_com_remuneracao", "sum"),
            vl_rem_dez_soma=("vl_rem_dez_soma", "sum"),
        )
    )
    base["remuneracao_dezembro_media"] = (
        base["vl_rem_dez_soma"]
        .div(base["qt_com_remuneracao"].where(base["qt_com_remuneracao"].ne(0)))
        .round(2)
    )
    indice = chaves
    largo = base.pivot(index=indice, columns="cd_sexo")
    resultado = largo.reset_index()
    resultado.columns = [
        "_".join(str(p) for p in coluna if str(p) != "").rstrip("_")
        if isinstance(coluna, tuple) else str(coluna)
        for coluna in resultado.columns
    ]
    renomear = {
        "qt_vinculos_1": "vinculos_homens",
        "qt_vinculos_2": "vinculos_mulheres",
        "qt_com_remuneracao_1": "homens_com_remuneracao",
        "qt_com_remuneracao_2": "mulheres_com_remuneracao",
        "vl_rem_dez_soma_1": "remuneracao_soma_homens",
        "vl_rem_dez_soma_2": "remuneracao_soma_mulheres",
        "remuneracao_dezembro_media_1": "remuneracao_media_homens",
        "remuneracao_dezembro_media_2": "remuneracao_media_mulheres",
    }
    resultado = resultado.rename(columns=renomear)
    resultado["vinculos_total"] = resultado["vinculos_homens"] + resultado["vinculos_mulheres"]
    resultado["participacao_feminina_pct"] = (
        resultado["vinculos_mulheres"].div(resultado["vinculos_total"]).mul(100).round(2)
    )
    suficiente = (
        resultado["homens_com_remuneracao"].ge(100)
        & resultado["mulheres_com_remuneracao"].ge(100)
    )
    resultado["razao_salarial_mulher_homem"] = (
        resultado["remuneracao_media_mulheres"]
        .div(resultado["remuneracao_media_homens"])
        .where(suficiente)
        .round(3)
    )
    resultado["piso_100_com_remuneracao_atendido"] = suficiente
    return resultado


def _gold_sexo(estoque: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    anual = estoque.loc[estoque["nivel_territorial"].isin(["brasil", "uf"])].copy()
    sexo = _agregar_sexo(
        anual,
        ["ano", "nivel_territorial", "id_territorio", "territorio", "sigla_uf"],
    )
    municipal = estoque.loc[estoque["nivel_territorial"].eq("municipio")].copy()
    municipal = _agregar_sexo(
        municipal,
        ["nivel_territorial", "id_territorio", "territorio", "sigla_uf"],
    )
    municipal["periodo_inicio"] = 2019
    municipal["periodo_fim"] = 2025
    municipal["anos_periodo"] = 7
    return sexo, municipal


def _gold_movimento(movimento: pd.DataFrame) -> pd.DataFrame:
    agregado = (
        movimento.groupby(
            ["ano", "mes", "nivel_territorial", "id_territorio", "territorio", "sigla_uf", "cd_sexo", "sexo"],
            as_index=False,
        )
        .agg(
            admissoes=("qt_admissoes", "sum"),
            desligamentos=("qt_desligamentos", "sum"),
            desligamentos_sem_justa_causa=("qt_desligamentos_sem_justa_causa", "sum"),
            saldo=("saldo", "sum"),
        )
    )
    if not (agregado["admissoes"] - agregado["desligamentos"]).eq(agregado["saldo"]).all():
        raise ValueError("Saldo mensal da RAIS nao reconcilia")
    return agregado.sort_values(["ano", "mes", "id_territorio", "cd_sexo"]).reset_index(drop=True)


def _qualidade_raca(estoque: pd.DataFrame) -> pd.DataFrame:
    base = estoque.loc[
        estoque["nivel_territorial"].isin(["brasil", "uf"]) & estoque["ano"].between(2024, 2025)
    ].copy()
    resultado = (
        base.groupby(["ano", "nivel_territorial", "id_territorio", "territorio", "sigla_uf"], as_index=False)
        .apply(
            lambda x: pd.Series(
                {
                    "vinculos_total": int(x.qt_vinculos.sum()),
                    "vinculos_raca_identificada": int(x.loc[x.raca_identificada, "qt_vinculos"].sum()),
                    "vinculos_raca_nao_identificada": int(x.loc[~x.raca_identificada, "qt_vinculos"].sum()),
                }
            ),
            include_groups=False,
        )
        .reset_index(drop=True)
    )
    resultado["pct_raca_nao_identificada"] = (
        resultado["vinculos_raca_nao_identificada"].div(resultado["vinculos_total"]).mul(100).round(2)
    )
    resultado["flag_cautela_acima_10pct"] = resultado["pct_raca_nao_identificada"].gt(10)
    return resultado


def _gold_insercao(estoque: pd.DataFrame, qualidade: pd.DataFrame) -> pd.DataFrame:
    base = estoque.loc[
        estoque["nivel_territorial"].isin(["brasil", "uf"])
        & estoque["ano"].between(2024, 2025)
        & estoque["cd_sexo"].eq(2)
    ].copy()
    linhas = []
    chaves = ["ano", "nivel_territorial", "id_territorio", "territorio", "sigla_uf"]
    for chave, grupo in base.groupby(chaves, sort=False):
        identificadas = grupo.loc[grupo.raca_identificada, "qt_vinculos"].sum()
        negras = grupo.loc[grupo.raca_negra, "qt_vinculos"].sum()
        linhas.append(dict(zip(chaves, chave)) | {
            "mulheres_vinculos": int(grupo.qt_vinculos.sum()),
            "mulheres_raca_identificada": int(identificadas),
            "mulheres_negras_vinculos": int(negras),
            "pct_mulheres_negras_rais": round(100 * negras / identificadas, 2) if identificadas else None,
        })
    resultado = pd.DataFrame(linhas)
    censo = pd.read_csv(CENSO_UF)
    censo = censo[["sigla_uf", "pct_negras_censo"]]
    resultado = resultado.merge(censo, on="sigla_uf", how="left", validate="many_to_one")
    resultado["indice_insercao_formal_mulheres_negras"] = (
        resultado["pct_mulheres_negras_rais"].div(resultado["pct_negras_censo"]).round(3)
    )
    resultado = resultado.merge(
        qualidade[["ano", "id_territorio", "pct_raca_nao_identificada", "flag_cautela_acima_10pct"]],
        on=["ano", "id_territorio"], how="left", validate="one_to_one",
    )
    return resultado.sort_values(["ano", "id_territorio"]).reset_index(drop=True)


def _salario_raca(estoque: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    base = estoque.loc[estoque["ano"].between(2024, 2025) & estoque["raca_identificada"]].copy()
    linhas = []
    for chave, grupo in base.groupby(chaves, sort=False):
        def media(sexo: int, racas: list[int]) -> tuple[int, float | None]:
            recorte = grupo.loc[grupo.cd_sexo.eq(sexo) & grupo.cd_raca.isin(racas)]
            quantidade = int(recorte.qt_com_remuneracao.sum())
            valor = float(recorte.vl_rem_dez_soma.sum() / quantidade) if quantidade else None
            return quantidade, valor

        mulheres_negras_n, mulheres_negras = media(2, [2, 4])
        homens_brancos_n, homens_brancos = media(1, [1])
        mulheres_brancas_n, mulheres_brancas = media(2, [1])
        piso = min(mulheres_negras_n, homens_brancos_n, mulheres_brancas_n) >= 100
        registro = dict(zip(chaves, chave))
        registro.update(
            {
                "mulheres_negras_com_remuneracao": mulheres_negras_n,
                "homens_brancos_com_remuneracao": homens_brancos_n,
                "mulheres_brancas_com_remuneracao": mulheres_brancas_n,
                "remuneracao_media_mulheres_negras": round(mulheres_negras, 2) if mulheres_negras else None,
                "remuneracao_media_homens_brancos": round(homens_brancos, 2) if homens_brancos else None,
                "remuneracao_media_mulheres_brancas": round(mulheres_brancas, 2) if mulheres_brancas else None,
                "razao_mulheres_negras_homens_brancos": round(mulheres_negras / homens_brancos, 3) if piso else None,
                "razao_mulheres_negras_mulheres_brancas": round(mulheres_negras / mulheres_brancas, 3) if piso else None,
                "piso_100_com_remuneracao_atendido": piso,
            }
        )
        linhas.append(registro)
    return pd.DataFrame(linhas)


def _gold_salario_raca(estoque: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    territorial = _salario_raca(
        estoque.loc[estoque.nivel_territorial.isin(["brasil", "uf"])],
        ["ano", "nivel_territorial", "id_territorio", "territorio", "sigla_uf"],
    )
    municipal = estoque.loc[
        estoque.nivel_territorial.eq("municipio") & estoque.ano.between(2024, 2025)
    ].copy()
    municipal = _salario_raca(
        municipal,
        ["nivel_territorial", "id_territorio", "territorio", "sigla_uf"],
    )
    municipal["periodo_inicio"] = 2024
    municipal["periodo_fim"] = 2025
    return territorial, municipal


def _gold_escolaridade(escolaridade: pd.DataFrame) -> pd.DataFrame:
    base = escolaridade.loc[
        escolaridade["ano"].between(2024, 2025)
        & escolaridade["cd_sexo"].eq(2)
        & escolaridade["raca_identificada"]
    ].copy()
    base["grupo_raca"] = base["cd_raca"].map(
        lambda x: "Negra" if x in [2, 4] else RACA_ROTULO[x]
    )
    chaves = [
        "ano", "nivel_territorial", "id_territorio", "territorio", "sigla_uf",
        "grupo_raca", "cd_escolaridade", "escolaridade",
    ]
    resultado = base.groupby(chaves, as_index=False).agg(vinculos=("qt_vinculos", "sum"))
    totais = resultado.groupby(
        ["ano", "id_territorio", "grupo_raca"], as_index=False
    ).agg(vinculos_grupo_raca=("vinculos", "sum"))
    resultado = resultado.merge(
        totais, on=["ano", "id_territorio", "grupo_raca"], validate="many_to_one"
    )
    resultado["distribuicao_escolaridade_pct"] = (
        resultado["vinculos"].div(resultado["vinculos_grupo_raca"]).mul(100).round(2)
    )
    return resultado.sort_values(
        ["ano", "id_territorio", "grupo_raca", "cd_escolaridade"]
    ).reset_index(drop=True)


def _conferencias(estoque: pd.DataFrame) -> dict:
    uf = estoque.loc[estoque.nivel_territorial.eq("uf")]
    br = estoque.loc[estoque.nivel_territorial.eq("brasil")]
    por_uf = uf.groupby("ano")["qt_vinculos"].sum()
    por_br = br.groupby("ano")["qt_vinculos"].sum()
    if not por_uf.eq(por_br).all():
        raise ValueError("A linha Brasil da RAIS difere da soma das UFs")
    sc = uf.loc[uf.sigla_uf.eq("SC")].groupby("ano")["qt_vinculos"].sum()
    if int(sc.loc[2019]) != 2_319_210 or int(sc.loc[2025]) != 2_949_150:
        raise ValueError("Controles de estoque da RAIS em Santa Catarina divergentes")
    return {
        "brasil_igual_soma_ufs": True,
        "sc_vinculos_2019": int(sc.loc[2019]),
        "sc_vinculos_2025": int(sc.loc[2025]),
    }


def main() -> None:
    _verificar_arquivos()
    mapa = _mapa_municipios()
    estoque = _silver_estoque(mapa)
    movimento = _silver_movimento()
    escolaridade = _silver_escolaridade()
    controles = _conferencias(estoque)

    SILVER.mkdir(parents=True, exist_ok=True)
    estoque.to_parquet(SILVER_ESTOQUE, index=False)
    movimento.to_parquet(SILVER_MOVIMENTO, index=False)
    escolaridade.to_parquet(SILVER_ESCOLARIDADE, index=False)

    sexo, sexo_municipios = _gold_sexo(estoque)
    movimento_gold = _gold_movimento(movimento)
    qualidade = _qualidade_raca(estoque)
    insercao = _gold_insercao(estoque, qualidade)
    salario_raca, salario_raca_municipios = _gold_salario_raca(estoque)
    escolaridade_gold = _gold_escolaridade(escolaridade)

    GOLD.mkdir(parents=True, exist_ok=True)
    sexo.to_csv(GOLD_SEXO, index=False, encoding="utf-8-sig")
    sexo_municipios.to_csv(GOLD_SEXO_MUNICIPIOS, index=False, encoding="utf-8-sig")
    movimento_gold.to_csv(GOLD_MOVIMENTO, index=False, encoding="utf-8-sig")
    insercao.to_csv(GOLD_INSERCAO, index=False, encoding="utf-8-sig")
    salario_raca.to_csv(GOLD_SALARIO_RACA, index=False, encoding="utf-8-sig")
    salario_raca_municipios.to_csv(GOLD_SALARIO_RACA_MUNICIPIOS, index=False, encoding="utf-8-sig")
    escolaridade_gold.to_csv(GOLD_ESCOLARIDADE, index=False, encoding="utf-8-sig")
    qualidade.to_csv(GOLD_QUALIDADE, index=False, encoding="utf-8-sig")

    resumo = {
        "gerado_em": date.today().isoformat(),
        "periodo": [2019, 2025],
        "raca_usavel": [2024, 2025],
        "controles": controles,
        "linhas": {
            "silver_estoque": len(estoque),
            "silver_movimento": len(movimento),
            "silver_escolaridade": len(escolaridade),
            "gold_sexo": len(sexo),
            "gold_sexo_municipios": len(sexo_municipios),
            "gold_movimento": len(movimento_gold),
            "gold_insercao": len(insercao),
            "gold_salario_raca": len(salario_raca),
            "gold_salario_raca_municipios": len(salario_raca_municipios),
            "gold_escolaridade": len(escolaridade_gold),
            "gold_qualidade": len(qualidade),
        },
    }
    GOLD_RESUMO.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
