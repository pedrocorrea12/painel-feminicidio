"""Testes dos ZIPs de download do atlas e da publicação conjunta com os dados."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

import pytest

from painel_dados.contracts import atlas_site
from painel_dados.contracts.atlas_site import validar_diretorio_site
from painel_dados.publish import publicar_conjunto

LINHAS_SIM = [["indicador", "ano"], ["sim_a", "2023"], ["sim_a", "2024"]]


def _csv_bytes(linhas: list[list[str]]) -> bytes:
    saida = io.StringIO(newline="")
    csv.writer(saida).writerows(linhas)
    return saida.getvalue().encode("utf-8-sig")


def _zip(caminho: Path, nome_csv: str, linhas: list[list[str]]) -> dict:
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as pacote:
        pacote.writestr(nome_csv, _csv_bytes(linhas))
    return {
        "fonte": "SIM",
        "arquivo": f"downloads/{caminho.name}",
        "linhas": len(linhas) - 1,
        "bytes": caminho.stat().st_size,
    }


def _tabela(colunas: list[str], linhas: list[list]) -> dict:
    return {"colunas": colunas, "linhas": linhas}


def _escrever(caminho: Path, conteudo) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(conteudo), encoding="utf-8")


def _site(destino: Path, downloads: list[dict]) -> None:
    ids = [f"4200{i:03d}" for i in range(atlas_site.MUNICIPIOS_SC)]
    unica = _tabela(["indicador", "ano"], [["sim_a", 2024]])
    _escrever(
        destino / "manifesto.json",
        {
            "atualizado_em": "2026-01-01",
            "periodo_consolidado": [2015, 2024],
            "territorios": {"brasil": 1, "ufs": 27, "municipios_sc": len(ids)},
            "municipios": [{"id": i, "nome": f"M{i}"} for i in ids],
            "indicadores": [{"id": "sim_a", "arquivo_mapa": "data/mapa/sim_a.json"}],
            "downloads": downloads,
            "arquivos": {},
        },
    )
    for nome in ("nacional.json", "idade.json", "mensal.json"):
        _escrever(destino / nome, unica)
    _escrever(
        destino / "desigualdades.json",
        {nome: unica for nome in atlas_site.TABELAS_DESIGUALDADES},
    )
    _escrever(destino / "malha_sc.json", {"type": "FeatureCollection"})
    _escrever(destino / "mapa" / "sim_a.json", unica)
    for i in ids:
        _escrever(destino / "municipio" / f"{i}.json", unica)


def _ler_manifesto(dados: Path) -> dict:
    return json.loads((dados / "manifesto.json").read_text(encoding="utf-8"))


@pytest.fixture
def conjunto(tmp_path: Path) -> tuple[Path, Path]:
    dados = tmp_path / "atlas" / "data"
    downloads = tmp_path / "atlas" / "downloads"
    downloads.mkdir(parents=True)
    entrada = _zip(downloads / "atlas_sim.zip", "atlas_sim.csv", LINHAS_SIM)
    _site(dados, [entrada])
    return dados, downloads


def test_downloads_validos_passam(conjunto: tuple[Path, Path]) -> None:
    dados, downloads = conjunto
    validar_diretorio_site(dados, diretorio_downloads=downloads)


def test_download_ausente_no_diretorio_informado(conjunto: tuple[Path, Path]) -> None:
    dados, downloads = conjunto
    (downloads / "atlas_sim.zip").unlink()
    with pytest.raises(ValueError, match="^Download ausente: downloads/atlas_sim.zip$"):
        validar_diretorio_site(dados, diretorio_downloads=downloads)


def test_zip_corrompido_e_rejeitado(conjunto: tuple[Path, Path]) -> None:
    dados, downloads = conjunto
    manifesto = _ler_manifesto(dados)
    lixo = b"conteudo que nao e um zip"
    (downloads / "atlas_sim.zip").write_bytes(lixo)
    manifesto["downloads"][0]["bytes"] = len(lixo)
    _escrever(dados / "manifesto.json", manifesto)
    with pytest.raises(ValueError, match="^Download corrompido: downloads/atlas_sim.zip$"):
        validar_diretorio_site(dados, diretorio_downloads=downloads)


def test_zip_sem_o_csv_esperado_e_rejeitado(tmp_path: Path) -> None:
    dados = tmp_path / "atlas" / "data"
    downloads = tmp_path / "atlas" / "downloads"
    downloads.mkdir(parents=True)
    entrada = _zip(downloads / "atlas_sim.zip", "outro.csv", LINHAS_SIM)
    _site(dados, [entrada])
    with pytest.raises(
        ValueError,
        match=r"^Download sem o CSV esperado: downloads/atlas_sim.zip \(atlas_sim.csv\)$",
    ):
        validar_diretorio_site(dados, diretorio_downloads=downloads)


def test_contagem_de_linhas_divergente_e_rejeitada(conjunto: tuple[Path, Path]) -> None:
    dados, downloads = conjunto
    manifesto = _ler_manifesto(dados)
    manifesto["downloads"][0]["linhas"] = 99
    _escrever(dados / "manifesto.json", manifesto)
    with pytest.raises(
        ValueError,
        match=r"^Download com contagem divergente: downloads/atlas_sim.zip "
        r"\(manifesto 99, arquivo 2\)$",
    ):
        validar_diretorio_site(dados, diretorio_downloads=downloads)


def test_tamanho_divergente_e_rejeitado(conjunto: tuple[Path, Path]) -> None:
    dados, downloads = conjunto
    manifesto = _ler_manifesto(dados)
    manifesto["downloads"][0]["bytes"] += 1
    _escrever(dados / "manifesto.json", manifesto)
    with pytest.raises(ValueError, match="^Download com tamanho divergente: "):
        validar_diretorio_site(dados, diretorio_downloads=downloads)


def test_arquivo_fora_do_manifesto_e_rejeitado(conjunto: tuple[Path, Path]) -> None:
    dados, downloads = conjunto
    (downloads / "sobra.zip").write_bytes(b"x")
    with pytest.raises(ValueError, match="^Download fora do manifesto: downloads/sobra.zip$"):
        validar_diretorio_site(dados, diretorio_downloads=downloads)


@pytest.mark.parametrize("caminho", ["../fora.zip", "downloads/sub/a.zip", "a.zip"])
def test_caminho_de_download_invalido_e_rejeitado(
    conjunto: tuple[Path, Path], caminho: str
) -> None:
    dados, downloads = conjunto
    manifesto = _ler_manifesto(dados)
    manifesto["downloads"][0]["arquivo"] = caminho
    _escrever(dados / "manifesto.json", manifesto)
    with pytest.raises(ValueError, match="^Download com caminho inválido: "):
        validar_diretorio_site(dados, diretorio_downloads=downloads)


def _validar_site(temporarios) -> None:
    novo_dados, novo_downloads = temporarios
    validar_diretorio_site(novo_dados, diretorio_downloads=novo_downloads)


def test_publicacao_conjunta_rejeita_zip_corrompido_e_mantem_a_versao_anterior(
    conjunto: tuple[Path, Path],
) -> None:
    dados, downloads = conjunto
    zip_anterior = (downloads / "atlas_sim.zip").read_bytes()
    manifesto_anterior = (dados / "manifesto.json").read_bytes()

    def gerar(temporarios) -> None:
        novo_dados, novo_downloads = temporarios
        lixo = b"corrompido"
        (novo_downloads / "atlas_sim.zip").write_bytes(lixo)
        entrada = {**_ler_manifesto(dados)["downloads"][0], "bytes": len(lixo)}
        _site(novo_dados, [entrada])

    with pytest.raises(ValueError, match="^Download corrompido: downloads/atlas_sim.zip$"):
        publicar_conjunto([dados, downloads], gerar, _validar_site)

    assert (downloads / "atlas_sim.zip").read_bytes() == zip_anterior
    assert (dados / "manifesto.json").read_bytes() == manifesto_anterior
    assert sorted(p.name for p in dados.parent.iterdir()) == ["data", "downloads"]


def test_publicacao_conjunta_troca_dados_e_downloads_juntos(
    conjunto: tuple[Path, Path],
) -> None:
    dados, downloads = conjunto
    novas_linhas = [*LINHAS_SIM, ["sim_a", "2025"]]

    def gerar(temporarios) -> None:
        novo_dados, novo_downloads = temporarios
        entrada = _zip(novo_downloads / "atlas_sim.zip", "atlas_sim.csv", novas_linhas)
        _site(novo_dados, [entrada])

    publicar_conjunto([dados, downloads], gerar, _validar_site)

    assert _ler_manifesto(dados)["downloads"][0]["linhas"] == 3
    with zipfile.ZipFile(downloads / "atlas_sim.zip") as pacote:
        assert pacote.namelist() == ["atlas_sim.csv"]
    validar_diretorio_site(dados)
    assert sorted(p.name for p in dados.parent.iterdir()) == ["data", "downloads"]


def test_csv_so_com_cabecalho_e_rejeitado(tmp_path: Path) -> None:
    dados = tmp_path / "atlas" / "data"
    downloads = tmp_path / "atlas" / "downloads"
    downloads.mkdir(parents=True)
    entrada = _zip(downloads / "atlas_sim.zip", "atlas_sim.csv", [["indicador", "ano"]])
    _site(dados, [entrada])
    with pytest.raises(ValueError, match="^Download sem registros: downloads/atlas_sim.zip$"):
        validar_diretorio_site(dados, diretorio_downloads=downloads)
