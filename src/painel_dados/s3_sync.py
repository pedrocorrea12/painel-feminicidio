"""Publicação da camada Gold no S3 por meio da AWS CLI."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from painel_dados.config import project_paths

NOME_MANIFESTO = "manifesto.json"
_PADRAO_BUCKET = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
_PADRAO_PREFIXO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_PADRAO_EXECUCAO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_PADRAO_PERFIL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@+-]{0,127}$")
_PREFIXOS_BUCKET_RESERVADOS = ("xn--", "sthree-", "amzn-s3-demo-")
_SUFIXOS_BUCKET_RESERVADOS = ("-s3alias", "--ol-s3", ".mrap", "--x-s3", "--table-s3")


@dataclass(frozen=True)
class ResultadoSincronizacao:
    """Resultado observável da execução da AWS CLI."""

    comando: tuple[str, ...]
    manifesto: Path
    processo: subprocess.CompletedProcess[str]


def _validar_bucket(bucket: str) -> None:
    invalido = (
        not _PADRAO_BUCKET.fullmatch(bucket)
        or ".." in bucket
        or bucket.startswith(_PREFIXOS_BUCKET_RESERVADOS)
        or bucket.endswith(_SUFIXOS_BUCKET_RESERVADOS)
    )
    try:
        ipaddress.ip_address(bucket)
    except ValueError:
        pass
    else:
        invalido = True
    if invalido:
        raise ValueError(f"Nome de bucket S3 inválido: {bucket}")


def _validar_prefixo(prefixo: str) -> None:
    segmentos = prefixo.split("/")
    if (
        not prefixo
        or len(prefixo) > 512
        or not _PADRAO_PREFIXO.fullmatch(prefixo)
        or prefixo.startswith("/")
        or prefixo.endswith("/")
        or "//" in prefixo
        or any(segmento in {".", ".."} for segmento in segmentos)
    ):
        raise ValueError(f"Prefixo S3 inválido: {prefixo}")


def _validar_id_execucao(id_execucao: str) -> None:
    if not _PADRAO_EXECUCAO.fullmatch(id_execucao):
        raise ValueError(f"ID de execução inválido: {id_execucao}")


def _validar_perfil(perfil: str | None) -> None:
    if perfil is not None and not _PADRAO_PERFIL.fullmatch(perfil):
        raise ValueError(f"Perfil AWS inválido: {perfil}")


def _resolver_diretorio_gold(
    diretorio_gold: str | Path,
    raiz_projeto: str | Path | None,
) -> tuple[Path, Path]:
    raiz = project_paths(raiz_projeto).root
    limite_gold = (raiz / "data" / "gold").resolve()
    origem = Path(diretorio_gold).resolve()
    if origem != limite_gold and not origem.is_relative_to(limite_gold):
        raise ValueError(f"Diretório de origem fora de data/gold: {origem}")
    if not origem.is_dir():
        raise ValueError(f"Diretório Gold inexistente: {origem}")
    return origem, raiz


def montar_comando_sync(
    diretorio_gold: str | Path,
    bucket: str,
    id_execucao: str,
    *,
    raiz_projeto: str | Path | None = None,
    prefixo: str = "gold",
    perfil: str | None = None,
    simulacao: bool = True,
) -> tuple[str, ...]:
    """Monta um ``aws s3 sync`` seguro, em dry-run por padrão."""

    origem, _ = _resolver_diretorio_gold(diretorio_gold, raiz_projeto)
    _validar_bucket(bucket)
    _validar_prefixo(prefixo)
    _validar_id_execucao(id_execucao)
    _validar_perfil(perfil)

    destino = f"s3://{bucket}/{prefixo}/{id_execucao}/"
    comando = ["aws", "s3", "sync", str(origem), destino, "--no-follow-symlinks"]
    if simulacao:
        comando.append("--dryrun")
    if perfil is not None:
        comando.extend(["--profile", perfil])
    return tuple(comando)


def _sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def construir_manifesto(
    diretorio_gold: str | Path,
    id_execucao: str,
    *,
    raiz_projeto: str | Path | None = None,
) -> dict[str, object]:
    """Constrói um manifesto determinístico sem incluir o próprio manifesto."""

    origem, raiz = _resolver_diretorio_gold(diretorio_gold, raiz_projeto)
    _validar_id_execucao(id_execucao)
    arquivos: list[dict[str, object]] = []
    for caminho in sorted(origem.rglob("*"), key=lambda item: item.as_posix()):
        if not caminho.is_file() or caminho == origem / NOME_MANIFESTO:
            continue
        arquivos.append(
            {
                "caminho": caminho.relative_to(origem).as_posix(),
                "sha256": _sha256(caminho),
                "tamanho_bytes": caminho.stat().st_size,
            }
        )
    return {
        "arquivos": arquivos,
        "id_execucao": id_execucao,
        "origem": origem.relative_to(raiz).as_posix(),
        "quantidade_arquivos": len(arquivos),
        "tamanho_total_bytes": sum(int(item["tamanho_bytes"]) for item in arquivos),
        "versao_manifesto": 1,
    }


def escrever_manifesto(
    diretorio_gold: str | Path,
    id_execucao: str,
    *,
    raiz_projeto: str | Path | None = None,
) -> Path:
    """Escreve ``manifesto.json`` na origem para inclusão no sync."""

    origem, _ = _resolver_diretorio_gold(diretorio_gold, raiz_projeto)
    manifesto = construir_manifesto(origem, id_execucao, raiz_projeto=raiz_projeto)
    destino = origem / NOME_MANIFESTO
    destino.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destino


def sincronizar_gold(
    diretorio_gold: str | Path,
    bucket: str,
    id_execucao: str,
    *,
    raiz_projeto: str | Path | None = None,
    prefixo: str = "gold",
    perfil: str | None = None,
    simulacao: bool = True,
) -> ResultadoSincronizacao:
    """Escreve o manifesto e executa a AWS CLI sem usar shell."""

    comando = montar_comando_sync(
        diretorio_gold,
        bucket,
        id_execucao,
        raiz_projeto=raiz_projeto,
        prefixo=prefixo,
        perfil=perfil,
        simulacao=simulacao,
    )
    manifesto = escrever_manifesto(
        diretorio_gold,
        id_execucao,
        raiz_projeto=raiz_projeto,
    )
    processo = subprocess.run(
        comando,
        check=True,
        capture_output=True,
        text=True,
    )
    return ResultadoSincronizacao(comando, manifesto, processo)
