"""Contrato de dados do Sinesp VDE (MJSP) nas camadas Silver e Gold.

Deriva de ``pipeline/extract_sinesp.py`` e ``docs/SINESP_VDE.md``. Cada função
levanta ``ValueError`` com mensagem estável quando o contrato é violado.
"""

from __future__ import annotations

import pandas as pd
from pandas.api import types as pdt

from painel_dados.quality import assert_required_columns, assert_unique

# Colunas mínimas do xlsx publicado, depois de normalizar os nomes.
BRONZE_COLUNAS_OBRIGATORIAS = ("uf", "municipio", "evento", "data_referencia")

ABRANGENCIAS = ("Estadual", "Polícia Federal", "Polícia Rodoviária Federal")
SITUACOES = ("consolidado_publicacao", "parcial")
TERRITORIOS = ("Brasil", "Santa Catarina")

COLUNAS_MEDIDA = (
    "vitimas_feminino",
    "vitimas_masculino",
    "vitimas_nao_informado",
    "total_vitimas",
    "total_ocorrencias",
    "total_peso",
)

# Tipos esperados: "inteiro", "numero" ou "texto".
SILVER_OCORRENCIAS = {
    "ano": "inteiro",
    "mes": "inteiro",
    "sigla_uf": "texto",
    "municipio": "texto",
    "evento": "texto",
    "abrangencia": "texto",
    "vitimas_feminino": "numero",
    "vitimas_masculino": "numero",
    "vitimas_nao_informado": "numero",
    "total_vitimas": "numero",
    "total_ocorrencias": "numero",
    "total_peso": "numero",
    "arquivo_origem": "texto",
    "situacao_dado": "texto",
}

SILVER_FEMINICIDIO = {
    "ano": "inteiro",
    "mes": "inteiro",
    "sigla_uf": "texto",
    "municipio": "texto",
    "vitimas_feminicidio": "inteiro",
    "situacao_dado": "texto",
}

GOLD_MENSAL = {
    "territorio": "texto",
    "ano": "inteiro",
    "mes": "inteiro",
    "evento": "texto",
    **{coluna: "inteiro" for coluna in COLUNAS_MEDIDA if coluna != "total_peso"},
    "total_peso": "numero",
    "situacao_dado": "texto",
}
GOLD_MENSAL_CHAVE = ("territorio", "ano", "mes", "evento")

GOLD_ANUAL = {
    **{k: v for k, v in GOLD_MENSAL.items() if k != "mes"},
    "meses_informados": "inteiro",
}
GOLD_ANUAL_CHAVE = ("territorio", "ano", "evento")


def _verificar_tipos(frame: pd.DataFrame, esquema: dict[str, str], nome: str) -> None:
    verificadores = {
        "inteiro": lambda s: pdt.is_integer_dtype(s),
        "numero": lambda s: pdt.is_numeric_dtype(s) and not pdt.is_bool_dtype(s),
        "texto": lambda s: pdt.is_string_dtype(s) or pdt.is_object_dtype(s),
    }
    errados = [
        f"{coluna}: esperado {tipo}, obtido {frame[coluna].dtype}"
        for coluna, tipo in esquema.items()
        if not verificadores[tipo](frame[coluna])
    ]
    if errados:
        raise ValueError(f"{nome}: tipos fora do contrato: {errados}")


def _verificar_dominio(
    frame: pd.DataFrame, coluna: str, validos: tuple[str, ...], nome: str
) -> None:
    invalidos = sorted(set(frame[coluna].dropna().astype(str)).difference(validos))
    if invalidos:
        raise ValueError(f"{nome}: valores inválidos em {coluna}: {invalidos}")


def _verificar_mes_e_medidas(frame: pd.DataFrame, nome: str, medidas: tuple[str, ...]) -> None:
    if not frame["mes"].between(1, 12).all():
        raise ValueError(f"{nome}: mes fora do intervalo 1 a 12")
    negativas = [c for c in medidas if (frame[c].dropna() < 0).any()]
    if negativas:
        raise ValueError(f"{nome}: medidas negativas em {negativas}")


def validar_bronze(frame: pd.DataFrame, ano_arquivo: int) -> None:
    """Valida as colunas do ``bancovde-AAAA.xlsx`` já normalizadas.

    Aceita colunas extras (a MJSP acrescenta desagregações); só exige o núcleo.
    """

    try:
        assert_required_columns(frame, BRONZE_COLUNAS_OBRIGATORIAS)
    except ValueError as erro:
        raise ValueError(f"bancovde-{ano_arquivo}: {erro}") from erro


def validar_silver_ocorrencias(frame: pd.DataFrame) -> None:
    """Valida ``sinesp_vde_ocorrencias``.

    A chave não é única de propósito: o MJSP envia várias linhas por mês para o
    mesmo evento e município (Estupro, DF) e elas devem ser somadas no Gold.
    """

    nome = "silver sinesp_vde_ocorrencias"
    assert_required_columns(frame, SILVER_OCORRENCIAS)
    _verificar_tipos(frame, SILVER_OCORRENCIAS, nome)
    _verificar_mes_e_medidas(frame, nome, COLUNAS_MEDIDA)
    _verificar_dominio(frame, "abrangencia", ABRANGENCIAS, nome)
    _verificar_dominio(frame, "situacao_dado", SITUACOES, nome)


def validar_silver_feminicidio(frame: pd.DataFrame) -> None:
    """Valida o recorte de feminicídio usado por ``build_gold.py``."""

    nome = "silver sinesp_feminicidio"
    assert_required_columns(frame, SILVER_FEMINICIDIO)
    _verificar_tipos(frame, SILVER_FEMINICIDIO, nome)
    _verificar_mes_e_medidas(frame, nome, ("vitimas_feminicidio",))
    _verificar_dominio(frame, "situacao_dado", SITUACOES, nome)


def validar_gold_mensal(frame: pd.DataFrame) -> None:
    """Valida ``sinesp_sc_brasil_mensal.csv``: chave única por território, ano, mês e evento."""

    nome = "gold sinesp_sc_brasil_mensal"
    assert_required_columns(frame, GOLD_MENSAL)
    _verificar_tipos(frame, GOLD_MENSAL, nome)
    _verificar_mes_e_medidas(frame, nome, COLUNAS_MEDIDA)
    _verificar_dominio(frame, "territorio", TERRITORIOS, nome)
    _verificar_dominio(frame, "situacao_dado", SITUACOES, nome)
    assert_unique(frame, GOLD_MENSAL_CHAVE)


def validar_gold_anual(frame: pd.DataFrame) -> None:
    """Valida ``sinesp_sc_brasil_anual.csv`` e a coerência entre meses e situação."""

    nome = "gold sinesp_sc_brasil_anual"
    assert_required_columns(frame, GOLD_ANUAL)
    _verificar_tipos(frame, GOLD_ANUAL, nome)
    _verificar_dominio(frame, "territorio", TERRITORIOS, nome)
    _verificar_dominio(frame, "situacao_dado", SITUACOES, nome)
    if not frame["meses_informados"].between(1, 12).all():
        raise ValueError(f"{nome}: meses_informados fora do intervalo 1 a 12")
    assert_unique(frame, GOLD_ANUAL_CHAVE)


def validar_cobertura_mensal(
    mensal: pd.DataFrame, eventos_obrigatorios: tuple[str, ...] = ("Feminicídio",)
) -> None:
    """Falha se um ano consolidado não tiver os 12 meses dos eventos obrigatórios.

    Anos ``parcial`` podem ter menos meses, mas não podem ter lacuna no meio:
    os meses presentes devem formar a sequência 1..N.
    """

    for evento in eventos_obrigatorios:
        recorte = mensal.loc[mensal["evento"].str.lower().eq(evento.lower())]
        if recorte.empty:
            raise ValueError(f"cobertura mensal: evento ausente: {evento}")
        grupos = recorte.groupby(["territorio", "ano"])
        for (territorio, ano), grupo in grupos:
            meses = sorted(set(grupo["mes"]))
            parcial = grupo["situacao_dado"].eq("parcial").all()
            esperado = list(range(1, (meses[-1] if parcial else 12) + 1))
            if meses != esperado:
                faltam = sorted(set(esperado).difference(meses))
                raise ValueError(
                    f"cobertura mensal incompleta: {evento} {territorio} {ano}: "
                    f"meses ausentes {faltam}"
                )
