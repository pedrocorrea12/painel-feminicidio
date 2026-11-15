import json
from pathlib import Path
from shutil import copytree

import pandas as pd
import pytest

from pipeline.validate_project import validar_dados_site, validar_reconciliacao_municipal

FIXTURE = Path(__file__).parent / "fixtures" / "validate_project"


def _escrever_json(caminho: Path, conteudo: object) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(conteudo, ensure_ascii=False),
        encoding="utf-8",
    )


def _criar_site_sintetico(raiz: Path) -> None:
    dados = raiz / "dashboard" / "atlas" / "data"
    municipios = [
        {"id": f"M-{indice:03d}", "nome": f"Município sintético {indice:03d}"}
        for indice in range(295)
    ]
    _escrever_json(
        dados / "manifesto.json",
        {
            "territorios": {"brasil": 1, "ufs": 27, "municipios_sc": 295},
            "municipios": municipios,
            "indicadores": [
                {
                    "id": "sinan_notificacoes_interpessoais",
                    "municipal": True,
                    "arquivo_mapa": "mapa/sinan_notificacoes_interpessoais.json",
                }
            ],
        },
    )
    for municipio in municipios:
        _escrever_json(dados / "municipio" / f"{municipio['id']}.json", {})
    _escrever_json(
        dados / "malha_sc.json",
        {"features": [{"id": municipio["id"]} for municipio in municipios]},
    )
    _escrever_json(
        dados / "mapa" / "sinan_notificacoes_interpessoais.json",
        {
            "colunas": ["sexo", "ano", "valor"],
            "linhas": [["feminino", 2024, 9647]],
        },
    )
    gold = raiz / "data" / "gold" / "atlas"
    gold.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "ano": 2024,
                "nivel_territorial": "municipio",
                "id_territorio": "M-000",
                "indicador": "notificacoes_interpessoais",
                "sexo": "feminino",
                "notificacoes": 9647,
            }
        ]
    ).to_csv(gold / "sinan_violencia_territorio_ano.csv", index=False)


def test_reconciliacao_municipal_aceita_fixture_sintetica() -> None:
    validar_reconciliacao_municipal(FIXTURE)


@pytest.mark.parametrize(
    ("arquivo", "coluna"),
    [
        ("sim_mortalidade_territorio_ano", "obitos"),
        ("sinan_violencia_territorio_ano", "notificacoes"),
        ("sinesp_prioridade_territorio_ano", "valor_absoluto"),
    ],
)
def test_reconciliacao_municipal_rejeita_cada_fonte_adulterada(
    tmp_path: Path,
    arquivo: str,
    coluna: str,
) -> None:
    raiz = tmp_path / "projeto"
    copytree(FIXTURE, raiz)
    caminho = raiz / "data" / "gold" / "atlas" / f"{arquivo}.csv"
    tabela = pd.read_csv(caminho)
    tabela.loc[tabela.id_territorio.eq("SC"), coluna] += 1
    tabela.to_csv(caminho, index=False)

    mensagem = f"{arquivo}: municípios não fecham com SC:"
    with pytest.raises(AssertionError, match=f"^{mensagem}"):
        validar_reconciliacao_municipal(raiz)


def test_estrutura_dados_site_aceita_fixture_gerada(tmp_path: Path) -> None:
    raiz = tmp_path / "projeto"
    _criar_site_sintetico(raiz)

    validar_dados_site(raiz)


def test_estrutura_dados_site_rejeita_malha_adulterada(tmp_path: Path) -> None:
    raiz = tmp_path / "projeto"
    _criar_site_sintetico(raiz)
    caminho = raiz / "dashboard" / "atlas" / "data" / "malha_sc.json"
    malha = json.loads(caminho.read_text(encoding="utf-8"))
    malha["features"].pop()
    _escrever_json(caminho, malha)

    with pytest.raises(AssertionError, match="^malha não casa com municípios$"):
        validar_dados_site(raiz)
