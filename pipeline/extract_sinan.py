"""Extracao do SINAN/VIOL (violencia domestica, sexual e/ou outras violencias)
do FTP publico do DataSUS via pysus 2.10, com cache em disco por ano.

Filtro aplicado (ver SINAN_FTP.md secoes 7-8):
  - CS_SEXO == 'F'       -> mulheres
  - LES_AUTOP == '2'     -> violencia interpessoal (exclui lesao autoprovocada)

NAO agrega: preserva id_municipio (= ID_MN_RESI, residencia, ja vem com 7
digitos/DV do pysus) + ano, para permitir os tres niveis territoriais
(Brasil / UF / municipio) no consumo posterior pelo painel web.

Os arquivos VIOL no FTP sao NACIONAIS por ano (nao particionados por UF),
entao o loop e por ANO apenas - nao "UF x ano" como em bases estaduais
(SIM, SINASC). O recorte de UF/municipio acontece depois, no consumo dos
dados, usando as colunas SG_UF / SG_UF_NOT / SG_UF_OCOR / id_municipio.

ID_MUNICIP (municipio de notificacao) e ID_MN_OCOR (municipio de ocorrencia,
vem com 6 digitos, SEM digito verificador) sao preservados como colunas
extras, sem de/para - nao usar ID_MN_OCOR como chave territorial ainda.
"""

import asyncio
import inspect
from pathlib import Path

import pandas as pd
import pysus

pysus.disable_progress_bars()

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "data" / "bronze" / "sinan" / "cache_bruto"
OUT_PARQUET = ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal.parquet"
OUT_PRELIMINAR = ROOT / "data" / "silver" / "sinan_viol_mulheres_interpessoal_2025_preliminar.parquet"

COLUNAS_MANTIDAS = [
    "NU_ANO", "DT_NOTIFIC", "DT_OCOR",
    "CS_SEXO", "NU_IDADE_N", "CS_RACA", "CS_GESTANT", "CS_ESCOL_N", "SIT_CONJUG",
    "LES_AUTOP",
    "ID_MUNICIP", "ID_MN_RESI", "ID_MN_OCOR",
    "SG_UF_NOT", "SG_UF", "SG_UF_OCOR",
    "LOCAL_OCOR", "LOCAL_ESPE",
    "VIOL_FISIC", "VIOL_PSICO", "VIOL_TORT", "VIOL_SEXU", "VIOL_TRAF",
    "VIOL_FINAN", "VIOL_NEGLI", "VIOL_INFAN", "VIOL_LEGAL", "VIOL_OUTR",
    "AG_FORCA", "AG_ENFOR", "AG_OBJETO", "AG_CORTE", "AG_QUENTE",
    "AG_ENVEN", "AG_FOGO", "AG_AMEACA", "AG_OUTROS",
    "REL_CONJ", "REL_EXCON", "REL_NAMO", "REL_EXNAM",
    "REL_PAI", "REL_MAE", "REL_PAD", "REL_MAD", "REL_FILHO", "REL_DESCO",
    "REL_IRMAO", "REL_CONHEC", "REL_CUIDA", "REL_PATRAO", "REL_INST",
    "REL_POL", "REL_PROPRI", "REL_OUTROS",
    "AUTOR_SEXO", "AUTOR_ALCO",
    "ENC_DEAM", "ENC_DPCA", "ENC_DELEG", "ENC_MPU", "ENC_MULHER",
    "ATEND_MULH", "DEFEN_PUBL", "DELEG_MULH", "DELEG", "DELEG_CRIA",
    "CONS_TUTEL", "DIR_HUMAN",
    "CLASSI_FIN", "EVOLUCAO",
]


async def _get_sinan_dataset(client):
    ftp = await client.get_ftp()
    datasets = await ftp.datasets()
    return [d for d in datasets if d.name == "SINAN"][0]


async def _baixar_ano(client, sinan, ano: int) -> pd.DataFrame:
    cache_file = CACHE_DIR / f"viol_{ano}_bruto.parquet"
    if cache_file.exists():
        return pd.read_parquet(cache_file)

    contents = await sinan.content
    candidatos = [
        f for f in contents
        if f.name.upper().startswith("VIOL") and f.year == ano
    ]
    situacao = "preliminar" if ano >= 2025 else "definitivo"
    pasta_esperada = "PRELIM" if situacao == "preliminar" else "FINAIS"
    candidatos_situacao = [f for f in candidatos if pasta_esperada in f.path.upper()]
    if candidatos_situacao:
        candidatos = candidatos_situacao
    if not candidatos:
        print(f"[{ano}] arquivo VIOL nao encontrado no FTP - pulando.")
        return pd.DataFrame()

    arquivo = candidatos[0]
    print(f"[{ano}] baixando {arquivo.name} de {arquivo.path} ...")
    parquet = await client.download_to_parquet(arquivo)
    load_result = parquet.load()
    df = await load_result if inspect.iscoroutine(load_result) else load_result

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_file, index=False)
    return df


def _filtrar_e_padronizar(df: pd.DataFrame, ano: int) -> pd.DataFrame:
    if df.empty:
        return df

    mulheres = df["CS_SEXO"] == "F"
    interpessoal = df["LES_AUTOP"] == "2"
    filtrado = df.loc[mulheres & interpessoal].copy()

    colunas_existentes = [c for c in COLUNAS_MANTIDAS if c in filtrado.columns]
    filtrado = filtrado[colunas_existentes]

    filtrado["id_municipio"] = filtrado["ID_MN_RESI"]
    filtrado["ano"] = ano
    filtrado["situacao_dado"] = "preliminar" if ano >= 2025 else "definitivo"
    return filtrado


async def extrair_sinan_viol(anos: list) -> pd.DataFrame:
    client = pysus.api.PySUSClient()
    sinan = await _get_sinan_dataset(client)

    partes = []
    for ano in anos:
        df_bruto = await _baixar_ano(client, sinan, ano)
        df_filtrado = _filtrar_e_padronizar(df_bruto, ano)
        print(
            f"[{ano}] {len(df_bruto)} notificacoes brutas -> "
            f"{len(df_filtrado)} apos filtro mulher + violencia interpessoal"
        )
        partes.append(df_filtrado)

    resultado = pd.concat([parte for parte in partes if not parte.empty], ignore_index=True)

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    definitivo = resultado.loc[resultado["situacao_dado"].eq("definitivo")].copy()
    preliminar = resultado.loc[resultado["situacao_dado"].eq("preliminar")].copy()
    definitivo.to_parquet(OUT_PARQUET, index=False)
    preliminar.to_parquet(OUT_PRELIMINAR, index=False)

    print()
    print(f"Definitivo salvo em: {OUT_PARQUET}")
    print(f"Preliminar salvo em: {OUT_PRELIMINAR}")
    print(f"Total de linhas: {len(resultado)}")
    print(f"Municipios distintos (id_municipio): {resultado['id_municipio'].nunique()}")
    print(f"Anos cobertos: {sorted(resultado['ano'].unique().tolist())}")

    return resultado


if __name__ == "__main__":
    # Alinhado ao periodo do SIM ja validado (2015-2024).
    # FTP tem VIOL desde 2009 - trocar o range abaixo se quiser historico maior.
    ANOS = list(range(2015, 2026))
    asyncio.run(extrair_sinan_viol(ANOS))
