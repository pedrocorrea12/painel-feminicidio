"""Gera o pacote analitico consumido pelo painel editorial.

O script usa apenas as camadas Silver consolidadas. Assim, a interface pode ser
reproduzida sem depender das extracoes ainda em desenvolvimento.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INDICADORES = ROOT / "data" / "silver" / "indicadores_territorio_ano.parquet"
SINAN = ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal.parquet"
OUTPUTS = (
    ROOT / "dashboard" / "dist" / "data" / "analise.json",
    ROOT / "data" / "gold" / "analise.json",
)

RACA = {
    "1": "Branca",
    "2": "Preta",
    "3": "Amarela",
    "4": "Parda",
    "5": "Indígena",
    "9": "Ignorada",
}

TIPOS = {
    "VIOL_FISIC": "Física",
    "VIOL_PSICO": "Psicológica/moral",
    "VIOL_SEXU": "Sexual",
    "VIOL_NEGLI": "Negligência/abandono",
    "VIOL_FINAN": "Financeira/econômica",
    "VIOL_TORT": "Tortura",
}

SERIE_COLS = [
    "ano",
    "populacao_feminina",
    "notificacoes",
    "parceiro",
    "residencia",
    "percentual_parceiro",
    "taxa_notificacoes_100mil",
    "taxa_parceiro_100mil",
    "dado_suficiente",
]

# Recortes compactos mantêm o arquivo servido pelo Pages leve. O detalhamento
# completo permanece nas séries nacional e estadual; no município, a interface
# usa apenas taxa, volume, vínculo e o sinalizador de suficiência.
MUNICIPIO_COLS = [
    "ano",
    "notificacoes",
    "parceiro",
    "taxa_notificacoes_100mil",
    "dado_suficiente",
]
UF_2024_COLS = [
    "ano",
    "notificacoes",
    "parceiro",
    "taxa_notificacoes_100mil",
]


def normalizar_numero(value):
    if pd.isna(value):
        return None
    if isinstance(value, (bool,)):  # bool precisa vir antes de int
        return bool(value)
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else round(float(value), 2)
    try:
        number = float(value)
        return int(number) if number.is_integer() else round(number, 2)
    except (TypeError, ValueError):
        return value


def registros(frame: pd.DataFrame, cols: list[str] = SERIE_COLS) -> list[dict]:
    return [
        {column: normalizar_numero(value) for column, value in row.items()}
        for row in frame[cols].sort_values("ano").to_dict("records")
    ]


def faixa_etaria(value: object) -> str:
    raw = str(value or "")
    if len(raw) != 4 or not raw.startswith("4") or not raw[1:].isdigit():
        return "Ignorada"
    idade = int(raw[1:])
    if idade <= 11:
        return "0 a 11"
    if idade <= 17:
        return "12 a 17"
    if idade <= 29:
        return "18 a 29"
    if idade <= 39:
        return "30 a 39"
    if idade <= 49:
        return "40 a 49"
    if idade <= 59:
        return "50 a 59"
    return "60 ou mais"


def perfil(frame: pd.DataFrame) -> dict:
    total = len(frame)
    raca = (
        frame["CS_RACA"]
        .fillna("9")
        .astype(str)
        .map(lambda value: RACA.get(value, "Ignorada"))
        .value_counts()
    )
    ordem_raca = ["Branca", "Parda", "Preta", "Indígena", "Amarela", "Ignorada"]

    idade = frame["NU_IDADE_N"].map(faixa_etaria).value_counts()
    ordem_idade = ["0 a 11", "12 a 17", "18 a 29", "30 a 39", "40 a 49", "50 a 59", "60 ou mais", "Ignorada"]

    tipos = []
    for column, label in TIPOS.items():
        count = int((frame[column].astype(str) == "1").sum())
        tipos.append({"categoria": label, "valor": count, "percentual": round(count / total * 100, 1)})

    return {
        "total": total,
        "raca": [
            {"categoria": label, "valor": int(raca.get(label, 0)), "percentual": round(raca.get(label, 0) / total * 100, 1)}
            for label in ordem_raca
        ],
        "idade": [
            {"categoria": label, "valor": int(idade.get(label, 0)), "percentual": round(idade.get(label, 0) / total * 100, 1)}
            for label in ordem_idade
        ],
        "tipos": sorted(tipos, key=lambda item: item["valor"], reverse=True),
    }


def construir() -> dict:
    indicadores = pd.read_parquet(INDICADORES)
    brasil = indicadores[indicadores["nivel_territorial"] == "brasil"]
    santa_catarina = indicadores[
        (indicadores["nivel_territorial"] == "uf") & (indicadores["sigla_uf"] == "SC")
    ]
    municipios = indicadores[
        (indicadores["nivel_territorial"] == "municipio") & (indicadores["sigla_uf"] == "SC")
    ]
    ufs = indicadores[indicadores["nivel_territorial"] == "uf"]

    municipios_saida = []
    for municipio_id, frame in municipios.groupby("id_territorio", sort=False):
        municipios_saida.append(
            {
                "id": str(municipio_id),
                "nome": str(frame.iloc[0]["territorio"]),
                "serie": registros(frame, MUNICIPIO_COLS),
            }
        )
    municipios_saida.sort(key=lambda item: item["nome"])

    ufs_saida = []
    for sigla, frame in ufs.groupby("sigla_uf", sort=True):
        ufs_saida.append({"sigla": str(sigla), "serie": registros(frame[frame["ano"] == 2024], UF_2024_COLS)})

    perfil_cols = ["ano", "SG_UF", "CS_RACA", "NU_IDADE_N", *TIPOS]
    sinan = pd.read_parquet(SINAN, columns=perfil_cols)
    sinan_2024 = sinan[sinan["ano"] == 2024]
    perfil_brasil = perfil(sinan_2024)
    perfil_sc = perfil(sinan_2024[sinan_2024["SG_UF"].astype(str) == "42"])

    return {
        "meta": {
            "gerado_em": date.today().isoformat(),
            "periodo": [2015, 2024],
            "unidade_taxa": "por 100 mil mulheres",
            "fonte_principal": "SINAN / Ministério da Saúde",
        },
        "series": {
            "brasil": registros(brasil),
            "santa_catarina": registros(santa_catarina),
        },
        "municipios_sc": municipios_saida,
        "ufs": ufs_saida,
        "perfis_2024": {"brasil": perfil_brasil, "santa_catarina": perfil_sc},
        "sim_referencia_sc": [
            {"ano": 2022, "obitos_agressao": 93},
            {"ano": 2023, "obitos_agressao": 105},
            {"ano": 2024, "obitos_agressao": 90},
        ],
    }


def main() -> None:
    payload = construir()
    rendered = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    for output in OUTPUTS:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"Gerado: {output.relative_to(ROOT)} ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
