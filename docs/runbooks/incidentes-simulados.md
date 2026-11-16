# Incidentes simulados da publicação da Gold

Registro da T21 (item do Gate C "incidentes simulados e recuperação demonstrada").
Cinco incidentes foram provocados em uma **cópia temporária** do atlas e recuperados
seguindo `docs/runbooks/publicacao-gold.md` ao pé da letra. Em nenhum momento
`dashboard/atlas` real foi alterado. Data: 16/11/2026, Windows 11, PowerShell 5.1,
Python 3.11, `publicar_conjunto` da T20.

## Método e ambiente

Cada incidente usa uma raiz própria `sim\<n>` (fora do repositório) com:

- `dashboard\atlas\data` e `dashboard\atlas\downloads`: cópia do atlas atual (318
  arquivos em `data`, 3 ZIPs em `downloads`), o "site publicado";
- `candidato\data` e `candidato\downloads`: a nova versão a publicar. É a mesma
  cópia com a chave extra `"simulacao": "versao-nova"` em `manifesto.json`, para
  distinguir a versão nova da anterior (o contrato aceita chaves extras);
- `.venv`: junção (`mklink /J`) para o ambiente do repositório, de modo que os
  comandos do runbook (`.venv\Scripts\python`, `dashboard/atlas`) rodem **sem
  alteração** a partir da raiz da simulação.

O script `publicar_sim.py` (apêndice) chama `publicar_conjunto` sobre essa raiz, com
gerador que copia o candidato e validador `validar_diretorio_site(data, downloads)`.
Os modos `segunda_troca` e `restauracao` injetam falha em `os.replace`. A impressão
digital do conjunto é um SHA-256 sobre os hashes de todos os arquivos de
`dashboard\atlas`, usada para provar que o estado voltou idêntico. Valor do conjunto
original (16 primeiros caracteres): `ABD0C28F18F7534A`.

Os caminhos de saída abaixo foram abreviados para `<raiz>`.

| # | Incidente | Detecção | Dados publicados afetados? | Recuperação | Runbook bastou? |
| --- | --- | --- | --- | --- | --- |
| 1 | Gold inválida | validação antes da troca | não | nenhuma necessária (conferida) | sim |
| 2 | ZIP corrompido | validação dos ZIPs antes da troca | não | nenhuma necessária (conferida) | sim |
| 3 | Backup órfão | bloqueio antes de gerar | não | remoção do backup validado | sim, com lacuna A |
| 4 | Falha na segunda troca | restauração automática | não (voltou sozinho) | nenhuma necessária (conferida) | sim |
| 5 | Falha na restauração | erro com backups preservados | sim (as duas pastas ausentes) | `Move-Item` dos dois backups | sim, com lacunas B a D |

## Incidente 1: Gold inválida na validação

**Cenário.** A geração produz um `nacional.json` com um indicador que não existe no
manifesto.

**Como provocar.** No candidato, trocar o valor da coluna `indicador` da primeira
linha por `indicador_inexistente`:

```powershell
$p = "$raiz\candidato\data\nacional.json"; $j = [IO.File]::ReadAllText($p) | ConvertFrom-Json
$col = [array]::IndexOf($j.colunas,'indicador'); $j.linhas[0][$col] = 'indicador_inexistente'
[IO.File]::WriteAllText($p, ($j | ConvertTo-Json -Depth 50 -Compress), (New-Object Text.UTF8Encoding $false))
```

**Comando.** `.venv\Scripts\python publicar_sim.py $raiz publicar`

**Saída.**

```text
ValueError: nacional.json: indicador fora do manifesto: indicador_inexistente
```

**Passos do runbook.** "Preparação segura" (listar backups: nenhum) e "Validar destino
e backup" (`validar_diretorio_site('dashboard/atlas/data', 'dashboard/atlas/downloads')`):

```text
dados e downloads válidos
```

**Resultado.** Tempo até a falha: 5 s. A impressão digital de `dashboard\atlas`
ficou idêntica (`ABD0C28F18F7534A`), nenhuma pasta `.tmp-*` ou `.backup-*` sobrou e o
conjunto publicado continua válido. **O runbook bastou**: o sintoma "erro de
validação antes da publicação (a versão anterior deve permanecer)" se confirmou e o
passo de validar o destino prova a permanência.

## Incidente 2: ZIP corrompido

**Cenário.** Um dos ZIPs candidatos chega danificado. Três variações, todas
rejeitadas antes da troca:

| Variação | Como provocar | Mensagem |
| --- | --- | --- |
| A. bytes alterados, mesmo tamanho | inverter 64 bytes a partir do byte 100001 de `atlas_sim.zip` | `ValueError: Download corrompido: downloads/atlas_sim.zip` |
| B. truncado | manter só os primeiros 200001 bytes | `ValueError: Download com tamanho divergente: downloads/atlas_sim.zip (manifesto 359977, arquivo 200001)` |
| C. vazio | arquivo de 0 byte | `ValueError: Download com tamanho divergente: downloads/atlas_sim.zip (manifesto 359977, arquivo 0)` |

```powershell
$z = "$raiz\candidato\downloads\atlas_sim.zip"; $b = [IO.File]::ReadAllBytes($z)
1..64 | % { $b[100000+$_] = $b[100000+$_] -bxor 0xFF }; [IO.File]::WriteAllBytes($z,$b)   # A
```

**Comando.** `.venv\Scripts\python publicar_sim.py $raiz publicar` após cada variação.

**Resultado.** Em A, só a verificação de integridade do ZIP (`testzip`, que confere o
CRC) detecta o dano, pois o tamanho bate com o manifesto: a validação de conteúdo
exigida pelo runbook é necessária e foi suficiente. Nas três variações a impressão
digital de `dashboard\atlas` permaneceu `ABD0C28F18F7534A`, sem resíduos, e a
validação do conjunto publicado deu `dados e downloads válidos`. **O runbook
bastou** (mesmo caminho do incidente 1).

## Incidente 3: backup órfão que bloqueia a publicação

**Cenário.** Uma publicação anterior foi interrompida e deixou `.data.backup-*` ao
lado de `data`.

**Como provocar.**

```powershell
Copy-Item -Recurse dashboard\atlas\data dashboard\atlas\.data.backup-0123456789abcdef0123456789abcdef
```

**Comando e saída.** `publicar_sim.py $raiz publicar`:

```text
RuntimeError: Backup órfão impede publicação: <raiz>\dashboard\atlas\.data.backup-0123456789abcdef0123456789abcdef
```

**Recuperação, passo a passo do runbook.**

1. Listar backups (`Get-ChildItem ... -like ".data.backup-*"`): um item, o acima.
2. Definir `$nome = "data"`, `$destino` e `$backup`: `Test-Path` devolve `True`.
3. Validar o destino: `dados e downloads válidos`.
4. Validar o backup. Não existe `.downloads.backup-*` para formar o par; o backup de
   `data` foi validado com o `downloads` atual (lacuna A): `backups válidos`.
5. Comparar com `Get-Retrato`: 318 arquivos contra 318, `Compare-Object` sem
   diferenças.
6. Caso "Destino existente e válido":
   `Remove-Item -LiteralPath $backup.FullName -Recurse`.
7. Nova publicação: `PUBLICADO ['None', 'None']`; `data` passou a ter
   `simulacao = versao-nova`, sem backups remanescentes.

**Resultado.** Bloqueio imediato, antes de gerar qualquer artefato. **O runbook
bastou**, com a lacuna A.

## Incidente 4: falha na segunda troca do `publicar_conjunto`

**Cenário.** A primeira pasta (`data`) já foi trocada e a instalação do temporário de
`downloads` falha.

**Como provocar.** Modo `segunda_troca` de `publicar_sim.py`: `os.replace` levanta
`OSError` quando a origem é `.downloads.tmp-*`.

**Comando e saída.** `publicar_sim.py $raiz segunda_troca`:

```text
OSError: falha simulada na segunda troca
```

**Resultado.** A restauração automática desfez a troca de `data`. Tempo: 6 s. A
impressão digital voltou a `ABD0C28F18F7534A`; `dashboard\atlas` ficou apenas com
`data` e `downloads` (sem backups nem temporários); `manifesto.json` segue sem a
chave `simulacao` (versão anterior) e a validação do conjunto deu
`dados e downloads válidos`. Uma nova publicação, sem a falha, concluiu
(`PUBLICADO ['None', 'None']`): nada ficou bloqueando. **O runbook bastou**: bastaram
"Preparação segura" e "Validar destino e backup"; nenhuma recuperação manual foi
necessária.

## Incidente 5: falha na restauração, com backups preservados

**Cenário.** A segunda troca falha e a restauração automática também falha nas duas
pastas. É o caso mais grave: o site publicado fica sem `data` nem `downloads`.

**Como provocar.** Modo `restauracao`: além da falha da segunda troca, `os.replace`
levanta `OSError` para qualquer origem `.*.backup-*`.

**Comando e saída.** `publicar_sim.py $raiz restauracao`:

```text
RuntimeError: Falha na troca conjunta dos destinos publicados: falha simulada na segunda troca. Falha também na restauração; backups preservados em: <raiz>\dashboard\atlas\.downloads.backup-9d03d8ba002646919b72f79aaef1d557, <raiz>\dashboard\atlas\.data.backup-c6ceb134258049aa85fd4ee89a1b0e77
```

Estado: `dashboard\atlas` contém somente os dois backups. A validação do conjunto
atual falha (`ValueError: Arquivo obrigatório ausente: manifesto.json`) e a validação
do par de backups dá `backups válidos`.

**Recuperação, passo a passo do runbook.** Caso "Destino ausente e backup válido",
para `data` e depois `downloads`:

```powershell
foreach ($nome in "data","downloads") {
  $destino = Join-Path $atlas $nome
  $backup = Get-ChildItem -LiteralPath $atlas -Directory | Where-Object { $_.Name -like ".$nome.backup-*" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  "$nome destino existe: " + (Test-Path -LiteralPath $destino)
  Move-Item -LiteralPath $backup.FullName -Destination $destino
}
```

```text
data destino existe: False
downloads destino existe: False
dados e downloads válidos
```

**Resultado.** Recuperação em 0,9 s de comandos (cerca de 1 min com a conferência). A
impressão digital voltou a `ABD0C28F18F7534A`, idêntica à original, sem resíduos. O
incidente foi executado duas vezes (a segunda com a saída acima), com o mesmo
resultado. **O runbook bastou**, com as lacunas abaixo.

## Lacunas observadas no runbook

Não foram corrigidas aqui (a tarefa não autoriza editar o runbook nem `src/`); estão
registradas como pedidos na Entrega da T21.

- **A. Backup de uma só pasta.** "Validar destino e backup" manda montar o par
  `.data.backup-*` com `.downloads.backup-*`, mas no incidente 3 só existe o backup de
  `data`. O texto não diz que se usa a outra pasta atual
  (`validar_diretorio_site(<backup de data>, 'dashboard/atlas/downloads')`).
- **B. Destino presente, mas de outra versão.** Se só uma restauração falhar, `data`
  pode ficar na versão nova (válida isoladamente) e `downloads` ausente. O caso
  "Destino inválido e backup válido" fala em destino "inválido"; este é válido, só
  incoerente com o conjunto. O runbook diz "decida pelo conjunto", mas não traz o caso
  explícito. **Não simulado aqui**; fica como pendência.
- **C. Listagem truncada.** `Select-Object FullName, LastWriteTime` em tabela corta o
  caminho do backup em consoles de largura padrão (visto no incidente 5). Sugestão:
  `Format-List` ou `Select-Object -ExpandProperty FullName`.
- **D. Sem backup.** Se a listagem não achar backup, `$backup` fica nulo e
  `$backup.FullName` imprime vazio sem mensagem clara.

## Apêndice: `publicar_sim.py`

Preparação de cada raiz: copiar `data` e `downloads` do atlas para `<raiz>\dashboard\atlas`
e para `<raiz>\candidato`, criar a junção `.venv` e acrescentar a chave `simulacao` ao
`manifesto.json` do candidato. Uso: `.venv\Scripts\python publicar_sim.py <raiz> <modo>`,
com modo `publicar`, `segunda_troca` ou `restauracao`.

```python
"""Provoca incidentes de publicação numa cópia temporária (uso: raiz modo)."""
import os, shutil, sys
from pathlib import Path
from painel_dados import publish
from painel_dados.contracts.atlas_site import validar_diretorio_site

raiz, modo = Path(sys.argv[1]), sys.argv[2]
atlas = raiz / "dashboard" / "atlas"
cand = raiz / "candidato"

def gerar(tmps):
    shutil.copytree(cand / "data", tmps[0], dirs_exist_ok=True)
    shutil.copytree(cand / "downloads", tmps[1], dirs_exist_ok=True)

def validar(tmps):
    validar_diretorio_site(tmps[0], tmps[1])

real = os.replace
if modo == "segunda_troca":  # falha ao instalar o temporário de downloads
    def falho(src, dst):
        if Path(src).name.startswith(".downloads.tmp-"):
            raise OSError("falha simulada na segunda troca")
        return real(src, dst)
    publish.os.replace = falho
elif modo == "restauracao":  # a segunda troca falha e nenhuma restauração funciona
    def falho(src, dst):
        n = Path(src).name
        if n.startswith(".downloads.tmp-"):
            raise OSError("falha simulada na segunda troca")
        if ".backup-" in n:
            raise OSError("falha simulada na restauração")
        return real(src, dst)
    publish.os.replace = falho

try:
    r = publish.publicar_conjunto([atlas / "data", atlas / "downloads"], gerar, validar)
    print("PUBLICADO", [str(x.backup_remanescente) for x in r])
except BaseException as e:
    print(f"{type(e).__name__}: {e}")
    sys.exit(1)
```
