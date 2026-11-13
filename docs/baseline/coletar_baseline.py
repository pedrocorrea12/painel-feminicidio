"""Coleta a baseline do pipeline atual sem alterar o projeto.

Três modos. A raiz informada só é lida; saídas e cópias devem ficar fora dela:

    python coletar_baseline.py inventario RAIZ --saida inventario.json
    python coletar_baseline.py reproduzir RAIZ COPIA --saida reproducao.json
    python coletar_baseline.py validador RAIZ --saida validador.json

``inventario`` registra bytes, linhas, colunas e SHA-256 de cada artefato Silver,
Gold e do site. ``reproduzir`` copia pipeline/, Silver, Gold e site para COPIA,
roda os construtores offline na cópia e compara os artefatos antes e depois,
guardando o que mudou em cada um. ``validador`` roda ``validate_project.py`` e,
numa cópia temporária, neutraliza uma a uma as asserções que falham para medir
quantas falham e se o restante passa.

Use o Python com pandas 2.2.2, pyarrow 16.1.0 e duckdb (Anaconda do autor).
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import pyarrow.parquet as pq

# Construtores sem rede e sem Bronze, na ordem de dependência.
# build_gold.py executa build_silver internamente (Silver territorial).
CONSTRUTORES_OFFLINE = [
    "build_gold.py",
    "build_dashboard_analysis.py",
    "build_integrated_analysis.py",
    "build_sinesp_analysis.py",
    "build_race_analysis.py",
    "build_sinesp_atlas.py",
    "build_atlas_catalog.py",
    "build_atlas_prototype_data.py",
    "build_atlas_site_data.py",
]
PASTAS_COPIADAS = [
    "pipeline",
    "data/silver",
    "data/gold",
    "dashboard/dist",
    "dashboard/atlas/data",
    "dashboard/atlas/downloads",
    "dashboard/prototipos/atlas-violencia",
]
PADROES = [
    "data/silver/*.parquet",
    "data/gold/**/*.csv",
    "data/gold/**/*.json",
    "dashboard/dist/data/*.json",
    "dashboard/atlas/data/**/*.json",
    "dashboard/atlas/downloads/*.zip",
    "dashboard/prototipos/atlas-violencia/data.json",
]


def sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        while bloco := arquivo.read(1 << 20):
            resumo.update(bloco)
    return resumo.hexdigest()


def forma_csv(caminho: Path) -> tuple[int, int]:
    """Conta registros e colunas com o módulo csv (campos com quebra de linha contam certo)."""

    csv.field_size_limit(1 << 30)
    with caminho.open(newline="", encoding="utf-8-sig") as arquivo:
        leitor = csv.reader(arquivo)
        cabecalho = next(leitor, [])
        return sum(1 for _ in leitor), len(cabecalho)


def conteudo_zip(caminho: Path) -> str:
    """Resumo do conteúdo do ZIP que ignora datas de modificação dos membros."""

    with zipfile.ZipFile(caminho) as pacote:
        membros = sorted((m.filename, m.CRC, m.file_size) for m in pacote.infolist())
    return hashlib.sha256(json.dumps(membros).encode()).hexdigest()


def descrever(caminho: Path, raiz: Path) -> dict:
    registro = {
        "arquivo": caminho.relative_to(raiz).as_posix(),
        "bytes": caminho.stat().st_size,
        "sha256": sha256(caminho),
    }
    if caminho.suffix == ".parquet":
        meta = pq.ParquetFile(caminho).metadata
        registro["linhas"], registro["colunas"] = meta.num_rows, meta.num_columns
    elif caminho.suffix == ".csv":
        registro["linhas"], registro["colunas"] = forma_csv(caminho)
    elif caminho.suffix == ".zip":
        registro["sha256_conteudo"] = conteudo_zip(caminho)
    return registro


def artefatos(raiz: Path) -> list[dict]:
    vistos = {c.as_posix(): c for padrao in PADROES for c in raiz.glob(padrao)}
    return [descrever(vistos[chave], raiz) for chave in sorted(vistos)]


def exigir_fora_da_raiz(raiz: Path, caminho: Path | None, nome: str) -> None:
    if caminho is None:
        return
    if caminho.resolve().is_relative_to(raiz.resolve()):
        raise SystemExit(f"{nome} ({caminho}) fica dentro da raiz; escolha um caminho fora dela.")


def inventario(raiz: Path) -> dict:
    inicio = time.perf_counter()
    lista = artefatos(raiz)
    return {
        "python": sys.version.split()[0],
        "segundos": round(time.perf_counter() - inicio, 1),
        "artefatos": lista,
    }


def diferencas_json(antes: object, depois: object, caminho: str = "") -> list[dict]:
    if isinstance(antes, dict) and isinstance(depois, dict):
        saida = []
        for chave in sorted(set(antes) | set(depois)):
            if chave not in antes or chave not in depois:
                saida.append({"caminho": f"{caminho}/{chave}", "mudanca": "chave só em um lado"})
            else:
                saida += diferencas_json(antes[chave], depois[chave], f"{caminho}/{chave}")
        return saida
    if isinstance(antes, list) and isinstance(depois, list) and len(antes) == len(depois):
        saida = []
        for indice, (a, d) in enumerate(zip(antes, depois, strict=True)):
            saida += diferencas_json(a, d, f"{caminho}[{indice}]")
        return saida
    if antes != depois:
        return [{"caminho": caminho, "antes": str(antes)[:60], "depois": str(depois)[:60]}]
    return []


def explicar_mudanca(arquivo: str, raiz: Path, copia: Path, antes: dict, depois: dict) -> dict:
    registro: dict = {"arquivo": arquivo}
    if arquivo.endswith(".json"):
        difs = diferencas_json(
            json.loads((raiz / arquivo).read_text(encoding="utf-8")),
            json.loads((copia / arquivo).read_text(encoding="utf-8")),
        )
        registro["total_diferencas"] = len(difs)
        registro["diferencas"] = difs[:10]
    elif arquivo.endswith(".zip"):
        registro["conteudo_igual"] = (
            antes[arquivo].get("sha256_conteudo") == depois[arquivo].get("sha256_conteudo")
        )
    return registro


def reproduzir(raiz: Path, copia: Path) -> dict:
    if copia.exists() and any(copia.iterdir()):
        raise SystemExit(f"{copia} não está vazio; use uma pasta nova.")
    for pasta in PASTAS_COPIADAS:
        shutil.copytree(raiz / pasta, copia / pasta)
    # Alguns construtores escrevem relatórios em docs/; a cópia recebe a pasta vazia.
    (copia / "docs").mkdir(exist_ok=True)
    antes = {a["arquivo"]: a for a in artefatos(copia)}
    execucoes = []
    for script in CONSTRUTORES_OFFLINE:
        inicio = time.perf_counter()
        resultado = subprocess.run(
            [sys.executable, str(copia / "pipeline" / script)],
            cwd=copia,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        execucoes.append(
            {
                "script": script,
                "codigo_saida": resultado.returncode,
                "segundos": round(time.perf_counter() - inicio, 1),
                "erro": resultado.stderr.strip().splitlines()[-1] if resultado.returncode else "",
            }
        )
    depois = {a["arquivo"]: a for a in artefatos(copia)}
    alterados = sorted(
        a for a in antes if a in depois and antes[a]["sha256"] != depois[a]["sha256"]
    )
    return {
        "python": sys.version.split()[0],
        "execucoes": execucoes,
        "total_comparado": len(antes),
        "alterados": [explicar_mudanca(a, raiz, copia, antes, depois) for a in alterados],
        "criados": sorted(set(depois) - set(antes)),
        "removidos": sorted(set(antes) - set(depois)),
        "relatorios_docs_gerados": sorted(p.name for p in (copia / "docs").iterdir()),
    }


def validador(raiz: Path) -> dict:
    """Roda validate_project.py e mede quantas asserções falham nos dados atuais."""

    original = raiz / "pipeline" / "validate_project.py"
    fonte = original.read_text(encoding="utf-8")
    linhas_originais = fonte.splitlines()
    marcador = "ROOT = Path(__file__).resolve().parents[1]"
    if marcador not in fonte:
        raise SystemExit("validate_project.py mudou: marcador de ROOT não encontrado.")
    # A cópia roda fora do projeto; ROOT passa a apontar para a raiz real (mesma linha).
    fonte = fonte.replace(marcador, f"ROOT = Path({str(raiz.resolve())!r})", 1)
    falhas: list[dict] = []
    with tempfile.TemporaryDirectory() as pasta:
        copia = Path(pasta) / "validate_project_copia.py"
        for _ in range(50):
            copia.write_text(fonte, encoding="utf-8")
            inicio = time.perf_counter()
            resultado = subprocess.run(
                [sys.executable, str(copia)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            segundos = round(time.perf_counter() - inicio, 1)
            if resultado.returncode == 0:
                return {
                    "python": sys.version.split()[0],
                    "original_passa": not falhas,
                    "assercoes_que_falham": falhas,
                    "restante_passa": True,
                    "segundos_ultima_execucao": segundos,
                }
            numeros = re.findall(r"line (\d+), in main", resultado.stderr)
            if "AssertionError" not in resultado.stderr or not numeros:
                return {
                    "python": sys.version.split()[0],
                    "original_passa": False,
                    "assercoes_que_falham": falhas,
                    "restante_passa": False,
                    "erro_nao_assercao": resultado.stderr.strip().splitlines()[-1],
                }
            numero = int(numeros[-1])
            no = next(
                n
                for n in ast.walk(ast.parse(fonte))
                if isinstance(n, ast.Assert) and n.lineno <= numero <= n.end_lineno
            )
            linhas = fonte.splitlines()
            texto = " ".join(parte.strip() for parte in linhas[no.lineno - 1 : no.end_lineno])
            # A neutralização preserva o número de linhas, então a linha vale para o original.
            assert linhas_originais[no.lineno - 1].strip() == linhas[no.lineno - 1].strip()
            falhas.append({"linha_original": no.lineno, "assercao": texto})
            recuo = re.match(r"\s*", linhas[no.lineno - 1]).group()
            linhas[no.lineno - 1] = recuo + "pass"
            for indice in range(no.lineno, no.end_lineno):
                linhas[indice] = ""
            fonte = "\n".join(linhas) + "\n"
    raise SystemExit("Mais de 50 asserções falharam; interrompido.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="modo", required=True)
    for nome in ("inventario", "reproduzir", "validador"):
        modo = sub.add_parser(nome)
        modo.add_argument("raiz", type=Path)
        if nome == "reproduzir":
            modo.add_argument("copia", type=Path)
        modo.add_argument("--saida", type=Path)
    args = parser.parse_args()
    exigir_fora_da_raiz(args.raiz, args.saida, "--saida")
    if args.modo == "inventario":
        dados = inventario(args.raiz)
    elif args.modo == "reproduzir":
        exigir_fora_da_raiz(args.raiz, args.copia, "COPIA")
        dados = reproduzir(args.raiz, args.copia)
    else:
        dados = validador(args.raiz)
    texto = json.dumps(dados, ensure_ascii=False, indent=2)
    if args.saida:
        args.saida.write_text(texto + "\n", encoding="utf-8")
    else:
        print(texto)


if __name__ == "__main__":
    main()
