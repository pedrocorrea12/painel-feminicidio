"""Publicação segura de diretórios de artefatos Gold."""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

GeradorArtefatos = Callable[[Path], None]
ValidadorArtefatos = Callable[[Path], None]
GeradorConjunto = Callable[[Sequence[Path]], None]
ValidadorConjunto = Callable[[Sequence[Path]], None]


@dataclass(frozen=True)
class ResultadoPublicacao:
    """Resultado de uma publicação concluída."""

    destino: Path
    backup_remanescente: Path | None = None


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


def _backup_orfao(destino: Path) -> Path | None:
    encontrados = sorted(
        destino.parent.glob(f".{destino.name}.backup-*"),
        key=lambda caminho: caminho.name,
    )
    return encontrados[0] if encontrados else None


def _trocar_com_backup(temporario: Path, destino: Path) -> Path | None:
    havia_destino = _existe(destino)
    backup = destino.parent / f".{destino.name}.backup-{uuid.uuid4().hex}"

    if havia_destino:
        if not destino.is_dir():
            raise NotADirectoryError(f"Destino publicado não é diretório: {destino}")
        os.replace(destino, backup)

    try:
        os.replace(temporario, destino)
    except BaseException as erro_troca:
        if havia_destino:
            try:
                _restaurar_destino(destino, backup)
            except BaseException as erro_restauracao:
                falha = RuntimeError(
                    "Falha na troca do destino publicado: "
                    f"{erro_troca}. Falha também na restauração; "
                    f"backup preservado em: {backup}"
                )
                falha.add_note(f"Erro de restauração: {erro_restauracao}")
                raise falha from erro_troca
        raise
    else:
        if havia_destino:
            try:
                _remover(backup)
            except OSError as erro_limpeza:
                remanescente = backup if _existe(backup) else None
                warnings.warn(
                    "Publicação concluída, mas o backup não pôde ser removido: "
                    f"{backup}. Erro: {erro_limpeza}",
                    RuntimeWarning,
                    stacklevel=3,
                )
                return remanescente
    return None


def publicar_diretorio(
    destino_publicado: str | Path,
    gerar_artefatos: GeradorArtefatos,
    validar_artefatos: ValidadorArtefatos,
) -> ResultadoPublicacao:
    """Gera, valida e publica um diretório com restauração em caso de falha.

    O diretório temporário e o backup são criados como irmãos do destino para
    que as renomeações permaneçam no mesmo volume. No Windows, há um intervalo
    entre mover o destino para backup e instalar a nova versão em que o caminho
    publicado não existe; portanto, a troca não é atômica em sentido estrito.
    Se geração, validação ou troca falhar, a exceção original é propagada após
    a limpeza e, quando já existia uma publicação, a versão anterior é
    restaurada.
    """

    destino = Path(destino_publicado).resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    orfao = _backup_orfao(destino)
    if orfao is not None:
        raise RuntimeError(f"Backup órfão impede publicação: {orfao}")

    temporario = Path(
        tempfile.mkdtemp(prefix=f".{destino.name}.tmp-", dir=destino.parent)
    )

    try:
        gerar_artefatos(temporario)
        validar_artefatos(temporario)
        backup_remanescente = _trocar_com_backup(temporario, destino)
        return ResultadoPublicacao(destino, backup_remanescente)
    finally:
        _remover(temporario)


def _remover_backups(backups: list[tuple[Path, Path | None]]) -> Path | None:
    remanescente = None
    for _, backup in backups:
        if backup is None:
            continue
        try:
            _remover(backup)
        except OSError as erro_limpeza:
            if _existe(backup):
                remanescente = remanescente or backup
            warnings.warn(
                "Publicação concluída, mas o backup não pôde ser removido: "
                f"{backup}. Erro: {erro_limpeza}",
                RuntimeWarning,
                stacklevel=4,
            )
    return remanescente


def _trocar_conjunto(
    temporarios: Sequence[Path], destinos: Sequence[Path]
) -> tuple[ResultadoPublicacao, ...]:
    backups: list[tuple[Path, Path | None]] = []
    instalados: set[Path] = set()
    try:
        for temporario, destino in zip(temporarios, destinos, strict=True):
            backup = None
            if _existe(destino):
                if not destino.is_dir():
                    raise NotADirectoryError(
                        f"Destino publicado não é diretório: {destino}"
                    )
                backup = destino.parent / f".{destino.name}.backup-{uuid.uuid4().hex}"
                os.replace(destino, backup)
            backups.append((destino, backup))
            os.replace(temporario, destino)
            instalados.add(destino)
    except BaseException as erro_troca:
        preservados: list[Path] = []
        for destino, backup in reversed(backups):
            try:
                if backup is not None:
                    _restaurar_destino(destino, backup)
                elif destino in instalados:
                    _remover(destino)
            except BaseException as erro_restauracao:
                if backup is not None and _existe(backup):
                    preservados.append(backup)
                erro_troca.add_note(
                    f"Erro de restauração de {destino}: {erro_restauracao}"
                )
        if preservados:
            falha = RuntimeError(
                "Falha na troca conjunta dos destinos publicados: "
                f"{erro_troca}. Falha também na restauração; "
                "backups preservados em: "
                + ", ".join(str(caminho) for caminho in preservados)
            )
            raise falha from erro_troca
        raise

    remanescente = _remover_backups(backups)
    return tuple(
        ResultadoPublicacao(destino, remanescente if backup is not None else None)
        for destino, backup in backups
    )


def publicar_conjunto(
    destinos_publicados: Sequence[str | Path],
    gerar_artefatos: GeradorConjunto,
    validar_artefatos: ValidadorConjunto,
) -> tuple[ResultadoPublicacao, ...]:
    """Gera, valida e publica vários diretórios como uma única unidade.

    Cada destino recebe um diretório temporário irmão. Os geradores e os
    validadores recebem a lista de temporários na mesma ordem dos destinos, o
    que permite validar os diretórios entre si antes de qualquer troca. A troca
    ocorre destino a destino; se uma delas falhar, as já feitas são desfeitas e
    todos os destinos voltam à versão anterior. Como em ``publicar_diretorio``,
    no Windows há um intervalo em que um destino não existe durante sua troca.
    """

    destinos = [Path(destino).resolve() for destino in destinos_publicados]
    if not destinos:
        raise ValueError("Nenhum destino informado para a publicação conjunta")
    if len(set(destinos)) != len(destinos):
        raise ValueError("Destinos duplicados na publicação conjunta")
    for destino in destinos:
        destino.parent.mkdir(parents=True, exist_ok=True)
        orfao = _backup_orfao(destino)
        if orfao is not None:
            raise RuntimeError(f"Backup órfão impede publicação: {orfao}")

    temporarios: list[Path] = []
    try:
        for destino in destinos:
            temporarios.append(
                Path(tempfile.mkdtemp(prefix=f".{destino.name}.tmp-", dir=destino.parent))
            )
        gerar_artefatos(tuple(temporarios))
        validar_artefatos(tuple(temporarios))
        return _trocar_conjunto(temporarios, destinos)
    finally:
        for temporario in temporarios:
            _remover(temporario)
