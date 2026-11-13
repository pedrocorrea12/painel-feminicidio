"""Publicação segura de diretórios de artefatos Gold."""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from collections.abc import Callable
from pathlib import Path

GeradorArtefatos = Callable[[Path], None]
ValidadorArtefatos = Callable[[Path], None]


def _existe(caminho: Path) -> bool:
    return caminho.exists() or caminho.is_symlink()


def _remover(caminho: Path) -> None:
    if not _existe(caminho):
        return
    if caminho.is_dir() and not caminho.is_symlink():
        shutil.rmtree(caminho)
    else:
        caminho.unlink()


def _restaurar_destino(destino: Path, backup: Path) -> None:
    if _existe(destino):
        _remover(destino)
    os.replace(backup, destino)


def _trocar_com_backup(temporario: Path, destino: Path) -> None:
    havia_destino = _existe(destino)
    backup = destino.parent / f".{destino.name}.backup-{uuid.uuid4().hex}"

    if havia_destino:
        if not destino.is_dir():
            raise NotADirectoryError(f"Destino publicado não é diretório: {destino}")
        os.replace(destino, backup)

    try:
        os.replace(temporario, destino)
    except BaseException:
        if havia_destino:
            try:
                _restaurar_destino(destino, backup)
            except BaseException as erro_restauracao:
                raise RuntimeError(
                    "Falha ao restaurar o destino publicado após erro na troca."
                ) from erro_restauracao
        raise
    else:
        if havia_destino:
            _remover(backup)


def publicar_diretorio(
    destino_publicado: str | Path,
    gerar_artefatos: GeradorArtefatos,
    validar_artefatos: ValidadorArtefatos,
) -> None:
    """Gera, valida e publica um diretório sem expor uma versão parcial.

    O diretório temporário e o backup são criados como irmãos do destino para
    que as renomeações permaneçam no mesmo volume. Se geração, validação ou
    troca falhar, a exceção original é propagada após a limpeza e, quando já
    existia uma publicação, a versão anterior é restaurada.
    """

    destino = Path(destino_publicado).resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = Path(
        tempfile.mkdtemp(prefix=f".{destino.name}.tmp-", dir=destino.parent)
    )

    try:
        gerar_artefatos(temporario)
        validar_artefatos(temporario)
        _trocar_com_backup(temporario, destino)
    finally:
        _remover(temporario)
