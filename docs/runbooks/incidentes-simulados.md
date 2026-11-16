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
Os modos `segunda_troca` e `restauracao` injetam falha em `os.replace`. O script se
recusa a rodar fora de uma raiz de simulação (exige o arquivo `SIMULACAO.txt` e
rejeita uma raiz com `.git` ou `pyproject.toml`), de modo que apontá-lo para o
repositório não troca dados reais.

A **impressão digital** do conjunto é o SHA-256 de todas as linhas
`caminho-relativo|sha256-do-arquivo` de `dashboard\atlas`, ordenadas (função
`Get-Digital`, apêndice B): ela muda se um arquivo for alterado, removido, criado ou
renomeado. Valor do conjunto original, 321 arquivos (318 de `data` e 3 ZIPs):
`528EDE0648C8961C` (16 primeiros caracteres; completo:
`528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5`). "Sem resíduos" é a
lista vazia de `Get-Residuos` (`.*.tmp-*` e `.*.backup-*`) e "válido" é a saída de
`validar_diretorio_site(data, downloads)`. Tudo isso é impresso pelo roteiro
`rodar_tudo.ps1` (apêndice C), que reproduz este documento do zero.

Os caminhos de saída abaixo foram abreviados para `<raiz>`.

| # | Incidente | Detecção | Dados publicados afetados? | Recuperação | Runbook bastou? |
| --- | --- | --- | --- | --- | --- |
| 1 | Gold inválida | validação antes da troca | não | nenhuma necessária (conferida) | sim |
| 2 | ZIP corrompido | validação dos ZIPs antes da troca | não | nenhuma necessária (conferida) | sim |
| 3 | Backup órfão | bloqueio antes de gerar | não | remoção do backup validado | em parte: precisou deduzir a lacuna A |
| 4 | Falha na segunda troca | restauração automática | não (voltou sozinho) | nenhuma necessária (conferida) | sim |
| 5 | Falha na restauração | erro com backups preservados | sim (as duas pastas ausentes) | `Move-Item` dos dois backups | em parte: lacuna C vista; B, D e E não exercitadas |

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

**Resultado.** A impressão digital de `dashboard\atlas`
ficou idêntica (`528EDE0648C8961C`), nenhuma pasta `.tmp-*` ou `.backup-*` sobrou e o
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
digital de `dashboard\atlas` permaneceu `528EDE0648C8961C`, sem resíduos, e a
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

**Resultado.** Bloqueio imediato, antes de gerar qualquer artefato. **O runbook bastou só em parte**: a recuperação funcionou, mas o passo de validar
o backup exigiu deduzir a lacuna A (não há `.downloads.backup-*` para formar o par).

## Incidente 4: falha na segunda troca do `publicar_conjunto`

**Cenário.** A primeira pasta (`data`) já foi trocada e a instalação do temporário de
`downloads` falha.

**Como provocar.** Modo `segunda_troca` de `publicar_sim.py`: `os.replace` levanta
`OSError` quando a origem é `.downloads.tmp-*`.

**Comando e saída.** `publicar_sim.py $raiz segunda_troca`:

```text
OSError: falha simulada na segunda troca
```

**Resultado.** A restauração automática desfez a troca de `data`. A
impressão digital voltou a `528EDE0648C8961C`; `dashboard\atlas` ficou apenas com
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

**Resultado.** Os dois `Move-Item` levaram menos de 1 s. A impressão digital voltou a
`528EDE0648C8961C`, idêntica à original, sem resíduos, e `validar_diretorio_site`
deu `dados e downloads válidos` (saída do roteiro `rodar_tudo.ps1`). **O runbook
bastou só em parte**: a listagem de backups cortou o caminho em console de largura
padrão (lacuna C) e, com mais de um backup por pasta, nada garante que o mais
recente de `data` e o de `downloads` sejam da mesma publicação (lacuna E, não
exercitada aqui).

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
- **E. Vários backups por pasta.** A preparação escolhe o mais recente de cada pasta de
  forma independente (`Sort-Object LastWriteTime -Descending | Select-Object -First 1`).
  Com backups de publicações diferentes, isso pode combinar `data` de uma execução com
  `downloads` de outra. Sugestão: parear pelos instantes de criação (diferença de
  poucos segundos) e validar o par antes de qualquer `Move-Item`. **Não simulado.**

## Apêndice A: `publicar_sim.py`

Uso: `.venv\Scripts\python publicar_sim.py <raiz> <modo>`, com modo `publicar`,
`segunda_troca` ou `restauracao`. A raiz precisa ter sido criada por `Novo-Sim`
(apêndice B), que grava o `SIMULACAO.txt`; o script recusa qualquer outra raiz.

```python
"""Provoca incidentes de publicação numa cópia temporária (uso: raiz modo)."""
import os
import shutil
import sys
from pathlib import Path

from painel_dados import publish
from painel_dados.contracts.atlas_site import validar_diretorio_site

raiz, modo = Path(sys.argv[1]).resolve(), sys.argv[2]

# Trava: só roda numa raiz de simulação, nunca no repositório.
if not (raiz / "SIMULACAO.txt").is_file():
    sys.exit("Recusado: a raiz não tem SIMULACAO.txt (não é uma raiz de simulação)")
if (raiz / ".git").exists() or (raiz / "pyproject.toml").exists():
    sys.exit("Recusado: a raiz parece ser um repositório")

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

## Apêndice B: funções de apoio (`lib.ps1`)

`Get-Digital` (impressão digital), `Get-Residuos` (temporários e backups sobrando),
`Novo-Sim` (cria a raiz de simulação: cópia do atlas e do candidato, junção `.venv` e
`SIMULACAO.txt`), `Rodar` e `Validar-Conjunto`. Grave os `.ps1` em UTF-8 **com BOM**:
o PowerShell 5.1 lê arquivo sem BOM como ANSI e corrompe os acentos.

```powershell
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = New-Object Text.UTF8Encoding $false
$OutputEncoding = [Console]::OutputEncoding

# Impressão digital do conjunto: SHA-256 sobre linhas "caminho-relativo|sha256-do-arquivo", ordenadas.
function Get-Digital([string]$raiz) {
    $base = (Resolve-Path -LiteralPath $raiz).Path.TrimEnd('\')
    $linhas = Get-ChildItem -LiteralPath $base -Recurse -File -Force | ForEach-Object {
        $rel = $_.FullName.Substring($base.Length + 1).Replace('\', '/')
        "$rel|" + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    } | Sort-Object
    $texto = ($linhas -join "`n")
    $sha = [Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($texto))
    [pscustomobject]@{
        Arquivos = @($linhas).Count
        Digital  = ([BitConverter]::ToString($sha).Replace('-', ''))
    }
}

# Resíduos de publicação ao lado de data e downloads.
function Get-Residuos([string]$atlas) {
    @(Get-ChildItem -LiteralPath $atlas -Directory -Force | Where-Object { $_.Name -like '.*.tmp-*' -or $_.Name -like '.*.backup-*' } | ForEach-Object Name)
}

function Novo-Sim([string]$S, [string]$repo, [string]$n) {
    $raiz = Join-Path $S "sim\$n"
    if (Test-Path $raiz) { Remove-Item -LiteralPath $raiz -Recurse -Force }
    New-Item -ItemType Directory "$raiz\dashboard\atlas", "$raiz\candidato" | Out-Null
    Copy-Item -Recurse "$repo\dashboard\atlas\data" "$raiz\dashboard\atlas\data"
    Copy-Item -Recurse "$repo\dashboard\atlas\downloads" "$raiz\dashboard\atlas\downloads"
    Copy-Item -Recurse "$repo\dashboard\atlas\data" "$raiz\candidato\data"
    Copy-Item -Recurse "$repo\dashboard\atlas\downloads" "$raiz\candidato\downloads"
    cmd /c mklink /J "$raiz\.venv" "$repo\.venv" | Out-Null
    $p = "$raiz\candidato\data\manifesto.json"
    $j = Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json
    $j | Add-Member simulacao "versao-nova"
    [IO.File]::WriteAllText($p, ($j | ConvertTo-Json -Depth 50 -Compress), (New-Object Text.UTF8Encoding $false))
    Set-Content -LiteralPath "$raiz\SIMULACAO.txt" -Value "raiz de simulação; segura para publicar_sim.py"
    $raiz
}

function Rodar([string]$raiz, [string]$modo) {
    Push-Location $raiz
    try { $saida = & .venv\Scripts\python (Join-Path $script:S "publicar_sim.py") $raiz $modo 2>&1 | Out-String } finally { Pop-Location }
    $saida.Trim()
}

function Validar-Conjunto([string]$raiz) {
    Push-Location $raiz
    try { & .venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'dashboard/atlas/data', r'dashboard/atlas/downloads'); print('dados e downloads válidos')" 2>&1 | Out-String } finally { Pop-Location }
}
```

## Apêndice C: roteiro `rodar_tudo.ps1`

Reproduz os cinco incidentes do zero e imprime, para cada um, saída, impressão digital,
resíduos e validação. No incidente 3, a checagem `I3 depois da recuperacao` roda depois
de remover o backup órfão e **antes** da nova publicação. Uso, a partir de um worktree
com `.venv`: `powershell -File rodar_tudo.ps1 -S <pasta com os scripts> -repo <raiz do repositório>`.

```powershell
param([string]$S, [string]$repo)
. "$S\lib.ps1"
$script:S = $S

function Mostrar($t, $v) { "[$t] $v" }

# Original
$ref = "$S\sim\original\atlas"
if (Test-Path "$S\sim\original") { Remove-Item -LiteralPath "$S\sim\original" -Recurse -Force }
New-Item -ItemType Directory $ref | Out-Null
Copy-Item -Recurse "$repo\dashboard\atlas\data" "$ref\data"
Copy-Item -Recurse "$repo\dashboard\atlas\downloads" "$ref\downloads"
$orig = Get-Digital $ref
Mostrar "ORIGINAL" "$($orig.Arquivos) arquivos; $($orig.Digital)"

# Trava: raiz do repositório e raiz sem marcador
Push-Location $repo
$t1 = (& .venv\Scripts\python "$S\publicar_sim.py" $repo publicar 2>&1 | Out-String).Trim()
Pop-Location
Mostrar "TRAVA repo" $t1
New-Item -ItemType Directory "$S\sim\vazia" -Force | Out-Null
Push-Location $repo
$t2 = (& .venv\Scripts\python "$S\publicar_sim.py" "$S\sim\vazia" publicar 2>&1 | Out-String).Trim()
Pop-Location
Mostrar "TRAVA sem marcador" $t2

function Checar($raiz, $rotulo, $antes) {
    $d = Get-Digital "$raiz\dashboard\atlas"
    $res = Get-Residuos "$raiz\dashboard\atlas"
    $v = Validar-Conjunto $raiz
    Mostrar $rotulo ("arquivos=$($d.Arquivos); digital=$($d.Digital); igual_ao_original=" + ($d.Digital -eq $antes.Digital) + "; residuos=[" + ($res -join ',') + "]; validacao=" + $v.Trim())
}

# 1. Gold inválida
$r = Novo-Sim $S $repo "i1"
$p = "$r\candidato\data\nacional.json"; $j = [IO.File]::ReadAllText($p) | ConvertFrom-Json
$col = [array]::IndexOf($j.colunas, 'indicador'); $j.linhas[0][$col] = 'indicador_inexistente'
[IO.File]::WriteAllText($p, ($j | ConvertTo-Json -Depth 50 -Compress), (New-Object Text.UTF8Encoding $false))
Mostrar "I1 saida" (Rodar $r "publicar")
Checar $r "I1 depois" $orig

# 2A/B/C ZIP corrompido
foreach ($v in "A","B","C") {
    $r = Novo-Sim $S $repo "i2$v"
    $z = "$r\candidato\downloads\atlas_sim.zip"
    if ($v -eq "A") { $b = [IO.File]::ReadAllBytes($z); 1..64 | % { $b[100000+$_] = $b[100000+$_] -bxor 0xFF }; [IO.File]::WriteAllBytes($z,$b) }
    if ($v -eq "B") { $b = [IO.File]::ReadAllBytes($z); [IO.File]::WriteAllBytes($z, $b[0..200000]) }
    if ($v -eq "C") { [IO.File]::WriteAllBytes($z, [byte[]]@()) }
    Mostrar "I2$v saida" (Rodar $r "publicar")
    Checar $r "I2$v depois" $orig
}

# 3. Backup órfão
$r = Novo-Sim $S $repo "i3"
Copy-Item -Recurse "$r\dashboard\atlas\data" "$r\dashboard\atlas\.data.backup-0123456789abcdef0123456789abcdef"
Mostrar "I3 saida" (Rodar $r "publicar")
Checar $r "I3 antes da recuperacao" $orig
$atlas = "$r\dashboard\atlas"
$bk = Get-ChildItem -LiteralPath $atlas -Directory -Force | Where-Object { $_.Name -like ".data.backup-*" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Push-Location $r
$vb = & .venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; import sys; validar_diretorio_site(sys.argv[1], r'dashboard/atlas/downloads'); print('backup de data valido')" $bk.FullName 2>&1 | Out-String
Pop-Location
Mostrar "I3 backup validado" $vb.Trim()
$dBk = Get-Digital $bk.FullName; $dDest = Get-Digital "$atlas\data"
Mostrar "I3 comparacao" "backup=$($dBk.Arquivos)/$($dBk.Digital); destino=$($dDest.Arquivos)/$($dDest.Digital); iguais=$($dBk.Digital -eq $dDest.Digital)"
Remove-Item -LiteralPath $bk.FullName -Recurse
Checar $r "I3 depois da recuperacao" $orig
Mostrar "I3 nova publicacao" (Rodar $r "publicar")
Mostrar "I3 residuos" ("[" + ((Get-Residuos $atlas) -join ',') + "]")

# 4. Falha na segunda troca
$r = Novo-Sim $S $repo "i4"
Mostrar "I4 saida" (Rodar $r "segunda_troca")
Checar $r "I4 depois" $orig
Mostrar "I4 nova publicacao" (Rodar $r "publicar")

# 5. Falha na restauração
$r = Novo-Sim $S $repo "i5"
$antes = Get-Digital "$r\dashboard\atlas"
Mostrar "I5 digital antes" "$($antes.Arquivos); $($antes.Digital)"
Mostrar "I5 saida" (Rodar $r "restauracao")
$atlas = "$r\dashboard\atlas"
Mostrar "I5 conteudo do atlas" ((Get-ChildItem -LiteralPath $atlas -Force | ForEach-Object Name) -join ' | ')
$sw = [Diagnostics.Stopwatch]::StartNew()
foreach ($nome in "data","downloads") {
    $destino = Join-Path $atlas $nome
    $b = Get-ChildItem -LiteralPath $atlas -Directory -Force | Where-Object { $_.Name -like ".$nome.backup-*" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Move-Item -LiteralPath $b.FullName -Destination $destino
}
$sw.Stop()
Mostrar "I5 recuperacao" "$([math]::Round($sw.Elapsed.TotalSeconds,2)) s"
Checar $r "I5 depois" $antes
$d5 = Get-Digital "$atlas"
Mostrar "I5 igual_ao_original" ($d5.Digital -eq $orig.Digital)
```

### Saída real da reexecução de 16/11/2026

Transcrição literal do roteiro (27 linhas); só o caminho da raiz de simulação foi
abreviado para `<raiz>`. Em `[I3 antes da recuperacao]` o `igual_ao_original=False` é
esperado: o backup órfão ainda está ao lado de `data`. As linhas `[TRAVA ...]` vêm
do PowerShell 5.1, que prefixa `python.exe :` na mensagem do `stderr`.

```text
[ORIGINAL] 321 arquivos; 528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5
[TRAVA repo] python.exe : Recusado: a raiz não tem SIMULACAO.txt (não é uma raiz de simulação)
[TRAVA sem marcador] python.exe : Recusado: a raiz não tem SIMULACAO.txt (não é uma raiz de simulação)
[I1 saida] ValueError: nacional.json: indicador fora do manifesto: indicador_inexistente
[I1 depois] arquivos=321; digital=528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5; igual_ao_original=True; residuos=[]; validacao=dados e downloads válidos
[I2A saida] ValueError: Download corrompido: downloads/atlas_sim.zip
[I2A depois] arquivos=321; digital=528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5; igual_ao_original=True; residuos=[]; validacao=dados e downloads válidos
[I2B saida] ValueError: Download com tamanho divergente: downloads/atlas_sim.zip (manifesto 359977, arquivo 200001)
[I2B depois] arquivos=321; digital=528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5; igual_ao_original=True; residuos=[]; validacao=dados e downloads válidos
[I2C saida] ValueError: Download com tamanho divergente: downloads/atlas_sim.zip (manifesto 359977, arquivo 0)
[I2C depois] arquivos=321; digital=528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5; igual_ao_original=True; residuos=[]; validacao=dados e downloads válidos
[I3 saida] RuntimeError: Backup órfão impede publicação: <raiz>\dashboard\atlas\.data.backup-0123456789abcdef0123456789abcdef
[I3 antes da recuperacao] arquivos=639; digital=377FBEA58851706CC552ACF2E29A69D8EECCEB904ADC8D43EFE14B66BB20E3A3; igual_ao_original=False; residuos=[.data.backup-0123456789abcdef0123456789abcdef]; validacao=dados e downloads válidos
[I3 backup validado] backup de data valido
[I3 comparacao] backup=318/D3CE0D4CAF6967176D8840184D03CF9053733B9A4BE9157E9E47B730A8B06B8D; destino=318/D3CE0D4CAF6967176D8840184D03CF9053733B9A4BE9157E9E47B730A8B06B8D; iguais=True
[I3 depois da recuperacao] arquivos=321; digital=528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5; igual_ao_original=True; residuos=[]; validacao=dados e downloads válidos
[I3 nova publicacao] PUBLICADO ['None', 'None']
[I3 residuos] []
[I4 saida] OSError: falha simulada na segunda troca
[I4 depois] arquivos=321; digital=528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5; igual_ao_original=True; residuos=[]; validacao=dados e downloads válidos
[I4 nova publicacao] PUBLICADO ['None', 'None']
[I5 digital antes] 321; 528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5
[I5 saida] RuntimeError: Falha na troca conjunta dos destinos publicados: falha simulada na segunda troca. Falha também na restauração; backups preservados em: <raiz>\dashboard\atlas\.downloads.backup-99b0031d2f794c709b195fd310b09b11, <raiz>\dashboard\atlas\.data.backup-aa16956e36084f128d4582808c08dc80
[I5 conteudo do atlas] .data.backup-aa16956e36084f128d4582808c08dc80 | .downloads.backup-99b0031d2f794c709b195fd310b09b11
[I5 recuperacao] 0.02 s
[I5 depois] arquivos=321; digital=528EDE0648C8961CA7000C9223B720ADA04E227A5F90439EC358C3F1C9EBB5D5; igual_ao_original=True; residuos=[]; validacao=dados e downloads válidos
[I5 igual_ao_original] True
```
