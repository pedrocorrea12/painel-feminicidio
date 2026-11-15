from pathlib import Path
from shutil import copytree

import pandas as pd
import pytest

from pipeline.validate_project import validar_reconciliacao_municipal

FIXTURE = Path(__file__).parent / "fixtures" / "validate_project"


def test_reconciliacao_municipal_aceita_fixture_sintetica() -> None:
    validar_reconciliacao_municipal(FIXTURE)


def test_reconciliacao_municipal_rejeita_fixture_adulterada(
    tmp_path: Path,
) -> None:
    raiz = tmp_path / "projeto"
    copytree(FIXTURE, raiz)
    caminho = raiz / "data" / "gold" / "atlas" / "sinan_violencia_territorio_ano.csv"
    tabela = pd.read_csv(caminho)
    tabela.loc[tabela.id_territorio.eq("SC"), "notificacoes"] = 12
    tabela.to_csv(caminho, index=False)

    mensagem = "sinan_violencia_territorio_ano: municípios não fecham com SC:"
    with pytest.raises(AssertionError, match=f"^{mensagem}"):
        validar_reconciliacao_municipal(raiz)
