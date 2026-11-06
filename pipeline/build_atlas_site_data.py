"""Gera os arquivos de dados do site do atlas a partir da Gold do atlas.

Saída em dashboard/atlas/data/:
  manifesto.json        metadados, indicadores, fontes e critérios
  nacional.json         Brasil e 27 UFs, todos os indicadores
  idade.json            recortes etários de Brasil e Santa Catarina
  mensal.json           série mensal do Sinesp (Brasil e Santa Catarina)
  desigualdades.json    raça ou cor e trabalho formal
  mapa/<indicador>.json municípios de Santa Catarina para um indicador
  municipio/<id>.json   todos os indicadores de um município

Downloads em dashboard/atlas/downloads/ (um ZIP por fonte).
Arquivos de linhas usam o formato {"colunas": [...], "linhas": [[...], ...]}.
"""

from __future__ import annotations

import json
import re
import shutil
import unicodedata
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

from build_atlas_prototype_data import (
    SIM_NOMES,
    SINAN_EIXOS,
    SINAN_NOMES,
    SINESP_EIXOS,
)


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "data" / "gold" / "atlas"
SITE = ROOT / "dashboard" / "atlas"
DADOS = SITE / "data"
DOWNLOADS = SITE / "downloads"
RACA = ROOT / "data" / "gold" / "raca"
RAIS = ROOT / "data" / "gold" / "rais"

MIN_CASOS = 5
JANELA_ANOS = 3

SEXOS_SITE = ["total", "feminino", "masculino"]
SITUACAO = {
    "definitivo": "consolidado",
    "consolidado_publicacao": "consolidado",
    "preliminar": "preliminar",
    "previa": "parcial",
    "parcial": "parcial",
}
COLUNAS = [
    "indicador", "nivel_territorial", "id_territorio", "territorio", "ano", "sexo",
    "valor", "populacao", "taxa", "meses_observados", "situacao_dado",
]
COLUNAS_SITE_MUNICIPIO = [
    "indicador", "ano", "sexo", "valor", "populacao", "taxa",
    "suficiente", "valor_3a", "taxa_3a", "suficiente_3a", "situacao_dado",
]
COLUNAS_SITE_NACIONAL = [
    "indicador", "nivel_territorial", "id_territorio", "territorio", "ano", "sexo",
    "valor", "populacao", "taxa", "meses_observados", "situacao_dado",
]


RESSALVAS = {
    "sim_agressao": "Óbitos por agressão (CID-10 X85 a Y09), pela residência da vítima. Não equivale a feminicídio nem a homicídio doloso policial. Taxas somente até 2024.",
    "sim_suicidio": "Óbitos por lesão autoprovocada (CID-10 X60 a X84), pela residência da vítima. Taxas somente até 2024.",
    "sim_acidente_transporte": "Óbitos por acidentes de transporte (CID-10 V01 a V99), pela residência da vítima. Taxas somente até 2024.",
    "sinesp_estupro": "Registro policial pelo local do fato. Santa Catarina tem quebra de classificação entre 2019 e 2020; avalie junto de estupro de vulnerável. Sem detalhe municipal.",
    "sinesp_estupro_de_vulneravel": "Registro policial pelo local do fato. Use junto de estupro: há quebra de classificação em Santa Catarina entre 2019 e 2020. Sem detalhe municipal.",
    "sinesp_violencia_sexual_policial_soma_das_classificacoes": "Soma de estupro e estupro de vulnerável. Não elimina quebras de classificação entre UFs e anos; Santa Catarina tem quebra entre 2019 e 2020. Sem detalhe municipal.",
    "sinesp_pessoa_desaparecida": "Registro pelo local do fato, com critérios informados pelos estados. Sem detalhe municipal.",
    "sinesp_pessoa_localizada": "Registro pelo local do fato, com critérios informados pelos estados. Sem detalhe municipal.",
}
RESSALVA_SINAN = "Conta notificações, não pessoas; os tipos de violência podem coexistir no mesmo registro e não devem ser somados."
RESSALVA_SINESP = "Registro policial pelo local do fato, com critérios informados pelos estados."


def ressalva(identificador: str) -> str:
    if identificador in RESSALVAS:
        return RESSALVAS[identificador]
    return RESSALVA_SINAN if identificador.startswith("sinan_") else RESSALVA_SINESP


def slug(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_")


def reparar_nome(texto: str) -> str:
    """Desfaz dupla codificação (UTF-8 lido como latin-1) quando presente."""
    try:
        return texto.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return texto


def ler(nome: str) -> pd.DataFrame:
    return pd.read_csv(
        ATLAS / nome, dtype={"id_territorio": "string"},
        encoding="utf-8-sig", low_memory=False,
    )


def padronizar_sexo(serie: pd.Series) -> pd.Series:
    return (
        serie.fillna("").astype(str).str.strip().str.lower()
        .map({"não informado": "nao_informado"}).fillna(serie)
    )


def carregar() -> tuple[pd.DataFrame, list[dict]]:
    """Une SIM, SINAN e Sinesp em um único esquema longo."""
    partes, indicadores = [], []

    sim = ler("sim_mortalidade_territorio_ano.csv")
    sim["indicador"] = "sim_" + sim.grupo_causa
    sim = sim.rename(columns={"obitos": "valor", "taxa_100mil": "taxa"})
    for causa, (rotulo, eixo) in SIM_NOMES.items():
        indicadores.append({
            "id": f"sim_{causa}", "rotulo": rotulo, "eixo": eixo, "fonte": "SIM",
            "unidade": "óbitos", "base_territorial": "residência",
            "municipal": True, "sexo": True,
        })
    partes.append(sim.assign(fonte="SIM"))

    sinan = ler("sinan_violencia_territorio_ano.csv")
    sinan["meses_observados"] = sinan.situacao_dado.eq("definitivo").map({True: 12, False: None})
    sinan = sinan.rename(columns={"notificacoes": "valor", "taxa_100mil": "taxa"})
    sinan["indicador"] = "sinan_" + sinan.indicador
    for codigo, rotulo in SINAN_NOMES.items():
        indicadores.append({
            "id": f"sinan_{codigo}", "rotulo": rotulo, "eixo": SINAN_EIXOS[rotulo],
            "fonte": "SINAN", "unidade": "notificações",
            "base_territorial": "residência", "municipal": True, "sexo": True,
        })
    partes.append(sinan.assign(fonte="SINAN"))

    sinesp = ler("sinesp_prioridade_territorio_ano.csv")
    sinesp = sinesp.rename(columns={"valor_absoluto": "valor", "taxa_100mil": "taxa"})
    rotulos_sinesp = sorted(sinesp.indicador.unique())
    sinesp["indicador"] = "sinesp_" + sinesp.indicador.map(slug)
    municipais = set(
        "sinesp_" + slug(r)
        for r in sinesp_municipais(ler("sinesp_prioridade_territorio_ano.csv"))
    )
    for rotulo in rotulos_sinesp:
        identificador = f"sinesp_{slug(rotulo)}"
        indicadores.append({
            "id": identificador, "rotulo": rotulo, "eixo": SINESP_EIXOS[rotulo],
            "fonte": "Sinesp VDE", "unidade": "vítimas",
            "base_territorial": "local do fato",
            "municipal": identificador in municipais, "sexo": True,
        })
    partes.append(sinesp.assign(fonte="Sinesp VDE"))

    for indicador in indicadores:
        indicador["ressalva"] = ressalva(indicador["id"])

    base = pd.concat(partes, ignore_index=True)
    base["sexo"] = padronizar_sexo(base.sexo)
    base["situacao_dado"] = base.situacao_dado.map(SITUACAO)
    if base.situacao_dado.isna().any():
        raise ValueError("Situação de dado não mapeada")
    base["ano"] = base.ano.astype(int)
    return base[["fonte"] + COLUNAS], indicadores


def sinesp_municipais(df: pd.DataFrame) -> list[str]:
    return sorted(df.loc[df.nivel_territorial.eq("municipio"), "indicador"].unique())


def nomes_municipios(base: pd.DataFrame) -> dict[str, str]:
    sim = base.loc[
        base.fonte.eq("SIM") & base.nivel_territorial.eq("municipio"),
        ["id_territorio", "territorio"],
    ].drop_duplicates("id_territorio")
    return {i: reparar_nome(n) for i, n in zip(sim.id_territorio, sim.territorio)}


def avaliar_suficiencia(base: pd.DataFrame) -> pd.DataFrame:
    """Marca suficiência anual e acumulada em três anos para municípios."""
    base = base.sort_values(["indicador", "id_territorio", "sexo", "ano"]).copy()
    grupo = base.groupby(["indicador", "id_territorio", "sexo"], sort=False)
    base["valor_3a"] = grupo.valor.transform(
        lambda s: s.rolling(JANELA_ANOS, min_periods=JANELA_ANOS).sum()
    )
    pop3 = grupo.populacao.transform(
        lambda s: s.rolling(JANELA_ANOS, min_periods=JANELA_ANOS).sum()
    )
    base["taxa_3a"] = (base.valor_3a / pop3 * 100_000).round(2)
    base.loc[pop3.isna(), ["valor_3a", "taxa_3a"]] = pd.NA
    municipio = base.nivel_territorial.eq("municipio")
    base["suficiente"] = ~municipio | base.valor.ge(MIN_CASOS)
    base["suficiente_3a"] = ~municipio | base.valor_3a.ge(MIN_CASOS).fillna(False)
    return base


def limpar(valor):
    if pd.isna(valor):
        return None
    if hasattr(valor, "item"):
        valor = valor.item()
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return valor


def linhas(df: pd.DataFrame, colunas: list[str]) -> dict:
    registros = [[limpar(v) for v in linha] for linha in df[colunas].itertuples(index=False)]
    return {"colunas": colunas, "linhas": registros}


def escrever(caminho: Path, conteudo: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(conteudo, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )


def gerar_downloads(base: pd.DataFrame) -> list[dict]:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    gerados = []
    for fonte, nome in [("SIM", "sim"), ("SINAN", "sinan"), ("Sinesp VDE", "sinesp")]:
        parte = base.loc[base.fonte.eq(fonte), COLUNAS]
        destino = DOWNLOADS / f"atlas_{nome}.zip"
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            z.writestr(
                f"atlas_{nome}.csv",
                parte.to_csv(index=False, encoding="utf-8").encode("utf-8-sig"),
            )
        gerados.append({
            "fonte": fonte,
            "arquivo": f"downloads/{destino.name}",
            "linhas": int(len(parte)),
            "bytes": destino.stat().st_size,
        })
    return gerados


def gerar_desigualdades() -> dict:
    """Reúne recortes já validados de raça ou cor e trabalho formal."""
    def csv(caminho: Path) -> pd.DataFrame:
        return pd.read_csv(caminho, encoding="utf-8-sig", low_memory=False)

    sim_mun = csv(RACA / "sim_raca_municipios_sc_2019_2024.csv")
    sim_uf = csv(RACA / "sim_raca_uf_ano_2019_2024.csv")
    sinan_mun = csv(RACA / "sinan_raca_municipios_sc_2019_2024.csv")
    trabalho_ano = csv(RAIS / "emprego_formal_sexo_2019_2025.csv")
    trabalho_mun = csv(RAIS / "emprego_formal_sexo_municipios_sc_2019_2025.csv")
    salario_raca_mun = csv(RAIS / "razao_salarial_raca_municipios_sc_2024_2025.csv")

    for df in [sim_mun, sinan_mun, trabalho_mun, salario_raca_mun]:
        coluna = "municipio" if "municipio" in df.columns else "territorio"
        df[coluna] = df[coluna].astype(str).map(reparar_nome)

    return {
        "sim_raca_municipios": linhas(sim_mun, [
            "id_municipio", "municipio", "raca", "obitos_mulheres_agressao",
            "populacao_feminina_raca", "taxa_anual_media_100mil_mulheres_censo2022",
            "indice_representacao", "percentual_raca_nao_informada", "dado_suficiente",
        ]),
        "sim_raca_uf_ano": linhas(sim_uf, [
            "ano", "sigla_uf", "raca", "obitos_mulheres_agressao",
            "populacao_feminina_raca", "taxa_100mil_mulheres_censo2022",
            "indice_representacao", "percentual_raca_nao_informada", "dado_suficiente",
        ]),
        "sinan_raca_municipios": linhas(sinan_mun, [
            "id_municipio", "municipio", "raca", "notificacoes",
            "indice_representacao", "percentual_raca_nao_informada", "dado_suficiente",
        ]),
        "trabalho_ano": linhas(trabalho_ano, [
            "ano", "nivel_territorial", "id_territorio", "territorio",
            "vinculos_total", "participacao_feminina_pct",
            "remuneracao_media_homens", "remuneracao_media_mulheres",
            "razao_salarial_mulher_homem",
        ]),
        "trabalho_municipios": linhas(trabalho_mun, [
            "id_territorio", "territorio", "vinculos_total",
            "participacao_feminina_pct", "remuneracao_media_homens",
            "remuneracao_media_mulheres", "razao_salarial_mulher_homem",
        ]),
        "salario_raca_municipios": linhas(salario_raca_mun, [
            "id_territorio", "territorio", "mulheres_negras_com_remuneracao",
            "remuneracao_media_mulheres_negras", "remuneracao_media_homens_brancos",
            "remuneracao_media_mulheres_brancas",
            "razao_mulheres_negras_homens_brancos",
            "razao_mulheres_negras_mulheres_brancas",
            "piso_100_com_remuneracao_atendido",
        ]),
    }


def main() -> None:
    base, indicadores = carregar()
    nomes = nomes_municipios(base)
    mascara_mun = base.nivel_territorial.eq("municipio")
    base.loc[mascara_mun, "territorio"] = base.loc[mascara_mun, "id_territorio"].map(nomes)
    if base.loc[mascara_mun, "territorio"].isna().any():
        raise ValueError("Município sem nome canônico")
    if base.loc[mascara_mun, "id_territorio"].nunique() != 295:
        raise ValueError("Esperados 295 municípios de Santa Catarina")

    base = avaliar_suficiencia(base)
    site = base.loc[base.sexo.isin(SEXOS_SITE)]

    if DADOS.exists():
        for item in DADOS.iterdir():
            if item.name == "malha_sc.json":
                continue
            shutil.rmtree(item) if item.is_dir() else item.unlink()

    nacional = site.loc[~site.nivel_territorial.eq("municipio")]
    escrever(DADOS / "nacional.json", linhas(nacional, COLUNAS_SITE_NACIONAL))

    municipios = site.loc[site.nivel_territorial.eq("municipio")]
    por_indicador = {ind["id"]: ind for ind in indicadores}
    arquivos_mapa = []
    for identificador, recorte in municipios.groupby("indicador"):
        colunas = ["id_territorio", "territorio"] + COLUNAS_SITE_MUNICIPIO[1:]
        escrever(DADOS / "mapa" / f"{identificador}.json", linhas(recorte, colunas))
        arquivos_mapa.append(identificador)
    for identificador in arquivos_mapa:
        por_indicador[identificador]["arquivo_mapa"] = f"data/mapa/{identificador}.json"

    for id_mun, recorte in municipios.groupby("id_territorio"):
        escrever(
            DADOS / "municipio" / f"{id_mun}.json",
            {"id": id_mun, "nome": nomes[id_mun],
             **linhas(recorte, COLUNAS_SITE_MUNICIPIO)},
        )

    idade = pd.concat([
        ler("sim_mortalidade_idade_ano.csv").rename(
            columns={"grupo_causa": "indicador", "obitos": "valor"}
        ).assign(indicador=lambda d: "sim_" + d.indicador),
        ler("sinan_violencia_idade_ano.csv").rename(
            columns={"notificacoes": "valor"}
        ).assign(indicador=lambda d: "sinan_" + d.indicador),
    ], ignore_index=True)
    idade["situacao_dado"] = idade.situacao_dado.map(SITUACAO)
    escrever(DADOS / "idade.json", linhas(
        idade.rename(columns={"taxa_100mil": "taxa"}),
        ["indicador", "territorio", "ano", "grupo_etario", "valor", "populacao", "taxa", "situacao_dado"],
    ))

    mensal = ler("sinesp_prioridade_mensal.csv")
    mensal = mensal.loc[mensal.sexo.isin(SEXOS_SITE)].copy()
    mensal["indicador"] = "sinesp_" + mensal.indicador.map(slug)
    mensal["situacao_dado"] = mensal.situacao_dado.map(SITUACAO)
    escrever(DADOS / "mensal.json", linhas(
        mensal.rename(columns={"valor_absoluto": "valor"}),
        ["indicador", "territorio", "ano", "mes", "sexo", "valor", "situacao_dado"],
    ))

    escrever(DADOS / "desigualdades.json", gerar_desigualdades())

    downloads = gerar_downloads(base)

    manifesto = {
        "atualizado_em": date.today().isoformat(),
        "periodo_consolidado": [2015, 2024],
        "monitoramento": "2025 preliminar; 2026 parcial até agosto",
        "criterio_suficiencia": {
            "min_casos": MIN_CASOS,
            "janela_anos": JANELA_ANOS,
            "regra": (
                "Município só entra em mapa e ranking com pelo menos "
                f"{MIN_CASOS} casos no ano ou na soma de {JANELA_ANOS} anos."
            ),
        },
        "territorios": {
            "brasil": 1,
            "ufs": int(nacional.loc[nacional.nivel_territorial.eq("uf"), "id_territorio"].nunique()),
            "municipios_sc": len(nomes),
        },
        "municipios": [
            {"id": i, "nome": n} for i, n in sorted(nomes.items(), key=lambda x: x[1])
        ],
        "indicadores": indicadores,
        "downloads": downloads,
        "arquivos": {
            "nacional": "data/nacional.json",
            "idade": "data/idade.json",
            "mensal": "data/mensal.json",
            "desigualdades": "data/desigualdades.json",
            "municipio": "data/municipio/{id}.json",
        },
    }
    escrever(DADOS / "manifesto.json", manifesto)

    tamanhos = sorted(
        ((p.stat().st_size, p.relative_to(SITE).as_posix()) for p in DADOS.rglob("*.json")),
        reverse=True,
    )
    print(f"Arquivos de dados: {len(tamanhos)}")
    for tamanho, nome in tamanhos[:5]:
        print(f"  {tamanho / 1024:8.0f} KB  {nome}")
    print(f"Downloads: {[(d['arquivo'], d['bytes'] // 1024) for d in downloads]}")


if __name__ == "__main__":
    main()
