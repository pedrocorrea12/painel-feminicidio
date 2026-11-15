from pathlib import Path

import pandas as pd
import pytest

from painel_dados.contracts import sinesp

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "sinesp"
NUMERICAS_SILVER = [
    "vitimas_feminino",
    "vitimas_masculino",
    "vitimas_nao_informado",
    "total_vitimas",
    "total_ocorrencias",
    "total_peso",
]


def ler(nome: str) -> pd.DataFrame:
    return pd.read_csv(FIXTURES / nome)


@pytest.fixture
def silver() -> pd.DataFrame:
    # Na Silver real as desagregações são "string" (nulas na maioria das linhas).
    quadro = ler("silver_ocorrencias.csv")
    for coluna in ["agente", "arma", "faixa_etaria"]:
        quadro[coluna] = quadro[coluna].astype("string")
    return quadro


@pytest.fixture
def mensal() -> pd.DataFrame:
    return ler("gold_mensal.csv")


@pytest.fixture
def anual() -> pd.DataFrame:
    return ler("gold_anual.csv")


def test_fixtures_validas_passam(silver, mensal, anual) -> None:
    sinesp.validar_silver_ocorrencias(silver)
    sinesp.validar_silver_feminicidio(ler("silver_feminicidio.csv"))
    sinesp.validar_gold_mensal(mensal)
    sinesp.validar_gold_anual(anual)
    sinesp.validar_cobertura_mensal(mensal)


def test_silver_aceita_linhas_repetidas_do_mesmo_mes(silver) -> None:
    repetidas = silver.duplicated(["ano", "mes", "sigla_uf", "municipio", "evento"], keep=False)
    assert repetidas.sum() == 2
    sinesp.validar_silver_ocorrencias(silver)


def test_bronze_aceita_colunas_extras_e_rejeita_ausencia() -> None:
    quadro = pd.DataFrame(columns=["uf", "municipio", "evento", "data_referencia", "nova"])
    sinesp.validar_bronze(quadro, 2024)
    with pytest.raises(ValueError, match=r"bancovde-2024: Colunas obrigatórias ausentes.*evento"):
        sinesp.validar_bronze(quadro.drop(columns="evento"), 2024)


def test_silver_rejeita_coluna_removida(silver) -> None:
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes.*abrangencia"):
        sinesp.validar_silver_ocorrencias(silver.drop(columns="abrangencia"))


def test_silver_rejeita_tipo_alterado(silver) -> None:
    silver["total_vitimas"] = silver["total_vitimas"].astype(str)
    with pytest.raises(ValueError, match="tipos fora do contrato.*total_vitimas"):
        sinesp.validar_silver_ocorrencias(silver)


def test_silver_rejeita_ano_como_texto(silver) -> None:
    silver["ano"] = silver["ano"].astype(str)
    with pytest.raises(ValueError, match="tipos fora do contrato.*ano"):
        sinesp.validar_silver_ocorrencias(silver)


def test_silver_rejeita_mes_invalido(silver) -> None:
    silver.loc[0, "mes"] = 13
    with pytest.raises(ValueError, match="mes fora do intervalo"):
        sinesp.validar_silver_ocorrencias(silver)


def test_silver_rejeita_abrangencia_desconhecida(silver) -> None:
    silver.loc[0, "abrangencia"] = "Municipal"
    with pytest.raises(ValueError, match="valores inválidos em abrangencia.*Municipal"):
        sinesp.validar_silver_ocorrencias(silver)


def test_silver_rejeita_medida_negativa(silver) -> None:
    silver.loc[0, "total_vitimas"] = -1.0
    with pytest.raises(ValueError, match="medidas negativas.*total_vitimas"):
        sinesp.validar_silver_ocorrencias(silver)


def test_gold_mensal_rejeita_chave_duplicada(mensal) -> None:
    duplicado = pd.concat([mensal, mensal.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Chave duplicada"):
        sinesp.validar_gold_mensal(duplicado)


def test_gold_mensal_rejeita_coluna_removida(mensal) -> None:
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes.*total_peso"):
        sinesp.validar_gold_mensal(mensal.drop(columns="total_peso"))


def test_gold_mensal_rejeita_tipo_alterado(mensal) -> None:
    mensal["total_vitimas"] = mensal["total_vitimas"].astype(float) + 0.5
    with pytest.raises(ValueError, match="tipos fora do contrato.*total_vitimas"):
        sinesp.validar_gold_mensal(mensal)


def test_gold_anual_rejeita_chave_duplicada(anual) -> None:
    duplicado = pd.concat([anual, anual.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Chave duplicada"):
        sinesp.validar_gold_anual(duplicado)


def test_gold_anual_rejeita_meses_informados_invalido(anual) -> None:
    anual.loc[0, "meses_informados"] = 13
    with pytest.raises(ValueError, match="meses_informados fora do intervalo"):
        sinesp.validar_gold_anual(anual)


def test_cobertura_rejeita_ano_consolidado_com_mes_faltando(mensal) -> None:
    junho = (mensal.evento == "Feminicídio") & (mensal.ano == 2024) & (mensal.mes == 6)
    sem_junho = mensal.loc[~junho]
    padrao = r"cobertura mensal incompleta: Feminicídio Brasil 2024.*\[6\]"
    with pytest.raises(ValueError, match=padrao):
        sinesp.validar_cobertura_mensal(sem_junho)


def test_cobertura_rejeita_lacuna_em_ano_parcial(mensal) -> None:
    fevereiro = (mensal.evento == "Feminicídio") & (mensal.ano == 2025) & (mensal.mes == 2)
    lacuna = mensal.loc[~fevereiro]
    with pytest.raises(ValueError, match=r"cobertura mensal incompleta.*2025.*\[2\]"):
        sinesp.validar_cobertura_mensal(lacuna)


def test_cobertura_aceita_ano_parcial_sem_lacuna(mensal) -> None:
    sinesp.validar_cobertura_mensal(mensal)


def test_cobertura_rejeita_evento_ausente(mensal) -> None:
    with pytest.raises(ValueError, match="evento ausente: Furto"):
        sinesp.validar_cobertura_mensal(mensal, eventos_obrigatorios=("Furto",))


def test_cobertura_rejeita_serie_inteira_ausente(mensal) -> None:
    sem_sc_2024 = mensal.loc[
        ~(
            (mensal.evento == "Feminicídio")
            & (mensal.territorio == "Santa Catarina")
            & (mensal.ano == 2024)
        )
    ]
    with pytest.raises(ValueError, match="série ausente: Feminicídio Santa Catarina 2024"):
        sinesp.validar_cobertura_mensal(sem_sc_2024)


@pytest.mark.parametrize("coluna", ["agente", "arma", "faixa_etaria"])
def test_silver_rejeita_desagregacao_removida(silver, coluna) -> None:
    with pytest.raises(ValueError, match=f"Colunas obrigatórias ausentes.*{coluna}"):
        sinesp.validar_silver_ocorrencias(silver.drop(columns=coluna))


def test_silver_feminicidio_rejeita_arquivo_origem_removido() -> None:
    quadro = ler("silver_feminicidio.csv").drop(columns="arquivo_origem")
    with pytest.raises(ValueError, match="Colunas obrigatórias ausentes.*arquivo_origem"):
        sinesp.validar_silver_feminicidio(quadro)


def test_gold_anual_rejeita_consolidado_com_meses_faltando(anual) -> None:
    anual.loc[anual.situacao_dado == "consolidado_publicacao", "meses_informados"] = 11
    with pytest.raises(ValueError, match="ano consolidado com menos de 12 meses"):
        sinesp.validar_gold_anual(anual)


def test_gold_anual_rejeita_parcial_com_12_meses(anual) -> None:
    anual.loc[anual.situacao_dado == "parcial", "meses_informados"] = 12
    with pytest.raises(ValueError, match="ano parcial com 12 meses"):
        sinesp.validar_gold_anual(anual)


def test_gold_anual_rejeita_medida_negativa(anual) -> None:
    anual.loc[0, "total_vitimas"] = -1
    with pytest.raises(ValueError, match="medidas negativas.*total_vitimas"):
        sinesp.validar_gold_anual(anual)
