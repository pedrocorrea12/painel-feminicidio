"""Baixa e prepara a populacao feminina municipal do Ministerio da Saude.

Fonte oficial:
https://demas-dados-abertos.s3.amazonaws.com/csv/ripsa014dm.csv.zip

O CSV da fonte tem cerca de 1,6 GB descompactado. A leitura e feita diretamente
do ZIP, em fluxo, e apenas as linhas da categoria Sexo/Feminino sao mantidas.
"""

from __future__ import annotations

import csv
import io
import json
import urllib.request
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
URL = "https://demas-dados-abertos.s3.amazonaws.com/csv/ripsa014dm.csv.zip"
URL_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
BRONZE = ROOT / "data" / "bronze" / "ibge" / "ripsa014dm.csv.zip"
MUNICIPIOS_BRASIL = ROOT / "data" / "bronze" / "ibge" / "municipios_brasil.json"
SILVER = ROOT / "data" / "silver" / "populacao_feminina_municipio.parquet"
ANOS = set(range(2015, 2025))


def _baixar(url: str, destino: Path) -> None:
    if destino.exists():
        print(f"Arquivo bruto ja existe: {destino}")
        return

    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + ".part")
    print(f"Baixando {url} ...")
    urllib.request.urlretrieve(url, temporario)
    temporario.replace(destino)
    print(f"Salvo em {destino}")


def baixar() -> None:
    _baixar(URL, BRONZE)
    _baixar(URL_MUNICIPIOS, MUNICIPIOS_BRASIL)


def carregar_municipios() -> dict[str, str]:
    itens = json.loads(MUNICIPIOS_BRASIL.read_text(encoding="utf-8"))
    if len(itens) < 5570:
        raise ValueError(f"Dimensao municipal incompleta: recebidos {len(itens)}")
    mapa = {str(item["id"])[:6]: str(item["id"]) for item in itens}
    if len(mapa) != len(itens):
        raise ValueError("Codigos municipais de seis digitos nao sao unicos")
    return mapa


def extrair() -> pd.DataFrame:
    registros: list[dict] = []
    totais_brasil: dict[int, int] = {}
    municipios = carregar_municipios()

    with ZipFile(BRONZE) as arquivo_zip:
        nomes = arquivo_zip.namelist()
        if len(nomes) != 1:
            raise ValueError(f"Esperado um CSV no ZIP, encontrados: {nomes}")

        with arquivo_zip.open(nomes[0]) as bruto:
            texto = io.TextIOWrapper(bruto, encoding="utf-8-sig", newline="")
            leitor = csv.DictReader(texto)
            for linha in leitor:
                ano = int(linha["co_anomes"][:4])
                if ano not in ANOS:
                    continue
                if linha["sg_categoria"] != "PESSOA1":
                    continue
                if linha["ds_item_categoria"].casefold() != "feminino":
                    continue

                populacao = int(float(linha["vl_indicador_calculado_mun"]))
                total_brasil = int(float(linha["vl_indicador_calculado_br"]))
                totais_brasil.setdefault(ano, total_brasil)
                if totais_brasil[ano] != total_brasil:
                    raise ValueError(f"Total Brasil inconsistente em {ano}")

                registros.append(
                    {
                        "ano": ano,
                        "id_municipio": municipios[linha["co_ibge"].strip().zfill(6)],
                        "municipio": linha["no_municipio"],
                        "sigla_uf": linha["sg_uf"],
                        "populacao_feminina": populacao,
                    }
                )

    dados = pd.DataFrame(registros).sort_values(["ano", "id_municipio"])
    dados = dados.reset_index(drop=True)

    esperado_anos = sorted(ANOS)
    if sorted(dados["ano"].unique().tolist()) != esperado_anos:
        raise ValueError("Cobertura anual incompleta")
    if dados.duplicated(["ano", "id_municipio"]).any():
        raise ValueError("Ha duplicidade na chave ano + id_municipio")
    if not dados.groupby("ano")["id_municipio"].nunique().eq(5570).all():
        raise ValueError("Nem todos os anos possuem os 5.570 municipios")

    calculados = dados.groupby("ano")["populacao_feminina"].sum().to_dict()
    if calculados != totais_brasil:
        raise ValueError(
            f"Totais municipais divergem do total Brasil: {calculados} != {totais_brasil}"
        )

    dados["ano"] = dados["ano"].astype("int16")
    dados["populacao_feminina"] = dados["populacao_feminina"].astype("int64")
    return dados


def main() -> None:
    baixar()
    dados = extrair()
    SILVER.parent.mkdir(parents=True, exist_ok=True)
    dados.to_parquet(SILVER, index=False)
    print(f"Salvo em: {SILVER}")
    print(f"Linhas: {len(dados)}")
    print(f"Anos: {dados['ano'].min()}-{dados['ano'].max()}")
    print(f"Municipios por ano: {dados.groupby('ano')['id_municipio'].nunique().min()}")
    print(f"Populacao feminina Brasil 2024: {dados.loc[dados.ano == 2024, 'populacao_feminina'].sum()}")


if __name__ == "__main__":
    main()
