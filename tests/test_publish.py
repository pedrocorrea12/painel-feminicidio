import os
import re
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

    resultado = publicar_diretorio(
        destino,
        lambda temporario: _escrever_versao(temporario, "nova"),
        _validar_versao_esperada("nova"),
    )

    assert (destino / "versao.txt").read_text(encoding="utf-8") == "nova"
    assert not (destino / "obsoleto.txt").exists()
    assert resultado.destino == destino.resolve()
    assert resultado.backup_remanescente is None
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


def test_falha_ao_remover_backup_mantem_publicacao_e_informa_caminho(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destino = tmp_path / "publicado"
    _escrever_versao(destino, "anterior")
    remover_real = modulo_publicacao._remover

    def remover_com_falha(caminho: Path) -> None:
        if caminho.name.startswith(f".{destino.name}.backup-"):
            raise PermissionError("backup em uso")
        remover_real(caminho)

    monkeypatch.setattr(modulo_publicacao, "_remover", remover_com_falha)

    with pytest.warns(
        RuntimeWarning,
        match=r"^Publicação concluída, mas o backup não pôde ser removido:",
    ):
        resultado = publicar_diretorio(
            destino,
            lambda temporario: _escrever_versao(temporario, "nova"),
            _validar_versao_esperada("nova"),
        )

    assert (destino / "versao.txt").read_text(encoding="utf-8") == "nova"
    assert resultado.backup_remanescente is not None
    assert resultado.backup_remanescente.exists()
    assert _retrato(resultado.backup_remanescente)["versao.txt"] == b"anterior"
    assert list(tmp_path.glob(f".{destino.name}.tmp-*")) == []


def test_falha_na_troca_e_restauracao_informa_backup_e_encadeia_erro(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destino = tmp_path / "publicado"
    _escrever_versao(destino, "anterior")
    anterior = _retrato(destino)
    replace_real = os.replace
    erro_troca = OSError("troca interrompida")
    chamadas = 0

    def replace_com_dupla_falha(origem: str | Path, destino_troca: str | Path) -> None:
        nonlocal chamadas
        chamadas += 1
        if chamadas == 2:
            raise erro_troca
        if chamadas == 3:
            raise PermissionError("restauração bloqueada")
        replace_real(origem, destino_troca)

    monkeypatch.setattr(modulo_publicacao.os, "replace", replace_com_dupla_falha)

    with pytest.raises(RuntimeError) as capturado:
        publicar_diretorio(
            destino,
            lambda temporario: _escrever_versao(temporario, "nova"),
            _validar_versao_esperada("nova"),
        )

    backups = list(tmp_path.glob(f".{destino.name}.backup-*"))
    assert len(backups) == 1
    assert _retrato(backups[0]) == anterior
    assert "troca interrompida" in str(capturado.value)
    assert str(backups[0]) in str(capturado.value)
    assert capturado.value.__cause__ is erro_troca
    assert capturado.value.__notes__ == ["Erro de restauração: restauração bloqueada"]
    assert list(tmp_path.glob(f".{destino.name}.tmp-*")) == []


def test_backup_orfao_impede_publicacao_com_mensagem_estavel(tmp_path: Path) -> None:
    destino = tmp_path / "publicado"
    _escrever_versao(destino, "anterior")
    anterior = _retrato(destino)
    orfao = tmp_path / f".{destino.name}.backup-interrompido"
    _escrever_versao(orfao, "backup")
    gerou = False

    def gerar(_temporario: Path) -> None:
        nonlocal gerou
        gerou = True

    with pytest.raises(
        RuntimeError,
        match=rf"^Backup órfão impede publicação: {re.escape(str(orfao))}$",
    ):
        publicar_diretorio(destino, gerar, lambda _temporario: None)

    assert not gerou
    assert _retrato(destino) == anterior
    assert orfao.exists()
    assert list(tmp_path.glob(f".{destino.name}.tmp-*")) == []


# --- publicação conjunta (T20) ---------------------------------------------


def _conjunto(tmp_path: Path) -> tuple[Path, Path]:
    dados = tmp_path / "data"
    downloads = tmp_path / "downloads"
    _escrever_versao(dados, "anterior")
    _escrever_versao(downloads, "anterior")
    return dados, downloads


def _gerar_conjunto(versao: str):
    def gerar(temporarios) -> None:
        for temporario in temporarios:
            temporario.mkdir(parents=True, exist_ok=True)
            _escrever_versao(temporario, versao)

    return gerar


def _validar_conjunto(versao: str):
    def validar(temporarios) -> None:
        for temporario in temporarios:
            assert (temporario / "versao.txt").read_text(encoding="utf-8") == versao

    return validar


def _assert_conjunto_sem_residuos(tmp_path: Path) -> None:
    residuos = [
        item.name
        for item in tmp_path.iterdir()
        if item.name.startswith(".") and (".tmp-" in item.name or ".backup-" in item.name)
    ]
    assert residuos == []


def _replace_que_falha_na_segunda_instalacao(monkeypatch, bloquear_restauracao=False):
    replace_original = os.replace
    instalacoes = 0

    def replace_com_falha(origem, destino):
        nonlocal instalacoes
        nome = Path(origem).name
        if ".tmp-" in nome:
            instalacoes += 1
            if instalacoes == 2:
                raise OSError("troca do segundo destino falhou")
        if bloquear_restauracao and ".backup-" in nome:
            raise OSError("restauração bloqueada")
        return replace_original(origem, destino)

    monkeypatch.setattr(modulo_publicacao.os, "replace", replace_com_falha)


def test_conjunto_valido_substitui_todos_os_destinos(tmp_path: Path) -> None:
    dados, downloads = _conjunto(tmp_path)

    resultados = modulo_publicacao.publicar_conjunto(
        [dados, downloads], _gerar_conjunto("novo"), _validar_conjunto("novo")
    )

    assert [r.destino for r in resultados] == [dados.resolve(), downloads.resolve()]
    assert all(r.backup_remanescente is None for r in resultados)
    assert (dados / "versao.txt").read_text(encoding="utf-8") == "novo"
    assert (downloads / "versao.txt").read_text(encoding="utf-8") == "novo"
    _assert_conjunto_sem_residuos(tmp_path)


def test_conjunto_cria_destinos_que_ainda_nao_existem(tmp_path: Path) -> None:
    dados = tmp_path / "data"
    downloads = tmp_path / "downloads"

    modulo_publicacao.publicar_conjunto(
        [dados, downloads], _gerar_conjunto("novo"), _validar_conjunto("novo")
    )

    assert (dados / "versao.txt").is_file()
    assert (downloads / "versao.txt").is_file()
    _assert_conjunto_sem_residuos(tmp_path)


def test_falha_na_geracao_preserva_todos_os_destinos(tmp_path: Path) -> None:
    dados, downloads = _conjunto(tmp_path)
    antes = (_retrato(dados), _retrato(downloads))

    def gerar(temporarios) -> None:
        _escrever_versao(temporarios[0], "novo")
        raise RuntimeError("geração interrompida")

    with pytest.raises(RuntimeError, match="^geração interrompida$"):
        modulo_publicacao.publicar_conjunto(
            [dados, downloads], gerar, lambda _temporarios: None
        )

    assert (_retrato(dados), _retrato(downloads)) == antes
    _assert_conjunto_sem_residuos(tmp_path)


def test_falha_na_validacao_preserva_todos_os_destinos(tmp_path: Path) -> None:
    dados, downloads = _conjunto(tmp_path)
    antes = (_retrato(dados), _retrato(downloads))

    def validar(_temporarios) -> None:
        raise ValueError("downloads inválidos")

    with pytest.raises(ValueError, match="^downloads inválidos$"):
        modulo_publicacao.publicar_conjunto(
            [dados, downloads], _gerar_conjunto("novo"), validar
        )

    assert (_retrato(dados), _retrato(downloads)) == antes
    _assert_conjunto_sem_residuos(tmp_path)


def test_falha_na_segunda_troca_desfaz_a_primeira(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dados, downloads = _conjunto(tmp_path)
    antes = (_retrato(dados), _retrato(downloads))
    _replace_que_falha_na_segunda_instalacao(monkeypatch)

    with pytest.raises(OSError, match="^troca do segundo destino falhou$"):
        modulo_publicacao.publicar_conjunto(
            [dados, downloads], _gerar_conjunto("novo"), _validar_conjunto("novo")
        )

    assert (_retrato(dados), _retrato(downloads)) == antes
    _assert_conjunto_sem_residuos(tmp_path)


def test_falha_na_segunda_troca_sem_destinos_anteriores_nao_deixa_resto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dados = tmp_path / "data"
    downloads = tmp_path / "downloads"
    _replace_que_falha_na_segunda_instalacao(monkeypatch)

    with pytest.raises(OSError, match="^troca do segundo destino falhou$"):
        modulo_publicacao.publicar_conjunto(
            [dados, downloads], _gerar_conjunto("novo"), _validar_conjunto("novo")
        )

    assert not dados.exists()
    assert not downloads.exists()
    _assert_conjunto_sem_residuos(tmp_path)


def test_falha_na_restauracao_preserva_backups_e_informa_caminhos(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dados, downloads = _conjunto(tmp_path)
    _replace_que_falha_na_segunda_instalacao(monkeypatch, bloquear_restauracao=True)

    with pytest.raises(RuntimeError) as capturado:
        modulo_publicacao.publicar_conjunto(
            [dados, downloads], _gerar_conjunto("novo"), _validar_conjunto("novo")
        )

    mensagem = str(capturado.value)
    assert mensagem.startswith("Falha na troca conjunta dos destinos publicados: ")
    assert "backups preservados em: " in mensagem
    backups = sorted(tmp_path.glob(".*.backup-*"))
    assert len(backups) == 2
    assert all(str(backup) in mensagem for backup in backups)


def test_conjunto_com_backup_orfao_nao_gera_nada(tmp_path: Path) -> None:
    dados, downloads = _conjunto(tmp_path)
    orfao = tmp_path / f".{downloads.name}.backup-interrompido"
    _escrever_versao(orfao, "backup")
    gerou = False

    def gerar(_temporarios) -> None:
        nonlocal gerou
        gerou = True

    with pytest.raises(
        RuntimeError,
        match=rf"^Backup órfão impede publicação: {re.escape(str(orfao))}$",
    ):
        modulo_publicacao.publicar_conjunto(
            [dados, downloads], gerar, lambda _temporarios: None
        )

    assert not gerou
    assert list(tmp_path.glob(".*.tmp-*")) == []


def test_conjunto_rejeita_destinos_duplicados_e_lista_vazia(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="^Destinos duplicados na publicação conjunta$"):
        modulo_publicacao.publicar_conjunto(
            [tmp_path / "a", tmp_path / "a"],
            lambda _t: None,
            lambda _t: None,
        )
    with pytest.raises(
        ValueError, match="^Nenhum destino informado para a publicação conjunta$"
    ):
        modulo_publicacao.publicar_conjunto([], lambda _t: None, lambda _t: None)
