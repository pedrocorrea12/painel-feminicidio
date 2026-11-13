"""Coleta a baseline do pipeline atual sem alterar o projeto.

Dois modos, ambos somente leitura sobre a raiz informada:

    python coletar_baseline.py inventario RAIZ [--saida inventario.json]
    python coletar_baseline.py reproduzir RAIZ COPIA [--saida reproducao.json]

``inventario`` registra linhas, colunas, tamanho e SHA-256 de cada artefato
Silver e Gold e dos dados do site. ``reproduzir`` copia pipeline/, Silver, Gold
e site para COPIA, roda os construtores offline na copia e compara os hashes da
Gold antes e depois. A raiz original nunca é escrita.

Use o Python com pandas 2.2.2, pyarrow 16.1.0 e duckdb (Anaconda do autor).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pyarrow.parquet as pq

# Ordem e escopo dos construtores offline (sem rede e sem Bronze).
CONSTRUTORES_OFFLINE = [
    "build_gold.py",
    "build_dashboard_analysis.py",
    "build_integrated_analysis.py",
    "build_sinesp_analysis.py",
    "build_race_analysis.py",
    "build_sinesp_atlas.py",
    "build_atlas_prototype_data.py",
    "build_atlas_site_data.py",
]
PASTAS_COPIADAS = ["pipeline", "data/silver", "data/gold", "dashboard/dist", "dashboard/atlas/data"]


def sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        while bloco := arquivo.read(1 << 20):
            resumo.update(bloco)
    return resumo.hexdigest()


def linhas_csv(caminho: Path) -> int:
    with caminho.open("rb") as arquivo:
        return max(sum(1 for _ in arquivo) - 1, 0)


def descrever(caminho: Path, raiz: Path) -> dict:
    registro = {
        "arquivo": caminho.relative_to(raiz).as_posix(),
        "bytes": caminho.stat().st_size,
        "sha256": sha256(caminho),
    }
    if caminho.suffix == ".parquet":
        meta = pq.ParquetFile(caminho)
        registro["linhas"] = meta.metadata.num_rows
        registro["colunas"] = meta.metadata.num_columns
    elif caminho.suffix == ".csv":
        registro["linhas"] = linhas_csv(caminho)
    return registro


def artefatos(raiz: Path) -> list[dict]:
    padroes = ["data/silver/*.parquet", "data/gold/**/*.csv", "data/gold/**/*.json",
               "dashboard/dist/data/*.json", "dashboard/atlas/data/**/*.json"]
    vistos: dict[str, Path] = {}
    for padrao in padroes:
        for caminho in sorted(raiz.glob(padrao)):
            vistos[caminho.as_posix()] = caminho
    return [descrever(c, raiz) for c in sorted(vistos.values())]


def inventario(raiz: Path) -> dict:
    inicio = time.perf_counter()
    lista = artefatos(raiz)
    return {
        "python": sys.version.split()[0],
        "segundos": round(time.perf_counter() - inicio, 1),
        "artefatos": lista,
    }


def reproduzir(raiz: Path, copia: Path) -> dict:
    if copia.exists() and any(copia.iterdir()):
        raise SystemExit(f"{copia} não está vazio; use uma pasta nova.")
    for pasta in PASTAS_COPIADAS:
        shutil.copytree(raiz / pasta, copia / pasta)
    # Alguns construtores escrevem relatórios em docs/; a cópia recebe a pasta vazia.
    (copia / "docs").mkdir(exist_ok=True)
    antes = {a["arquivo"]: a["sha256"] for a in artefatos(copia)}
    execucoes = []
    for script in CONSTRUTORES_OFFLINE:
        inicio = time.perf_counter()
        resultado = subprocess.run(
            [sys.executable, str(copia / "pipeline" / script)],
            cwd=copia, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        execucoes.append({
            "script": script,
            "codigo_saida": resultado.returncode,
            "segundos": round(time.perf_counter() - inicio, 1),
            "erro": resultado.stderr.strip().splitlines()[-1] if resultado.returncode else "",
        })
    depois = {a["arquivo"]: a["sha256"] for a in artefatos(copia)}
    return {
        "python": sys.version.split()[0],
        "execucoes": execucoes,
        "alterados": sorted(a for a in antes if a in depois and antes[a] != depois[a]),
        "criados": sorted(set(depois) - set(antes)),
        "removidos": sorted(set(antes) - set(depois)),
        "total_comparado": len(antes),
        "relatorios_docs_gerados": sorted(p.name for p in (copia / "docs").iterdir()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="modo", required=True)
    inv = sub.add_parser("inventario")
    inv.add_argument("raiz", type=Path)
    inv.add_argument("--saida", type=Path)
    rep = sub.add_parser("reproduzir")
    rep.add_argument("raiz", type=Path)
    rep.add_argument("copia", type=Path)
    rep.add_argument("--saida", type=Path)
    args = parser.parse_args()
    dados = inventario(args.raiz) if args.modo == "inventario" else reproduzir(args.raiz, args.copia)
    texto = json.dumps(dados, ensure_ascii=False, indent=2)
    if args.saida:
        args.saida.write_text(texto + "\n", encoding="utf-8")
    else:
        print(texto)


if __name__ == "__main__":
    main()
