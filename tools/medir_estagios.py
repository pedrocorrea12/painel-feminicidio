"""Mede tempo, pico de memória e volume de saída dos estágios do pipeline.

Roda numa CÓPIA do repositório (nunca na raiz) para não alterar dados versionados:

    python tools/medir_estagios.py --copia C:/caminho/vazio --saida docs/benchmark/medicoes.json

Estágios de rede (extract_*, fetch_*) não são executados. Cada estágio roda em um
subprocesso; o pico de memória é o maior entre o pico do conjunto de
trabalho de um processo da árvore e a soma simultânea dos processos, amostrado a cada
20 ms com psutil (sem psutil = None). Só o arquivo de resultados (--saida) é gravado
onde você indicar; os estágios rodam e gravam apenas na cópia.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# Ordem de dependência: Bronze -> Silver por fonte -> Silver territorial/Gold -> atlas.
ESTAGIOS = [
    ("bronze_para_silver", "build_populacao_2025.py"),
    ("bronze_para_silver", "build_sinan_atlas.py"),
    ("bronze_para_silver", "build_sim_atlas.py"),
    ("bronze_para_silver", "build_rais.py"),
    ("silver_para_gold", "build_gold.py"),
    ("gold_analitica", "build_dashboard_analysis.py"),
    ("gold_analitica", "build_integrated_analysis.py"),
    ("gold_analitica", "build_sinesp_analysis.py"),
    ("gold_analitica", "build_race_analysis.py"),
    ("gold_analitica", "build_sinesp_atlas.py"),
    ("site", "build_atlas_catalog.py"),
    ("site", "build_atlas_prototype_data.py"),
    ("site", "build_atlas_site_data.py"),
]
PASTAS = [
    "pipeline",
    "src",
    "data/bronze",
    "data/silver",
    "data/gold",
    "dashboard/dist",
    "dashboard/atlas/data",
    "dashboard/atlas/downloads",
    "dashboard/prototipos/atlas-violencia",
]


def bytes_da_arvore(pasta: Path) -> int:
    return sum(p.stat().st_size for p in pasta.rglob("*") if p.is_file())


def instantaneo(copia: Path, pastas: list[str]) -> dict[str, tuple[int, int]]:
    estado = {}
    for pasta in pastas:
        base = copia / pasta
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file():
                    st = p.stat()
                    estado[str(p)] = (st.st_size, st.st_mtime_ns)
    return estado


def acompanhar(processo: subprocess.Popen) -> tuple[float | None, str]:
    """Espera o processo e devolve o pico de memória (MB) da árvore e o stderr.

    No Windows o python de um venv é um lançador que cria o interpretador real como
    filho; por isso a árvore inteira é amostrada (psutil), não só o processo direto.
    """
    try:
        import psutil
    except ImportError:
        _, erro = processo.communicate()
        return None, erro
    raiz = psutil.Process(processo.pid)
    picos: dict[int, int] = {}
    pico_soma = 0
    while processo.poll() is None:
        soma = 0
        try:
            for p in [raiz, *raiz.children(recursive=True)]:
                info = p.memory_info()
                picos[p.pid] = max(picos.get(p.pid, 0), getattr(info, "peak_wset", info.rss))
                soma += info.rss
        except psutil.Error:
            pass
        pico_soma = max(pico_soma, soma)
        time.sleep(0.02)
    erro = processo.stderr.read() if processo.stderr else ""
    maior = max(picos.values(), default=0)
    # Referência conservadora: o maior entre o pico de um processo e a soma simultânea.
    return round(max(maior, pico_soma) / 1024 / 1024, 1), erro


def medir(copia: Path, grupo: str, script: str) -> dict:
    antes = instantaneo(copia, PASTAS[3:])
    inicio = time.perf_counter()
    processo = subprocess.Popen(
        [sys.executable, str(copia / "pipeline" / script)],
        cwd=copia,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONPATH": str(copia / "src"), "PYTHONIOENCODING": "utf-8"},
    )
    pico, erro = acompanhar(processo)
    segundos = round(time.perf_counter() - inicio, 2)
    depois = instantaneo(copia, PASTAS[3:])
    gravados = [k for k, v in depois.items() if antes.get(k) != v]
    return {
        "grupo": grupo,
        "script": script,
        "codigo_saida": processo.returncode,
        "segundos": segundos,
        "pico_memoria_mb": pico,
        "arquivos_gravados": len(gravados),
        "mb_gravados": round(sum(depois[k][0] for k in gravados) / 1024 / 1024, 2),
        "erro": erro.strip().splitlines()[-1] if processo.returncode and erro.strip() else "",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--copia", required=True, type=Path, help="pasta nova e vazia fora do repositório"
    )
    ap.add_argument(
        "--origem", type=Path, default=RAIZ, help="raiz com data/ completo (Bronze e Silver)"
    )
    ap.add_argument("--saida", type=Path, help="JSON de saída")
    ap.add_argument("--repeticoes", type=int, default=1)
    args = ap.parse_args()

    copia = args.copia.resolve()
    if RAIZ in copia.parents or copia == RAIZ:
        raise SystemExit("A cópia deve ficar fora do repositório.")
    if copia.exists() and any(copia.iterdir()):
        raise SystemExit(f"{copia} não está vazia.")
    origem = args.origem.resolve()
    for pasta in PASTAS:
        fonte = (origem if pasta.startswith("data/") else RAIZ) / pasta
        if fonte.exists():
            shutil.copytree(fonte, copia / pasta)
    (copia / "docs").mkdir(exist_ok=True)

    medicoes = []
    for grupo, script in ESTAGIOS:
        for rodada in range(1, args.repeticoes + 1):
            r = medir(copia, grupo, script)
            r["rodada"] = rodada
            medicoes.append(r)
            print(
                f"{script:36s} {r['segundos']:8.2f}s {r['pico_memoria_mb']} MB "
                f"saída={r['codigo_saida']}"
            )

    resultado = {
        "ambiente": {
            "so": platform.platform(),
            "python": platform.python_version(),
            "cpus": os.cpu_count(),
        },
        "tamanho_entrada_mb": {
            p: round(bytes_da_arvore(origem / p) / 1024 / 1024, 1)
            for p in ("data/bronze", "data/silver", "data/gold")
            if (origem / p).exists()
        },
        "medicoes": medicoes,
    }
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
