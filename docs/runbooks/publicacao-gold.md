# Runbook: publicação segura da Gold do atlas

Este procedimento cobre a publicação de `dashboard/atlas/data` e
`dashboard/atlas/downloads` feita por `pipeline/build_atlas_site_data.py`. O
script gera os JSONs e os ZIPs em diretórios temporários, valida o contrato
(incluindo o conteúdo dos ZIPs) e chama
`painel_dados.publish.publicar_conjunto` para trocar as duas pastas juntas; se
qualquer etapa falhar, as duas permanecem na versão anterior. O contrato
completo está em `docs/contracts/atlas_site.md`.

## Sintomas

- `RuntimeError: Backup órfão impede publicação: ...\.data.backup-*` (ou
  `...\.downloads.backup-*`);
- `RuntimeError: Falha na troca conjunta dos destinos publicados: ...` com a lista
  de backups preservados: a restauração automática falhou, e cada backup listado
  é a versão anterior daquela pasta;
- `RuntimeWarning: Publicação concluída, mas o backup não pôde ser removido`;
- `dashboard/atlas/data` ausente após interrupção durante a troca;
- erro de validação antes da publicação (a versão anterior deve permanecer).

## Preparação segura

1. Pare novas execuções de `build_atlas_site_data.py`; não faça duas publicações
   concorrentes.
2. Feche processos que mantenham arquivos do atlas abertos.
3. Liste os backups das duas pastas, sem remover nada. `Format-List` evita que o
   caminho seja cortado em consoles estreitos:

```powershell
$atlas = (Resolve-Path "dashboard/atlas").Path
Get-ChildItem -LiteralPath $atlas -Directory -Force |
    Where-Object { $_.Name -like ".data.backup-*" -or $_.Name -like ".downloads.backup-*" } |
    Sort-Object LastWriteTime -Descending |
    Format-List FullName, LastWriteTime
```

Os dois destinos formam um conjunto: `data` e `downloads` devem voltar juntos à
mesma versão. Os passos abaixo valem para **cada pasta separadamente**; defina
`$nome` como `data` ou `downloads` e repita o procedimento para a outra.

4. Veja o backup de cada pasta com a função abaixo. Ela falha com uma mensagem
   clara quando não há backup (em vez de imprimir um valor vazio) e, quando há mais
   de um, mostra todos e devolve o mais recente. Este passo é só inspeção: o backup
   que será comparado, restaurado ou removido é o do par, definido no passo 5:

```powershell
function Get-Backup([string]$nome) {
    $todos = @(Get-ChildItem -LiteralPath $atlas -Directory -Force |
        Where-Object { $_.Name -like ".$nome.backup-*" } |
        Sort-Object LastWriteTime -Descending)
    if ($todos.Count -eq 0) {
        throw "Nenhum backup de '$nome' em $atlas. Se o destino existe e é válido, não há o que recuperar; se não existe, não improvise: pare e acione o dono."
    }
    if ($todos.Count -gt 1) {
        Write-Warning "$($todos.Count) backups de '$nome'; usando o mais recente. Confira o pareamento abaixo."
        $todos | Format-List FullName, LastWriteTime | Out-Host
    }
    $todos[0]
}

$nome = "data"   # depois repita com "downloads"
$destino = Join-Path $atlas $nome
Test-Path -LiteralPath $destino
(Get-Backup $nome).FullName
```

5. **Pareie os backups.** Com um backup por pasta, o par é óbvio. Com mais de um, o
   "mais recente de cada pasta" pode vir de publicações diferentes. Escolha o
   `downloads` mais próximo, no tempo, do `data` e confira a diferença:

```powershell
$bd = $null
$bz = $null
$bd = Get-Backup "data"
if ($bd) {
    $bz = Get-ChildItem -LiteralPath $atlas -Directory -Force |
        Where-Object { $_.Name -like ".downloads.backup-*" } |
        Sort-Object { [math]::Abs(($_.LastWriteTime - $bd.LastWriteTime).TotalSeconds) } |
        Select-Object -First 1
}
if ($bd -and $bz) {
    "data:      $($bd.FullName)  $($bd.LastWriteTime)"
    "downloads: $($bz.FullName)  $($bz.LastWriteTime)"
    "diferença: " + [math]::Round([math]::Abs(($bd.LastWriteTime - $bz.LastWriteTime).TotalSeconds)) + " s"
} else {
    Write-Warning "Par de backups incompleto: não siga para a validação do par."
}
```

   O bloco começa zerando `$bd` e `$bz` para que um valor antigo da mesma sessão não
   seja reaproveitado. Colado no console, um erro de `Get-Backup` não interrompe as
   linhas seguintes; por isso o par só é impresso quando as duas variáveis estão
   definidas. Se aparecer o aviso de par incompleto, **não siga** para a validação
   do par.

   Backups da mesma publicação têm horários próximos (segundos). Uma diferença de
   minutos ou mais indica publicações diferentes: **pare** e decida pelo dono. O
   horário é só uma heurística: o par só vale depois de passar na validação do par,
   na próxima seção.

   Se existir o backup de **uma só** pasta, o bloco acima termina no aviso de par
   incompleto. Nesse caso defina apenas a variável da pasta que tem (`$bd = Get-Backup
   "data"` **ou** `$bz = Get-Backup "downloads"`), deixe a outra nula e use os
   comandos de "uma só pasta" da próxima seção.

## Validar destino e backup

Valide o conjunto atual (dados e ZIPs): confere o contrato, o tamanho, a integridade
e a contagem de linhas de cada ZIP.

```powershell
.venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'dashboard/atlas/data', r'dashboard/atlas/downloads'); print('dados e downloads válidos')"
```

Para validar a versão anterior, passe o par de backups escolhido no passo 5:

```powershell
.venv\Scripts\python -c "import sys; from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(sys.argv[1], sys.argv[2]); print('backups válidos')" $bd.FullName $bz.FullName
```

Se existir o backup de **uma só** pasta (por exemplo, só `.data.backup-*`), valide-o
com a outra pasta **atual** (a que não foi trocada):

```powershell
# só existe o backup de data: usa o downloads atual
.venv\Scripts\python -c "import sys; from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(sys.argv[1], r'dashboard/atlas/downloads'); print('backup de data válido')" $bd.FullName

# só existe o backup de downloads: usa o data atual
.venv\Scripts\python -c "import sys; from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'dashboard/atlas/data', sys.argv[1]); print('backup de downloads válido')" $bz.FullName
```

Isso só vale se a pasta atual for a da mesma versão do backup (por exemplo, o
backup órfão de uma publicação que já terminou); confira com a comparação abaixo.

Para comparar as árvores de uma pasta por caminho relativo, tamanho e SHA-256, use
o backup **do par** (`$bd` para `data`, `$bz` para `downloads`), que é o mesmo que
a seção "Recuperar" restaura ou remove. O mais recente da pasta, mostrado no passo
4, pode ser outro quando há vários backups:

```powershell
$nome = "data"   # depois repita com "downloads"
$destino = Join-Path $atlas $nome
$backup = if ($nome -eq "data") { $bd } else { $bz }
if (-not $backup) { Write-Warning "Sem backup de '$nome' no par: não há o que comparar." }
$backup.FullName   # confira: é o caminho exato que passou na validação

function Get-Retrato([string]$raiz) {
    $resolvida = (Resolve-Path -LiteralPath $raiz).Path
    Get-ChildItem -LiteralPath $resolvida -Recurse -File | ForEach-Object {
        [pscustomobject]@{
            Caminho = $_.FullName.Substring($resolvida.Length).TrimStart('\')
            Bytes   = $_.Length
            SHA256  = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
        }
    }
}

$atual = Get-Retrato $destino
$anterior = Get-Retrato $backup.FullName
Compare-Object $atual $anterior -Property Caminho, Bytes, SHA256
```

Uma diferença pode ser esperada (por exemplo, `atualizado_em`), mas deve ser
explicada antes de qualquer remoção.

## Recuperar

Decida pelo **conjunto**: nunca deixe `data` de uma versão com `downloads` de outra.
**Não mova nenhuma pasta antes de o par de backups ter passado na validação da
seção anterior.**

O backup mais recente de uma pasta pode não ser o do par validado quando há vários.
Antes de recuperar, aponte `$backup` para o backup que foi **validado e comparado**
(`$bd` para `data`, `$bz` para `downloads`), como na comparação da seção anterior:

```powershell
$nome = "data"   # depois repita com "downloads"
$destino = Join-Path $atlas $nome
$backup = if ($nome -eq "data") { $bd } else { $bz }
$backup.FullName   # confira: é o caminho exato que passou na validação
```

Aplique o caso abaixo a cada pasta, com `$nome`, `$destino` e `$backup` assim
definidos.

Toda movimentação de pasta deste runbook usa as duas funções abaixo.

- `Move-Pasta` renomeia a pasta inteira de uma vez (`[System.IO.Directory]::Move`,
  a mesma operação de renomeação que a publicação usa). Se algum arquivo da pasta
  estiver aberto por outro processo, a renomeação falha **sem mover nada**. Não
  troque por `Move-Item`: no Windows PowerShell 5.1 ele move arquivo por arquivo e,
  ao falhar no arquivo aberto, deixa a pasta dividida entre a origem e o destino.
- `Restore-Backup` **não move nada** se o destino ainda existir: mover um backup
  para um destino existente não substitui a pasta e pode pôr o backup **dentro**
  dela (`data\.data.backup-*`), onde a listagem da preparação não o encontra.

Quarentena, backup e destino ficam todos sob `$atlas`, portanto no mesmo volume, e
a renomeação nunca atravessa volumes. Não troque o alvo por uma pasta de outra
unidade: entre volumes diferentes `[System.IO.Directory]::Move` falha sem mover
nada, com o motivo na `Causa:` da mensagem.

```powershell
function Move-Pasta([string]$origem, [string]$alvo, [string]$etapa) {
    $ErrorActionPreference = 'Stop'
    try {
        [System.IO.Directory]::Move($origem, $alvo)
    } catch {
        $causa = $_.Exception.GetBaseException().Message
        if ((Test-Path -LiteralPath $origem) -and -not (Test-Path -LiteralPath $alvo)) {
            throw "$etapa falhou e nada foi movido: $origem continua inteira e $alvo não foi criada. Veja 'Se a restauração parar' no runbook. Causa: $causa"
        }
        throw "$etapa falhou em estado inesperado (origem: $origem; alvo: $alvo). Não repita o bloco: pare e acione o dono. Causa: $causa"
    }
}

function Restore-Backup($backup, [string]$destino) {
    $ErrorActionPreference = 'Stop'
    if (-not $backup) {
        throw "Backup não definido para $destino. Nada foi movido."
    }
    if (-not (Test-Path -LiteralPath $backup.FullName)) {
        throw "Backup ausente: $($backup.FullName). Nada foi movido. Se $destino já foi restaurado por uma execução anterior, não há o que repetir."
    }
    if (Test-Path -LiteralPath $destino) {
        throw "Destino ainda existe: $destino. O backup não foi movido. Veja 'Se a restauração parar' no runbook."
    }
    Move-Pasta $backup.FullName $destino "Restauração de $destino"
}
```

Os blocos com mais de um passo vêm dentro de `& { ... }` e começam com
`$ErrorActionPreference = 'Stop'`: mesmo colados no console, param no primeiro erro
de qualquer comando, em vez de seguir para a linha seguinte. A preferência vale só
dentro do bloco (e dentro das duas funções); a da sessão do operador não muda.

### Se a restauração parar

Cada mensagem diz qual etapa parou. Nenhuma delas deixa pasta pela metade: a
quarentena e a restauração movem a pasta inteira ou não movem nada. As mensagens
abaixo são todas as que as funções e os blocos da seção "Recuperar" emitem.

**Leia a `Causa:` antes de repetir** qualquer bloco que parou em `falhou e nada foi
movido`. Repetir só resolve quando a causa é acesso negado ou arquivo em uso por
outro processo, o que inclui um terminal ou programa com a pasta (ou uma subpasta
dela) como diretório atual: feche o processo, ou saia da pasta, e repita. Qualquer
outra causa (caminho inválido ou não encontrado, permissão que continua negada sem
nenhum processo usando a pasta, volumes diferentes) não se resolve repetindo:
**pare** e acione o dono.

Etapa que falhou:

- **`Quarentena de '...' falhou e nada foi movido`**: o **destino** não pôde ser
  renomeado. Ele continua inteiro no lugar e o backup, intacto ao lado. O caso comum
  é um arquivo do destino aberto por outro processo (passo 2 da preparação). Se a
  `Causa:` for essa, libere a pasta e rode o mesmo bloco de novo; senão, pare.
- **`Restauração de ... falhou e nada foi movido`**: o **backup** não pôde ser
  renomeado. Ele continua inteiro; o destino **não existe** (se o bloco tinha
  quarentena, ela já levou a pasta inteira). Não mova o backup à mão, nem arquivo por
  arquivo. O caso comum é um arquivo do backup aberto por outro processo. Se a
  `Causa:` for essa, libere a pasta e rode o mesmo bloco de novo: ele avisa que o
  destino está ausente, não cria outra quarentena e só restaura o backup. Senão,
  pare.
- **`falhou em estado inesperado`**: depois da falha, a origem e o alvo não estão
  como deveriam. Não repita o bloco. Liste os resíduos com o comando da seção
  "Encerramento e evidências", **pare** e acione o dono.

Conferência que parou antes de mover (a mensagem termina dizendo que nada, ou que o
backup, não foi movido):

- **`Defina $nova`**: `$nova` não é `data` nem `downloads`. Corrija a variável e
  rode o bloco de novo.
- **`Par de backups não definido`**: `$bd` ou `$bz` está nulo. Refaça o pareamento
  (passo 5 da preparação) e a validação do par. Se só uma pasta tem backup, este não
  é o caso de restauração parcial: **pare** e acione o dono.
- **`Backup não definido para`**: `$backup` está nulo. Defina `$nome`, `$destino` e
  `$backup` com o bloco do início de "Recuperar" e repita o comando.
- **`Backup de '...' não definido ou ausente`** (bloco "Destino inválido e backup
  válido"): se você está repetindo o bloco depois de ele ter terminado sem erro, a
  pasta já foi restaurada e não há o que repetir; confirme que o destino existe e
  que há uma quarentena `.<nome>.quarentena-*` e siga para a validação do conjunto.
  Na primeira execução, `$backup` está nulo ou aponta para um backup que não existe
  mais (variável antiga da sessão): refaça o passo 5 e a validação antes de repetir.
- **`Backup ausente: ...`**: o backup indicado não existe. A mensagem **não** prova
  que a pasta já foi restaurada; confira antes de seguir.
  - No bloco da restauração parcial, a saída a seguir só vale se a execução anterior
    **deste mesmo bloco** parou em `Restauração de ... falhou e nada foi movido` na
    **outra** pasta. Confirme com o comando de resíduos de "Encerramento e
    evidências" e olhando as pastas: a pasta do backup ausente está no lugar, a outra
    pasta está ausente com o backup dela intacto e, se a pasta nova existia quando o
    bloco começou, há uma quarentena `.<nova>.quarentena-*`. Confirmado isso, conclua
    a outra pasta por "Destino ausente e backup válido", com `$nome`, `$destino` e
    `$backup` apontados para ela, e rode a validação do conjunto.
  - Se a mensagem saiu na **primeira** execução do bloco, ou se a conferência acima
    não fecha, `$bd` ou `$bz` aponta para um backup que não existe mais (variável
    antiga da sessão, validação do par pulada). **Não** restaure só a outra pasta:
    ficaria uma pasta na versão nova e a outra na anterior, o conjunto misto que este
    runbook proíbe. Refaça o passo 5 e a validação do par; sem backup das duas
    pastas, **pare** e acione o dono.
  - No comando de "Destino ausente e backup válido": se o destino existe porque você
    acabou de restaurá-lo, não há o que repetir; se não existe, `$backup` está
    desatualizado: refaça o passo 5.
- **`Destino ainda existe`**: o backup não foi movido. Dentro de um bloco com
  quarentena isso não deveria acontecer; confira `$nome`, `$destino` e `$backup` e se
  não há uma publicação rodando (passo 1 da preparação).
- **`A pasta '...' existe`**: a outra pasta está no lugar, então este não é o caso de
  restauração parcial. Não insista no bloco: valide o conjunto atual e escolha o caso
  pelo estado de cada pasta ("Destino existente e válido" ou "Destino inválido e
  backup válido").
- **`Quarentena já existe`**: o bloco foi repetido no mesmo segundo. Rode de novo.

Aviso, que não para o bloco:

- **`Destino ausente (já está em quarentena?)`**: o destino não existe, então o bloco
  não cria quarentena e só restaura. É o esperado ao repetir depois de uma
  restauração que falhou. Na primeira execução do bloco "Destino inválido e backup
  válido", significa que o caso era "Destino ausente e backup válido"; o resultado é
  o mesmo.

Qualquer outro erro: nada mais foi executado depois dele. Não repita o bloco. Liste
os resíduos com o comando da seção "Encerramento e evidências" e, se o estado não
corresponder a nenhum caso deste runbook, **pare** e acione o dono.

### Destino ausente e backup válido

Isso indica interrupção na janela entre as duas renomeações. Restaure o backup
validado no mesmo volume:

```powershell
Restore-Backup $backup $destino
```

Se parar com `Restauração de ... falhou e nada foi movido`, leia a `Causa:`: se for
arquivo em uso ou acesso negado (um arquivo do backup aberto, ou um terminal com a
pasta como diretório atual), libere a pasta e repita o comando; se for outra, pare
(veja "Se a restauração parar").

Depois de restaurar as duas pastas, rode a validação do conjunto (acima).

### Destino existente e válido

Se o destino é a versão desejada, o backup é apenas resíduo de limpeza. Depois
de validar e comparar as duas árvores, remova somente o caminho exato exibido:

```powershell
Remove-Item -LiteralPath $backup.FullName -Recurse
```

Nunca use curinga em `Remove-Item` e nunca remova um backup que ainda não foi
validado e comparado.

### Destino inválido e backup válido

Preserve o destino para diagnóstico e restaure o backup:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    if (-not $backup -or -not (Test-Path -LiteralPath $backup.FullName)) {
        throw "Backup de '$nome' não definido ou ausente. Nada foi movido."
    }
    if (Test-Path -LiteralPath $destino) {
        $quarentena = Join-Path $atlas (".$nome.quarentena-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
        if (Test-Path -LiteralPath $quarentena) {
            throw "Quarentena já existe: $quarentena. Nada foi movido."
        }
        Move-Pasta $destino $quarentena "Quarentena de '$nome'"
    } else {
        Write-Warning "Destino ausente (já está em quarentena?): $destino. Só o backup será restaurado."
    }
    Restore-Backup $backup $destino
}
```

Se o bloco parar, veja "Se a restauração parar". O bloco pode ser repetido: se a
quarentena já tirou o destino e a restauração falhou, a repetição só restaura.

Depois de restaurar as duas pastas, rode a validação do conjunto. Mantenha as
quarentenas até registrar a causa e confirmar o site restaurado.

### Uma pasta na versão nova e a outra ausente (restauração parcial)

Acontece quando a restauração automática falha no meio: por exemplo, `data` ficou
na versão **nova** (válida isoladamente) e `downloads` sumiu, com o backup de cada
pasta preservado. A versão nova de uma pasta sozinha é incoerente com o conjunto e
não deve ficar publicada. Decida pelo conjunto, voltando as duas à versão anterior:

1. Confirme o par de backups e valide-o (seções anteriores). Sem backup das duas
   pastas, **pare** e acione o dono.
2. Ponha em quarentena a pasta que ficou na versão nova e restaure as duas pastas a
   partir do par validado (`$bd` e `$bz`):

```powershell
$nova = "data"   # a pasta que ficou na versão nova; use "downloads" se for o caso
& {
    $ErrorActionPreference = 'Stop'
    if ($nova -ne "data" -and $nova -ne "downloads") {
        throw 'Defina $nova como "data" ou "downloads". Nada foi movido.'
    }
    if (-not $bd -or -not $bz) {
        throw "Par de backups não definido. Nada foi movido."
    }
    foreach ($b in $bd, $bz) {
        if (-not (Test-Path -LiteralPath $b.FullName)) {
            throw "Backup ausente: $($b.FullName). Nada foi movido. Se este bloco já restaurou essa pasta e parou na outra, veja 'Se a restauração parar' no runbook."
        }
    }
    $outra = if ($nova -eq "data") { "downloads" } else { "data" }
    if (Test-Path -LiteralPath (Join-Path $atlas $outra)) {
        throw "A pasta '$outra' existe: este não é o caso de restauração parcial. Nada foi movido."
    }
    $destinoNova = Join-Path $atlas $nova
    if (Test-Path -LiteralPath $destinoNova) {
        $quarentena = Join-Path $atlas (".$nova.quarentena-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
        if (Test-Path -LiteralPath $quarentena) {
            throw "Quarentena já existe: $quarentena. Nada foi movido."
        }
        Move-Pasta $destinoNova $quarentena "Quarentena de '$nova'"
    } else {
        Write-Warning "Destino ausente (já está em quarentena?): $destinoNova. Só os backups serão restaurados."
    }
    Restore-Backup $bd (Join-Path $atlas "data")
    Restore-Backup $bz (Join-Path $atlas "downloads")
}
```

   O bloco confere tudo antes de mover: se a **outra** pasta existir, o diagnóstico
   está errado (não é este caso) e nada é movido. Se o bloco parar, veja "Se a
   restauração parar": parando antes de restaurar `data`, ele pode ser repetido;
   parando em `downloads` com `data` já restaurada, a repetição responde `Backup
   ausente` e a saída é o caso "Destino ausente e backup válido" para `downloads`.
   `Backup ausente` na **primeira** execução é outra coisa (`$bd` ou `$bz`
   desatualizado): não restaure só uma pasta; veja a entrada dessa mensagem em "Se a
   restauração parar".

3. Rode a validação do conjunto e confira que não restaram `.tmp-*` nem `.backup-*`
   com o comando da seção "Encerramento e evidências". Mantenha a quarentena até
   registrar a causa e confirmar o site restaurado.

Esta seção e o pareamento de vários backups foram simulados na T23, em cópia
temporária, com os mesmos scripts de `incidentes-simulados.md`: a versão nova de
`data` ao lado dos dois backups voltou ao conjunto anterior, idêntico ao original, e,
com dois backups de `downloads` (3 s e 9 dias de diferença), o pareamento escolheu o
de 3 s. Como o horário é só uma heurística, a validação do par continua obrigatória.

Na T26 os blocos deste runbook foram reexecutados em cópias temporárias (Windows
PowerShell 5.1) com um arquivo mantido aberto por outro processo, ora no destino,
ora dentro do backup: em todos os casos o bloco parou sem deixar pasta pela metade
e, liberado o arquivo, o caminho indicado em "Se a restauração parar" devolveu o
conjunto anterior, idêntico ao original, com uma só quarentena por pasta e nenhum
backup aninhado.

## Interpretar `RuntimeWarning`

O aviso sobre backup não removido ocorre **depois** que a nova versão foi
instalada. A publicação terminou, e `ResultadoPublicacao.backup_remanescente`
informa o resíduo. Não repita a publicação imediatamente: valide o destino,
compare-o com o backup e siga o caso "Destino existente e válido". Enquanto o
backup existir, a próxima publicação será bloqueada de propósito.

## Janela sem destino no Windows

A troca de cada pasta usa duas renomeações no mesmo volume: `data` (ou `downloads`)
vira backup e o temporário vira a pasta. Entre elas há um intervalo curto em que
`dashboard/atlas/data` (ou `downloads`) não existe; portanto, a operação não é atômica em sentido estrito no Windows. Uma
interrupção nessa janela deixa o backup para restauração. Execute a publicação
sem concorrência e, quando possível, fora de uma janela de acesso intenso.

## Encerramento e evidências

1. Rode `pipeline/validate_project.py` no ambiente que possui a Silver local.
2. Confirme que não restaram `.data.tmp-*`, `.data.backup-*`, `.downloads.tmp-*`,
   `.downloads.backup-*` nem quarentenas (`.data.quarentena-*`,
   `.downloads.quarentena-*`) sem justificativa. O comando abaixo lista todos
   eles, inclusive dentro de `data` e de `downloads` (um backup aninhado por engano
   não aparece na listagem da preparação); saída vazia significa que não há resíduo:

```powershell
Get-ChildItem -LiteralPath $atlas -Directory -Force -Recurse |
    Where-Object { $_.Name -match '^\.(data|downloads)\.(tmp|backup|quarentena)-' } |
    Format-List FullName, LastWriteTime
```

3. Registre horário, comando, mensagem de erro ou aviso, caminho recuperado,
   resultado da validação e hashes comparados. Não anexe dados pessoais nem
   artefatos brutos ao registro do incidente.
