"""Contratos dos artefatos SINAN usados pelo atlas territorial."""

from __future__ import annotations

from datetime import date

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_integer_dtype,
    is_numeric_dtype,
)

from painel_dados.quality import assert_required_columns, assert_unique

ANOS_CONTRATO = tuple(range(2015, 2026))
ANO_PRELIMINAR = 2025

TIPOS_VIOLENCIA = (
    "violencia_fisica",
    "violencia_psicologica",
    "violencia_sexual",
    "violencia_financeira",
    "negligencia",
    "tortura",
    "trafico_pessoas",
)

COLUNAS_SILVER_ATLAS = (
    "ano",
    "mes",
    "data_ocorrencia",
    "sexo",
    "raca",
    "idade_anos",
    "grupo_etario",
    "natureza_violencia",
    "id_municipio_residencia",
    "sigla_uf_residencia",
    *TIPOS_VIOLENCIA,
    "situacao_dado",
)

COLUNAS_GOLD_TERRITORIAL = (
    "ano",
    "nivel_territorial",
    "id_territorio",
    "territorio",
    "indicador",
    "sexo",
    "notificacoes",
    "populacao",
    "tipo_denominador",
    "taxa_100mil",
    "situacao_dado",
)

CHAVE_GOLD_TERRITORIAL = (
    "ano",
    "nivel_territorial",
    "id_territorio",
    "indicador",
    "sexo",
)

CHAVE_SERIE_TERRITORIAL = (
    "nivel_territorial",
    "id_territorio",
    "indicador",
    "sexo",
)

_TIPOS_SILVER_ATLAS = {
    "ano": "inteiro",
    "mes": "inteiro anulável",
    "data_ocorrencia": "data",
    "sexo": "texto",
    "raca": "texto",
    "idade_anos": "inteiro anulável",
    "grupo_etario": "texto",
    "natureza_violencia": "texto",
    "id_municipio_residencia": "texto",
    "sigla_uf_residencia": "texto",
    **{coluna: "booleano" for coluna in TIPOS_VIOLENCIA},
    "situacao_dado": "texto",
}

_TIPOS_GOLD_TERRITORIAL = {
    "ano": "inteiro",
    "nivel_territorial": "texto",
    "id_territorio": "texto",
    "territorio": "texto",
    "indicador": "texto",
    "sexo": "texto",
    "notificacoes": "inteiro",
    "populacao": "numerico",
    "tipo_denominador": "texto",
    "taxa_100mil": "numerico",
    "situacao_dado": "texto",
}


def _validar_colunas(
    quadro: pd.DataFrame,
    colunas: tuple[str, ...],
    artefato: str,
) -> None:
    try:
        assert_required_columns(quadro, colunas)
    except ValueError as erro:
        raise ValueError(f"Contrato SINAN {artefato}: {erro}") from None


def _serie_textual(serie: pd.Series) -> bool:
    valores = serie.dropna()
    return bool(valores.map(lambda valor: isinstance(valor, str)).all())


def _serie_data(serie: pd.Series) -> bool:
    if is_datetime64_any_dtype(serie.dtype):
        return True
    valores = serie.dropna()
    return bool(valores.map(lambda valor: isinstance(valor, date)).all())


def _tipo_valido(serie: pd.Series, esperado: str) -> bool:
    if esperado == "inteiro":
        return bool(is_integer_dtype(serie.dtype))
    if esperado == "inteiro anulável":
        if not is_numeric_dtype(serie.dtype) or is_bool_dtype(serie.dtype):
            return False
        valores = serie.dropna()
        return bool(valores.mod(1).eq(0).all())
    if esperado == "numerico":
        return bool(is_numeric_dtype(serie.dtype))
    if esperado == "booleano":
        return bool(is_bool_dtype(serie.dtype))
    if esperado == "texto":
        return _serie_textual(serie)
    if esperado == "data":
        return _serie_data(serie)
    raise RuntimeError(f"Tipo de contrato desconhecido: {esperado}")


def _validar_tipos(
    quadro: pd.DataFrame,
    tipos: dict[str, str],
    artefato: str,
) -> None:
    for coluna, esperado in tipos.items():
        if not _tipo_valido(quadro[coluna], esperado):
            raise ValueError(
                f"Contrato SINAN {artefato}: tipo inválido em '{coluna}'; "
                f"esperado {esperado}."
            )


def _validar_situacao_dado(quadro: pd.DataFrame, artefato: str) -> None:
    esperado = quadro["ano"].map(
        lambda ano: "preliminar" if int(ano) >= ANO_PRELIMINAR else "definitivo"
    )
    if not quadro["situacao_dado"].eq(esperado).all():
        raise ValueError(
            f"Contrato SINAN {artefato}: situacao_dado incompatível com o ano."
        )


def validar_silver_atlas(quadro: pd.DataFrame) -> None:
    """Valida a Silver por notificação produzida para o atlas SINAN."""

    artefato = "atlas"
    if quadro.empty:
        raise ValueError("Contrato SINAN atlas: conjunto vazio.")
    _validar_colunas(quadro, COLUNAS_SILVER_ATLAS, artefato)
    _validar_tipos(quadro, _TIPOS_SILVER_ATLAS, artefato)

    if not quadro["ano"].isin(ANOS_CONTRATO).all():
        raise ValueError("Contrato SINAN atlas: ano fora do período 2015 a 2025.")
    mes_nulo = quadro["mes"].isna()
    data_nula = quadro["data_ocorrencia"].isna()
    if not mes_nulo.eq(data_nula).all():
        raise ValueError(
            "Contrato SINAN atlas: mes e data_ocorrencia devem ser nulos juntos."
        )

    meses_presentes = quadro.loc[~mes_nulo, "mes"]
    if not meses_presentes.between(1, 12).all():
        raise ValueError("Contrato SINAN atlas: mês fora do intervalo 1 a 12.")

    linhas_com_data = ~data_nula
    datas_presentes = pd.to_datetime(
        quadro.loc[linhas_com_data, "data_ocorrencia"], errors="coerce"
    )
    meses_data = datas_presentes.dt.month
    meses_registro = quadro.loc[linhas_com_data, "mes"]
    if datas_presentes.isna().any() or not meses_data.eq(meses_registro).all():
        raise ValueError("Contrato SINAN atlas: mes incompatível com data_ocorrencia.")

    naturezas = {"interpessoal", "autoprovocada"}
    if not quadro["natureza_violencia"].isin(naturezas).all():
        raise ValueError("Contrato SINAN atlas: natureza_violencia inválida.")
    _validar_situacao_dado(quadro, artefato)


def validar_gold_territorial(quadro: pd.DataFrame) -> None:
    """Valida a Gold anual e sua chave territorial declarada."""

    artefato = "territorial"
    if quadro.empty:
        raise ValueError("Contrato SINAN territorial: conjunto vazio.")
    _validar_colunas(quadro, COLUNAS_GOLD_TERRITORIAL, artefato)
    _validar_tipos(quadro, _TIPOS_GOLD_TERRITORIAL, artefato)

    try:
        assert_unique(quadro, CHAVE_GOLD_TERRITORIAL)
    except ValueError:
        raise ValueError(
            "Contrato SINAN territorial: chave de granularidade duplicada."
        ) from None

    anos_esperados = set(ANOS_CONTRATO)
    cobertura = quadro.groupby(list(CHAVE_SERIE_TERRITORIAL), dropna=False)["ano"].agg(set)
    if cobertura.empty or not cobertura.map(lambda anos: anos == anos_esperados).all():
        raise ValueError(
            "Contrato SINAN territorial: série anual incompleta; esperado 2015 a 2025."
        )

    _validar_situacao_dado(quadro, artefato)
