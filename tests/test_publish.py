import os
from pathlib import Path

import pytest

import painel_dados.publish as modulo_publicacao
from painel_dados.publish import publicar_diretorio


def _escrever_versao(diretorio: Path, versao: str) -> None:
    diretorio.mkdir(parents=True, exist_ok=True)
    (diretorio / "versao.txt").write_text(versao, encoding="utf-8")
    subdiretorio = diretorio / "dados"
    subdiretorio.mkdir()
    (subdiretorio / "artefato.bin").write_bytes(versao.encode("utf-8") + b"\x00\xff")


def _retrato(diretorio: Path) -> dict[str, bytes | None]:
    retrato: dict[str, bytes | None] = {}
    for caminho in sorted(diretorio.rglob("*")):
        chave = caminho.relative_to(diretorio).as_posix()
        retrato[chave] = None if caminho.is_dir() else caminho.read_bytes()
    return retrato


def _validar_versao_esperada(versao: str):
    def validar(diretorio: Path) -> None:
        assert (diretorio / "versao.txt").read_text(encoding="utf-8") == versao

    return validar


def _assert_sem_residuos(pai: Path, destino: Path) -> None:
    prefixos = (f".{destino.name}.tmp-", f".{destino.name}.backup-")
    residuos = [item.name for item in pai.iterdir() if item.name.startswith(prefixos)]
    assert residuos == []


def test_publicacao_valida_substitui_destino(tmp_path: Path) -> None:
    destino = tmp_path / "publicado"
    _escrever_versao(destino, "anterior")
    (destino / "obsoleto.txt").write_text("remover", encoding="utf-8")

    publicar_diretorio(
        destino,
        lambda temporario: _escrever_versao(temporario, "nova"),
        _validar_versao_esperada("nova"),
    )

    assert (destino / "versao.txt").read_text(encoding="utf-8") == "nova"
    assert not (destino / "obsoleto.txt").exists()
    _assert_sem_residuos(tmp_path, destino)


def test_validacao_com_erro_preserva_destino_byte_a_byte(tmp_path: Path) -> None:
    destino = tmp_path / "publicado"
    _escrever_versao(destino, "anterior")
    anterior = _retrato(destino)

    def validar_com_erro(_temporario: Path) -> None:
        raise ValueError("Gold inválida")

    with pytest.raises(ValueError, match="^Gold inválida$"):
        publicar_diretorio(
            destino,
            lambda temporario: _escrever_versao(temporario, "nova"),
            validar_com_erro,
        )

    assert _retrato(destino) == anterior
    _assert_sem_residuos(tmp_path, destino)


def test_falha_de_geracao_preserva_destino_byte_a_byte(tmp_path: Path) -> None:
    destino = tmp_path / "publicado"
    _escrever_versao(destino, "anterior")
    anterior = _retrato(destino)

    def gerar_com_erro(temporario: Path) -> None:
        _escrever_versao(temporario, "incompleta")
        raise RuntimeError("geração interrompida")

    with pytest.raises(RuntimeError, match="^geração interrompida$"):
        publicar_diretorio(destino, gerar_com_erro, lambda _temporario: None)

    assert _retrato(destino) == anterior
    _assert_sem_residuos(tmp_path, destino)


def test_falha_no_meio_da_troca_restaura_destino(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destino = tmp_path / "publicado"
    _escrever_versao(destino, "anterior")
    anterior = _retrato(destino)
    replace_real = os.replace
    chamadas = 0

    def replace_com_falha(origem: str | Path, destino_troca: str | Path) -> None:
        nonlocal chamadas
        chamadas += 1
        if chamadas == 2:
            raise OSError("falha simulada na instalação")
        replace_real(origem, destino_troca)

    monkeypatch.setattr(modulo_publicacao.os, "replace", replace_com_falha)

    with pytest.raises(OSError, match="^falha simulada na instalação$"):
        publicar_diretorio(
            destino,
            lambda temporario: _escrever_versao(temporario, "nova"),
            _validar_versao_esperada("nova"),
        )

    assert chamadas == 3
    assert _retrato(destino) == anterior
    _assert_sem_residuos(tmp_path, destino)


def test_primeira_publicacao_sem_destino_anterior_funciona(tmp_path: Path) -> None:
    destino = tmp_path / "publicado"

    publicar_diretorio(
        destino,
        lambda temporario: _escrever_versao(temporario, "primeira"),
        _validar_versao_esperada("primeira"),
    )

    assert (destino / "versao.txt").read_text(encoding="utf-8") == "primeira"
    _assert_sem_residuos(tmp_path, destino)


def test_falha_na_primeira_publicacao_remove_temporario(tmp_path: Path) -> None:
    destino = tmp_path / "publicado"

    def validar_com_erro(_temporario: Path) -> None:
        raise ValueError("Gold inválida")

    with pytest.raises(ValueError, match="^Gold inválida$"):
        publicar_diretorio(
            destino,
            lambda temporario: _escrever_versao(temporario, "primeira"),
            validar_com_erro,
        )

    assert not destino.exists()
    _assert_sem_residuos(tmp_path, destino)
