"""Contrato dos arquivos de dados do site do atlas (``dashboard/atlas/data``).

Deriva de ``pipeline/build_atlas_site_data.py``. Valida um diretório inteiro
antes da publicação; cada falha levanta ``ValueError`` com mensagem estável.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path

ARQUIVOS_OBRIGATORIOS = (
    "manifesto.json",
    "nacional.json",
    "idade.json",
    "mensal.json",
    "desigualdades.json",
    "malha_sc.json",
)
CHAVES_MANIFESTO = (
    "atualizado_em",
    "periodo_consolidado",
    "territorios",
    "municipios",
    "indicadores",
    "downloads",
    "arquivos",
)
ARQUIVOS_DE_LINHAS = ("nacional.json", "idade.json", "mensal.json")
MUNICIPIOS_SC = 295
TABELAS_DESIGUALDADES = (
    "sim_raca_municipios",
    "sim_raca_uf_ano",
    "sinan_raca_municipios",
    "trabalho_ano",
    "trabalho_municipios",
    "salario_raca_municipios",
)


def _ler_json(caminho: Path, nome: str):
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError) as erro:
        raise ValueError(f"{nome}: JSON ilegível ({erro})") from erro


def _validar_tabela(conteudo: dict, nome: str) -> None:
    if not isinstance(conteudo, dict) or set(("colunas", "linhas")) - set(conteudo):
        raise ValueError(f"{nome}: esperado objeto com 'colunas' e 'linhas'")
    colunas, linhas = conteudo["colunas"], conteudo["linhas"]
    if not colunas or not linhas:
        raise ValueError(f"{nome}: tabela vazia")
    largura = len(colunas)
    for posicao, linha in enumerate(linhas):
        if len(linha) != largura:
            raise ValueError(
                f"{nome}: linha {posicao} com {len(linha)} valores, esperados {largura}"
            )


def validar_diretorio_site(
    diretorio: str | Path, diretorio_downloads: str | Path | None = None
) -> None:
    """Confere arquivos obrigatórios, manifesto e consistência entre eles.

    Sem ``diretorio_downloads``, os downloads do manifesto só precisam existir em
    ``downloads/``, ao lado do diretório. Com ele, o diretório informado (a
    versão ainda não publicada) é validado a fundo: ZIP íntegro, CSV esperado,
    linhas e bytes iguais aos do manifesto, e nenhum arquivo fora dele.
    """
    try:
        _validar(Path(diretorio), diretorio_downloads)
    except (KeyError, TypeError, AttributeError, IndexError) as erro:
        raise ValueError(
            f"Estrutura inválida: {type(erro).__name__}: {erro}"
        ) from erro


def _validar(raiz: Path, diretorio_downloads: str | Path | None = None) -> None:
    for nome in ARQUIVOS_OBRIGATORIOS:
        if not (raiz / nome).is_file():
            raise ValueError(f"Arquivo obrigatório ausente: {nome}")

    manifesto = _ler_json(raiz / "manifesto.json", "manifesto.json")
    ausentes = [c for c in CHAVES_MANIFESTO if c not in manifesto]
    if ausentes:
        raise ValueError(f"manifesto.json: chaves ausentes: {', '.join(ausentes)}")

    for nome in ARQUIVOS_DE_LINHAS:
        _validar_tabela(_ler_json(raiz / nome, nome), nome)
    desigualdades = _ler_json(raiz / "desigualdades.json", "desigualdades.json")
    for tabela in TABELAS_DESIGUALDADES:
        if tabela not in desigualdades:
            raise ValueError(f"desigualdades.json: tabela ausente: {tabela}")
        _validar_tabela(desigualdades[tabela], f"desigualdades.json/{tabela}")
    _ler_json(raiz / "malha_sc.json", "malha_sc.json")

    indicadores = manifesto["indicadores"]
    ids = [i["id"] for i in indicadores]
    if not ids:
        raise ValueError("manifesto.json: sem indicadores")
    if len(ids) != len(set(ids)):
        raise ValueError("manifesto.json: indicadores duplicados")

    municipios = manifesto["municipios"]
    ids_municipios = {m["id"] for m in municipios}
    if len(ids_municipios) != MUNICIPIOS_SC or manifesto["territorios"].get(
        "municipios_sc"
    ) != MUNICIPIOS_SC:
        raise ValueError(f"Esperados {MUNICIPIOS_SC} municípios de Santa Catarina")
    arquivos_municipio = {p.stem for p in (raiz / "municipio").glob("*.json")}
    if arquivos_municipio != ids_municipios:
        raise ValueError("Arquivos de município divergem do manifesto")
    for id_municipio in sorted(ids_municipios):
        nome = f"municipio/{id_municipio}.json"
        _validar_tabela(_ler_json(raiz / nome, nome), nome)

    for indicador in indicadores:
        caminho_mapa = indicador.get("arquivo_mapa")
        if caminho_mapa is None:
            continue
        mapa = raiz / caminho_mapa.removeprefix("data/")
        if not mapa.is_file():
            raise ValueError(f"Arquivo de mapa ausente: {caminho_mapa}")
        _validar_tabela(_ler_json(mapa, caminho_mapa), caminho_mapa)

    nacional = _ler_json(raiz / "nacional.json", "nacional.json")
    if "indicador" not in nacional["colunas"]:
        raise ValueError("nacional.json: coluna 'indicador' ausente")
    posicao = nacional["colunas"].index("indicador")
    desconhecidos = {linha[posicao] for linha in nacional["linhas"]} - set(ids)
    if desconhecidos:
        raise ValueError(
            f"nacional.json: indicador fora do manifesto: {sorted(desconhecidos)[0]}"
        )

    if diretorio_downloads is not None:
        _validar_downloads(Path(diretorio_downloads), manifesto["downloads"])
        return
    for download in manifesto["downloads"]:
        if not (raiz.parent / download["arquivo"]).is_file():
            raise ValueError(f"Download ausente: {download['arquivo']}")


def _validar_downloads(diretorio: Path, downloads: list[dict]) -> None:
    esperados = set()
    for download in downloads:
        arquivo = download["arquivo"]
        partes = Path(arquivo).parts
        if len(partes) != 2 or partes[0] != "downloads":
            raise ValueError(f"Download com caminho inválido: {arquivo}")
        nome = partes[1]
        esperados.add(nome)
        caminho = diretorio / nome
        if not caminho.is_file():
            raise ValueError(f"Download ausente: {arquivo}")
        _validar_zip(caminho, arquivo, download)
    fora = sorted(item.name for item in diretorio.iterdir() if item.name not in esperados)
    if fora:
        raise ValueError(f"Download fora do manifesto: downloads/{fora[0]}")


def _validar_zip(caminho: Path, arquivo: str, download: dict) -> None:
    tamanho = caminho.stat().st_size
    if tamanho != download["bytes"]:
        raise ValueError(
            f"Download com tamanho divergente: {arquivo} "
            f"(manifesto {download['bytes']}, arquivo {tamanho})"
        )
    csv_esperado = f"{caminho.stem}.csv"
    try:
        with zipfile.ZipFile(caminho) as pacote:
            if pacote.testzip() is not None:
                raise ValueError(f"Download corrompido: {arquivo}")
            if pacote.namelist() != [csv_esperado]:
                raise ValueError(f"Download sem o CSV esperado: {arquivo} ({csv_esperado})")
            with pacote.open(csv_esperado) as bruto:
                texto = io.TextIOWrapper(bruto, encoding="utf-8-sig", newline="")
                linhas = sum(1 for _ in csv.reader(texto)) - 1
    except (zipfile.BadZipFile, UnicodeDecodeError, csv.Error) as erro:
        raise ValueError(f"Download corrompido: {arquivo}") from erro
    if linhas != download["linhas"]:
        raise ValueError(
            f"Download com contagem divergente: {arquivo} "
            f"(manifesto {download['linhas']}, arquivo {linhas})"
        )
