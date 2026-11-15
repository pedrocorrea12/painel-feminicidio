"""Prepara denominadores municipais de populacao total, sexo e idade.

Fonte oficial local ja usada pelo projeto:
https://demas-dados-abertos.s3.amazonaws.com/csv/ripsa014dm.csv.zip

O arquivo bruto contem tres recortes independentes: total, sexo e idade
simples. Sexo e idade nao aparecem cruzados. Por isso, esta rotina nao gera
denominadores conjuntos de sexo por idade.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from zipfile import ZipFile

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "data" / "bronze" / "ibge" / "ripsa014dm.csv.zip"
MUNICIPIOS_BRASIL = ROOT / "data" / "bronze" / "ibge" / "municipios_brasil.json"
SILVER_TOTAL = ROOT / "data" / "silver" / "populacao_municipio_ano.parquet"
SILVER_SEXO = ROOT / "data" / "silver" / "populacao_municipio_sexo_ano.parquet"
SILVER_IDADE = ROOT / "data" / "silver" / "populacao_municipio_idade_ano.parquet"
ANO_INICIAL = 2015
CHUNK_SIZE = 500_000

COLUNAS_BRONZE = [
    "co_anomes",
    "co_ibge",
    "no_municipio",
    "sg_uf",
    "sg_categoria",
    "ds_item_categoria",
    "vl_indicador_calculado_mun",
]

SCHEMA_TOTAL = pa.schema(
    [
        ("ano", pa.int16()),
        ("id_municipio", pa.string()),
        ("municipio", pa.string()),
        ("sigla_uf", pa.string()),
        ("populacao", pa.int64()),
    ]
)

SCHEMA_SEXO = pa.schema(
    [
        ("ano", pa.int16()),
        ("id_municipio", pa.string()),
        ("municipio", pa.string()),
        ("sigla_uf", pa.string()),
        ("sexo", pa.string()),
        ("populacao", pa.int64()),
    ]
)

SCHEMA_IDADE = pa.schema(
    [
        ("ano", pa.int16()),
        ("id_municipio", pa.string()),
        ("municipio", pa.string()),
        ("sigla_uf", pa.string()),
        ("idade_inicio", pa.int16()),
        ("idade_aberta", pa.bool_()),
        ("idade_rotulo", pa.string()),
        ("grupo_etario", pa.string()),
        ("populacao", pa.int64()),
    ]
)


def carregar_municipios() -> dict[str, str]:
    itens = json.loads(MUNICIPIOS_BRASIL.read_text(encoding="utf-8"))
    if len(itens) < 5570:
        raise ValueError(f"Dimensao municipal incompleta: recebidos {len(itens)}")
    mapa = {str(item["id"])[:6]: str(item["id"]) for item in itens}
    if len(mapa) != len(itens):
        raise ValueError("Codigos municipais de seis digitos nao sao unicos")
    return mapa


def idade_inicio(rotulo: str) -> int:
    if rotulo == "Menor de 1 ano":
        return 0
    encontrado = re.match(r"(\d+)", rotulo)
    if not encontrado:
        raise ValueError(f"Rotulo de idade nao reconhecido: {rotulo}")
    return int(encontrado.group(1))


def grupo_etario(idade: int) -> str:
    if idade < 5:
        return "0 a 4 anos"
    if idade < 10:
        return "5 a 9 anos"
    if idade < 15:
        return "10 a 14 anos"
    if idade < 20:
        return "15 a 19 anos"
    if idade < 30:
        return "20 a 29 anos"
    if idade < 40:
        return "30 a 39 anos"
    if idade < 50:
        return "40 a 49 anos"
    if idade < 60:
        return "50 a 59 anos"
    if idade < 70:
        return "60 a 69 anos"
    if idade < 80:
        return "70 a 79 anos"
    return "80 anos e mais"


def tabela_arrow(dados: pd.DataFrame, schema: pa.Schema) -> pa.Table:
    return pa.Table.from_pandas(
        dados[[campo.name for campo in schema]],
        schema=schema,
        preserve_index=False,
        safe=True,
    )


def preparar_base(chunk: pd.DataFrame, municipios: dict[str, str]) -> pd.DataFrame:
    chunk["ano"] = chunk["co_anomes"].str[:4].astype("int16")
    chunk = chunk.loc[chunk["ano"].ge(ANO_INICIAL)].copy()
    if chunk.empty:
        return chunk

    codigos = chunk["co_ibge"].str.strip().str.zfill(6)
    chunk["id_municipio"] = codigos.map(municipios)
    if chunk["id_municipio"].isna().any():
        ausentes = sorted(codigos.loc[chunk["id_municipio"].isna()].unique())
        raise ValueError(f"Codigos municipais sem correspondencia: {ausentes[:10]}")

    chunk = chunk.rename(
        columns={
            "no_municipio": "municipio",
            "sg_uf": "sigla_uf",
            "vl_indicador_calculado_mun": "populacao",
        }
    )
    chunk["populacao"] = chunk["populacao"].round().astype("int64")
    return chunk


def extrair() -> None:
    if not BRONZE.exists():
        raise FileNotFoundError(f"Arquivo bruto nao encontrado: {BRONZE}")
    if not MUNICIPIOS_BRASIL.exists():
        raise FileNotFoundError(f"Dimensao municipal nao encontrada: {MUNICIPIOS_BRASIL}")

    municipios = carregar_municipios()
    destinos = [SILVER_TOTAL, SILVER_SEXO, SILVER_IDADE]
    temporarios = [destino.with_suffix(destino.suffix + ".part") for destino in destinos]
    for temporario in temporarios:
        if temporario.exists():
            temporario.unlink()

    escritores = [
        pq.ParquetWriter(temporarios[0], SCHEMA_TOTAL, compression="zstd"),
        pq.ParquetWriter(temporarios[1], SCHEMA_SEXO, compression="zstd"),
        pq.ParquetWriter(temporarios[2], SCHEMA_IDADE, compression="zstd"),
    ]
    linhas = {"total": 0, "sexo": 0, "idade": 0}

    try:
        with ZipFile(BRONZE) as arquivo_zip:
            nomes = arquivo_zip.namelist()
            if len(nomes) != 1:
                raise ValueError(f"Esperado um CSV no ZIP, encontrados: {nomes}")

            with arquivo_zip.open(nomes[0]) as bruto:
                leitor = pd.read_csv(
                    bruto,
                    usecols=COLUNAS_BRONZE,
                    dtype={
                        "co_anomes": "string",
                        "co_ibge": "string",
                        "no_municipio": "string",
                        "sg_uf": "string",
                        "sg_categoria": "string",
                        "ds_item_categoria": "string",
                    },
                    encoding="latin1",
                    chunksize=CHUNK_SIZE,
                )
                for numero, chunk in enumerate(leitor, start=1):
                    base = preparar_base(chunk, municipios)
                    if base.empty:
                        continue

                    total = base.loc[base["sg_categoria"].eq("TC")].copy()
                    if not total.empty:
                        escritores[0].write_table(tabela_arrow(total, SCHEMA_TOTAL))
                        linhas["total"] += len(total)

                    sexo = base.loc[base["sg_categoria"].eq("PESSOA1")].copy()
                    if not sexo.empty:
                        sexo["sexo"] = sexo["ds_item_categoria"].str.lower()
                        escritores[1].write_table(tabela_arrow(sexo, SCHEMA_SEXO))
                        linhas["sexo"] += len(sexo)

                    idade = base.loc[base["sg_categoria"].eq("Idade")].copy()
                    if not idade.empty:
                        idade["idade_rotulo"] = idade["ds_item_categoria"]
                        idade["idade_inicio"] = idade["idade_rotulo"].map(idade_inicio).astype("int16")
                        idade["idade_aberta"] = idade["idade_rotulo"].eq("80 anos e mais")
                        idade["grupo_etario"] = idade["idade_inicio"].map(grupo_etario)
                        escritores[2].write_table(tabela_arrow(idade, SCHEMA_IDADE))
                        linhas["idade"] += len(idade)

                    print(f"Bloco {numero}: {sum(linhas.values())} linhas gravadas")
    finally:
        for escritor in escritores:
            escritor.close()

    for temporario, destino in zip(temporarios, destinos, strict=True):
        temporario.replace(destino)

    print(f"Linhas por arquivo: {linhas}")


def validar() -> None:
    conexao = duckdb.connect()
    total = SILVER_TOTAL.as_posix()
    sexo = SILVER_SEXO.as_posix()
    idade = SILVER_IDADE.as_posix()

    esperado_anos = list(range(ANO_INICIAL, 2025))
    anos = [
        linha[0]
        for linha in conexao.execute(
            f"SELECT DISTINCT ano FROM read_parquet('{total}') ORDER BY ano"
        ).fetchall()
    ]
    if anos != esperado_anos:
        raise ValueError(f"Cobertura anual inesperada: {anos}")

    esperados = {
        "total": len(esperado_anos) * 5570,
        "sexo": len(esperado_anos) * 5570 * 2,
        "idade": len(esperado_anos) * 5570 * 81,
    }
    encontrados = {
        "total": conexao.execute(f"SELECT count(*) FROM read_parquet('{total}')").fetchone()[0],
        "sexo": conexao.execute(f"SELECT count(*) FROM read_parquet('{sexo}')").fetchone()[0],
        "idade": conexao.execute(f"SELECT count(*) FROM read_parquet('{idade}')").fetchone()[0],
    }
    if encontrados != esperados:
        raise ValueError(f"Quantidade de linhas inesperada: {encontrados} != {esperados}")

    testes_duplicidade = [
        (total, "ano, id_municipio"),
        (sexo, "ano, id_municipio, sexo"),
        (idade, "ano, id_municipio, idade_inicio"),
    ]
    for arquivo, chave in testes_duplicidade:
        duplicados = conexao.execute(
            f"""
            SELECT count(*) FROM (
                SELECT {chave}, count(*) AS n
                FROM read_parquet('{arquivo}')
                GROUP BY {chave}
                HAVING count(*) <> 1
            )
            """
        ).fetchone()[0]
        if duplicados:
            raise ValueError(f"Chave duplicada ou incompleta em {arquivo}: {duplicados}")

    divergencia_sexo = conexao.execute(
        f"""
        WITH s AS (
            SELECT ano, id_municipio, sum(populacao) AS populacao
            FROM read_parquet('{sexo}')
            GROUP BY ano, id_municipio
        )
        SELECT count(*)
        FROM read_parquet('{total}') t
        JOIN s USING (ano, id_municipio)
        WHERE t.populacao <> s.populacao
        """
    ).fetchone()[0]
    divergencia_idade = conexao.execute(
        f"""
        WITH i AS (
            SELECT ano, id_municipio, sum(populacao) AS populacao
            FROM read_parquet('{idade}')
            GROUP BY ano, id_municipio
        )
        SELECT count(*)
        FROM read_parquet('{total}') t
        JOIN i USING (ano, id_municipio)
        WHERE t.populacao <> i.populacao
        """
    ).fetchone()[0]
    if divergencia_sexo or divergencia_idade:
        raise ValueError(
            "Totais municipais divergem dos recortes: "
            f"sexo={divergencia_sexo}, idade={divergencia_idade}"
        )

    sexos = {
        linha[0]
        for linha in conexao.execute(
            f"SELECT DISTINCT sexo FROM read_parquet('{sexo}')"
        ).fetchall()
    }
    if sexos != {"feminino", "masculino"}:
        raise ValueError(f"Categorias de sexo inesperadas: {sexos}")

    brasil_2024 = conexao.execute(
        f"SELECT sum(populacao) FROM read_parquet('{total}') WHERE ano = 2024"
    ).fetchone()[0]
    conexao.close()
    print("Validacao concluida: total, sexo e idade reconciliados por municipio e ano")
    print(f"Populacao Brasil 2024: {brasil_2024}")


def main() -> None:
    SILVER_TOTAL.parent.mkdir(parents=True, exist_ok=True)
    extrair()
    validar()
    print(f"Salvo em: {SILVER_TOTAL}")
    print(f"Salvo em: {SILVER_SEXO}")
    print(f"Salvo em: {SILVER_IDADE}")


if __name__ == "__main__":
    main()
