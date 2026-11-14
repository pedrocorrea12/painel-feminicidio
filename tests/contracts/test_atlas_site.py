"""Testes do contrato dos dados do site do atlas, com diretório sintético."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from painel_dados.contracts import atlas_site
from painel_dados.contracts.atlas_site import validar_diretorio_site
from painel_dados.publish import publicar_diretorio


def _escrever(caminho: Path, conteudo) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(conteudo), encoding="utf-8")


def _tabela(colunas: list[str], linhas: list[list]) -> dict:
    return {"colunas": colunas, "linhas": linhas}


def _gerar_site_valido(destino: Path) -> None:
    ids = [f"4200{i:03d}" for i in range(atlas_site.MUNICIPIOS_SC)]
    (destino.parent / "downloads").mkdir(parents=True, exist_ok=True)
    (destino.parent / "downloads" / "atlas_sim.zip").write_bytes(b"zip")
    _escrever(
        destino / "manifesto.json",
        {
            "atualizado_em": "2026-01-01",
            "periodo_consolidado": [2015, 2024],
            "territorios": {"brasil": 1, "ufs": 27, "municipios_sc": len(ids)},
            "municipios": [{"id": i, "nome": f"M{i}"} for i in ids],
            "indicadores": [
                {"id": "sim_a", "arquivo_mapa": "data/mapa/sim_a.json"},
                {"id": "sinesp_b"},
            ],
            "downloads": [{"fonte": "SIM", "arquivo": "downloads/atlas_sim.zip"}],
            "arquivos": {},
        },
    )
    unica = _tabela(["indicador", "ano"], [["sim_a", 2024]])
    _escrever(destino / "nacional.json", unica)
    _escrever(destino / "idade.json", unica)
    _escrever(destino / "mensal.json", unica)
    _escrever(destino / "desigualdades.json", {"x": 1})
    _escrever(destino / "malha_sc.json", {"type": "FeatureCollection"})
    _escrever(destino / "mapa" / "sim_a.json", unica)
    for i in ids:
        _escrever(destino / "municipio" / f"{i}.json", unica)


@pytest.fixture
def site(tmp_path: Path) -> Path:
    destino = tmp_path / "atlas" / "data"
    _gerar_site_valido(destino)
    return destino


def test_site_valido_passa(site: Path) -> None:
    validar_diretorio_site(site)


@pytest.mark.parametrize("nome", ["manifesto.json", "nacional.json", "malha_sc.json"])
def test_arquivo_obrigatorio_ausente(site: Path, nome: str) -> None:
    (site / nome).unlink()
    with pytest.raises(ValueError, match=f"Arquivo obrigatório ausente: {nome}"):
        validar_diretorio_site(site)


def test_json_ilegivel(site: Path) -> None:
    (site / "idade.json").write_text("{nao e json", encoding="utf-8")
    with pytest.raises(ValueError, match="idade.json: JSON ilegível"):
        validar_diretorio_site(site)


def test_manifesto_sem_chave(site: Path) -> None:
    manifesto = json.loads((site / "manifesto.json").read_text(encoding="utf-8"))
    del manifesto["indicadores"]
    _escrever(site / "manifesto.json", manifesto)
    with pytest.raises(ValueError, match="chaves ausentes: indicadores"):
        validar_diretorio_site(site)


def test_tabela_vazia(site: Path) -> None:
    _escrever(site / "mensal.json", _tabela(["indicador"], []))
    with pytest.raises(ValueError, match="mensal.json: tabela vazia"):
        validar_diretorio_site(site)


def test_linha_com_largura_errada(site: Path) -> None:
    _escrever(site / "nacional.json", _tabela(["indicador", "ano"], [["sim_a"]]))
    with pytest.raises(ValueError, match="nacional.json: linha 0 com 1 valores"):
        validar_diretorio_site(site)


def test_municipio_faltando(site: Path) -> None:
    next((site / "municipio").glob("*.json")).unlink()
    with pytest.raises(ValueError, match="Arquivos de município divergem"):
        validar_diretorio_site(site)


def test_mapa_ausente(site: Path) -> None:
    (site / "mapa" / "sim_a.json").unlink()
    with pytest.raises(ValueError, match="Arquivo de mapa ausente"):
        validar_diretorio_site(site)


def test_indicador_fora_do_manifesto(site: Path) -> None:
    _escrever(site / "nacional.json", _tabela(["indicador", "ano"], [["desconhecido", 2024]]))
    with pytest.raises(ValueError, match="indicador fora do manifesto: desconhecido"):
        validar_diretorio_site(site)


def test_download_ausente(site: Path) -> None:
    (site.parent / "downloads" / "atlas_sim.zip").unlink()
    with pytest.raises(ValueError, match="Download ausente"):
        validar_diretorio_site(site)


def test_publicacao_invalida_mantem_versao_anterior(tmp_path: Path) -> None:
    destino = tmp_path / "atlas" / "data"
    publicar_diretorio(destino, _gerar_site_valido, validar_diretorio_site)
    antes = (destino / "manifesto.json").read_text(encoding="utf-8")

    def gerar_quebrado(temporario: Path) -> None:
        _gerar_site_valido(temporario)
        (temporario / "nacional.json").unlink()

    with pytest.raises(ValueError, match="Arquivo obrigatório ausente: nacional.json"):
        publicar_diretorio(destino, gerar_quebrado, validar_diretorio_site)

    assert (destino / "manifesto.json").read_text(encoding="utf-8") == antes
    assert (destino / "nacional.json").is_file()
    assert [p.name for p in destino.parent.iterdir() if p.name.startswith(".")] == []
