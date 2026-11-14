"""Contrato dos arquivos de dados do site do atlas (``dashboard/atlas/data``).

Deriva de ``pipeline/build_atlas_site_data.py``. Valida um diretório inteiro
antes da publicação; cada falha levanta ``ValueError`` com mensagem estável.
"""

from __future__ import annotations

import json
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


def validar_diretorio_site(diretorio: str | Path) -> None:
    """Confere arquivos obrigatórios, manifesto e consistência entre eles."""
    raiz = Path(diretorio)
    for nome in ARQUIVOS_OBRIGATORIOS:
        if not (raiz / nome).is_file():
            raise ValueError(f"Arquivo obrigatório ausente: {nome}")

    manifesto = _ler_json(raiz / "manifesto.json", "manifesto.json")
    ausentes = [c for c in CHAVES_MANIFESTO if c not in manifesto]
    if ausentes:
        raise ValueError(f"manifesto.json: chaves ausentes: {', '.join(ausentes)}")

    for nome in ARQUIVOS_DE_LINHAS:
        _validar_tabela(_ler_json(raiz / nome, nome), nome)
    _ler_json(raiz / "desigualdades.json", "desigualdades.json")
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
    posicao = nacional["colunas"].index("indicador")
    desconhecidos = {linha[posicao] for linha in nacional["linhas"]} - set(ids)
    if desconhecidos:
        raise ValueError(
            f"nacional.json: indicador fora do manifesto: {sorted(desconhecidos)[0]}"
        )

    for download in manifesto["downloads"]:
        if not (raiz.parent / download["arquivo"]).is_file():
            raise ValueError(f"Download ausente: {download['arquivo']}")
