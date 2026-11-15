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
3. Liste o destino e todos os backups, sem remover nada:

```powershell
$atlas = (Resolve-Path "dashboard/atlas").Path
$destino = Join-Path $atlas "data"
$backups = Get-ChildItem -LiteralPath $atlas -Directory | Where-Object { $_.Name -like ".data.backup-*" -or $_.Name -like ".downloads.backup-*" }
$backups | Select-Object FullName, LastWriteTime
Test-Path -LiteralPath $destino
```

Se houver mais de um backup, trate cada um individualmente e preserve o mais
recente até concluir a recuperação.

## Validar destino e backup

Valide o destino, quando existir, e cada candidato a backup. Para o diretório de
dados, a validação confere que os ZIPs do manifesto existem em `downloads/`. Para
validar a fundo os ZIPs (íntegros, com o CSV esperado e linhas e bytes iguais aos
do manifesto), passe também o diretório de downloads (ou o backup
`.downloads.backup-*`):

```powershell
.venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'dashboard/atlas/data', r'dashboard/atlas/downloads'); print('dados e downloads válidos')"
```

Os comandos abaixo validam a pasta de dados:

```powershell
.venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'dashboard/atlas/data'); print('destino válido')"

# Substitua pelo caminho exato listado na etapa anterior.
$backup = $backups | Sort-Object LastWriteTime -Descending | Select-Object -First 1
.venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'$($backup.FullName)'); print('backup válido')"
```

Para comparar as árvores por caminho relativo, tamanho e SHA-256:

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

### Destino ausente e backup válido

Isso indica interrupção na janela entre as duas renomeações. Restaure o backup
validado no mesmo volume:

```powershell
Move-Item -LiteralPath $backup.FullName -Destination $destino
.venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'dashboard/atlas/data'); print('restauração validada')"
```

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
$quarentena = Join-Path $atlas (".data.quarentena-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
Move-Item -LiteralPath $destino -Destination $quarentena
Move-Item -LiteralPath $backup.FullName -Destination $destino
.venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'dashboard/atlas/data'); print('restauração validada')"
```

Mantenha a quarentena até registrar a causa e confirmar o site restaurado.

## Interpretar `RuntimeWarning`

O aviso sobre backup não removido ocorre **depois** que a nova versão foi
instalada. A publicação terminou, e `ResultadoPublicacao.backup_remanescente`
informa o resíduo. Não repita a publicação imediatamente: valide o destino,
compare-o com o backup e siga o caso "Destino existente e válido". Enquanto o
backup existir, a próxima publicação será bloqueada de propósito.

## Janela sem destino no Windows

A troca usa duas renomeações no mesmo volume: `data` vira backup e o temporário
vira `data`. Entre elas há um intervalo curto em que `dashboard/atlas/data` não
existe; portanto, a operação não é atômica em sentido estrito no Windows. Uma
interrupção nessa janela deixa o backup para restauração. Execute a publicação
sem concorrência e, quando possível, fora de uma janela de acesso intenso.

## Encerramento e evidências

1. Rode `pipeline/validate_project.py` no ambiente que possui a Silver local.
2. Confirme que não restaram `.data.tmp-*`, `.data.backup-*` nem quarentenas sem
   justificativa.
3. Registre horário, comando, mensagem de erro ou aviso, caminho recuperado,
   resultado da validação e hashes comparados. Não anexe dados pessoais nem
   artefatos brutos ao registro do incidente.
