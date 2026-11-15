import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import painel_dados.s3_sync as modulo_s3
from painel_dados.s3_sync import (
    construir_manifesto,
    escrever_manifesto,
    montar_comando_sync,
    sincronizar_gold,
)


def _projeto_com_gold(tmp_path: Path) -> tuple[Path, Path]:
    raiz = tmp_path / "projeto"
    gold = raiz / "data" / "gold"
    (gold / "atlas").mkdir(parents=True)
    (gold / "resumo.json").write_text('{"total": 2}\n', encoding="utf-8")
    (gold / "atlas" / "serie.csv").write_bytes(b"ano,valor\n2025,2\n")
    return raiz, gold


def test_comando_sync_usa_dryrun_por_padrao_e_nao_exclui(tmp_path: Path) -> None:
    raiz, gold = _projeto_com_gold(tmp_path)

    comando = montar_comando_sync(
        gold,
        "dados-violencia-sc-lab-123456789012",
        "20261114T120000Z-abc1234",
        raiz_projeto=raiz,
        perfil="lab-painel",
    )

    assert comando == (
        "aws",
        "s3",
        "sync",
        str(gold.resolve()),
        "s3://dados-violencia-sc-lab-123456789012/gold/20261114T120000Z-abc1234/",
        "--no-follow-symlinks",
        "--dryrun",
        "--profile",
        "lab-painel",
    )
    assert "--delete" not in comando


def test_comando_real_remove_apenas_dryrun(tmp_path: Path) -> None:
    raiz, gold = _projeto_com_gold(tmp_path)

    comando = montar_comando_sync(
        gold,
        "dados-violencia-sc-lab-123456789012",
        "execucao-001",
        raiz_projeto=raiz,
        simulacao=False,
    )

    assert "--dryrun" not in comando
    assert "--delete" not in comando


@pytest.mark.parametrize("simulacao", [True, False])
def test_comando_sync_nao_segue_links_simbolicos(
    tmp_path: Path,
    simulacao: bool,
) -> None:
    raiz, gold = _projeto_com_gold(tmp_path)

    comando = montar_comando_sync(
        gold,
        "dados-violencia-sc-lab-123456789012",
        "execucao-001",
        raiz_projeto=raiz,
        simulacao=simulacao,
    )

    assert "--no-follow-symlinks" in comando


@pytest.mark.parametrize(
    "bucket",
    ["ab", "Bucket_Invalido", "nome..duplicado", "192.168.0.1", "xn--reservado"],
)
def test_recusa_nome_de_bucket_invalido(tmp_path: Path, bucket: str) -> None:
    raiz, gold = _projeto_com_gold(tmp_path)

    with pytest.raises(ValueError, match=r"^Nome de bucket S3 inválido:"):
        montar_comando_sync(gold, bucket, "execucao-001", raiz_projeto=raiz)


@pytest.mark.parametrize("prefixo", ["", "/gold", "gold/", "gold//atlas", "gold/../atlas"])
def test_recusa_prefixo_invalido(tmp_path: Path, prefixo: str) -> None:
    raiz, gold = _projeto_com_gold(tmp_path)

    with pytest.raises(ValueError, match=r"^Prefixo S3 inválido:"):
        montar_comando_sync(
            gold,
            "dados-violencia-sc-lab-123456789012",
            "execucao-001",
            raiz_projeto=raiz,
            prefixo=prefixo,
        )


def test_recusa_origem_fora_de_data_gold(tmp_path: Path) -> None:
    raiz, _ = _projeto_com_gold(tmp_path)
    fora = tmp_path / "fora"
    fora.mkdir()

    with pytest.raises(ValueError, match=r"^Diretório de origem fora de data/gold:"):
        montar_comando_sync(
            fora,
            "dados-violencia-sc-lab-123456789012",
            "execucao-001",
            raiz_projeto=raiz,
        )


def test_manifesto_e_deterministico_e_contem_tamanho_e_sha256(tmp_path: Path) -> None:
    raiz, gold = _projeto_com_gold(tmp_path)

    primeiro = escrever_manifesto(gold, "execucao-001", raiz_projeto=raiz)
    bytes_primeiro = primeiro.read_bytes()
    segundo = escrever_manifesto(gold, "execucao-001", raiz_projeto=raiz)

    assert segundo.read_bytes() == bytes_primeiro
    manifesto = json.loads(bytes_primeiro)
    assert [item["caminho"] for item in manifesto["arquivos"]] == [
        "atlas/serie.csv",
        "resumo.json",
    ]
    assert manifesto["quantidade_arquivos"] == 2
    assert manifesto["tamanho_total_bytes"] == sum(
        item["tamanho_bytes"] for item in manifesto["arquivos"]
    )
    resumo = (gold / "resumo.json").read_bytes()
    assert manifesto["arquivos"][1]["sha256"] == hashlib.sha256(resumo).hexdigest()
    assert construir_manifesto(gold, "execucao-001", raiz_projeto=raiz) == manifesto


def test_sincronizar_gold_usa_subprocess_sem_rede(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raiz, gold = _projeto_com_gold(tmp_path)
    chamada: dict[str, object] = {}

    def executar_falso(
        comando: tuple[str, ...],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
    ) -> subprocess.CompletedProcess[str]:
        chamada.update(
            comando=comando,
            check=check,
            capture_output=capture_output,
            text=text,
        )
        assert (gold / "manifesto.json").exists()
        return subprocess.CompletedProcess(comando, 0, stdout="dryrun: upload", stderr="")

    monkeypatch.setattr(modulo_s3.subprocess, "run", executar_falso)

    resultado = sincronizar_gold(
        gold,
        "dados-violencia-sc-lab-123456789012",
        "execucao-001",
        raiz_projeto=raiz,
    )

    assert chamada["check"] is True
    assert chamada["capture_output"] is True
    assert chamada["text"] is True
    assert "--dryrun" in resultado.comando
    assert resultado.manifesto == gold / "manifesto.json"
    assert resultado.processo.stdout == "dryrun: upload"
