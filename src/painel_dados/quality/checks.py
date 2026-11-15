"""Checagens pequenas e determinísticas usadas pelos pipelines e pelos testes."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def assert_required_columns(frame: pd.DataFrame, required: Iterable[str]) -> None:
    """Falha com mensagem estável quando o contrato de colunas muda."""

    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")


def assert_unique(frame: pd.DataFrame, keys: Iterable[str]) -> None:
    """Garante que uma chave declarada não contenha duplicatas."""

    key_list = list(keys)
    assert_required_columns(frame, key_list)
    duplicated = frame.duplicated(key_list, keep=False)
    if duplicated.any():
        sample = frame.loc[duplicated, key_list].head(5).to_dict(orient="records")
        raise ValueError(f"Chave duplicada em {key_list}: amostra={sample}")
