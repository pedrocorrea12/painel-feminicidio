"""Baixa a malha municipal de Santa Catarina (IBGE) e gera o GeoJSON do site.

Fonte: API de malhas do IBGE (servicodados.ibge.gov.br/api/v3/malhas).
Saída: dashboard/atlas/data/malha_sc.json, com coordenadas arredondadas
e identificação pelo código de 7 dígitos do município.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/estados/42"
    "?formato=application/vnd.geo+json&intrarregiao=municipio&qualidade=intermediaria"
)
BRONZE = ROOT / "data" / "bronze" / "ibge" / "malha_sc_municipios.geojson"
POPULACAO = ROOT / "data" / "silver" / "populacao_municipio_ano.parquet"
SAIDA = ROOT / "dashboard" / "atlas" / "data" / "malha_sc.json"
CASAS = 3


def _anel(pontos: list) -> list:
    saida = []
    for x, y in pontos:
        ponto = [round(x, CASAS), round(y, CASAS)]
        if not saida or ponto != saida[-1]:
            saida.append(ponto)
    return saida if len(saida) >= 4 else []


def _geometria(geom: dict) -> dict | None:
    poligonos = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    resultado = []
    for poligono in poligonos:
        aneis = [_anel(anel) for anel in poligono]
        aneis = [anel for anel in aneis if anel]
        if aneis:
            resultado.append(aneis)
    if not resultado:
        return None
    if len(resultado) == 1:
        return {"type": "Polygon", "coordinates": resultado[0]}
    return {"type": "MultiPolygon", "coordinates": resultado}


def main() -> None:
    if not BRONZE.exists() or BRONZE.stat().st_size == 0:
        BRONZE.parent.mkdir(parents=True, exist_ok=True)
        print("Baixando malha municipal de SC ...")
        urllib.request.urlretrieve(URL, BRONZE)
    bruto = json.loads(BRONZE.read_text(encoding="utf-8"))

    pop = pd.read_parquet(POPULACAO, columns=["id_municipio", "municipio", "sigla_uf"])
    nomes = dict(
        zip(*pop.loc[pop.sigla_uf.eq("SC")].drop_duplicates("id_municipio")[["id_municipio", "municipio"]].T.values)
    )

    features = []
    for item in bruto["features"]:
        codigo = str(item["properties"]["codarea"])
        geometria = _geometria(item["geometry"])
        if geometria is None:
            raise ValueError(f"Geometria vazia: {codigo}")
        features.append({
            "type": "Feature",
            "id": codigo,
            "properties": {"id": codigo, "nome": nomes.get(codigo)},
            "geometry": geometria,
        })

    ids = {f["id"] for f in features}
    if ids != set(nomes):
        raise ValueError(
            f"Malha não casa com a população: faltam {sorted(set(nomes) - ids)[:5]}, "
            f"sobram {sorted(ids - set(nomes))[:5]}"
        )

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(
        json.dumps({"type": "FeatureCollection", "features": features},
                   ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"Malha: {SAIDA.relative_to(ROOT)} ({len(features)} municípios, {SAIDA.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
