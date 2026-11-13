from pathlib import Path

import pandas as pd
import pytest

from painel_dados.contracts.sinan import validar_gold_territorial, validar_silver_atlas

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "sinan"


def _silver_valida() -> pd.DataFrame:
    return pd.read_csv(
        FIXTURES / "silver_atlas_valida.csv",
        parse_dates=["data_ocorrencia"],
        dtype={
            "ano": "int16",
            "mes": "int8",
            "sexo": "string",
            "raca": "string",
            "idade_anos": "Int16",
            "grupo_etario": "string",
            "natureza_violencia": "string",
            "id_municipio_residencia": "string",
            "sigla_uf_residencia": "string",
            "violencia_fisica": "boolean",
            "violencia_psicologica": "boolean",
            "violencia_sexual": "boolean",
            "violencia_financeira": "boolean",
            "negligencia": "boolean",
            "tortura": "boolean",
            "trafico_pessoas": "boolean",
            "situacao_dado": "string",
        },
    )


def _gold_valida() -> pd.DataFrame:
    return pd.read_csv(
        FIXTURES / "gold_territorial_valida.csv",
        dtype={
            "ano": "int16",
            "nivel_territorial": "string",
            "id_territorio": "string",
            "territorio": "string",
            "indicador": "string",
            "sexo": "string",
            "notificacoes": "int64",
            "populacao": "float64",
            "tipo_denominador": "string",
            "taxa_100mil": "float64",
            "situacao_dado": "string",
        },
    )


def test_fixtures_validas_atendem_aos_contratos() -> None:
    validar_silver_atlas(_silver_valida())
    validar_gold_territorial(_gold_valida())


def test_coluna_removida_falha_com_mensagem_estavel() -> None:
    quadro = _silver_valida().drop(columns="sexo")

    with pytest.raises(
        ValueError,
        match=r"^Contrato SINAN atlas: Colunas obrigatórias ausentes: \['sexo'\]$",
    ):
        validar_silver_atlas(quadro)


def test_tipo_alterado_falha_com_mensagem_estavel() -> None:
    quadro = _gold_valida()
    quadro["notificacoes"] = quadro["notificacoes"].astype("string")

    with pytest.raises(
        ValueError,
        match=(
            r"^Contrato SINAN territorial: tipo inválido em 'notificacoes'; "
            r"esperado inteiro\.$"
        ),
    ):
        validar_gold_territorial(quadro)


def test_chave_duplicada_falha_com_mensagem_estavel() -> None:
    quadro = _gold_valida()
    quadro = pd.concat([quadro, quadro.iloc[[0]]], ignore_index=True)

    with pytest.raises(
        ValueError,
        match=r"^Contrato SINAN territorial: chave de granularidade duplicada\.$",
    ):
        validar_gold_territorial(quadro)


def test_serie_anual_incompleta_falha() -> None:
    quadro = _gold_valida().loc[lambda dados: dados["ano"].ne(2020)]

    with pytest.raises(
        ValueError,
        match=r"^Contrato SINAN territorial: série anual incompleta; esperado 2015 a 2025\.$",
    ):
        validar_gold_territorial(quadro)


def test_ano_preliminar_com_status_definitivo_falha() -> None:
    quadro = _gold_valida()
    quadro.loc[quadro["ano"].eq(2025), "situacao_dado"] = "definitivo"

    with pytest.raises(
        ValueError,
        match=r"^Contrato SINAN territorial: situacao_dado incompatível com o ano\.$",
    ):
        validar_gold_territorial(quadro)
