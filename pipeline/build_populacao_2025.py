"""Prepara os denominadores municipais de 2025 usados nas taxas do atlas.

A população total é a estimativa oficial do IBGE para 1º de julho de 2025.
A população por sexo é estimada aplicando a proporção municipal de 2024 à
população total de 2025. Para município criado em 2025, usa-se a proporção da
respectiva unidade da federação em 2024.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
URL = "https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/POP2025_20260828.xls"
FONTE = ROOT / "data" / "bronze" / "ibge" / "POP2025_20260828.xls"
POP_TOTAL_2024 = ROOT / "data" / "silver" / "populacao_municipio_ano.parquet"
POP_SEXO_2024 = ROOT / "data" / "silver" / "populacao_municipio_sexo_ano.parquet"
DESTINO = ROOT / "data" / "silver" / "populacao_municipio_2025.parquet"

TOTAL_BRASIL_2025 = 213_421_037
TOTAL_SC_2025 = 8_187_029


def baixar() -> None:
    if FONTE.exists():
        return
    FONTE.parent.mkdir(parents=True, exist_ok=True)
    temporario = FONTE.with_suffix(FONTE.suffix + ".part")
    urllib.request.urlretrieve(URL, temporario)
    temporario.replace(FONTE)


def reparar_nome(texto: object) -> str:
    valor = str(texto)
    try:
        return valor.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return valor


def ler_estimativas_ibge() -> pd.DataFrame:
    bruto = pd.read_excel(FONTE, sheet_name=1, header=1, dtype=str).iloc[:, :5]
    bruto.columns = ["sigla_uf", "codigo_uf", "codigo_municipio", "municipio", "populacao"]
    valido = (
        bruto.sigla_uf.str.fullmatch(r"[A-Z]{2}", na=False)
        & bruto.codigo_uf.str.fullmatch(r"\d{2}", na=False)
        & bruto.codigo_municipio.str.fullmatch(r"\d{5}", na=False)
        & bruto.populacao.str.fullmatch(r"\d+", na=False)
    )
    dados = bruto.loc[valido].copy()
    dados["id_municipio"] = dados.codigo_uf + dados.codigo_municipio
    dados["municipio"] = dados.municipio.map(reparar_nome)
    dados["populacao"] = dados.populacao.astype("int64")
    dados["ano"] = 2025
    return dados[["ano", "id_municipio", "municipio", "sigla_uf", "populacao"]]


def proporcoes_2024() -> tuple[pd.DataFrame, pd.DataFrame]:
    total = pd.read_parquet(POP_TOTAL_2024)
    total = total.loc[total.ano.eq(2024), ["id_municipio", "sigla_uf", "populacao"]]
    sexo = pd.read_parquet(POP_SEXO_2024)
    sexo = sexo.loc[
        sexo.ano.eq(2024) & sexo.sexo.eq("feminino"),
        ["id_municipio", "populacao"],
    ].rename(columns={"populacao": "populacao_feminina"})
    municipal = total.merge(sexo, on="id_municipio", how="inner", validate="one_to_one")
    municipal["proporcao_feminina_2024"] = (
        municipal.populacao_feminina / municipal.populacao
    )
    uf = municipal.groupby("sigla_uf", as_index=False).agg(
        populacao=("populacao", "sum"),
        populacao_feminina=("populacao_feminina", "sum"),
    )
    uf["proporcao_feminina_uf_2024"] = uf.populacao_feminina / uf.populacao
    return (
        municipal[["id_municipio", "proporcao_feminina_2024"]],
        uf[["sigla_uf", "proporcao_feminina_uf_2024"]],
    )


def construir() -> pd.DataFrame:
    dados = ler_estimativas_ibge()
    nomes_2024 = (
        pd.read_parquet(POP_TOTAL_2024, columns=["id_municipio", "municipio"])
        .drop_duplicates("id_municipio")
        .rename(columns={"municipio": "municipio_2024"})
    )
    dados = dados.merge(nomes_2024, on="id_municipio", how="left", validate="one_to_one")
    dados["municipio"] = dados.municipio_2024.fillna(dados.municipio)
    dados = dados.drop(columns="municipio_2024")
    proporcao_municipal, proporcao_uf = proporcoes_2024()
    dados = dados.merge(proporcao_municipal, on="id_municipio", how="left", validate="one_to_one")
    dados = dados.merge(proporcao_uf, on="sigla_uf", how="left", validate="many_to_one")
    dados["proporcao_feminina_usada"] = dados.proporcao_feminina_2024.fillna(
        dados.proporcao_feminina_uf_2024
    )
    if dados.proporcao_feminina_usada.isna().any():
        raise ValueError("Município sem proporção feminina de referência")
    dados["populacao_feminina_estimada"] = (
        dados.populacao * dados.proporcao_feminina_usada
    ).round().astype("int64")
    dados["populacao_masculina_estimada"] = (
        dados.populacao - dados.populacao_feminina_estimada
    ).astype("int64")
    dados["tipo_denominador_sexo"] = "estimado_proporcao_2024"
    return dados[
        [
            "ano", "id_municipio", "municipio", "sigla_uf", "populacao",
            "populacao_feminina_estimada", "populacao_masculina_estimada",
            "tipo_denominador_sexo",
        ]
    ].sort_values("id_municipio").reset_index(drop=True)


def validar(dados: pd.DataFrame) -> None:
    if len(dados) != 5_571:
        raise ValueError(f"Esperados 5.571 municípios em 2025, encontrados {len(dados)}")
    if dados.id_municipio.duplicated().any():
        raise ValueError("Código municipal duplicado em 2025")
    if int(dados.populacao.sum()) != TOTAL_BRASIL_2025:
        raise ValueError("Total Brasil de 2025 divergente da publicação do IBGE")
    sc = dados.loc[dados.sigla_uf.eq("SC")]
    if len(sc) != 295 or int(sc.populacao.sum()) != TOTAL_SC_2025:
        raise ValueError("Cobertura municipal de Santa Catarina divergente")
    soma_sexos = dados.populacao_feminina_estimada + dados.populacao_masculina_estimada
    if not soma_sexos.eq(dados.populacao).all():
        raise ValueError("Estimativas por sexo não fecham com a população total")


def main() -> None:
    baixar()
    for caminho in [POP_TOTAL_2024, POP_SEXO_2024]:
        if not caminho.exists():
            raise FileNotFoundError(caminho)
    dados = construir()
    validar(dados)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    dados.to_parquet(DESTINO, index=False)
    print(f"População 2025: {DESTINO} ({len(dados)} municípios)")
    print(f"Santa Catarina: {int(dados.loc[dados.sigla_uf.eq('SC'), 'populacao'].sum())}")


if __name__ == "__main__":
    main()
