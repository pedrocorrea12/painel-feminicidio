"""Gera tabelas integradas de SINAN, SIM, Sinesp e população feminina.

O script não altera os arquivos do painel. As saídas ficam em
``data/gold/integrado`` e o relatório analítico fica em ``docs``.

Rodar: ``python pipeline/build_integrated_analysis.py``.
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
RELATORIO = ROOT / "docs" / "RELATORIO_INTEGRACAO_DADOS.md"

INDICADORES = SILVER / "indicadores_territorio_ano.parquet"
POPULACAO = SILVER / "populacao_feminina_municipio.parquet"
SINAN = SILVER / "sinan_viol_mulheres_interpessoal.parquet"
SINAN_2025 = SILVER / "sinan_viol_mulheres_interpessoal_2025_preliminar.parquet"
SIM = SILVER / "sim_mulheres_agressao.parquet"
SINESP = SILVER / "sinesp_feminicidio.parquet"

HISTORICO = DESTINO / "historico_integrado_2019_2024.csv"
MONITORAMENTO = DESTINO / "monitoramento_atual_2025_2026.csv"
VALIDACAO_MUNICIPIOS = DESTINO / "validacao_municipios_sinesp_sc.csv"
RESUMO = DESTINO / "resumo_integracao.json"
README = DESTINO / "README.md"

NIVEL_ORDEM = {"brasil": 0, "uf": 1, "municipio": 2}


def _normalizar_nome(valor: object) -> str:
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = texto.encode("ascii", "ignore").decode("ascii").upper()
    return re.sub(r"[^A-Z0-9]+", " ", texto).strip()


def _formatar_numero(valor: int | float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def _formatar_percentual(valor: float) -> str:
    sinal = "+" if valor > 0 else ""
    return f"{sinal}{valor:.1f}%".replace(".", ",")


def _formatar_taxa(valor: float) -> str:
    return f"{valor:.2f}".replace(".", ",")


def _carregar_fontes() -> dict[str, pd.DataFrame]:
    arquivos = [INDICADORES, POPULACAO, SINAN, SINAN_2025, SIM, SINESP]
    ausentes = [str(caminho) for caminho in arquivos if not caminho.exists()]
    if ausentes:
        raise FileNotFoundError(f"Arquivos Silver ausentes: {ausentes}")
    return {
        "indicadores": pd.read_parquet(INDICADORES),
        "populacao": pd.read_parquet(POPULACAO),
        "sinan": pd.read_parquet(
            SINAN, columns=["ano", "DT_NOTIFIC", "SG_UF", "id_municipio"]
        ),
        "sinan_2025": pd.read_parquet(
            SINAN_2025, columns=["ano", "DT_NOTIFIC", "SG_UF", "id_municipio"]
        ),
        "sim": pd.read_parquet(
            SIM,
            columns=[
                "ano", "DTOBITO", "id_municipio", "sigla_uf", "situacao_dado"
            ],
        ),
        "sinesp": pd.read_parquet(SINESP),
    }


def _cadastro_territorial(populacao: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    municipios = (
        populacao.loc[populacao["sigla_uf"].eq("SC"), ["id_municipio", "municipio", "sigla_uf"]]
        .drop_duplicates()
        .sort_values("id_municipio")
        .reset_index(drop=True)
    )
    if len(municipios) != 295:
        raise ValueError(f"Esperados 295 municípios de SC, encontrados {len(municipios)}")
    if municipios["id_municipio"].duplicated().any():
        raise ValueError("Cadastro populacional de SC possui código municipal duplicado")

    territorios = pd.concat(
        [
            pd.DataFrame(
                [
                    {
                        "nivel_territorial": "brasil",
                        "id_territorio": "BR",
                        "territorio": "Brasil",
                        "sigla_uf": "",
                    },
                    {
                        "nivel_territorial": "uf",
                        "id_territorio": "SC",
                        "territorio": "Santa Catarina",
                        "sigla_uf": "SC",
                    },
                ]
            ),
            municipios.rename(
                columns={"id_municipio": "id_territorio", "municipio": "territorio"}
            ).assign(nivel_territorial="municipio")[
                ["nivel_territorial", "id_territorio", "territorio", "sigla_uf"]
            ],
        ],
        ignore_index=True,
    )
    return territorios, municipios


def _mapa_municipios(
    sinesp: pd.DataFrame, municipios: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, str]]:
    ibge = municipios.copy()
    ibge["chave_nome"] = ibge["municipio"].map(_normalizar_nome)
    if ibge["chave_nome"].duplicated().any():
        duplicados = ibge.loc[ibge["chave_nome"].duplicated(False), "municipio"].tolist()
        raise ValueError(f"Nomes municipais duplicados após normalização: {duplicados}")

    sc = sinesp.loc[sinesp["sigla_uf"].eq("SC")].copy()
    nomes = pd.DataFrame(
        {"municipio_sinesp": sorted(sc["municipio"].dropna().unique().tolist())}
    )
    nomes["chave_nome"] = nomes["municipio_sinesp"].map(_normalizar_nome)
    if nomes["chave_nome"].duplicated().any():
        duplicados = nomes.loc[nomes["chave_nome"].duplicated(False), "municipio_sinesp"].tolist()
        raise ValueError(f"Nomes do Sinesp duplicados após normalização: {duplicados}")

    cobertura = (
        sc.assign(chave_nome=sc["municipio"].map(_normalizar_nome))
        .groupby("chave_nome", as_index=False)
        .agg(
            primeiro_ano=("ano", "min"),
            ultimo_ano=("ano", "max"),
            anos_presentes=("ano", "nunique"),
            periodos_ano_mes=("mes", "size"),
            total_vitimas_2019_2026=("vitimas_feminicidio", "sum"),
        )
    )
    validacao = nomes.merge(cobertura, on="chave_nome", how="left", validate="one_to_one")
    validacao = validacao.merge(
        ibge[["chave_nome", "id_municipio", "municipio"]],
        on="chave_nome",
        how="left",
        validate="one_to_one",
    ).rename(columns={"municipio": "municipio_ibge"})
    validacao["tipo_registro"] = "municipio"
    especial = validacao["chave_nome"].eq("NAO INFORMADO")
    validacao.loc[especial, "tipo_registro"] = "registro_especial"
    validacao["correspondencia"] = "nao_encontrada"
    validacao.loc[validacao["id_municipio"].notna(), "correspondencia"] = "encontrada"
    validacao.loc[especial, "correspondencia"] = "nao_se_aplica"
    validacao["cobertura_esperada"] = validacao["periodos_ano_mes"].eq(92)
    validacao["observacao"] = ""
    validacao.loc[especial, "observacao"] = (
        "Registro de origem sem município informado. Não recebe código IBGE."
    )

    municipios_nao_encontrados = validacao.loc[
        validacao["tipo_registro"].eq("municipio")
        & validacao["id_municipio"].isna(),
        "municipio_sinesp",
    ].tolist()
    if municipios_nao_encontrados:
        raise ValueError(
            f"Municípios do Sinesp sem correspondência no IBGE: {municipios_nao_encontrados}"
        )
    if int(validacao["id_municipio"].notna().sum()) != 295:
        raise ValueError("A validação não encontrou exatamente 295 municípios de SC")

    mapa = (
        validacao.dropna(subset=["id_municipio"])
        .set_index("chave_nome")["id_municipio"]
        .astype(str)
        .to_dict()
    )
    ordem = [
        "tipo_registro",
        "municipio_sinesp",
        "chave_nome",
        "id_municipio",
        "municipio_ibge",
        "correspondencia",
        "primeiro_ano",
        "ultimo_ano",
        "anos_presentes",
        "periodos_ano_mes",
        "cobertura_esperada",
        "total_vitimas_2019_2026",
        "observacao",
    ]
    return validacao[ordem].sort_values(["tipo_registro", "municipio_sinesp"]), mapa


def _agregar_sinesp(
    dados: pd.DataFrame,
    territorios: pd.DataFrame,
    mapa_municipios: dict[str, str],
) -> pd.DataFrame:
    dados = dados.copy()
    dados["chave_nome"] = dados["municipio"].map(_normalizar_nome)
    linhas = []
    for ano, ano_base in dados.groupby("ano"):
        valores = territorios.copy()
        valores["ano"] = int(ano)
        valores["valor"] = 0
        valores.loc[valores["nivel_territorial"].eq("brasil"), "valor"] = int(
            ano_base["vitimas_feminicidio"].sum()
        )
        sc = ano_base.loc[ano_base["sigla_uf"].eq("SC")]
        valores.loc[valores["nivel_territorial"].eq("uf"), "valor"] = int(
            sc["vitimas_feminicidio"].sum()
        )
        municipal = (
            sc.assign(id_territorio=sc["chave_nome"].map(mapa_municipios))
            .dropna(subset=["id_territorio"])
            .groupby("id_territorio")["vitimas_feminicidio"]
            .sum()
        )
        alvo = valores["nivel_territorial"].eq("municipio")
        valores.loc[alvo, "valor"] = (
            valores.loc[alvo, "id_territorio"].map(municipal).fillna(0).astype("int64")
        )
        linhas.append(valores)
    resultado = pd.concat(linhas, ignore_index=True)
    resultado["valor"] = resultado["valor"].astype("int64")
    return resultado


def _agregar_registros(
    dados: pd.DataFrame,
    territorios: pd.DataFrame,
    coluna_uf: str,
    valor_sc: str,
) -> pd.DataFrame:
    valores = territorios.copy()
    valores["valor"] = 0
    valores.loc[valores["nivel_territorial"].eq("brasil"), "valor"] = len(dados)
    sc = dados.loc[dados[coluna_uf].fillna("").astype(str).eq(valor_sc)].copy()
    valores.loc[valores["nivel_territorial"].eq("uf"), "valor"] = len(sc)
    municipal = sc.groupby("id_municipio").size()
    alvo = valores["nivel_territorial"].eq("municipio")
    valores.loc[alvo, "valor"] = (
        valores.loc[alvo, "id_territorio"].map(municipal).fillna(0).astype("int64")
    )
    valores["valor"] = valores["valor"].astype("int64")
    return valores


def _historico(
    indicadores: pd.DataFrame,
    sinesp: pd.DataFrame,
    territorios: pd.DataFrame,
    mapa_municipios: dict[str, str],
) -> pd.DataFrame:
    base = indicadores.loc[
        indicadores["ano"].between(2019, 2024)
        & (
            indicadores["nivel_territorial"].eq("brasil")
            | (
                indicadores["nivel_territorial"].eq("uf")
                & indicadores["id_territorio"].eq("SC")
            )
            | (
                indicadores["nivel_territorial"].eq("municipio")
                & indicadores["sigla_uf"].eq("SC")
            )
        )
    ].copy()
    base = base.rename(
        columns={
            "notificacoes": "sinan_notificacoes",
            "parceiro": "sinan_notificacoes_parceiro",
            "taxa_notificacoes_100mil": "sinan_taxa_notificacoes_100mil",
            "taxa_parceiro_100mil": "sinan_taxa_parceiro_100mil",
            "obitos_mulheres_agressao": "sim_obitos_mulheres_agressao",
            "taxa_obitos_mulheres_agressao_100mil": "sim_taxa_obitos_agressao_100mil",
        }
    )
    sinesp_anual = _agregar_sinesp(
        sinesp.loc[sinesp["ano"].between(2019, 2024)],
        territorios,
        mapa_municipios,
    ).rename(columns={"valor": "sinesp_vitimas_feminicidio"})
    chaves = ["ano", "nivel_territorial", "id_territorio"]
    base = base.merge(
        sinesp_anual[chaves + ["sinesp_vitimas_feminicidio"]],
        on=chaves,
        how="left",
        validate="one_to_one",
    )
    base["sinesp_vitimas_feminicidio"] = (
        base["sinesp_vitimas_feminicidio"].fillna(0).astype("int64")
    )
    base["sinesp_taxa_feminicidio_100mil"] = (
        base["sinesp_vitimas_feminicidio"].div(base["populacao_feminina"]) * 100_000
    ).round(2)
    base["sinesp_dado_suficiente"] = (
        base["nivel_territorial"].ne("municipio")
        | base["sinesp_vitimas_feminicidio"].ge(5)
    )
    base["sinan_situacao_dado"] = "definitivo"
    base["sim_situacao_dado"] = "definitivo"
    base["sinesp_situacao_dado"] = "consolidado_publicacao"
    base["sinan_base_territorial"] = "residencia_da_vitima"
    base["sim_base_territorial"] = "residencia_da_vitima"
    base["sinesp_base_territorial"] = "municipio_do_fato"
    colunas = [
        "ano",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "sigla_uf",
        "populacao_feminina",
        "sinan_notificacoes",
        "sinan_notificacoes_parceiro",
        "sinan_taxa_notificacoes_100mil",
        "sinan_taxa_parceiro_100mil",
        "sim_obitos_mulheres_agressao",
        "sim_taxa_obitos_agressao_100mil",
        "sinesp_vitimas_feminicidio",
        "sinesp_taxa_feminicidio_100mil",
        "dado_suficiente",
        "sinesp_dado_suficiente",
        "sinan_situacao_dado",
        "sim_situacao_dado",
        "sinesp_situacao_dado",
        "sinan_base_territorial",
        "sim_base_territorial",
        "sinesp_base_territorial",
    ]
    base["ordem_nivel"] = base["nivel_territorial"].map(NIVEL_ORDEM)
    base = base.sort_values(["ano", "ordem_nivel", "id_territorio"]).drop(
        columns="ordem_nivel"
    )
    base = base[colunas].reset_index(drop=True)
    if len(base) != 6 * len(territorios):
        raise ValueError(f"Histórico integrado com {len(base)} linhas, esperado {6 * len(territorios)}")
    if base.duplicated(chaves).any():
        raise ValueError("Histórico integrado possui chave duplicada")
    if base.isna().any().any():
        raise ValueError("Histórico integrado possui valores nulos")
    return base


def _montar_linha_monitoramento(
    atual: pd.DataFrame,
    anterior: pd.DataFrame,
    fonte: str,
    indicador: str,
    ano: int,
    ano_comparacao: int,
    periodo_referencia: str,
    data_inicio: str,
    data_fim: str,
    meses_informados: int,
    situacao_dado: str,
    situacao_comparacao: str,
    base_territorial: str,
) -> pd.DataFrame:
    chaves = ["nivel_territorial", "id_territorio", "territorio", "sigla_uf"]
    resultado = atual.rename(columns={"valor": "valor_absoluto"}).merge(
        anterior[chaves + ["valor"]].rename(columns={"valor": "valor_periodo_anterior"}),
        on=chaves,
        how="left",
        validate="one_to_one",
    )
    resultado.insert(0, "fonte", fonte)
    resultado.insert(1, "indicador", indicador)
    resultado.insert(2, "ano", ano)
    resultado.insert(3, "ano_comparacao", ano_comparacao)
    resultado["periodo_referencia"] = periodo_referencia
    resultado["data_inicio"] = data_inicio
    resultado["data_fim"] = data_fim
    resultado["meses_informados"] = meses_informados
    resultado["situacao_dado"] = situacao_dado
    resultado["situacao_comparacao"] = situacao_comparacao
    resultado["base_territorial"] = base_territorial
    resultado["comparacao_mesmo_periodo"] = True
    resultado["variacao_absoluta"] = (
        resultado["valor_absoluto"] - resultado["valor_periodo_anterior"]
    )
    resultado["variacao_percentual"] = (
        resultado["variacao_absoluta"]
        .div(resultado["valor_periodo_anterior"].where(resultado["valor_periodo_anterior"].ne(0)))
        .mul(100)
        .round(2)
    )
    return resultado


def _monitoramento(
    sinan: pd.DataFrame,
    sinan_2025: pd.DataFrame,
    sim: pd.DataFrame,
    sinesp: pd.DataFrame,
    territorios: pd.DataFrame,
    mapa_municipios: dict[str, str],
) -> pd.DataFrame:
    partes = []

    sinan_2024 = _agregar_registros(
        sinan.loc[sinan["ano"].eq(2024)], territorios, "SG_UF", "42"
    )
    sinan_atual = _agregar_registros(sinan_2025, territorios, "SG_UF", "42")
    partes.append(
        _montar_linha_monitoramento(
            sinan_atual,
            sinan_2024,
            "SINAN",
            "notificacoes_violencia_interpessoal",
            2025,
            2024,
            "ano_completo",
            "2025-01-01",
            "2025-12-31",
            12,
            "preliminar",
            "definitivo",
            "residencia_da_vitima",
        )
    )

    sim = sim.copy()
    data_texto = sim["DTOBITO"].astype(str).str.strip()
    formato_separado = data_texto.str.contains("-", regex=False)
    sim["data_obito"] = pd.NaT
    sim.loc[formato_separado, "data_obito"] = pd.to_datetime(
        data_texto.loc[formato_separado], format="%d-%m-%Y", errors="coerce"
    )
    sim.loc[~formato_separado, "data_obito"] = pd.to_datetime(
        data_texto.loc[~formato_separado].str.zfill(8),
        format="%d%m%Y",
        errors="coerce",
    )
    if sim["data_obito"].isna().any():
        raise ValueError("SIM possui datas de óbito inválidas")
    for ano, anterior, situacao, situacao_anterior in [
        (2025, 2024, "preliminar", "definitivo"),
        (2026, 2025, "previa", "preliminar"),
    ]:
        atual = sim.loc[
            sim["ano"].eq(ano)
            & (
                (sim["data_obito"].dt.month.lt(8))
                | (
                    sim["data_obito"].dt.month.eq(8)
                    & sim["data_obito"].dt.day.le(26)
                )
            )
        ]
        comparacao = sim.loc[
            sim["ano"].eq(anterior)
            & (
                (sim["data_obito"].dt.month.lt(8))
                | (
                    sim["data_obito"].dt.month.eq(8)
                    & sim["data_obito"].dt.day.le(26)
                )
            )
        ]
        atual_agregado = _agregar_registros(atual, territorios, "sigla_uf", "SC")
        anterior_agregado = _agregar_registros(
            comparacao, territorios, "sigla_uf", "SC"
        )
        partes.append(
            _montar_linha_monitoramento(
                atual_agregado,
                anterior_agregado,
                "SIM",
                "obitos_mulheres_por_agressao",
                ano,
                anterior,
                "01_janeiro_a_26_agosto",
                f"{ano}-01-01",
                f"{ano}-08-26",
                8,
                situacao,
                situacao_anterior,
                "residencia_da_vitima",
            )
        )

    sinesp_2024 = _agregar_sinesp(
        sinesp.loc[sinesp["ano"].eq(2024)], territorios, mapa_municipios
    ).drop(columns="ano")
    sinesp_2025 = _agregar_sinesp(
        sinesp.loc[sinesp["ano"].eq(2025)], territorios, mapa_municipios
    ).drop(columns="ano")
    partes.append(
        _montar_linha_monitoramento(
            sinesp_2025,
            sinesp_2024,
            "Sinesp VDE",
            "vitimas_de_feminicidio",
            2025,
            2024,
            "ano_completo",
            "2025-01-01",
            "2025-12-31",
            12,
            "consolidado_publicacao",
            "consolidado_publicacao",
            "municipio_do_fato",
        )
    )
    sinesp_2025_ago = _agregar_sinesp(
        sinesp.loc[sinesp["ano"].eq(2025) & sinesp["mes"].le(8)],
        territorios,
        mapa_municipios,
    ).drop(columns="ano")
    sinesp_2026_ago = _agregar_sinesp(
        sinesp.loc[sinesp["ano"].eq(2026) & sinesp["mes"].le(8)],
        territorios,
        mapa_municipios,
    ).drop(columns="ano")
    partes.append(
        _montar_linha_monitoramento(
            sinesp_2026_ago,
            sinesp_2025_ago,
            "Sinesp VDE",
            "vitimas_de_feminicidio",
            2026,
            2025,
            "janeiro_a_agosto",
            "2026-01-01",
            "2026-08-31",
            8,
            "parcial",
            "recorte_comparavel",
            "municipio_do_fato",
        )
    )

    resultado = pd.concat(partes, ignore_index=True)
    resultado["ordem_nivel"] = resultado["nivel_territorial"].map(NIVEL_ORDEM)
    resultado = resultado.sort_values(
        ["fonte", "ano", "ordem_nivel", "id_territorio"]
    ).drop(columns="ordem_nivel")
    colunas = [
        "fonte",
        "indicador",
        "ano",
        "ano_comparacao",
        "periodo_referencia",
        "data_inicio",
        "data_fim",
        "meses_informados",
        "situacao_dado",
        "situacao_comparacao",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "sigla_uf",
        "base_territorial",
        "valor_absoluto",
        "valor_periodo_anterior",
        "variacao_absoluta",
        "variacao_percentual",
        "comparacao_mesmo_periodo",
    ]
    resultado = resultado[colunas].reset_index(drop=True)
    esperado = 5 * len(territorios)
    if len(resultado) != esperado:
        raise ValueError(f"Monitoramento com {len(resultado)} linhas, esperado {esperado}")
    chave = ["fonte", "indicador", "ano", "nivel_territorial", "id_territorio"]
    if resultado.duplicated(chave).any():
        raise ValueError("Monitoramento possui chave duplicada")
    return resultado


def _registro(
    dados: pd.DataFrame, fonte: str, ano: int, id_territorio: str
) -> pd.Series:
    recorte = dados.loc[
        dados["fonte"].eq(fonte)
        & dados["ano"].eq(ano)
        & dados["id_territorio"].eq(id_territorio)
    ]
    if len(recorte) != 1:
        raise ValueError(
            f"Registro não único para fonte={fonte}, ano={ano}, território={id_territorio}"
        )
    return recorte.iloc[0]


def _gerar_relatorio(
    historico: pd.DataFrame,
    monitoramento: pd.DataFrame,
    validacao: pd.DataFrame,
) -> tuple[str, dict]:
    sinan_br = _registro(monitoramento, "SINAN", 2025, "BR")
    sinan_sc = _registro(monitoramento, "SINAN", 2025, "SC")
    sinesp_br_2025 = _registro(monitoramento, "Sinesp VDE", 2025, "BR")
    sinesp_sc_2025 = _registro(monitoramento, "Sinesp VDE", 2025, "SC")
    sinesp_br_2026 = _registro(monitoramento, "Sinesp VDE", 2026, "BR")
    sinesp_sc_2026 = _registro(monitoramento, "Sinesp VDE", 2026, "SC")
    sim_br_2025 = _registro(monitoramento, "SIM", 2025, "BR")
    sim_sc_2025 = _registro(monitoramento, "SIM", 2025, "SC")
    sim_br_2026 = _registro(monitoramento, "SIM", 2026, "BR")
    sim_sc_2026 = _registro(monitoramento, "SIM", 2026, "SC")

    positivos_2025 = int(
        monitoramento.loc[
            monitoramento["fonte"].eq("Sinesp VDE")
            & monitoramento["ano"].eq(2025)
            & monitoramento["nivel_territorial"].eq("municipio")
            & monitoramento["valor_absoluto"].gt(0)
        ].shape[0]
    )
    encontrados = int(validacao["correspondencia"].eq("encontrada").sum())
    especiais = int(validacao["tipo_registro"].eq("registro_especial").sum())

    br_2019 = historico.loc[
        historico["ano"].eq(2019) & historico["id_territorio"].eq("BR")
    ].iloc[0]
    br_2024 = historico.loc[
        historico["ano"].eq(2024) & historico["id_territorio"].eq("BR")
    ].iloc[0]
    sc_2019 = historico.loc[
        historico["ano"].eq(2019) & historico["id_territorio"].eq("SC")
    ].iloc[0]
    sc_2024 = historico.loc[
        historico["ano"].eq(2024) & historico["id_territorio"].eq("SC")
    ].iloc[0]

    resumo = {
        "gerado_em": date.today().isoformat(),
        "arquivos": {
            "historico": str(HISTORICO.relative_to(ROOT)),
            "monitoramento": str(MONITORAMENTO.relative_to(ROOT)),
            "validacao_municipios": str(VALIDACAO_MUNICIPIOS.relative_to(ROOT)),
            "relatorio": str(RELATORIO.relative_to(ROOT)),
        },
        "controle": {
            "linhas_historico": len(historico),
            "linhas_monitoramento": len(monitoramento),
            "registros_validacao_municipios": len(validacao),
            "municipios_sc_correspondencia_encontrada": encontrados,
            "registros_especiais_sinesp": especiais,
            "municipios_sc_com_feminicidio_2025": positivos_2025,
        },
        "atuais": {
            "sinan_2025_brasil": int(sinan_br.valor_absoluto),
            "sinan_2025_sc": int(sinan_sc.valor_absoluto),
            "sinesp_2025_brasil": int(sinesp_br_2025.valor_absoluto),
            "sinesp_2025_sc": int(sinesp_sc_2025.valor_absoluto),
            "sinesp_2026_jan_ago_brasil": int(sinesp_br_2026.valor_absoluto),
            "sinesp_2026_jan_ago_sc": int(sinesp_sc_2026.valor_absoluto),
            "sim_2025_ate_26_ago_brasil": int(sim_br_2025.valor_absoluto),
            "sim_2025_ate_26_ago_sc": int(sim_sc_2025.valor_absoluto),
            "sim_2026_ate_26_ago_brasil": int(sim_br_2026.valor_absoluto),
            "sim_2026_ate_26_ago_sc": int(sim_sc_2026.valor_absoluto),
        },
    }

    texto = f"""# Relatório de integração dos dados

Atualizado em {date.today().isoformat()}.

## Escopo concluído

1. A série histórica comum reúne SINAN, SIM, Sinesp VDE e população feminina para 2019 a 2024.
2. O monitoramento recente usa números absolutos e compara períodos equivalentes em 2025 e 2026.
3. Os municípios do Sinesp foram associados ao cadastro populacional de Santa Catarina.
4. As limitações de conceito, território, cobertura e situação dos dados foram registradas.

O painel não foi alterado nem publicado durante este trabalho.

## Resultados principais

1. O SINAN preliminar de 2025 contém {_formatar_numero(sinan_br.valor_absoluto)} notificações no Brasil e {_formatar_numero(sinan_sc.valor_absoluto)} em Santa Catarina. Em relação a 2024, as variações são {_formatar_percentual(sinan_br.variacao_percentual)} no Brasil e {_formatar_percentual(sinan_sc.variacao_percentual)} em Santa Catarina.
2. O Sinesp registra {_formatar_numero(sinesp_br_2025.valor_absoluto)} vítimas de feminicídio no Brasil e {_formatar_numero(sinesp_sc_2025.valor_absoluto)} em Santa Catarina em 2025. As variações sobre 2024 são {_formatar_percentual(sinesp_br_2025.variacao_percentual)} e {_formatar_percentual(sinesp_sc_2025.variacao_percentual)}, respectivamente.
3. Entre janeiro e agosto de 2026, o Sinesp registra {_formatar_numero(sinesp_br_2026.valor_absoluto)} vítimas no Brasil e {_formatar_numero(sinesp_sc_2026.valor_absoluto)} em Santa Catarina. Contra janeiro a agosto de 2025, as variações são {_formatar_percentual(sinesp_br_2026.variacao_percentual)} e {_formatar_percentual(sinesp_sc_2026.variacao_percentual)}.
4. O SIM registra {_formatar_numero(sim_br_2026.valor_absoluto)} mortes de mulheres por agressão no Brasil e {_formatar_numero(sim_sc_2026.valor_absoluto)} em Santa Catarina entre 1 de janeiro e 26 de agosto de 2026. As comparações com o mesmo período de 2025 são {_formatar_percentual(sim_br_2026.variacao_percentual)} e {_formatar_percentual(sim_sc_2026.variacao_percentual)}.
5. Em 2025, {positivos_2025} municípios catarinenses possuem pelo menos uma vítima de feminicídio registrada no Sinesp.

## Leitura das taxas históricas

1. No Brasil, a taxa de notificações do SINAN passou de {_formatar_taxa(br_2019.sinan_taxa_notificacoes_100mil)} em 2019 para {_formatar_taxa(br_2024.sinan_taxa_notificacoes_100mil)} por 100 mil mulheres em 2024.
2. Em Santa Catarina, a taxa de notificações passou de {_formatar_taxa(sc_2019.sinan_taxa_notificacoes_100mil)} para {_formatar_taxa(sc_2024.sinan_taxa_notificacoes_100mil)} por 100 mil mulheres no mesmo período.
3. A taxa de mortes de mulheres por agressão no SIM passou de {_formatar_taxa(br_2019.sim_taxa_obitos_agressao_100mil)} para {_formatar_taxa(br_2024.sim_taxa_obitos_agressao_100mil)} no Brasil e de {_formatar_taxa(sc_2019.sim_taxa_obitos_agressao_100mil)} para {_formatar_taxa(sc_2024.sim_taxa_obitos_agressao_100mil)} em Santa Catarina.
4. A taxa de vítimas de feminicídio do Sinesp passou de {_formatar_taxa(br_2019.sinesp_taxa_feminicidio_100mil)} para {_formatar_taxa(br_2024.sinesp_taxa_feminicidio_100mil)} no Brasil e de {_formatar_taxa(sc_2019.sinesp_taxa_feminicidio_100mil)} para {_formatar_taxa(sc_2024.sinesp_taxa_feminicidio_100mil)} em Santa Catarina.

Cada taxa permanece acompanhada de seu número absoluto na tabela histórica.

## Validação territorial

1. Foram encontrados {encontrados} municípios do Sinesp com correspondência única no cadastro populacional.
2. O Sinesp contém {especiais} registro adicional chamado “NÃO INFORMADO”. Ele permanece na auditoria, mas não recebe código IBGE e não entra nas taxas municipais.
3. Os 295 municípios aparecem em todos os arquivos anuais de 2019 a 2026. Cada município possui 92 combinações de ano e mês, considerando 2026 até agosto.
4. O total estadual do Sinesp continua incluindo registros sem município quando houver valor publicado nessa categoria. No conjunto atual, essa categoria tem valor zero para feminicídio em Santa Catarina.

## Limitações para interpretação

1. SINAN mede notificações de violência atendidas pela saúde. Uma pessoa pode aparecer em mais de uma notificação.
2. SIM mede mortes de mulheres cuja causa básica pertence ao grupo de agressões. Esse conceito é mais amplo que feminicídio.
3. Sinesp mede vítimas classificadas como feminicídio pelos órgãos de segurança pública.
4. SINAN e SIM usam residência da vítima na consolidação atual. Sinesp usa município do fato.
5. As três fontes não devem ser somadas e não formam uma sequência direta.
6. As taxas usam a população feminina oficial disponível até 2024. O monitoramento de 2025 e 2026 apresenta números absolutos.
7. SINAN 2025 é preliminar. SIM 2025 é preliminar e SIM 2026 é prévia. Sinesp 2026 possui janeiro a agosto.
8. Taxas municipais de feminicídio com menos de cinco vítimas recebem indicação de dado insuficiente para comparação.
9. O Sinesp publica o total de vítimas classificadas no evento Feminicídio. Registros residuais informados com sexo masculino permanecem no total oficial.

## Arquivos produzidos

1. `data/gold/integrado/historico_integrado_2019_2024.csv`
2. `data/gold/integrado/monitoramento_atual_2025_2026.csv`
3. `data/gold/integrado/validacao_municipios_sinesp_sc.csv`
4. `data/gold/integrado/resumo_integracao.json`

## Reprodução

Execute `python pipeline/build_integrated_analysis.py` na raiz do projeto depois de atualizar as camadas Silver.
"""
    return texto, resumo


def _escrever_readme() -> None:
    texto = """# Dados integrados

Esta pasta reúne saídas analíticas que não são consumidas pelo painel atual.

## Arquivos

1. `historico_integrado_2019_2024.csv`: Brasil, Santa Catarina e 295 municípios catarinenses, com população feminina, números absolutos e taxas de SINAN, SIM e Sinesp.
2. `monitoramento_atual_2025_2026.csv`: números absolutos recentes e comparação com o mesmo período anterior.
3. `validacao_municipios_sinesp_sc.csv`: correspondência entre o nome publicado pelo Sinesp e o código municipal do cadastro populacional.
4. `resumo_integracao.json`: controles usados no relatório e na retomada do trabalho.

## Regras centrais

1. As taxas são calculadas apenas entre 2019 e 2024, período com população feminina disponível.
2. SINAN e SIM usam residência da vítima. Sinesp usa município do fato.
3. Números das três fontes não são somados.
4. Comparações recentes usam o mesmo período de cada fonte.

## Atualização

Execute `python pipeline/build_integrated_analysis.py` depois de atualizar as camadas Silver.
"""
    README.write_text(texto, encoding="utf-8")


def main() -> None:
    fontes = _carregar_fontes()
    territorios, municipios = _cadastro_territorial(fontes["populacao"])
    validacao, mapa_municipios = _mapa_municipios(fontes["sinesp"], municipios)
    historico = _historico(
        fontes["indicadores"], fontes["sinesp"], territorios, mapa_municipios
    )
    monitoramento = _monitoramento(
        fontes["sinan"],
        fontes["sinan_2025"],
        fontes["sim"],
        fontes["sinesp"],
        territorios,
        mapa_municipios,
    )
    relatorio, resumo = _gerar_relatorio(historico, monitoramento, validacao)

    DESTINO.mkdir(parents=True, exist_ok=True)
    historico.to_csv(HISTORICO, index=False, encoding="utf-8-sig")
    monitoramento.to_csv(MONITORAMENTO, index=False, encoding="utf-8-sig")
    validacao.to_csv(VALIDACAO_MUNICIPIOS, index=False, encoding="utf-8-sig")
    RESUMO.write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    RELATORIO.write_text(relatorio, encoding="utf-8")
    _escrever_readme()

    print(f"Histórico: {HISTORICO} ({len(historico)} linhas)")
    print(f"Monitoramento: {MONITORAMENTO} ({len(monitoramento)} linhas)")
    print(f"Validação municipal: {VALIDACAO_MUNICIPIOS} ({len(validacao)} linhas)")
    print(f"Relatório: {RELATORIO}")
    print(json.dumps(resumo["controle"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
