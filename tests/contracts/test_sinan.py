from datetime import date
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


def _silver_formato_real() -> pd.DataFrame:
    quadro = pd.read_csv(
        FIXTURES / "silver_atlas_formato_real.csv",
        dtype={
            "sexo": "string",
            "raca": "string",
            "grupo_etario": "string",
            "natureza_violencia": "string",
            "id_municipio_residencia": "string",
            "sigla_uf_residencia": "string",
            "situacao_dado": "string",
        },
    )
    quadro["data_ocorrencia"] = quadro["data_ocorrencia"].map(
        lambda valor: date.fromisoformat(valor) if pd.notna(valor) else None
    )
    return quadro


def test_fixtures_validas_atendem_aos_contratos() -> None:
    validar_silver_atlas(_silver_valida())
    validar_gold_territorial(_gold_valida())


def test_fixture_no_formato_real_aceita_nulos_coerentes() -> None:
    quadro = _silver_formato_real()

    assert quadro["mes"].dtype == "float64"
    assert quadro["idade_anos"].dtype == "float64"
    assert isinstance(quadro.loc[0, "data_ocorrencia"], date)
    assert quadro.loc[1, "data_ocorrencia"] is None
    validar_silver_atlas(quadro)


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


def test_mes_fracionario_falha_com_mensagem_estavel() -> None:
    quadro = _silver_formato_real()
    quadro.loc[0, "mes"] = 3.5

    with pytest.raises(
        ValueError,
        match=(
            r"^Contrato SINAN atlas: tipo inválido em 'mes'; "
            r"esperado inteiro anulável\.$"
        ),
    ):
        validar_silver_atlas(quadro)


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


def test_mes_fora_do_intervalo_falha() -> None:
    quadro = _silver_valida()
    quadro.loc[0, "mes"] = 13

    with pytest.raises(
        ValueError,
        match=r"^Contrato SINAN atlas: mês fora do intervalo 1 a 12\.$",
    ):
        validar_silver_atlas(quadro)


def test_natureza_violencia_invalida_falha() -> None:
    quadro = _silver_valida()
    quadro.loc[0, "natureza_violencia"] = "ignorada"

    with pytest.raises(
        ValueError,
        match=r"^Contrato SINAN atlas: natureza_violencia inválida\.$",
    ):
        validar_silver_atlas(quadro)


def test_mes_incoerente_com_data_falha() -> None:
    quadro = _silver_valida()
    quadro.loc[0, "data_ocorrencia"] = pd.Timestamp("2024-07-15")

    with pytest.raises(
        ValueError,
        match=r"^Contrato SINAN atlas: mes incompatível com data_ocorrencia\.$",
    ):
        validar_silver_atlas(quadro)


def test_situacao_dado_errada_na_silver_falha() -> None:
    quadro = _silver_valida()
    quadro.loc[quadro["ano"].eq(2025), "situacao_dado"] = "definitivo"

    with pytest.raises(
        ValueError,
        match=r"^Contrato SINAN atlas: situacao_dado incompatível com o ano\.$",
    ):
        validar_silver_atlas(quadro)


def test_mes_nulo_sem_data_nula_falha() -> None:
    quadro = _silver_valida()
    quadro["mes"] = quadro["mes"].astype("float64")
    quadro.loc[0, "mes"] = pd.NA

    with pytest.raises(
        ValueError,
        match=(
            r"^Contrato SINAN atlas: mes e data_ocorrencia devem ser nulos juntos\.$"
        ),
    ):
        validar_silver_atlas(quadro)
