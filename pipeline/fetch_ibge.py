"""Baixa a dimensão oficial de municípios de Santa Catarina da API do IBGE."""

from __future__ import annotations

import json
import gzip
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
DESTINO = ROOT / "data" / "bronze" / "ibge" / "municipios_sc.json"
URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/42/municipios"


def main() -> None:
    with urlopen(URL, timeout=30) as resposta:
        bruto = resposta.read()
        if resposta.headers.get("Content-Encoding") == "gzip" or bruto[:2] == b"\x1f\x8b":
            bruto = gzip.decompress(bruto)
        dados = json.loads(bruto.decode("utf-8"))
    dimensao = [{"id": int(item["id"]), "nome": item["nome"]} for item in dados]
    if len(dimensao) != 295:
        raise ValueError(f"Esperados 295 municípios de SC, recebidos {len(dimensao)}")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(dimensao, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Dimensão salva em {DESTINO} ({len(dimensao)} municípios)")


if __name__ == "__main__":
    main()

