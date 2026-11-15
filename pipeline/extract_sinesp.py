"""Materializa a base oficial Sinesp VDE (MJSP) para Brasil e Santa Catarina.

Fonte: página "Base de Dados e Notas Metodológicas dos Gestores Estaduais -
Sinesp VDE" do Ministério da Justiça e Segurança Pública. O MJSP publica um
arquivo ``bancovde-AAAA.xlsx`` por ano, com ocorrências e vítimas por UF,
município, mês e evento (31 indicadores, incluindo Feminicídio).

Camadas produzidas:

- Bronze: ``data/bronze/sinesp/vde/bancovde-AAAA.xlsx`` preservado como
  publicado, mais um cache ``.parquet`` equivalente (a leitura do xlsx leva
  cerca de dois minutos por ano).
- Silver: ``sinesp_vde_ocorrencias.parquet`` com todos os eventos, UFs e
  municípios, tipado e padronizado; ``sinesp_feminicidio.parquet`` com o
  recorte de Feminicídio consumido por ``build_gold.py``.
- Gold: CSVs pequenos em ``data/gold/sinesp/`` com Brasil e Santa Catarina
  por ano, mês e evento, e os municípios catarinenses por ano.

Regras herdadas da nota metodológica do MJSP: nos indicadores Estupro e
Tentativa de Homicídio um mesmo mês pode ter duas linhas, que devem ser
somadas. Valor zero significa ausência de ocorrência, não ausência de dado.
Rodar: ``python pipeline/extract_sinesp.py [--inicio 2019] [--refazer]``.
"""

from __future__ import annotations

import argparse
import re
import unicodedata
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
URL = (
    "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/"
    "estatistica/download/dnsp-base-de-dados/bancovde-{ano}.xlsx/@@download/file"
)
PAGINA = (
    "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/"
    "dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-"
    "sinesp-vde-2022-e-2023"
)
BRONZE = ROOT / "data" / "bronze" / "sinesp" / "vde"
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold" / "sinesp"
OUT_OCORRENCIAS = SILVER / "sinesp_vde_ocorrencias.parquet"
OUT_FEMINICIDIO = SILVER / "sinesp_feminicidio.parquet"

ANO_INICIO_PADRAO = 2019
COLUNAS_TEXTO = ["uf", "municipio", "evento", "agente", "arma", "faixa_etaria", "abrangencia"]
COLUNAS_NUMERO = ["feminino", "masculino", "nao_informado", "total_vitima", "total", "total_peso"]
# Eventos medidos em vítimas (colunas feminino/masculino/total_vitima); os
# demais são contagens de ocorrências ou registros (coluna total).
METRICAS = {"vitimas": "total_vitimas", "ocorrencias": "total_ocorrencias", "peso_kg": "total_peso"}


def _normalizar(valor: object) -> str:
    texto = unicodedata.normalize("NFKD", str(valor)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


def _baixar(ano: int, refazer: bool = False) -> Path | None:
    BRONZE.mkdir(parents=True, exist_ok=True)
    destino = BRONZE / f"bancovde-{ano}.xlsx"
    if destino.exists() and destino.stat().st_size > 0 and not refazer:
        return destino
    pedido = urllib.request.Request(URL.format(ano=ano), headers={"User-Agent": "Mozilla/5.0"})
    temporario = destino.with_suffix(".xlsx.part")
    try:
        with urllib.request.urlopen(pedido, timeout=300) as resposta, temporario.open("wb") as saida:
            tipo = resposta.headers.get("Content-Type", "")
            if "spreadsheet" not in tipo and "octet-stream" not in tipo:
                raise urllib.error.HTTPError(URL, 404, f"conteúdo inesperado: {tipo}", None, None)
            while bloco := resposta.read(1 << 20):
                saida.write(bloco)
    except urllib.error.HTTPError as erro:
        temporario.unlink(missing_ok=True)
        if erro.code == 404:
            print(f"Sinesp VDE {ano}: ainda não publicado ({erro.code}).")
            return None
        raise
    temporario.replace(destino)
    print(f"Sinesp VDE {ano}: baixado ({destino.stat().st_size / 1e6:.1f} MB)")
    return destino


def _cache_parquet(xlsx: Path) -> pd.DataFrame:
    """Lê o xlsx uma única vez e guarda um parquet idêntico ao lado dele."""
    cache = xlsx.with_suffix(".parquet")
    if cache.exists() and cache.stat().st_mtime >= xlsx.stat().st_mtime:
        return pd.read_parquet(cache)
    quadro = pd.read_excel(xlsx, dtype={coluna: "string" for coluna in COLUNAS_TEXTO})
    quadro.to_parquet(cache, index=False)
    return quadro


def _padronizar(quadro: pd.DataFrame, ano_arquivo: int) -> pd.DataFrame:
    quadro = quadro.copy()
    quadro.columns = [_normalizar(coluna) for coluna in quadro.columns]
    faltantes = {"uf", "municipio", "evento", "data_referencia"} - set(quadro.columns)
    if faltantes:
        raise KeyError(f"bancovde-{ano_arquivo}: colunas ausentes {sorted(faltantes)}")
    for coluna in COLUNAS_TEXTO:
        if coluna not in quadro.columns:
            quadro[coluna] = pd.NA
        quadro[coluna] = quadro[coluna].astype("string").str.strip()
    for coluna in COLUNAS_NUMERO:
        if coluna not in quadro.columns:
            quadro[coluna] = pd.NA
        quadro[coluna] = pd.to_numeric(quadro[coluna], errors="coerce")

    data = pd.to_datetime(quadro["data_referencia"], errors="coerce")
    saida = pd.DataFrame(
        {
            "ano": data.dt.year.astype("Int64"),
            "mes": data.dt.month.astype("Int64"),
            "sigla_uf": quadro["uf"].str.upper(),
            "municipio": quadro["municipio"].str.upper(),
            "evento": quadro["evento"],
            "abrangencia": quadro["abrangencia"],
            "agente": quadro["agente"],
            "arma": quadro["arma"],
            "faixa_etaria": quadro["faixa_etaria"],
            "vitimas_feminino": quadro["feminino"],
            "vitimas_masculino": quadro["masculino"],
            "vitimas_nao_informado": quadro["nao_informado"],
            "total_vitimas": quadro["total_vitima"],
            "total_ocorrencias": quadro["total"],
            "total_peso": quadro["total_peso"],
            "arquivo_origem": f"bancovde-{ano_arquivo}.xlsx",
        }
    ).dropna(subset=["ano", "mes"])
    fora_do_ano = saida["ano"].ne(ano_arquivo)
    if fora_do_ano.any():
        print(f"AVISO: bancovde-{ano_arquivo}: {int(fora_do_ano.sum())} linhas com ano diferente, descartadas.")
        saida = saida.loc[~fora_do_ano]
    return saida


def _marcar_situacao(dados: pd.DataFrame) -> pd.DataFrame:
    """Último ano publicado com menos de 12 meses é marcado como parcial."""
    dados = dados.copy()
    dados["situacao_dado"] = "consolidado_publicacao"
    ultimo_ano = int(dados["ano"].max())
    meses = int(dados.loc[dados["ano"].eq(ultimo_ano), "mes"].nunique())
    if meses < 12:
        dados.loc[dados["ano"].eq(ultimo_ano), "situacao_dado"] = "parcial"
    return dados


def _agregar(dados: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    """Soma vítimas e ocorrências; linhas repetidas do mesmo mês são somadas (nota MJSP)."""
    medidas = {
        "vitimas_feminino": "sum",
        "vitimas_masculino": "sum",
        "vitimas_nao_informado": "sum",
        "total_vitimas": "sum",
        "total_ocorrencias": "sum",
        "total_peso": "sum",
    }
    agregado = dados.groupby(chaves, as_index=False, dropna=False).agg(medidas)
    for coluna in ["vitimas_feminino", "vitimas_masculino", "vitimas_nao_informado", "total_vitimas", "total_ocorrencias"]:
        agregado[coluna] = agregado[coluna].round().astype("Int64")
    agregado["total_peso"] = agregado["total_peso"].round(3)
    return agregado


def _gold(dados: pd.DataFrame) -> None:
    GOLD.mkdir(parents=True, exist_ok=True)
    estadual = dados.loc[dados["abrangencia"].eq("Estadual")]
    situacao = dados.groupby("ano")["situacao_dado"].first()

    brasil = _agregar(estadual, ["ano", "mes", "evento"])
    brasil.insert(0, "territorio", "Brasil")
    sc = _agregar(estadual.loc[estadual["sigla_uf"].eq("SC")], ["ano", "mes", "evento"])
    sc.insert(0, "territorio", "Santa Catarina")
    mensal = pd.concat([brasil, sc], ignore_index=True)
    mensal["situacao_dado"] = mensal["ano"].map(situacao)
    mensal = mensal.sort_values(["territorio", "evento", "ano", "mes"]).reset_index(drop=True)
    mensal.to_csv(GOLD / "sinesp_sc_brasil_mensal.csv", index=False, encoding="utf-8")

    anual = _agregar(mensal, ["territorio", "ano", "evento"]).merge(
        mensal.groupby(["territorio", "ano", "evento"], as_index=False)["mes"].nunique()
        .rename(columns={"mes": "meses_informados"}),
        on=["territorio", "ano", "evento"],
    )
    anual["situacao_dado"] = anual["ano"].map(situacao)
    anual = anual.sort_values(["territorio", "evento", "ano"]).reset_index(drop=True)
    anual.to_csv(GOLD / "sinesp_sc_brasil_anual.csv", index=False, encoding="utf-8")

    ufs = _agregar(estadual, ["sigla_uf", "ano", "evento"])
    ufs["situacao_dado"] = ufs["ano"].map(situacao)
    ufs.sort_values(["evento", "ano", "sigla_uf"]).to_csv(
        GOLD / "sinesp_uf_anual.csv", index=False, encoding="utf-8"
    )

    municipios_sc = _agregar(
        estadual.loc[estadual["sigla_uf"].eq("SC")], ["sigla_uf", "municipio", "ano", "evento"]
    )
    municipios_sc["situacao_dado"] = municipios_sc["ano"].map(situacao)
    municipios_sc.sort_values(["evento", "ano", "municipio"]).to_csv(
        GOLD / "sinesp_sc_municipios_anual.csv", index=False, encoding="utf-8"
    )

    feminicidio = anual.loc[anual["evento"].str.lower().eq("feminicídio")].copy()
    feminicidio = feminicidio.pivot(index="ano", columns="territorio", values="total_vitimas").reset_index()
    feminicidio.columns.name = None
    feminicidio["situacao_dado"] = feminicidio["ano"].map(situacao)
    feminicidio.to_csv(GOLD / "sinesp_feminicidio_sc_brasil_anual.csv", index=False, encoding="utf-8")

    (GOLD / "README.md").write_text(
        "# Sinesp VDE — Brasil e Santa Catarina\n\n"
        f"Gerado por `pipeline/extract_sinesp.py` em {date.today().isoformat()} a partir dos arquivos "
        "`bancovde-AAAA.xlsx` publicados pelo MJSP.\n\n"
        f"Fonte: {PAGINA}\n\n"
        "Arquivos:\n\n"
        "- `sinesp_sc_brasil_mensal.csv`: Brasil e SC por ano, mês e evento.\n"
        "- `sinesp_sc_brasil_anual.csv`: mesma base agregada por ano, com `meses_informados`.\n"
        "- `sinesp_uf_anual.csv`: todas as UFs por ano e evento, para comparação.\n"
        "- `sinesp_sc_municipios_anual.csv`: municípios catarinenses por ano e evento.\n"
        "- `sinesp_feminicidio_sc_brasil_anual.csv`: vítimas de feminicídio, Brasil × SC, por ano.\n\n"
        "Leitura das medidas:\n\n"
        "- Eventos contra a pessoa (Feminicídio, Homicídio doloso, Estupro, Estupro de vulnerável, "
        "Lesão corporal seguida de morte, Latrocínio, Tentativas, Suicídio, Mortes no trânsito, "
        "Pessoa Desaparecida/Localizada) são medidos em vítimas: `vitimas_feminino`, "
        "`vitimas_masculino`, `vitimas_nao_informado` e `total_vitimas`.\n"
        "- Eventos patrimoniais e de produtividade (Furto e Roubo de veículo, Roubo de carga, "
        "Roubo a instituição financeira, Tráfico de drogas, Arma de Fogo Apreendida, Mandado de "
        "prisão cumprido, atividades de bombeiros) são contagens em `total_ocorrencias`.\n"
        "- Apreensões de Cocaína e Maconha são medidas em quilos em `total_peso`.\n"
        "- Só a abrangência `Estadual` entra nos totais. Linhas da Polícia Federal e da PRF ficam "
        "na Silver, separadas, para não dobrar a contagem.\n"
        "- Linhas repetidas do mesmo mês (Estupro e Tentativa de Homicídio) são somadas, "
        "conforme nota do MJSP. Zero significa ausência de ocorrência, não ausência de dado.\n"
        "- `situacao_dado = parcial` marca o último ano publicado com menos de 12 meses.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--inicio", type=int, default=ANO_INICIO_PADRAO, help="primeiro ano da série")
    parser.add_argument("--refazer", action="store_true", help="baixa de novo os xlsx já presentes")
    args = parser.parse_args()

    partes = []
    for ano in range(args.inicio, date.today().year + 1):
        xlsx = _baixar(ano, refazer=args.refazer)
        if xlsx is None:
            continue
        partes.append(_padronizar(_cache_parquet(xlsx), ano))
        print(f"Sinesp VDE {ano}: {len(partes[-1])} linhas")
    if not partes:
        raise RuntimeError("Nenhum arquivo bancovde-AAAA.xlsx disponível")

    dados = _marcar_situacao(pd.concat(partes, ignore_index=True))
    dados = dados.sort_values(["ano", "mes", "sigla_uf", "municipio", "evento"]).reset_index(drop=True)
    SILVER.mkdir(parents=True, exist_ok=True)
    dados.to_parquet(OUT_OCORRENCIAS, index=False)

    feminicidio = dados.loc[
        dados["evento"].str.lower().eq("feminicídio") & dados["abrangencia"].eq("Estadual"),
        ["ano", "mes", "sigla_uf", "municipio", "total_vitimas", "arquivo_origem", "situacao_dado"],
    ].rename(columns={"total_vitimas": "vitimas_feminicidio"})
    feminicidio = feminicidio.dropna(subset=["vitimas_feminicidio"]).copy()
    feminicidio[["ano", "mes", "vitimas_feminicidio"]] = feminicidio[
        ["ano", "mes", "vitimas_feminicidio"]
    ].astype("int64")
    feminicidio["municipio"] = feminicidio["municipio"].fillna("").astype(str)
    feminicidio.to_parquet(OUT_FEMINICIDIO, index=False)

    _gold(dados)

    ultimo_ano = int(dados["ano"].max())
    ultimo_mes = int(dados.loc[dados["ano"].eq(ultimo_ano), "mes"].max())
    resumo = (
        feminicidio.groupby("ano")["vitimas_feminicidio"].sum().rename("Brasil").to_frame()
        .join(feminicidio.loc[feminicidio.sigla_uf.eq("SC")].groupby("ano")["vitimas_feminicidio"].sum().rename("SC"))
    )
    print(f"Silver Sinesp: {OUT_OCORRENCIAS} ({len(dados)} linhas; até {ultimo_ano}-{ultimo_mes:02d})")
    print(f"Silver Feminicídio: {OUT_FEMINICIDIO} ({len(feminicidio)} linhas)")
    print(f"Gold: {GOLD}")
    print("Vítimas de feminicídio por ano:")
    print(resumo.to_string())


if __name__ == "__main__":
    main()
