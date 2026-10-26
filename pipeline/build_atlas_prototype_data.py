"""Gera um JSON compacto para o prototipo local do atlas territorial."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "data" / "gold" / "atlas"
DESTINO = ROOT / "dashboard" / "prototipos" / "atlas-violencia" / "data.json"


SIM_NOMES = {
    "agressao": ("Mortes por agressão", "Violência letal"),
    "suicidio": ("Mortes por suicídio", "Violência autoprovocada"),
    "acidente_transporte": ("Mortes no trânsito", "Trânsito"),
}

SINAN_NOMES = {
    "notificacoes_interpessoais": "Notificações de violência interpessoal",
    "notificacoes_autoprovocadas": "Notificações de violência autoprovocada",
    "violencia_fisica": "Violência física",
    "violencia_psicologica": "Violência psicológica",
    "violencia_sexual": "Violência sexual notificada",
    "violencia_financeira": "Violência financeira",
    "negligencia": "Negligência",
    "tortura": "Tortura",
    "trafico_pessoas": "Tráfico de pessoas",
}

SINAN_EIXOS = {
    "Notificações de violência interpessoal": "Violência interpessoal",
    "Notificações de violência autoprovocada": "Violência autoprovocada",
    "Violência física": "Violência interpessoal",
    "Violência psicológica": "Violência interpessoal",
    "Violência sexual notificada": "Violência sexual",
    "Violência financeira": "Violência interpessoal",
    "Negligência": "Violência interpessoal",
    "Tortura": "Violência interpessoal",
    "Tráfico de pessoas": "Violência interpessoal",
}

SINESP_EIXOS = {
    "Feminicídio": "Violência contra a mulher",
    "Tentativa de feminicídio": "Violência contra a mulher",
    "Homicídio doloso": "Violência letal",
    "Tentativa de homicídio": "Violência letal",
    "Estupro": "Violência sexual",
    "Estupro de vulnerável": "Violência sexual",
    "Violência sexual policial, soma das classificações": "Violência sexual",
    "Suicídio": "Violência autoprovocada",
    "Pessoa Desaparecida": "Desaparecimentos",
    "Pessoa Localizada": "Desaparecimentos",
}


def registros_sinesp() -> tuple[list[dict], list[dict]]:
    anual = pd.read_csv(
        ATLAS / "sinesp_prioridade_territorio_ano.csv",
        dtype={"id_territorio": "string"},
    )
    anual = anual.loc[anual.sexo.eq("total")].copy()
    anual["fonte"] = "Sinesp VDE"
    anual["eixo"] = anual.indicador.map(SINESP_EIXOS)
    anual["unidade"] = "vítimas"
    anual = anual.rename(columns={"valor_absoluto": "valor", "taxa_100mil": "taxa"})
    colunas = [
        "fonte",
        "eixo",
        "indicador",
        "unidade",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "ano",
        "valor",
        "taxa",
        "meses_observados",
        "situacao_dado",
    ]

    mensal = pd.read_csv(ATLAS / "sinesp_prioridade_mensal.csv")
    mensal = mensal.loc[mensal.sexo.eq("total")].copy()
    mensal = mensal.rename(columns={"valor_absoluto": "valor"})
    mensal = mensal[
        ["territorio", "ano", "mes", "indicador", "valor", "situacao_dado"]
    ]
    return anual[colunas].to_dict("records"), mensal.to_dict("records")


def registros_sim() -> list[dict]:
    base = pd.read_csv(
        ATLAS / "sim_mortalidade_territorio_ano.csv",
        dtype={"id_territorio": "string"},
    )
    base = base.loc[base.sexo.eq("total")].copy()
    base[["indicador", "eixo"]] = base.grupo_causa.map(SIM_NOMES).apply(pd.Series)
    base["fonte"] = "SIM"
    base["unidade"] = "óbitos"
    base = base.rename(columns={"obitos": "valor", "taxa_100mil": "taxa"})
    colunas = [
        "fonte",
        "eixo",
        "indicador",
        "unidade",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "ano",
        "valor",
        "taxa",
        "meses_observados",
        "situacao_dado",
    ]
    return base[colunas].to_dict("records")


def registros_sinan() -> list[dict]:
    base = pd.read_csv(
        ATLAS / "sinan_violencia_territorio_ano.csv",
        dtype={"id_territorio": "string"},
        low_memory=False,
    )
    base = base.loc[base.sexo.eq("total")].copy()
    base["fonte"] = "SINAN"
    base["indicador"] = base.indicador.map(SINAN_NOMES)
    base["meses_observados"] = base.situacao_dado.eq("definitivo").map({True: 12, False: None})
    base["eixo"] = base.indicador.map(SINAN_EIXOS)
    base["unidade"] = "notificações"
    base = base.rename(columns={"notificacoes": "valor", "taxa_100mil": "taxa"})
    colunas = [
        "fonte",
        "eixo",
        "indicador",
        "unidade",
        "nivel_territorial",
        "id_territorio",
        "territorio",
        "ano",
        "valor",
        "taxa",
        "meses_observados",
        "situacao_dado",
    ]
    return base[colunas].to_dict("records")


def limpar_nulos(registros: list[dict]) -> list[dict]:
    for linha in registros:
        for chave, valor in list(linha.items()):
            if pd.isna(valor):
                linha[chave] = None
            elif isinstance(valor, float) and valor.is_integer():
                linha[chave] = int(valor)
    return registros


def main() -> None:
    sinesp, mensal = registros_sinesp()
    sim = registros_sim()
    nomes = {
        linha["id_territorio"]: linha["territorio"]
        for linha in sim
        if linha["nivel_territorial"] == "municipio"
    }
    registros = limpar_nulos(sinesp + sim + registros_sinan())
    for linha in registros:
        if linha["nivel_territorial"] == "municipio":
            linha["territorio"] = nomes.get(linha["id_territorio"], linha["territorio"])
    mensal = limpar_nulos(mensal)
    cobertura = pd.read_csv(ATLAS / "sinesp_cobertura_evento_resumo.csv").to_dict("records")
    catalogo = pd.read_csv(ATLAS / "catalogo_indicadores.csv")
    catalogo = catalogo.loc[catalogo.prioridade.eq(1)].to_dict("records")
    municipios = sorted(
        {
            (linha["id_territorio"], linha["territorio"])
            for linha in registros
            if linha["nivel_territorial"] == "municipio"
        },
        key=lambda item: item[1],
    )
    conteudo = {
        "meta": {
            "titulo": "Territórios da Violência",
            "atualizado_em": "2026-10-26",
            "periodo_consolidado": "2015 a 2024",
            "monitoramento": "2025 completo nas fontes disponíveis e 2026 parcial até agosto",
            "fontes": ["SIM", "SINAN", "Sinesp VDE", "IBGE", "Censo 2022", "RAIS"],
        },
        "municipios": [
            {"id": identificador, "nome": nome} for identificador, nome in municipios
        ],
        "registros": registros,
        "mensal_sinesp": mensal,
        "cobertura_sinesp": limpar_nulos(cobertura),
        "catalogo_prioritario": limpar_nulos(catalogo),
    }
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(
        json.dumps(conteudo, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"JSON do protótipo: {DESTINO.relative_to(ROOT)}")
    print(f"Registros anuais: {len(registros)}")
    print(f"Registros mensais: {len(mensal)}")
    print(f"Municípios de Santa Catarina: {len(municipios)}")


if __name__ == "__main__":
    main()
