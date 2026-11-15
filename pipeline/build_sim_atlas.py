"""Constrói a camada SIM do Panorama Territorial da Violência.

O processo usa os arquivos anuais já armazenados em data/bronze/sim e mantém
três grupos de causa básica:

* agressões, CID-10 X85 a Y09;
* suicídios, CID-10 X60 a X84;
* acidentes de transporte, CID-10 V01 a V99.

As taxas usam residência e denominadores populacionais de 2015 a 2024. Os
anos de 2025 e 2026 permanecem sem taxa porque a população da fonte local
termina em 2024.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "data" / "bronze" / "sim"
MUNICIPIOS_BRASIL = ROOT / "data" / "bronze" / "ibge" / "municipios_brasil.json"
SIM_MULHERES = ROOT / "data" / "silver" / "sim_mulheres_agressao.parquet"
POP_TOTAL = ROOT / "data" / "silver" / "populacao_municipio_ano.parquet"
POP_SEXO = ROOT / "data" / "silver" / "populacao_municipio_sexo_ano.parquet"
POP_IDADE = ROOT / "data" / "silver" / "populacao_municipio_idade_ano.parquet"
SILVER = ROOT / "data" / "silver" / "sim_atlas_mortalidade.parquet"
GOLD_TERRITORIO = ROOT / "data" / "gold" / "atlas" / "sim_mortalidade_territorio_ano.csv"
GOLD_IDADE = ROOT / "data" / "gold" / "atlas" / "sim_mortalidade_idade_ano.csv"
MANIFESTO = ROOT / "data" / "gold" / "atlas" / "sim_mortalidade_metodologia.json"
ANOS = range(2015, 2027)
USECOLS = ["DTOBITO", "SEXO", "RACACOR", "IDADE", "CODMUNRES", "CODMUNOCOR", "CAUSABAS"]

RACAS = {
    "1": "Branca",
    "2": "Preta",
    "3": "Amarela",
    "4": "Parda",
    "5": "Indígena",
}

SEXOS = {
    "1": "masculino",
    "M": "masculino",
    "2": "feminino",
    "F": "feminino",
}

GRUPOS_ETARIOS = [
    "0 a 4 anos",
    "5 a 9 anos",
    "10 a 14 anos",
    "15 a 19 anos",
    "20 a 29 anos",
    "30 a 39 anos",
    "40 a 49 anos",
    "50 a 59 anos",
    "60 a 69 anos",
    "70 a 79 anos",
    "80 anos e mais",
]

SCHEMA = pa.schema(
    [
        ("ano", pa.int16()),
        ("mes", pa.int8()),
        ("data_obito", pa.date32()),
        ("sexo", pa.string()),
        ("raca", pa.string()),
        ("idade_anos", pa.int16()),
        ("grupo_etario", pa.string()),
        ("id_municipio_residencia", pa.string()),
        ("sigla_uf_residencia", pa.string()),
        ("id_municipio_ocorrencia", pa.string()),
        ("sigla_uf_ocorrencia", pa.string()),
        ("causa_basica", pa.string()),
        ("grupo_causa", pa.string()),
        ("situacao_dado", pa.string()),
    ]
)


def carregar_municipios() -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    itens = json.loads(MUNICIPIOS_BRASIL.read_text(encoding="utf-8"))
    if len(itens) < 5570:
        raise ValueError(f"Dimensao municipal incompleta: {len(itens)}")
    mapa_id = {str(item["id"])[:6]: str(item["id"]) for item in itens}
    mapa_nome = {str(item["id"]): str(item["nome"]) for item in itens}

    populacao = pd.read_parquet(POP_TOTAL, columns=["id_municipio", "sigla_uf"])
    dimensao = populacao.drop_duplicates("id_municipio")
    mapa_uf = dict(zip(dimensao.id_municipio.str[:6], dimensao.sigla_uf))
    return mapa_id, mapa_uf, mapa_nome


def opcoes_leitura(caminho: Path) -> tuple[str, dict, list[str] | None]:
    with zipfile.ZipFile(caminho) as arquivo_zip:
        nomes = [nome for nome in arquivo_zip.namelist() if nome.lower().endswith(".csv")]
        if len(nomes) != 1:
            raise RuntimeError(f"Esperado um CSV em {caminho.name}; encontrados {nomes}")
        nome = nomes[0]
        with arquivo_zip.open(nome) as inspecao:
            primeira_linha = inspecao.readline().decode("latin-1", errors="replace")

    tem_cabecalho = "CAUSABAS" in primeira_linha and "SEXO" in primeira_linha
    if tem_cabecalho:
        return nome, {"usecols": USECOLS}, None

    quantidade = len(next(csv.reader(io.StringIO(primeira_linha), delimiter=";")))
    indices = [2, 8, 9, 7, 15, 19, 45] if quantidade == 87 else [3, 8, 9, 10, 16, 19, 45]
    if quantidade not in (86, 87):
        raise RuntimeError(f"CSV sem cabecalho com {quantidade} campos em {caminho.name}")
    nomes_lidos = ["DTOBITO", "IDADE", "SEXO", "RACACOR", "CODMUNRES", "CODMUNOCOR", "CAUSABAS"]
    return nome, {"header": None, "usecols": indices}, nomes_lidos


def classificar_causa(causa: pd.Series) -> pd.Series:
    resultado = pd.Series(pd.NA, index=causa.index, dtype="string")
    resultado.loc[causa.str.match(r"^(X8[5-9]|X9\d|Y0\d)")] = "agressao"
    resultado.loc[causa.str.match(r"^(X6\d|X7\d|X8[0-4])")] = "suicidio"
    resultado.loc[causa.str.match(r"^V\d{2}")] = "acidente_transporte"
    return resultado


def idade_em_anos(codigo: object) -> object:
    texto = str(codigo).strip()
    if len(texto) != 3 or not texto.isdigit() or texto.startswith("9"):
        return pd.NA
    unidade = texto[0]
    valor = int(texto[1:])
    if unidade in {"0", "1", "2", "3"}:
        return 0
    if unidade == "4":
        return valor
    if unidade == "5":
        return 100 + valor
    return pd.NA


def grupo_etario(idade: object) -> str:
    if pd.isna(idade):
        return "Idade não informada"
    valor = int(idade)
    if valor < 5:
        return "0 a 4 anos"
    if valor < 10:
        return "5 a 9 anos"
    if valor < 15:
        return "10 a 14 anos"
    if valor < 20:
        return "15 a 19 anos"
    if valor < 30:
        return "20 a 29 anos"
    if valor < 40:
        return "30 a 39 anos"
    if valor < 50:
        return "40 a 49 anos"
    if valor < 60:
        return "50 a 59 anos"
    if valor < 70:
        return "60 a 69 anos"
    if valor < 80:
        return "70 a 79 anos"
    return "80 anos e mais"


def situacao_dado(ano: int) -> str:
    if ano <= 2024:
        return "definitivo"
    if ano == 2025:
        return "preliminar"
    return "previa"


def preparar_bloco(
    bloco: pd.DataFrame,
    ano: int,
    mapa_id: dict[str, str],
    mapa_uf: dict[str, str],
) -> pd.DataFrame:
    causa = bloco["CAUSABAS"].fillna("").str.upper().str.strip()
    grupos = classificar_causa(causa)
    bloco = bloco.loc[grupos.notna()].copy()
    if bloco.empty:
        return pd.DataFrame(columns=[campo.name for campo in SCHEMA])
    bloco["grupo_causa"] = grupos.loc[bloco.index]
    bloco["causa_basica"] = causa.loc[bloco.index]

    data_obito = pd.to_datetime(bloco["DTOBITO"], format="%d%m%Y", errors="coerce")
    bloco["ano"] = pd.Series(ano, index=bloco.index, dtype="int16")
    bloco["mes"] = data_obito.dt.month.astype("Int8")
    bloco["data_obito"] = data_obito.dt.date

    codigo_sexo = bloco["SEXO"].fillna("").str.upper().str.strip()
    bloco["sexo"] = codigo_sexo.map(SEXOS).fillna("não informado")
    codigo_raca = bloco["RACACOR"].fillna("").str.strip()
    bloco["raca"] = codigo_raca.map(RACAS).fillna("Não informada")
    bloco["idade_anos"] = bloco["IDADE"].map(idade_em_anos).astype("Int16")
    bloco["grupo_etario"] = bloco["idade_anos"].map(grupo_etario)

    residencia = bloco["CODMUNRES"].fillna("").str.strip().str[:6]
    ocorrencia = bloco["CODMUNOCOR"].fillna("").str.strip().str[:6]
    bloco["id_municipio_residencia"] = residencia.map(mapa_id)
    bloco["sigla_uf_residencia"] = residencia.map(mapa_uf)
    bloco["id_municipio_ocorrencia"] = ocorrencia.map(mapa_id)
    bloco["sigla_uf_ocorrencia"] = ocorrencia.map(mapa_uf)
    bloco["situacao_dado"] = situacao_dado(ano)
    return bloco[[campo.name for campo in SCHEMA]]


def construir_silver() -> None:
    mapa_id, mapa_uf, _ = carregar_municipios()
    temporario = SILVER.with_suffix(SILVER.suffix + ".part")
    if temporario.exists():
        temporario.unlink()
    escritor = pq.ParquetWriter(temporario, SCHEMA, compression="zstd")
    totais: dict[int, int] = {}
    try:
        for ano in ANOS:
            caminho = BRONZE / f"Mortalidade_Geral_{ano}_csv.zip"
            if not caminho.exists():
                raise FileNotFoundError(f"Arquivo SIM ausente: {caminho}")
            nome, opcoes, nomes_lidos = opcoes_leitura(caminho)
            total_ano = 0
            with zipfile.ZipFile(caminho) as arquivo_zip, arquivo_zip.open(nome) as arquivo:
                for bloco in pd.read_csv(
                    arquivo,
                    sep=";",
                    quotechar='"',
                    dtype="string",
                    chunksize=200_000,
                    encoding="latin-1",
                    low_memory=False,
                    **opcoes,
                ):
                    if nomes_lidos:
                        bloco.columns = nomes_lidos
                    filtrado = preparar_bloco(bloco, ano, mapa_id, mapa_uf)
                    if filtrado.empty:
                        continue
                    tabela = pa.Table.from_pandas(filtrado, schema=SCHEMA, preserve_index=False, safe=True)
                    escritor.write_table(tabela)
                    total_ano += len(filtrado)
            totais[ano] = total_ano
            print(f"SIM {ano}: {total_ano} óbitos nos grupos selecionados")
    finally:
        escritor.close()
    temporario.replace(SILVER)
    print(f"Silver SIM atlas: {SILVER} ({sum(totais.values())} registros)")


def cobertura_anual(sim: pd.DataFrame) -> pd.DataFrame:
    return (
        sim.groupby("ano", as_index=False)
        .agg(data_maxima=("data_obito", "max"), meses_observados=("mes", "nunique"))
        .assign(situacao_dado=lambda x: x.ano.map(situacao_dado))
    )


def denominadores_territoriais() -> pd.DataFrame:
    total = pd.read_parquet(POP_TOTAL)
    sexo = pd.read_parquet(POP_SEXO)
    total["id_uf"] = total["id_municipio"].str[:2]
    sexo["id_uf"] = sexo["id_municipio"].str[:2]

    partes = []
    for base, rotulo_sexo in [(total, "total")]:
        br = base.groupby("ano", as_index=False).agg(populacao=("populacao", "sum"))
        br = br.assign(nivel_territorial="brasil", id_territorio="BR", territorio="Brasil", sexo=rotulo_sexo)
        uf = base.groupby(["ano", "sigla_uf"], as_index=False).agg(populacao=("populacao", "sum"))
        uf = uf.assign(nivel_territorial="uf", id_territorio=uf.sigla_uf, territorio=uf.sigla_uf, sexo=rotulo_sexo)
        mun = base.loc[base.sigla_uf.eq("SC")].rename(columns={"id_municipio": "id_territorio", "municipio": "territorio"})
        mun = mun.assign(nivel_territorial="municipio", sexo=rotulo_sexo)
        partes.extend([br, uf, mun])

    br_sexo = sexo.groupby(["ano", "sexo"], as_index=False).agg(populacao=("populacao", "sum"))
    br_sexo = br_sexo.assign(nivel_territorial="brasil", id_territorio="BR", territorio="Brasil")
    uf_sexo = sexo.groupby(["ano", "sigla_uf", "sexo"], as_index=False).agg(populacao=("populacao", "sum"))
    uf_sexo = uf_sexo.assign(nivel_territorial="uf", id_territorio=uf_sexo.sigla_uf, territorio=uf_sexo.sigla_uf)
    mun_sexo = sexo.loc[sexo.sigla_uf.eq("SC")].rename(columns={"id_municipio": "id_territorio", "municipio": "territorio"})
    mun_sexo = mun_sexo.assign(nivel_territorial="municipio")
    partes.extend([br_sexo, uf_sexo, mun_sexo])
    colunas = ["ano", "nivel_territorial", "id_territorio", "territorio", "sexo", "populacao"]
    return pd.concat([parte[colunas] for parte in partes], ignore_index=True)


def contagens_territoriais(sim: pd.DataFrame, mapa_nome: dict[str, str]) -> pd.DataFrame:
    partes = []
    base = sim.loc[sim.id_municipio_residencia.notna()].copy()
    for sexo in ["feminino", "masculino", "não informado"]:
        recorte = base.loc[base.sexo.eq(sexo)]
        br = recorte.groupby(["ano", "grupo_causa"], as_index=False).size().rename(columns={"size": "obitos"})
        br = br.assign(nivel_territorial="brasil", id_territorio="BR", territorio="Brasil", sexo=sexo)
        uf = recorte.groupby(["ano", "grupo_causa", "sigla_uf_residencia"], as_index=False).size().rename(columns={"size": "obitos"})
        uf = uf.assign(nivel_territorial="uf", id_territorio=uf.sigla_uf_residencia, territorio=uf.sigla_uf_residencia, sexo=sexo)
        mun = recorte.loc[recorte.sigla_uf_residencia.eq("SC")].groupby(
            ["ano", "grupo_causa", "id_municipio_residencia"], as_index=False
        ).size().rename(columns={"size": "obitos", "id_municipio_residencia": "id_territorio"})
        mun = mun.assign(nivel_territorial="municipio", territorio=mun.id_territorio.map(mapa_nome), sexo=sexo)
        partes.extend([br, uf, mun])

    br = base.groupby(["ano", "grupo_causa"], as_index=False).size().rename(columns={"size": "obitos"})
    br = br.assign(nivel_territorial="brasil", id_territorio="BR", territorio="Brasil", sexo="total")
    uf = base.groupby(["ano", "grupo_causa", "sigla_uf_residencia"], as_index=False).size().rename(columns={"size": "obitos"})
    uf = uf.assign(nivel_territorial="uf", id_territorio=uf.sigla_uf_residencia, territorio=uf.sigla_uf_residencia, sexo="total")
    mun = base.loc[base.sigla_uf_residencia.eq("SC")].groupby(
        ["ano", "grupo_causa", "id_municipio_residencia"], as_index=False
    ).size().rename(columns={"size": "obitos", "id_municipio_residencia": "id_territorio"})
    mun = mun.assign(nivel_territorial="municipio", territorio=mun.id_territorio.map(mapa_nome), sexo="total")
    partes.extend([br, uf, mun])
    colunas = ["ano", "nivel_territorial", "id_territorio", "territorio", "grupo_causa", "sexo", "obitos"]
    return pd.concat([parte[colunas] for parte in partes], ignore_index=True)


def construir_gold_territorio(sim: pd.DataFrame, mapa_nome: dict[str, str]) -> pd.DataFrame:
    anos = list(ANOS)
    causas = ["agressao", "suicidio", "acidente_transporte"]
    sexos = ["total", "feminino", "masculino", "não informado"]
    dimensao_pop = pd.read_parquet(
        POP_TOTAL, columns=["id_municipio", "municipio", "sigla_uf"]
    ).drop_duplicates("id_municipio")
    territorios = pd.concat(
        [
            pd.DataFrame([{"nivel_territorial": "brasil", "id_territorio": "BR", "territorio": "Brasil"}]),
            pd.DataFrame({"nivel_territorial": "uf", "id_territorio": sorted(dimensao_pop.sigla_uf.unique())}).assign(
                territorio=lambda x: x.id_territorio
            ),
            dimensao_pop.loc[dimensao_pop.sigla_uf.eq("SC"), ["id_municipio", "municipio"]]
            .rename(columns={"id_municipio": "id_territorio", "municipio": "territorio"})
            .assign(nivel_territorial="municipio"),
        ],
        ignore_index=True,
    )
    grade = territorios.merge(pd.DataFrame({"ano": anos}), how="cross")
    grade = grade.merge(pd.DataFrame({"grupo_causa": causas}), how="cross")
    grade = grade.merge(pd.DataFrame({"sexo": sexos}), how="cross")

    contagens = contagens_territoriais(sim, mapa_nome)
    resultado = grade.merge(
        contagens.drop(columns="territorio"),
        on=["ano", "nivel_territorial", "id_territorio", "grupo_causa", "sexo"],
        how="left",
        validate="one_to_one",
    )
    resultado["obitos"] = resultado["obitos"].fillna(0).astype("int64")
    resultado = resultado.merge(
        denominadores_territoriais(),
        on=["ano", "nivel_territorial", "id_territorio", "territorio", "sexo"],
        how="left",
        validate="many_to_one",
    )
    resultado.loc[resultado.sexo.eq("não informado"), "populacao"] = pd.NA
    resultado["taxa_100mil"] = resultado.obitos.div(resultado.populacao).mul(100_000).round(2)
    resultado = resultado.merge(cobertura_anual(sim), on="ano", how="left", validate="many_to_one")
    resultado = resultado.sort_values(
        ["ano", "nivel_territorial", "id_territorio", "grupo_causa", "sexo"]
    ).reset_index(drop=True)
    GOLD_TERRITORIO.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(GOLD_TERRITORIO, index=False, encoding="utf-8-sig")
    return resultado


def construir_gold_idade(sim: pd.DataFrame) -> pd.DataFrame:
    recortes = []
    for territorio, filtro in [
        ("Brasil", pd.Series(True, index=sim.index)),
        ("Santa Catarina", sim.sigla_uf_residencia.eq("SC")),
    ]:
        agregado = sim.loc[filtro].groupby(
            ["ano", "grupo_causa", "grupo_etario"], as_index=False
        ).size().rename(columns={"size": "obitos"})
        agregado["territorio"] = territorio
        recortes.append(agregado)
    contagens = pd.concat(recortes, ignore_index=True)

    faixas = GRUPOS_ETARIOS + ["Idade não informada"]
    grade = pd.DataFrame({"ano": list(ANOS)}).merge(
        pd.DataFrame({"territorio": ["Brasil", "Santa Catarina"]}), how="cross"
    ).merge(pd.DataFrame({"grupo_causa": ["agressao", "suicidio", "acidente_transporte"]}), how="cross")
    grade = grade.merge(pd.DataFrame({"grupo_etario": faixas}), how="cross")
    resultado = grade.merge(
        contagens,
        on=["ano", "territorio", "grupo_causa", "grupo_etario"],
        how="left",
        validate="one_to_one",
    )
    resultado["obitos"] = resultado.obitos.fillna(0).astype("int64")

    pop = pd.read_parquet(POP_IDADE)
    denominadores = []
    br = pop.groupby(["ano", "grupo_etario"], as_index=False).agg(populacao=("populacao", "sum"))
    br["territorio"] = "Brasil"
    sc = pop.loc[pop.sigla_uf.eq("SC")].groupby(["ano", "grupo_etario"], as_index=False).agg(populacao=("populacao", "sum"))
    sc["territorio"] = "Santa Catarina"
    denominadores.extend([br, sc])
    denominador = pd.concat(denominadores, ignore_index=True)
    resultado = resultado.merge(
        denominador,
        on=["ano", "territorio", "grupo_etario"],
        how="left",
        validate="many_to_one",
    )
    resultado.loc[resultado.grupo_etario.eq("Idade não informada"), "populacao"] = pd.NA
    resultado["taxa_100mil"] = resultado.obitos.div(resultado.populacao).mul(100_000).round(2)
    resultado = resultado.merge(cobertura_anual(sim), on="ano", how="left", validate="many_to_one")
    resultado = resultado.sort_values(["ano", "territorio", "grupo_causa", "grupo_etario"]).reset_index(drop=True)
    resultado.to_csv(GOLD_IDADE, index=False, encoding="utf-8-sig")
    return resultado


def validar(sim: pd.DataFrame, territorio: pd.DataFrame, idade: pd.DataFrame) -> None:
    if sorted(sim.ano.unique().tolist()) != list(ANOS):
        raise ValueError("Cobertura anual incompleta no SIM do atlas")
    if set(sim.grupo_causa.unique()) != {"agressao", "suicidio", "acidente_transporte"}:
        raise ValueError("Grupos de causa inesperados")

    anterior = pd.read_parquet(SIM_MULHERES, columns=["ano"])
    controle_anterior = anterior.groupby("ano").size().to_dict()
    controle_novo = sim.loc[
        sim.grupo_causa.eq("agressao") & sim.sexo.eq("feminino")
    ].groupby("ano").size().to_dict()
    if controle_anterior != controle_novo:
        raise ValueError(f"Óbitos femininos por agressão divergentes: {controle_anterior} != {controle_novo}")

    chave_territorio = ["ano", "nivel_territorial", "id_territorio", "grupo_causa", "sexo"]
    if territorio.duplicated(chave_territorio).any():
        raise ValueError("Chave duplicada na Gold territorial do SIM")
    chave_idade = ["ano", "territorio", "grupo_causa", "grupo_etario"]
    if idade.duplicated(chave_idade).any():
        raise ValueError("Chave duplicada na Gold etária do SIM")

    consolidados = territorio.ano.le(2024) & territorio.sexo.isin(["total", "feminino", "masculino"])
    recentes = territorio.ano.ge(2025)
    if territorio.loc[consolidados, "taxa_100mil"].isna().any():
        raise ValueError("Taxas ausentes no período com denominador")
    if territorio.loc[recentes, "taxa_100mil"].notna().any():
        raise ValueError("Taxa calculada sem denominador em 2025 ou 2026")


def main() -> None:
    obrigatorios = [MUNICIPIOS_BRASIL, SIM_MULHERES, POP_TOTAL, POP_SEXO, POP_IDADE]
    ausentes = [str(caminho.relative_to(ROOT)) for caminho in obrigatorios if not caminho.exists()]
    if ausentes:
        raise FileNotFoundError(f"Arquivos ausentes: {ausentes}")

    SILVER.parent.mkdir(parents=True, exist_ok=True)
    construir_silver()
    sim = pd.read_parquet(SILVER)
    _, _, mapa_nome = carregar_municipios()
    territorio = construir_gold_territorio(sim, mapa_nome)
    idade = construir_gold_idade(sim)
    validar(sim, territorio, idade)

    metodologia = {
        "fonte": "Portal de Dados Abertos do SUS, Sistema de Informações sobre Mortalidade",
        "documentacao": "https://svs.aids.gov.br/daent/cgiae/coesv/sistemas-informacao/sim/documentacao/dicionario-de-dados-SIM-tabela-DO.pdf",
        "territorio_taxas": "município de residência",
        "grupos_cid10": {
            "agressao": "X85 a Y09",
            "suicidio": "X60 a X84",
            "acidente_transporte": "V01 a V99",
        },
        "denominadores": "população total, por sexo e por idade, de 2015 a 2024",
        "limite": "sexo e idade não podem ser cruzados porque a fonte populacional os fornece separadamente",
        "situacao_dado": {
            "2015 a 2024": "definitivo",
            "2025": "preliminar",
            "2026": "prévia",
        },
    }
    MANIFESTO.write_text(json.dumps(metodologia, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gold territorial: {GOLD_TERRITORIO} ({len(territorio)} linhas)")
    print(f"Gold por idade: {GOLD_IDADE} ({len(idade)} linhas)")
    print("SIM do atlas validado contra a série feminina existente")


if __name__ == "__main__":
    main()
