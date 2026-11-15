"""Configuração central do pipeline, sem efeitos colaterais na importação."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Caminhos do projeto derivados de uma única raiz configurável."""

    root: Path

    @property
    def bronze(self) -> Path:
        return self.root / "data" / "bronze"

    @property
    def silver(self) -> Path:
        return self.root / "data" / "silver"

    @property
    def gold(self) -> Path:
        return self.root / "data" / "gold"

    @property
    def dashboard(self) -> Path:
        return self.root / "dashboard" / "atlas"


def project_paths(root: str | Path | None = None) -> ProjectPaths:
    """Resolve a raiz explicitamente, por variável de ambiente ou pelo checkout."""

    configured = root or os.getenv("PAINEL_PROJECT_ROOT")
    resolved = Path(configured).expanduser() if configured else Path(__file__).resolve().parents[2]
    return ProjectPaths(root=resolved.resolve())
