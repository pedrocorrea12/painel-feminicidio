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

4. Escolha o backup de cada pasta com a função abaixo. Ela falha com uma mensagem
   clara quando não há backup (em vez de imprimir um valor vazio) e, quando há mais
   de um, mostra todos e usa o mais recente:

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
        $todos | Format-List FullName, LastWriteTime
    }
    $todos[0]
}

$nome = "data"   # depois repita com "downloads"
$destino = Join-Path $atlas $nome
$backup = Get-Backup $nome
Test-Path -LiteralPath $destino
$backup.FullName
```

5. **Pareie os backups.** Com um backup por pasta, o par é óbvio. Com mais de um, o
   "mais recente de cada pasta" pode vir de publicações diferentes. Escolha o
   `downloads` mais próximo, no tempo, do `data` e confira a diferença:

```powershell
$bd = Get-Backup "data"
$bz = Get-ChildItem -LiteralPath $atlas -Directory -Force |
    Where-Object { $_.Name -like ".downloads.backup-*" } |
    Sort-Object { [math]::Abs(($_.LastWriteTime - $bd.LastWriteTime).TotalSeconds) } |
    Select-Object -First 1
if (-not $bz) { throw "Nenhum backup de 'downloads' para formar o par." }
"data:      $($bd.FullName)  $($bd.LastWriteTime)"
"downloads: $($bz.FullName)  $($bz.LastWriteTime)"
"diferença: " + [math]::Round([math]::Abs(($bd.LastWriteTime - $bz.LastWriteTime).TotalSeconds)) + " s"
```

   Backups da mesma publicação têm horários próximos (segundos). Uma diferença de
   minutos ou mais indica publicações diferentes: **pare** e decida pelo dono. O
   horário é só uma heurística: o par só vale depois de passar na validação do par,
   na próxima seção.

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

Para comparar as árvores de uma pasta (`$destino` e `$backup` da preparação) por
caminho relativo, tamanho e SHA-256:

```powershell
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
Aplique o caso abaixo a cada pasta, com `$nome`, `$destino` e `$backup` definidos
como na preparação e o par validado na seção anterior.

### Destino ausente e backup válido

Isso indica interrupção na janela entre as duas renomeações. Restaure o backup
validado no mesmo volume:

```powershell
Move-Item -LiteralPath $backup.FullName -Destination $destino
```

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
$quarentena = Join-Path $atlas (".$nome.quarentena-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
Move-Item -LiteralPath $destino -Destination $quarentena
Move-Item -LiteralPath $backup.FullName -Destination $destino
```

Depois de restaurar as duas pastas, rode a validação do conjunto. Mantenha as
quarentenas até registrar a causa e confirmar o site restaurado.

### Uma pasta na versão nova e a outra ausente (restauração parcial)

Acontece quando a restauração automática falha no meio: por exemplo, `data` ficou
na versão **nova** (válida isoladamente) e `downloads` sumiu, com o backup de cada
pasta preservado. A versão nova de uma pasta sozinha é incoerente com o conjunto e
não deve ficar publicada. Decida pelo conjunto, voltando as duas à versão anterior:

1. Confirme o par de backups e valide-o (seções anteriores). Sem backup das duas
   pastas, **pare** e acione o dono.
2. Para a pasta que ficou na versão nova, ponha-a em quarentena (como no caso
   anterior) e restaure o backup dela.
3. Para a pasta ausente, restaure o backup (caso "Destino ausente").
4. Rode a validação do conjunto e confira que não restaram `.tmp-*` nem `.backup-*`.

Esta seção e o pareamento de vários backups foram simulados na T23, em cópia
temporária, com os mesmos scripts de `incidentes-simulados.md`: a versão nova de
`data` ao lado dos dois backups voltou ao conjunto anterior, idêntico ao original, e,
com dois backups de `downloads` (3 s e 9 dias de diferença), o pareamento escolheu o
de 3 s. Como o horário é só uma heurística, a validação do par continua obrigatória.

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
   `.downloads.quarentena-*`) sem justificativa.
3. Registre horário, comando, mensagem de erro ou aviso, caminho recuperado,
   resultado da validação e hashes comparados. Não anexe dados pessoais nem
   artefatos brutos ao registro do incidente.
