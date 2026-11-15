"""CLI de transição para diagnóstico e futuras execuções do pipeline."""

from __future__ import annotations

import argparse
import json

from .config import project_paths


def diagnose() -> int:
    """Verifica somente a estrutura; não baixa nem transforma dados."""

    paths = project_paths()
    required = {
        "pipeline": paths.root / "pipeline",
        "bronze": paths.bronze,
        "silver": paths.silver,
        "gold": paths.gold,
        "dashboard": paths.dashboard,
        "pages_workflow": paths.root / ".github" / "workflows" / "pages.yml",
    }
    status = {name: path.exists() for name, path in required.items()}
    print(json.dumps({"root": str(paths.root), "checks": status}, indent=2, ensure_ascii=False))
    return 0 if all(status.values()) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="painel-dados")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("diagnose", help="verifica a estrutura sem processar dados")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "diagnose":
        return diagnose()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
