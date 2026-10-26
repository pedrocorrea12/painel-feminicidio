"""Gera a camada Gold a partir das Silvers consolidadas de SINAN e população."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from build_silver import construir as construir_silver
from build_silver import construir_preliminar


ROOT = Path(__file__).resolve().parents[1]
SINAN = ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal.parquet"
SINESP = ROOT / "data" / "silver" / "sinesp_feminicidio.parquet"
GOLD = ROOT / "data" / "gold" / "painel.json"
SITE_DATA = ROOT / "dashboard" / "dist" / "data" / "painel.json"
RACA_DIR = ROOT / "data" / "gold" / "raca"
RAIS_DIR = ROOT / "data" / "gold" / "rais"

COLS_PERFIL = ["ano", "SG_UF", "VIOL_FISIC", "VIOL_PSICO", "VIOL_SEXU", "CS_RACA"]

RACA = {
    "1": "Branca", "2": "Preta", "3": "Amarela", "4": "Parda",
    "5": "Indígena", "9": "Ignorada", "": "Não informada",
}


def serie(grupo: pd.DataFrame) -> list[dict]:
    return grupo.to_dict(orient="records")


def registros_csv(caminho: Path) -> list[dict]:
    dados = pd.read_csv(caminho, dtype={"id_municipio": "string", "id_territorio": "string"})
    dados = dados.astype(object).where(pd.notna(dados), None)
    return dados.to_dict(orient="records")


def main() -> None:
    indicadores = construir_silver()
    if not SINAN.exists():
        raise FileNotFoundError(f"Parquet Silver não encontrado: {SINAN}")

    campos_serie = [
        "ano", "notificacoes", "parceiro", "residencia", "percentual_parceiro",
        "populacao_feminina", "taxa_notificacoes_100mil", "taxa_parceiro_100mil",
        "obitos_mulheres_agressao", "taxa_obitos_mulheres_agressao_100mil",
    ]
    selecoes = {
        "brasil": ("brasil", "BR"),
        "santa_catarina": ("uf", "SC"),
        "florianopolis": ("municipio", "4205407"),
    }
    territorios = {}
    for chave, (nivel, codigo) in selecoes.items():
        base = indicadores.loc[
            indicadores["nivel_territorial"].eq(nivel)
            & indicadores["id_territorio"].eq(codigo),
            campos_serie,
        ].sort_values("ano")
        if len(base) != 10:
            raise ValueError(f"Série incompleta para {chave}: {len(base)} anos")
        territorios[chave] = serie(base)

    sc24 = indicadores.loc[
        indicadores["ano"].eq(2024)
        & indicadores["nivel_territorial"].eq("uf")
        & indicadores["id_territorio"].eq("SC")
    ].iloc[0]
    floripa24 = indicadores.loc[
        indicadores["ano"].eq(2024)
        & indicadores["nivel_territorial"].eq("municipio")
        & indicadores["id_territorio"].eq("4205407")
    ].iloc[0]
    controle = {
        "sc_2024": int(sc24.notificacoes),
        "sc_parceiro_2024": int(sc24.parceiro),
        "florianopolis_parceiro_2024": int(floripa24.parceiro),
        "pop_feminina_sc_2024": int(sc24.populacao_feminina),
        "taxa_sc_2024": float(sc24.taxa_notificacoes_100mil),
        "sim_agressao_sc_2024": int(sc24.obitos_mulheres_agressao),
    }
    esperado = {
        "sc_2024": 9647,
        "sc_parceiro_2024": 2918,
        "florianopolis_parceiro_2024": 120,
        "pop_feminina_sc_2024": 4071859,
        "taxa_sc_2024": 236.92,
        "sim_agressao_sc_2024": 90,
    }
    if controle != esperado:
        raise ValueError(f"Falha nos números de controle: obtido={controle}, esperado={esperado}")

    municipios = indicadores.loc[
        indicadores["ano"].eq(2024)
        & indicadores["nivel_territorial"].eq("municipio")
        & indicadores["sigla_uf"].eq("SC")
    ].copy()
    municipios = municipios.rename(
        columns={"id_territorio": "id_municipio", "territorio": "municipio"}
    )[
        [
            "id_municipio", "municipio", "populacao_feminina", "notificacoes",
            "parceiro", "percentual_parceiro", "taxa_notificacoes_100mil",
            "taxa_parceiro_100mil", "dado_suficiente",
        ]
    ].sort_values(["parceiro", "notificacoes"], ascending=False)

    df = pd.read_parquet(SINAN, columns=COLS_PERFIL)
    df["SG_UF"] = df["SG_UF"].fillna("").astype(str).str.strip()
    sc = df.loc[df.SG_UF.eq("42") & df.ano.eq(2024)].copy()
    perfil_raca = (
        sc.assign(categoria=lambda x: x.CS_RACA.fillna("").astype(str).map(RACA).fillna("Não informada"))
        .groupby("categoria", as_index=False)
        .size()
        .rename(columns={"size": "notificacoes"})
        .sort_values("notificacoes", ascending=False)
    )

    tipos = []
    for coluna, rotulo in [
        ("VIOL_FISIC", "Física"),
        ("VIOL_PSICO", "Psicológica"),
        ("VIOL_SEXU", "Sexual"),
    ]:
        tipos.append({"tipo": rotulo, "notificacoes": int(sc[coluna].eq("1").sum())})

    brasil = indicadores.loc[indicadores["nivel_territorial"].eq("brasil")]
    preliminar = construir_preliminar()
    sinan_2025 = {}
    for chave, (nivel, codigo) in {
        "brasil": ("brasil", "BR"),
        "santa_catarina": ("uf", "42"),
        "florianopolis": ("municipio", "4205407"),
    }.items():
        recorte = preliminar.loc[
            preliminar.nivel_territorial.eq(nivel)
            & preliminar.id_territorio.eq(codigo)
        ]
        sinan_2025[chave] = (
            recorte[["ano", "notificacoes", "parceiro", "situacao_dado"]]
            .to_dict(orient="records")
        )

    sinesp_payload = None
    if SINESP.exists():
        sinesp = pd.read_parquet(SINESP)
        sinesp_ano_uf = (
            sinesp.groupby(["ano", "sigla_uf", "situacao_dado"], as_index=False)
            .agg(vitimas_feminicidio=("vitimas_feminicidio", "sum"))
        )
        sinesp_brasil = (
            sinesp_ano_uf.groupby(["ano", "situacao_dado"], as_index=False)
            .agg(vitimas_feminicidio=("vitimas_feminicidio", "sum"))
        )
        sinesp_sc = sinesp_ano_uf.loc[sinesp_ano_uf.sigla_uf.eq("SC")].drop(columns="sigla_uf")
        sinesp_floripa = (
            sinesp.loc[sinesp.municipio.fillna("").str.upper().isin(["FLORIANÓPOLIS", "FLORIANOPOLIS"])]
            .groupby(["ano", "situacao_dado"], as_index=False)
            .agg(vitimas_feminicidio=("vitimas_feminicidio", "sum"))
        )
        sinesp_payload = {
            "brasil": serie(sinesp_brasil),
            "santa_catarina": serie(sinesp_sc),
            "florianopolis": serie(sinesp_floripa),
        }
    else:
        print(f"AVISO: Silver Sinesp ausente ({SINESP}); seção sinesp_feminicidio omitida.")

    payload = {
        "meta": {
            "titulo": "Violência contra a mulher em Santa Catarina",
            "atualizado": date.today().isoformat(),
            "periodo": [int(brasil.ano.min()), int(brasil.ano.max())],
            "fontes": [
                "SINAN/Violência: DataSUS",
                "SIM/Mortalidade: Portal de Dados Abertos do SUS",
                "Sinesp VDE: Ministério da Justiça e Segurança Pública",
                "População municipal por sexo e idade: Ministério da Saúde/RIPSA",
            ],
            "territorio_padrao": "Residência da vítima",
            "metodologia_taxa": "Notificações divididas pela população feminina, multiplicadas por 100 mil.",
            "nota": "Notificações não equivalem a ocorrências policiais nem a feminicídios.",
        },
        "controle": controle,
        "territorios": territorios,
        "municipios_sc_2024": serie(municipios),
        "perfil_sc_2024": {
            "raca": serie(perfil_raca),
            "tipos_violencia": tipos,
        },
        "sinan_2025_preliminar": sinan_2025,
    }

    if sinesp_payload is not None:
        payload["sinesp_feminicidio"] = sinesp_payload

    arquivos_raca = {
        "sim_uf_ano": RACA_DIR / "sim_raca_uf_ano_2019_2024.csv",
        "sim_municipios_sc": RACA_DIR / "sim_raca_municipios_sc_2019_2024.csv",
        "sinan_uf_2024": RACA_DIR / "sinan_raca_uf_2024.csv",
        "sinan_municipios_sc": RACA_DIR / "sinan_raca_municipios_sc_2019_2024.csv",
    }
    if all(caminho.exists() for caminho in arquivos_raca.values()):
        payload["sim_raca"] = {
            "metodo": {
                "denominador": "Censo 2022, mulheres por cor ou raça",
                "periodo_sim": [2019, 2024],
                "regra_negra": "Preta mais parda",
                "territorio": "Residência da vítima",
            },
            "uf_ano": registros_csv(arquivos_raca["sim_uf_ano"]),
            "municipios_sc": registros_csv(arquivos_raca["sim_municipios_sc"]),
        }
        payload["sinan_raca"] = {
            "metodo": {
                "unidade": "Notificações",
                "nao_interpretar_como": "Pessoas únicas",
                "denominador": "Censo 2022, mulheres por cor ou raça",
            },
            "uf_2024": registros_csv(arquivos_raca["sinan_uf_2024"]),
            "municipios_sc": registros_csv(arquivos_raca["sinan_municipios_sc"]),
        }
    else:
        print("AVISO: análises de raça ausentes; seções sim_raca e sinan_raca omitidas.")

    arquivos_rais = {
        "sexo_ano": RAIS_DIR / "emprego_formal_sexo_2019_2025.csv",
        "sexo_municipios_sc": RAIS_DIR / "emprego_formal_sexo_municipios_sc_2019_2025.csv",
        "insercao_mulheres_negras": RAIS_DIR / "insercao_formal_mulheres_negras_2024_2025.csv",
        "salario_raca": RAIS_DIR / "razao_salarial_raca_2024_2025.csv",
        "salario_raca_municipios_sc": RAIS_DIR / "razao_salarial_raca_municipios_sc_2024_2025.csv",
    }
    if all(caminho.exists() for caminho in arquivos_rais.values()):
        payload["rais"] = {
            "metodo": {
                "territorio": "Local do estabelecimento",
                "periodo_sexo": [2019, 2025],
                "periodo_raca": [2024, 2025],
                "cobertura": "Vínculos formais",
            },
            **{
                chave: registros_csv(caminho)
                for chave, caminho in arquivos_rais.items()
            },
        }
    else:
        print("AVISO: análises da RAIS ausentes; seção rais omitida.")

    texto = json.dumps(payload, ensure_ascii=False, indent=2)
    for destino in (GOLD, SITE_DATA):
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")

    print(f"Gold gerado: {GOLD}")
    print(f"Painel atualizado: {SITE_DATA}")
    print(f"Municípios SC em 2024: {len(municipios)}")
    print(f"Controles: {controle}")


if __name__ == "__main__":
    main()
