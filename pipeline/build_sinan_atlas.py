"""Constrói a camada SINAN do Panorama Territorial da Violência."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "bronze" / "sinan" / "cache_bruto"
MUNICIPIOS = ROOT / "data" / "bronze" / "ibge" / "municipios_brasil.json"
SINAN_MULHERES = ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal.parquet"
SINAN_MULHERES_2025 = ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal_2025_preliminar.parquet"
POP_TOTAL = ROOT / "data" / "silver" / "populacao_municipio_ano.parquet"
POP_SEXO = ROOT / "data" / "silver" / "populacao_municipio_sexo_ano.parquet"
POP_IDADE = ROOT / "data" / "silver" / "populacao_municipio_idade_ano.parquet"
POP_2025 = ROOT / "data" / "silver" / "populacao_municipio_2025.parquet"
SILVER = ROOT / "data" / "silver" / "sinan_atlas_violencia.parquet"
GOLD_TERRITORIO = ROOT / "data" / "gold" / "atlas" / "sinan_violencia_territorio_ano.csv"
GOLD_IDADE = ROOT / "data" / "gold" / "atlas" / "sinan_violencia_idade_ano.csv"
METODOLOGIA = ROOT / "data" / "gold" / "atlas" / "sinan_violencia_metodologia.json"
ANOS = range(2015, 2026)

TIPOS = {
    "violencia_fisica": "VIOL_FISIC",
    "violencia_psicologica": "VIOL_PSICO",
    "violencia_sexual": "VIOL_SEXU",
    "violencia_financeira": "VIOL_FINAN",
    "negligencia": "VIOL_NEGLI",
    "tortura": "VIOL_TORT",
    "trafico_pessoas": "VIOL_TRAF",
}

INDICADORES = [
    "notificacoes_interpessoais",
    "notificacoes_autoprovocadas",
    *TIPOS,
]

GRUPOS_ETARIOS = [
    "0 a 4 anos", "5 a 9 anos", "10 a 14 anos", "15 a 19 anos",
    "20 a 29 anos", "30 a 39 anos", "40 a 49 anos", "50 a 59 anos",
    "60 a 69 anos", "70 a 79 anos", "80 anos e mais",
]

SCHEMA = pa.schema(
    [
        ("ano", pa.int16()), ("mes", pa.int8()), ("data_ocorrencia", pa.date32()),
        ("sexo", pa.string()), ("raca", pa.string()), ("idade_anos", pa.int16()),
        ("grupo_etario", pa.string()), ("natureza_violencia", pa.string()),
        ("id_municipio_residencia", pa.string()), ("sigla_uf_residencia", pa.string()),
        *[(nome, pa.bool_()) for nome in TIPOS],
        ("situacao_dado", pa.string()),
    ]
)


def mapas_municipios() -> tuple[dict[str, str], dict[str, str]]:
    itens = json.loads(MUNICIPIOS.read_text(encoding="utf-8"))
    mapa_id = {str(item["id"])[:6]: str(item["id"]) for item in itens}
    pop = pd.read_parquet(POP_TOTAL, columns=["id_municipio", "sigla_uf"])
    dim = pop.drop_duplicates("id_municipio")
    mapa_uf = dict(zip(dim.id_municipio, dim.sigla_uf))
    return mapa_id, mapa_uf


def idade_anos(codigo: object) -> object:
    texto = str(codigo).strip()
    if len(texto) != 4 or not texto.isdigit():
        return pd.NA
    unidade, valor = texto[0], int(texto[1:])
    if unidade in {"1", "2", "3"}:
        return 0
    if unidade == "4":
        return valor
    if unidade == "5":
        return 100 + valor
    return pd.NA


def grupo_etario(idade: object) -> str:
    if pd.isna(idade): return "Idade não informada"
    valor = int(idade)
    limites = [(5, "0 a 4 anos"), (10, "5 a 9 anos"), (15, "10 a 14 anos"),
               (20, "15 a 19 anos"), (30, "20 a 29 anos"), (40, "30 a 39 anos"),
               (50, "40 a 49 anos"), (60, "50 a 59 anos"), (70, "60 a 69 anos"),
               (80, "70 a 79 anos")]
    for limite, rotulo in limites:
        if valor < limite: return rotulo
    return "80 anos e mais"


def preparar(base: pd.DataFrame, ano: int, mapa_id: dict[str, str], mapa_uf: dict[str, str]) -> pd.DataFrame:
    base = base.loc[base.LES_AUTOP.isin(["1", "2"])].copy()
    data = pd.to_datetime(base.DT_OCOR, errors="coerce")
    base["ano"] = pd.Series(ano, index=base.index, dtype="int16")
    base["mes"] = data.dt.month.astype("Int8")
    base["data_ocorrencia"] = data.dt.date
    base["sexo"] = base.CS_SEXO.map({"F": "feminino", "M": "masculino"}).fillna("não informado")
    base["raca"] = base.CS_RACA.map({"1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda", "5": "Indígena"}).fillna("Não informada")
    base["idade_anos"] = base.NU_IDADE_N.map(idade_anos).astype("Int16")
    base["grupo_etario"] = base.idade_anos.map(grupo_etario)
    base["natureza_violencia"] = base.LES_AUTOP.map({"1": "autoprovocada", "2": "interpessoal"})
    codigos = base.ID_MN_RESI.fillna("").astype(str).str.strip()
    ids = codigos.where(codigos.str.len().eq(7), codigos.str[:6].map(mapa_id))
    ids = ids.where(ids.isin(set(mapa_uf)))
    base["id_municipio_residencia"] = ids
    base["sigla_uf_residencia"] = ids.map(mapa_uf)
    for nome, coluna in TIPOS.items():
        base[nome] = base[coluna].eq("1") & base.natureza_violencia.eq("interpessoal")
    base["situacao_dado"] = "definitivo" if ano <= 2024 else "preliminar"
    return base[[campo.name for campo in SCHEMA]]


def construir_silver() -> None:
    mapa_id, mapa_uf = mapas_municipios()
    temporario = SILVER.with_suffix(SILVER.suffix + ".part")
    if temporario.exists(): temporario.unlink()
    escritor = pq.ParquetWriter(temporario, SCHEMA, compression="zstd")
    totais = {}
    try:
        for ano in ANOS:
            caminho = CACHE / f"viol_{ano}_bruto.parquet"
            if not caminho.exists(): raise FileNotFoundError(caminho)
            colunas = ["DT_OCOR", "CS_SEXO", "CS_RACA", "NU_IDADE_N", "LES_AUTOP", "ID_MN_RESI", *TIPOS.values()]
            base = pd.read_parquet(caminho, columns=colunas)
            tratada = preparar(base, ano, mapa_id, mapa_uf)
            escritor.write_table(pa.Table.from_pandas(tratada, schema=SCHEMA, preserve_index=False, safe=True))
            totais[ano] = len(tratada)
            print(f"SINAN {ano}: {len(tratada)} notificações classificadas")
    finally:
        escritor.close()
    temporario.replace(SILVER)
    print(f"Silver SINAN atlas: {SILVER} ({sum(totais.values())} registros)")


def sql_eventos() -> str:
    partes = [
        "SELECT *, 'notificacoes_interpessoais' AS indicador FROM sinan WHERE natureza_violencia = 'interpessoal'",
        "SELECT *, 'notificacoes_autoprovocadas' AS indicador FROM sinan WHERE natureza_violencia = 'autoprovocada'",
    ]
    partes.extend(
        f"SELECT *, '{nome}' AS indicador FROM sinan WHERE {nome}"
        for nome in TIPOS
    )
    return " UNION ALL ".join(partes)


def contagens() -> tuple[pd.DataFrame, pd.DataFrame]:
    conexao = duckdb.connect()
    conexao.execute(f"CREATE VIEW sinan AS SELECT * FROM read_parquet('{SILVER.as_posix()}')")
    eventos = sql_eventos()
    consultas = [
        f"SELECT ano, 'brasil' nivel_territorial, 'BR' id_territorio, 'Brasil' territorio, indicador, sexo, count(*) notificacoes FROM ({eventos}) GROUP BY ano, indicador, sexo",
        f"SELECT ano, 'uf' nivel_territorial, sigla_uf_residencia id_territorio, sigla_uf_residencia territorio, indicador, sexo, count(*) notificacoes FROM ({eventos}) WHERE sigla_uf_residencia IS NOT NULL GROUP BY ano, sigla_uf_residencia, indicador, sexo",
        f"SELECT ano, 'municipio' nivel_territorial, id_municipio_residencia id_territorio, id_municipio_residencia territorio, indicador, sexo, count(*) notificacoes FROM ({eventos}) WHERE sigla_uf_residencia = 'SC' GROUP BY ano, id_municipio_residencia, indicador, sexo",
    ]
    detalhadas = pd.concat([conexao.execute(q).df() for q in consultas], ignore_index=True)
    total = detalhadas.groupby(["ano", "nivel_territorial", "id_territorio", "territorio", "indicador"], as_index=False).notificacoes.sum()
    total["sexo"] = "total"
    territorio = pd.concat([detalhadas, total], ignore_index=True)

    idade_br = conexao.execute(f"SELECT ano, 'Brasil' territorio, indicador, grupo_etario, count(*) notificacoes FROM ({eventos}) GROUP BY ano, indicador, grupo_etario").df()
    idade_sc = conexao.execute(f"SELECT ano, 'Santa Catarina' territorio, indicador, grupo_etario, count(*) notificacoes FROM ({eventos}) WHERE sigla_uf_residencia = 'SC' GROUP BY ano, indicador, grupo_etario").df()
    conexao.close()
    return territorio, pd.concat([idade_br, idade_sc], ignore_index=True)


def denominadores_territorio() -> pd.DataFrame:
    total = pd.read_parquet(POP_TOTAL)
    sexo = pd.read_parquet(POP_SEXO)
    pop_2025 = pd.read_parquet(POP_2025)
    total["tipo_denominador"] = "publicado"
    sexo["tipo_denominador"] = "publicado"
    total_2025 = pop_2025[
        ["ano", "id_municipio", "municipio", "sigla_uf", "populacao"]
    ].assign(sexo="total", tipo_denominador="publicado")
    sexo_2025 = pd.concat(
        [
            pop_2025[
                ["ano", "id_municipio", "municipio", "sigla_uf", "populacao_feminina_estimada"]
            ].rename(columns={"populacao_feminina_estimada": "populacao"}).assign(sexo="feminino"),
            pop_2025[
                ["ano", "id_municipio", "municipio", "sigla_uf", "populacao_masculina_estimada"]
            ].rename(columns={"populacao_masculina_estimada": "populacao"}).assign(sexo="masculino"),
        ],
        ignore_index=True,
    ).assign(tipo_denominador="estimado_proporcao_2024")
    total = pd.concat([total.assign(sexo="total"), total_2025], ignore_index=True)
    sexo = pd.concat([sexo, sexo_2025], ignore_index=True)
    partes = []
    for base in [total, sexo]:
        br = base.groupby(["ano", "sexo", "tipo_denominador"], as_index=False).agg(populacao=("populacao", "sum")).assign(nivel_territorial="brasil", id_territorio="BR", territorio="Brasil")
        uf = base.groupby(["ano", "sigla_uf", "sexo", "tipo_denominador"], as_index=False).agg(populacao=("populacao", "sum")).assign(nivel_territorial="uf", id_territorio=lambda x: x.sigla_uf, territorio=lambda x: x.sigla_uf)
        mun = base.loc[base.sigla_uf.eq("SC")].rename(columns={"id_municipio": "id_territorio", "municipio": "territorio"}).assign(nivel_territorial="municipio")
        partes.extend([br, uf, mun])
    colunas = ["ano", "nivel_territorial", "id_territorio", "territorio", "sexo", "populacao", "tipo_denominador"]
    return pd.concat([p[colunas] for p in partes], ignore_index=True)


def construir_gold() -> tuple[pd.DataFrame, pd.DataFrame]:
    contagem, contagem_idade = contagens()
    pop_total = pd.read_parquet(POP_TOTAL)
    dim = pop_total.drop_duplicates("id_municipio")
    territorios = pd.concat([
        pd.DataFrame([{"nivel_territorial": "brasil", "id_territorio": "BR", "territorio": "Brasil"}]),
        pd.DataFrame({"nivel_territorial": "uf", "id_territorio": sorted(dim.sigla_uf.unique())}).assign(territorio=lambda x: x.id_territorio),
        dim.loc[dim.sigla_uf.eq("SC"), ["id_municipio", "municipio"]].rename(columns={"id_municipio": "id_territorio", "municipio": "territorio"}).assign(nivel_territorial="municipio"),
    ], ignore_index=True)
    grade = territorios.merge(pd.DataFrame({"ano": list(ANOS)}), how="cross").merge(pd.DataFrame({"indicador": INDICADORES}), how="cross").merge(pd.DataFrame({"sexo": ["total", "feminino", "masculino", "não informado"]}), how="cross")
    resultado = grade.merge(contagem.drop(columns="territorio"), on=["ano", "nivel_territorial", "id_territorio", "indicador", "sexo"], how="left", validate="one_to_one")
    resultado.notificacoes = resultado.notificacoes.fillna(0).astype("int64")
    resultado = resultado.merge(denominadores_territorio(), on=["ano", "nivel_territorial", "id_territorio", "territorio", "sexo"], how="left", validate="many_to_one")
    resultado.loc[resultado.sexo.eq("não informado"), "populacao"] = pd.NA
    resultado.loc[resultado.sexo.eq("não informado"), "tipo_denominador"] = pd.NA
    resultado["taxa_100mil"] = resultado.notificacoes.div(resultado.populacao).mul(100_000).round(2)
    resultado["situacao_dado"] = resultado.ano.map(lambda a: "definitivo" if a <= 2024 else "preliminar")
    resultado.to_csv(GOLD_TERRITORIO, index=False, encoding="utf-8-sig")

    faixas = GRUPOS_ETARIOS + ["Idade não informada"]
    grade_i = pd.DataFrame({"ano": list(ANOS)}).merge(pd.DataFrame({"territorio": ["Brasil", "Santa Catarina"]}), how="cross").merge(pd.DataFrame({"indicador": INDICADORES}), how="cross").merge(pd.DataFrame({"grupo_etario": faixas}), how="cross")
    idade = grade_i.merge(contagem_idade, on=["ano", "territorio", "indicador", "grupo_etario"], how="left", validate="one_to_one")
    idade.notificacoes = idade.notificacoes.fillna(0).astype("int64")
    pop_i = pd.read_parquet(POP_IDADE)
    br = pop_i.groupby(["ano", "grupo_etario"], as_index=False).agg(populacao=("populacao", "sum")).assign(territorio="Brasil")
    sc = pop_i.loc[pop_i.sigla_uf.eq("SC")].groupby(["ano", "grupo_etario"], as_index=False).agg(populacao=("populacao", "sum")).assign(territorio="Santa Catarina")
    idade = idade.merge(pd.concat([br, sc]), on=["ano", "territorio", "grupo_etario"], how="left", validate="many_to_one")
    idade.loc[idade.grupo_etario.eq("Idade não informada"), "populacao"] = pd.NA
    idade["taxa_100mil"] = idade.notificacoes.div(idade.populacao).mul(100_000).round(2)
    idade["situacao_dado"] = idade.ano.map(lambda a: "definitivo" if a <= 2024 else "preliminar")
    idade.to_csv(GOLD_IDADE, index=False, encoding="utf-8-sig")
    return resultado, idade


def validar(territorio: pd.DataFrame, idade: pd.DataFrame) -> None:
    novo = pd.read_parquet(SILVER)
    antigo = pd.concat([pd.read_parquet(SINAN_MULHERES), pd.read_parquet(SINAN_MULHERES_2025)], ignore_index=True)
    esperado = antigo.groupby("ano").size().to_dict()
    encontrado = novo.loc[(novo.sexo == "feminino") & (novo.natureza_violencia == "interpessoal")].groupby("ano").size().to_dict()
    if esperado != encontrado: raise ValueError(f"Controle feminino divergente: {esperado} != {encontrado}")
    if territorio.duplicated(["ano", "nivel_territorial", "id_territorio", "indicador", "sexo"]).any(): raise ValueError("Chave territorial duplicada")
    if idade.duplicated(["ano", "territorio", "indicador", "grupo_etario"]).any(): raise ValueError("Chave etária duplicada")
    if territorio.loc[territorio.ano.le(2024) & territorio.sexo.isin(["total", "feminino", "masculino"]), "taxa_100mil"].isna().any(): raise ValueError("Taxa histórica ausente")
    taxas_2025 = territorio.loc[
        territorio.ano.eq(2025) & territorio.sexo.isin(["total", "feminino", "masculino"])
    ]
    if taxas_2025.taxa_100mil.isna().any(): raise ValueError("Taxa de 2025 ausente")
    if not taxas_2025.loc[taxas_2025.sexo.eq("total"), "tipo_denominador"].eq("publicado").all():
        raise ValueError("Denominador total de 2025 não identificado como publicado")
    if not taxas_2025.loc[
        taxas_2025.sexo.isin(["feminino", "masculino"]), "tipo_denominador"
    ].eq("estimado_proporcao_2024").all():
        raise ValueError("Denominador por sexo de 2025 não identificado como estimado")


def main() -> None:
    construir_silver()
    territorio, idade = construir_gold()
    validar(territorio, idade)
    METODOLOGIA.write_text(json.dumps({
        "fonte": "SINAN Violência, arquivos nacionais anuais do DataSUS",
        "territorio": "município de residência da pessoa notificada",
        "interpessoal": "LES_AUTOP igual a 2",
        "autoprovocada": "LES_AUTOP igual a 1",
        "tipos": {nome: f"{campo} igual a 1 e LES_AUTOP igual a 2" for nome, campo in TIPOS.items()},
        "unidade": "notificações, não pessoas únicas",
        "limite": "tipos de violência podem coexistir no mesmo registro",
        "taxas": "2015 a 2024 usam população publicada; 2025 usa população total oficial e população por sexo estimada pela proporção de 2024",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gold territorial SINAN: {len(territorio)} linhas")
    print(f"Gold etária SINAN: {len(idade)} linhas")
    print("SINAN do atlas validado contra a série feminina existente")


if __name__ == "__main__":
    main()
