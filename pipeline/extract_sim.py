"""Baixa e trata o SIM definitivo para óbitos femininos por agressão.

Fonte: Portal de Dados Abertos do SUS, recursos CSV anuais do SIM.
Recorte: sexo feminino (SEXO=2), causa básica CID-10 X85-X99 ou Y00-Y09,
território pelo município de residência (CODMUNRES).
"""

from __future__ import annotations

import json
import csv
import io
import re
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "data" / "bronze" / "sim"
POPULACAO = ROOT / "data" / "silver" / "populacao_feminina_municipio.parquet"
OUT = ROOT / "data" / "silver" / "sim_mulheres_agressao.parquet"
DATASET_URL = "https://dadosabertos.saude.gov.br/dataset/sim"
ANOS = range(2015, 2025)
USECOLS = ["DTOBITO", "SEXO", "RACACOR", "IDADE", "CODMUNRES", "CODMUNOCOR", "CAUSABAS"]


def _recursos_csv() -> dict[int, str]:
    html = urllib.request.urlopen(DATASET_URL, timeout=120).read().decode("utf-8")
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    if not match:
        raise RuntimeError("Metadados do Portal de Dados Abertos do SUS não encontrados")
    dados = json.loads(match.group(1))
    recursos = dados["props"]["pageProps"]["resources"]
    urls = {}
    for recurso in recursos:
        if recurso.get("format") != "CSV":
            continue
        ano_match = re.search(r"(20\d{2})", recurso.get("name", ""))
        if ano_match:
            urls[int(ano_match.group(1))] = recurso["url"]
    ausentes = sorted(set(ANOS) - set(urls))
    if ausentes:
        raise RuntimeError(f"Recursos CSV anuais ausentes: {ausentes}")
    return {ano: urls[ano] for ano in ANOS}


def _baixar(url: str, destino: Path) -> None:
    if destino.exists() and destino.stat().st_size > 0:
        return
    print(f"Baixando {destino.name} ...")
    temporario = destino.with_suffix(destino.suffix + ".part")
    urllib.request.urlretrieve(url, temporario)
    temporario.replace(destino)


def _mapa_municipios() -> tuple[dict[str, str], dict[str, str]]:
    pop = pd.read_parquet(POPULACAO, columns=["id_municipio", "sigla_uf"])
    dimensao = pop.drop_duplicates("id_municipio")
    mapa_id = dict(zip(dimensao.id_municipio.str[:6], dimensao.id_municipio))
    mapa_uf = dict(zip(dimensao.id_municipio.str[:6], dimensao.sigla_uf))
    return mapa_id, mapa_uf


def _processar_zip(caminho: Path, ano: int, mapa_id: dict, mapa_uf: dict) -> pd.DataFrame:
    partes = []
    with zipfile.ZipFile(caminho) as arquivo_zip:
        nomes = [nome for nome in arquivo_zip.namelist() if nome.lower().endswith(".csv")]
        if len(nomes) != 1:
            raise RuntimeError(f"Esperado um CSV em {caminho.name}; encontrados {nomes}")
        with arquivo_zip.open(nomes[0]) as inspecao:
            primeira_linha = inspecao.readline().decode("latin-1", errors="replace")
        tem_cabecalho = "CAUSABAS" in primeira_linha and "SEXO" in primeira_linha
        if tem_cabecalho:
            opcoes_cabecalho = {"usecols": USECOLS}
            nomes_lidos = None
        else:
            quantidade = len(next(csv.reader(io.StringIO(primeira_linha), delimiter=";")))
            # Em 2022 o CSV tem 87 campos; em 2023, 86 e não traz ESTABDESCR.
            indices = [2, 8, 9, 7, 15, 19, 45] if quantidade == 87 else [2, 8, 9, 7, 15, 18, 44]
            if quantidade not in (86, 87):
                raise RuntimeError(f"CSV sem cabeçalho com {quantidade} campos em {caminho.name}")
            opcoes_cabecalho = {"header": None, "usecols": indices}
            nomes_lidos = [
                "DTOBITO", "IDADE", "SEXO", "RACACOR",
                "CODMUNRES", "CODMUNOCOR", "CAUSABAS",
            ]
        with arquivo_zip.open(nomes[0]) as arquivo:
            for bloco in pd.read_csv(
                arquivo,
                sep=";",
                quotechar='"',
                dtype="string",
                chunksize=200_000,
                encoding="latin-1",
                low_memory=False,
                **opcoes_cabecalho,
            ):
                if nomes_lidos:
                    bloco.columns = nomes_lidos
                causa = bloco["CAUSABAS"].fillna("").str.upper().str.strip()
                filtro = bloco["SEXO"].eq("2") & causa.str.match(r"^(X8[5-9]|X9\d|Y0\d)")
                if filtro.any():
                    parte = bloco.loc[filtro].copy()
                    cod6 = parte["CODMUNRES"].fillna("").str.strip().str[:6]
                    parte["ano"] = ano
                    parte["id_municipio"] = cod6.map(mapa_id)
                    parte["sigla_uf"] = cod6.map(mapa_uf)
                    parte["situacao_dado"] = "definitivo"
                    partes.append(parte)
    if not partes:
        return pd.DataFrame(columns=USECOLS + ["ano", "id_municipio", "sigla_uf", "situacao_dado"])
    return pd.concat(partes, ignore_index=True)


def main() -> None:
    BRONZE.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    urls = _recursos_csv()
    mapa_id, mapa_uf = _mapa_municipios()
    partes = []
    for ano, url in urls.items():
        caminho = BRONZE / f"Mortalidade_Geral_{ano}_csv.zip"
        _baixar(url, caminho)
        filtrado = _processar_zip(caminho, ano, mapa_id, mapa_uf)
        print(f"[{ano}] {len(filtrado)} óbitos femininos por agressão")
        partes.append(filtrado)

    resultado = pd.concat(partes, ignore_index=True)
    resultado.to_parquet(OUT, index=False)
    manifesto = {
        "fonte": DATASET_URL,
        "criterio": "SEXO=2; CAUSABAS X85-X99 ou Y00-Y09; CODMUNRES",
        "situacao": "definitivo",
        "recursos": [{"ano": ano, "url": url} for ano, url in urls.items()],
    }
    (BRONZE / "manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Silver SIM: {OUT} ({len(resultado)} registros)")


if __name__ == "__main__":
    main()
