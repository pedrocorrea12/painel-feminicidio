"""Valida a cobertura e gera as camadas tematicas prioritarias do Sinesp.

O arquivo do Sinesp registra ocorrencias pelo local do fato. Somente linhas de
abrangencia estadual entram nos totais, para evitar dupla contagem com PF e
PRF. Zero e interpretado como ausencia de ocorrencia quando o mes esta
presente. A ausencia da linha mensal e tratada como lacuna de cobertura.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SILVER = ROOT / "data" / "silver" / "sinesp_vde_ocorrencias.parquet"
POP_TOTAL = ROOT / "data" / "silver" / "populacao_municipio_ano.parquet"
POP_SEXO = ROOT / "data" / "silver" / "populacao_municipio_sexo_ano.parquet"
MAPA_MUNICIPIOS = ROOT / "data" / "gold" / "integrado" / "validacao_municipios_sinesp_sc.csv"
GOLD = ROOT / "data" / "gold" / "atlas"
COBERTURA_UF = GOLD / "sinesp_cobertura_evento_uf_ano.csv"
COBERTURA_RESUMO = GOLD / "sinesp_cobertura_evento_resumo.csv"
TERRITORIO_ANO = GOLD / "sinesp_prioridade_territorio_ano.csv"
MENSAL = GOLD / "sinesp_prioridade_mensal.csv"
METODOLOGIA = GOLD / "sinesp_prioridade_metodologia.json"

EVENTOS = [
    "Pessoa Desaparecida",
    "Pessoa Localizada",
    "Suicídio",
    "Feminicídio",
    "Tentativa de feminicídio",
    "Homicídio doloso",
    "Tentativa de homicídio",
    "Estupro",
    "Estupro de vulnerável",
]

# Os nomes sao comparados sem acentos para tolerar a codificacao dos arquivos.
EVENTOS_CANONICOS = {
    "pessoa desaparecida": "Pessoa Desaparecida",
    "pessoa localizada": "Pessoa Localizada",
    "suicidio": "Suicídio",
    "feminicidio": "Feminicídio",
    "tentativa de feminicidio": "Tentativa de feminicídio",
    "homicidio doloso": "Homicídio doloso",
    "tentativa de homicidio": "Tentativa de homicídio",
    "estupro": "Estupro",
    "estupro de vulneravel": "Estupro de vulnerável",
}

EVENTOS_MUNICIPAIS_SC = {
    "Suicídio",
    "Feminicídio",
    "Tentativa de feminicídio",
    "Homicídio doloso",
    "Tentativa de homicídio",
}

INDICADOR_DERIVADO = "Violência sexual policial, soma das classificações"


def sem_acentos(valor: object) -> str:
    import unicodedata

    texto = unicodedata.normalize("NFKD", str(valor))
    return "".join(caractere for caractere in texto if not unicodedata.combining(caractere))


def nome_canonico(valor: object) -> str | None:
    return EVENTOS_CANONICOS.get(sem_acentos(valor).strip().lower())


def meses_esperados(ano: int) -> int:
    return 8 if ano == 2026 else 12


def carregar_base() -> pd.DataFrame:
    colunas = [
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
    ]
    base = pd.read_parquet(SILVER, columns=colunas)
    base = base.loc[base.abrangencia.eq("Estadual")].copy()
    base["indicador"] = base.evento.map(nome_canonico)
    base = base.loc[base.indicador.notna()].copy()
    base["municipio_nao_informado"] = (
        base.municipio.fillna("").map(sem_acentos).str.upper().isin({"", "NAO INFORMADO"})
    )
    numericas = [
        "vitimas_feminino",
        "vitimas_masculino",
        "vitimas_nao_informado",
        "total_vitimas",
    ]
    base[numericas] = base[numericas].fillna(0)
    return base


def construir_cobertura(base: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    chaves = ["indicador", "ano", "sigla_uf"]
    cobertura = (
        base.groupby(chaves, as_index=False)
        .agg(
            meses_informados=("mes", "nunique"),
            municipios_distintos=("municipio", "nunique"),
            municipios_informados=(
                "municipio_nao_informado",
                lambda serie: int((~serie).groupby(base.loc[serie.index, "municipio"]).any().sum()),
            ),
            linhas=("municipio", "size"),
            linhas_municipio_nao_informado=("municipio_nao_informado", "sum"),
            valor_total=("total_vitimas", "sum"),
        )
    )

    valor_nao_informado = (
        base.loc[base.municipio_nao_informado]
        .groupby(chaves, as_index=False)
        .agg(valor_municipio_nao_informado=("total_vitimas", "sum"))
    )
    cobertura = cobertura.merge(valor_nao_informado, on=chaves, how="left", validate="one_to_one")
    cobertura["valor_municipio_nao_informado"] = cobertura.valor_municipio_nao_informado.fillna(0)
    cobertura["meses_esperados"] = cobertura.ano.map(meses_esperados)
    cobertura["cobertura_mensal_completa"] = cobertura.meses_informados.eq(cobertura.meses_esperados)
    cobertura["somente_municipio_nao_informado"] = cobertura.municipios_informados.eq(0)
    cobertura["participacao_valor_municipio_nao_informado_pct"] = (
        cobertura.valor_municipio_nao_informado.div(cobertura.valor_total.where(cobertura.valor_total.ne(0)))
        .mul(100)
        .round(2)
    )
    cobertura["classificacao_cobertura"] = "municipal informada"
    cobertura.loc[~cobertura.cobertura_mensal_completa, "classificacao_cobertura"] = "meses incompletos"
    cobertura.loc[cobertura.somente_municipio_nao_informado, "classificacao_cobertura"] = "somente total estadual"
    cobertura.loc[
        cobertura.participacao_valor_municipio_nao_informado_pct.gt(10)
        & ~cobertura.somente_municipio_nao_informado,
        "classificacao_cobertura",
    ] = "municipal com parcela elevada sem municipio"
    cobertura["situacao_dado"] = cobertura.ano.map(
        lambda ano: "parcial" if ano == 2026 else "consolidado_publicacao"
    )
    cobertura = cobertura.sort_values(chaves).reset_index(drop=True)

    resumo = (
        cobertura.groupby("indicador", as_index=False)
        .agg(
            ano_inicial=("ano", "min"),
            ano_final=("ano", "max"),
            uf_anos_avaliados=("sigla_uf", "size"),
            uf_anos_completos=("cobertura_mensal_completa", "sum"),
            uf_anos_com_cobertura_municipal=("somente_municipio_nao_informado", lambda s: int((~s).sum())),
        )
    )
    sc = cobertura.loc[cobertura.sigla_uf.eq("SC"), [
        "indicador",
        "cobertura_mensal_completa",
        "somente_municipio_nao_informado",
        "municipios_informados",
    ]]
    resumo_sc = sc.groupby("indicador", as_index=False).agg(
        sc_todos_anos_completos=("cobertura_mensal_completa", "all"),
        sc_tem_cobertura_municipal=("somente_municipio_nao_informado", lambda s: bool((~s).all())),
        sc_minimo_municipios_informados=("municipios_informados", "min"),
    )
    resumo = resumo.merge(resumo_sc, on="indicador", how="left", validate="one_to_one")
    resumo["todos_uf_anos_completos"] = resumo.uf_anos_avaliados.eq(resumo.uf_anos_completos)
    resumo["comparabilidade"] = "comparável com ressalva de registro policial"
    resumo.loc[resumo.indicador.eq("Feminicídio"), "comparabilidade"] = "comparável no período observado"
    resumo.loc[
        resumo.indicador.isin({"Estupro", "Estupro de vulnerável"}),
        "comparabilidade",
    ] = "classificação varia entre UFs e anos"
    resumo.loc[
        resumo.indicador.isin({"Pessoa Desaparecida", "Pessoa Localizada"}),
        "comparabilidade",
    ] = "séries separadas, sem razão direta entre registros"
    resumo["ressalva_principal"] = "local do fato e critérios informados pelos estados"
    resumo.loc[resumo.indicador.eq("Estupro"), "ressalva_principal"] = (
        "Santa Catarina tem quebra de classificação entre 2019 e 2020"
    )
    resumo.loc[resumo.indicador.eq("Estupro de vulnerável"), "ressalva_principal"] = (
        "usar junto da categoria Estupro e manter a quebra de Santa Catarina sinalizada"
    )
    resumo.loc[
        resumo.indicador.isin({"Pessoa Desaparecida", "Pessoa Localizada", "Estupro", "Estupro de vulnerável"}),
        "ressalva_principal",
    ] += "; sem detalhamento municipal no arquivo atual"
    resumo = resumo.sort_values("indicador").reset_index(drop=True)
    return cobertura, resumo


def adicionar_indicador_derivado(base: pd.DataFrame) -> pd.DataFrame:
    sexos = [
        "vitimas_feminino",
        "vitimas_masculino",
        "vitimas_nao_informado",
        "total_vitimas",
    ]
    recorte = base.loc[base.indicador.isin({"Estupro", "Estupro de vulnerável"})]
    chaves = ["ano", "mes", "sigla_uf", "municipio", "municipio_nao_informado", "situacao_dado"]
    derivado = recorte.groupby(chaves, as_index=False, dropna=False)[sexos].sum()
    derivado["indicador"] = INDICADOR_DERIVADO
    return pd.concat([base, derivado], ignore_index=True, sort=False)


def denominadores() -> pd.DataFrame:
    total = pd.read_parquet(POP_TOTAL)
    sexo = pd.read_parquet(POP_SEXO)
    partes = []

    br = total.groupby("ano", as_index=False).agg(populacao=("populacao", "sum"))
    partes.append(br.assign(nivel_territorial="brasil", id_territorio="BR", sexo="total"))
    uf = total.groupby(["ano", "sigla_uf"], as_index=False).agg(populacao=("populacao", "sum"))
    partes.append(uf.assign(nivel_territorial="uf", id_territorio=uf.sigla_uf, sexo="total"))
    mun = total.loc[total.sigla_uf.eq("SC")].rename(columns={"id_municipio": "id_territorio"})
    partes.append(mun.assign(nivel_territorial="municipio", sexo="total"))

    br_sexo = sexo.groupby(["ano", "sexo"], as_index=False).agg(populacao=("populacao", "sum"))
    partes.append(br_sexo.assign(nivel_territorial="brasil", id_territorio="BR"))
    uf_sexo = sexo.groupby(["ano", "sigla_uf", "sexo"], as_index=False).agg(populacao=("populacao", "sum"))
    partes.append(uf_sexo.assign(nivel_territorial="uf", id_territorio=uf_sexo.sigla_uf))
    mun_sexo = sexo.loc[sexo.sigla_uf.eq("SC")].rename(columns={"id_municipio": "id_territorio"})
    partes.append(mun_sexo.assign(nivel_territorial="municipio"))

    colunas = ["ano", "nivel_territorial", "id_territorio", "sexo", "populacao"]
    return pd.concat([parte[colunas] for parte in partes], ignore_index=True)


def dimensao_municipios() -> pd.DataFrame:
    mapa = pd.read_csv(MAPA_MUNICIPIOS, dtype={"id_municipio": "string"})
    mapa = mapa.loc[mapa.tipo_registro.eq("municipio") & mapa.correspondencia.eq("encontrada")].copy()
    if len(mapa) != 295:
        raise ValueError(f"Mapa municipal de Santa Catarina incompleto: {len(mapa)}")
    return mapa[["municipio_sinesp", "id_municipio", "municipio_ibge"]].rename(
        columns={"municipio_sinesp": "municipio", "municipio_ibge": "territorio"}
    )


def agregar_sexos(base: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    mapa = {
        "total": "total_vitimas",
        "feminino": "vitimas_feminino",
        "masculino": "vitimas_masculino",
        "não informado": "vitimas_nao_informado",
    }
    partes = []
    for sexo, coluna in mapa.items():
        agregado = base.groupby(chaves, as_index=False, dropna=False).agg(valor_absoluto=(coluna, "sum"))
        agregado["sexo"] = sexo
        partes.append(agregado)
    return pd.concat(partes, ignore_index=True)


def construir_territorio_ano(base: pd.DataFrame) -> pd.DataFrame:
    base = adicionar_indicador_derivado(base)
    indicadores = EVENTOS + [INDICADOR_DERIVADO]
    partes = []

    br = agregar_sexos(base, ["ano", "indicador", "situacao_dado"])
    br = br.assign(nivel_territorial="brasil", id_territorio="BR", territorio="Brasil")
    partes.append(br)

    uf = agregar_sexos(base, ["ano", "sigla_uf", "indicador", "situacao_dado"])
    uf = uf.assign(nivel_territorial="uf", id_territorio=uf.sigla_uf, territorio=uf.sigla_uf)
    partes.append(uf)

    mapa = dimensao_municipios()
    municipal = base.loc[
        base.sigla_uf.eq("SC")
        & base.indicador.isin(EVENTOS_MUNICIPAIS_SC)
        & ~base.municipio_nao_informado
    ].merge(mapa, on="municipio", how="left", validate="many_to_one")
    if municipal.id_municipio.isna().any():
        ausentes = sorted(municipal.loc[municipal.id_municipio.isna(), "municipio"].unique())
        raise ValueError(f"Municipios sem correspondencia: {ausentes}")
    mun = agregar_sexos(
        municipal,
        ["ano", "id_municipio", "territorio", "indicador", "situacao_dado"],
    ).rename(columns={"id_municipio": "id_territorio"})
    mun["nivel_territorial"] = "municipio"
    partes.append(mun)

    resultado = pd.concat(partes, ignore_index=True, sort=False)
    resultado = resultado.loc[resultado.indicador.isin(indicadores)].copy()
    resultado = resultado.merge(
        denominadores(),
        on=["ano", "nivel_territorial", "id_territorio", "sexo"],
        how="left",
        validate="many_to_one",
    )
    resultado.loc[resultado.sexo.eq("não informado"), "populacao"] = pd.NA
    resultado["taxa_100mil"] = resultado.valor_absoluto.div(resultado.populacao).mul(100_000).round(2)
    resultado["meses_observados"] = resultado.ano.map(lambda ano: 8 if ano == 2026 else 12)
    resultado["periodo_completo"] = resultado.ano.ne(2026)
    resultado["base_territorial"] = "local do fato"
    resultado["cobertura_municipal_disponivel"] = ~resultado.indicador.isin(
        {"Pessoa Desaparecida", "Pessoa Localizada", "Estupro", "Estupro de vulnerável", INDICADOR_DERIVADO}
    )
    resultado["cobertura_municipal_disponivel"] = resultado[
        "cobertura_municipal_disponivel"
    ].astype("object")
    resultado.loc[resultado.nivel_territorial.ne("municipio"), "cobertura_municipal_disponivel"] = pd.NA
    colunas = [
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "ano",
        "indicador",
        "sexo",
        "valor_absoluto",
        "populacao",
        "taxa_100mil",
        "meses_observados",
        "periodo_completo",
        "situacao_dado",
        "base_territorial",
        "cobertura_municipal_disponivel",
    ]
    return resultado[colunas].sort_values(
        ["ano", "nivel_territorial", "id_territorio", "indicador", "sexo"]
    ).reset_index(drop=True)


def construir_mensal(base: pd.DataFrame) -> pd.DataFrame:
    base = adicionar_indicador_derivado(base)
    partes = []
    for territorio, filtro in [
        ("Brasil", pd.Series(True, index=base.index)),
        ("Santa Catarina", base.sigla_uf.eq("SC")),
    ]:
        agregado = agregar_sexos(
            base.loc[filtro],
            ["ano", "mes", "indicador", "situacao_dado"],
        )
        agregado["territorio"] = territorio
        partes.append(agregado)
    resultado = pd.concat(partes, ignore_index=True)
    resultado["periodo_completo"] = resultado.ano.ne(2026)
    resultado["base_territorial"] = "local do fato"
    return resultado[
        [
            "territorio",
            "ano",
            "mes",
            "indicador",
            "sexo",
            "valor_absoluto",
            "periodo_completo",
            "situacao_dado",
            "base_territorial",
        ]
    ].sort_values(["ano", "mes", "territorio", "indicador", "sexo"]).reset_index(drop=True)


def validar(
    cobertura: pd.DataFrame,
    resumo: pd.DataFrame,
    territorio: pd.DataFrame,
    mensal: pd.DataFrame,
) -> None:
    assert len(cobertura) == 9 * 8 * 27
    assert cobertura.cobertura_mensal_completa.all()
    assert resumo.todos_uf_anos_completos.all()
    assert set(resumo.loc[resumo.sc_tem_cobertura_municipal, "indicador"]) == EVENTOS_MUNICIPAIS_SC
    assert set(resumo.loc[~resumo.sc_tem_cobertura_municipal, "indicador"]) == {
        "Pessoa Desaparecida",
        "Pessoa Localizada",
        "Estupro",
        "Estupro de vulnerável",
    }
    assert territorio.loc[territorio.ano.ge(2025), "taxa_100mil"].isna().all()
    assert not territorio.duplicated(
        ["nivel_territorial", "id_territorio", "ano", "indicador", "sexo"]
    ).any()
    assert not mensal.duplicated(["territorio", "ano", "mes", "indicador", "sexo"]).any()
    assert int(
        territorio.loc[
            territorio.nivel_territorial.eq("brasil")
            & territorio.ano.eq(2025)
            & territorio.indicador.eq("Feminicídio")
            & territorio.sexo.eq("total"),
            "valor_absoluto",
        ].iloc[0]
    ) > 0


def escrever_metodologia() -> None:
    conteudo = {
        "fonte": "Sinesp VDE, Ministério da Justiça e Segurança Pública",
        "periodo": "2019 a agosto de 2026",
        "unidade": "vítimas",
        "territorio_referencia": "local do fato",
        "abrangencia_incluida": "Estadual",
        "abrangencias_excluidas": ["Polícia Federal", "Polícia Rodoviária Federal"],
        "eventos_prioritarios": EVENTOS,
        "indicador_derivado": {
            "nome": INDICADOR_DERIVADO,
            "calculo": "Estupro mais Estupro de vulnerável",
            "ressalva": "não elimina quebras de classificação entre UFs e anos",
        },
        "regras": [
            "linhas repetidas no mesmo mês são somadas",
            "zero significa ausência de ocorrência quando a linha mensal existe",
            "mês sem linha seria tratado como lacuna",
            "taxas usam população total ou do sexo correspondente",
            "taxas são calculadas somente até 2024",
            "2026 cobre janeiro a agosto e permanece parcial",
            "estupro, estupro de vulnerável, pessoa desaparecida e pessoa localizada não têm detalhamento municipal no arquivo atual",
        ],
        "quebras_conhecidas": [
            "Santa Catarina muda a classificação de Estupro entre 2019 e 2020",
            "Espírito Santo, Rondônia e Maranhão têm quedas atípicas em anos específicos para estupro",
        ],
    }
    METODOLOGIA.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    obrigatorios = [SILVER, POP_TOTAL, POP_SEXO, MAPA_MUNICIPIOS]
    ausentes = [str(caminho.relative_to(ROOT)) for caminho in obrigatorios if not caminho.exists()]
    if ausentes:
        raise FileNotFoundError(f"Arquivos ausentes: {ausentes}")

    base = carregar_base()
    cobertura, resumo = construir_cobertura(base)
    territorio = construir_territorio_ano(base)
    mensal = construir_mensal(base)
    validar(cobertura, resumo, territorio, mensal)

    GOLD.mkdir(parents=True, exist_ok=True)
    cobertura.to_csv(COBERTURA_UF, index=False, encoding="utf-8-sig")
    resumo.to_csv(COBERTURA_RESUMO, index=False, encoding="utf-8-sig")
    territorio.to_csv(TERRITORIO_ANO, index=False, encoding="utf-8-sig")
    mensal.to_csv(MENSAL, index=False, encoding="utf-8-sig")
    escrever_metodologia()

    print(f"Cobertura por UF e ano: {len(cobertura)} linhas")
    print(f"Resumo de cobertura: {len(resumo)} indicadores")
    print(f"Gold territorial: {len(territorio)} linhas")
    print(f"Gold mensal: {len(mensal)} linhas")


if __name__ == "__main__":
    main()
