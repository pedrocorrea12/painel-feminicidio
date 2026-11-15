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
3. Liste os backups das duas pastas, sem remover nada:

```powershell
$atlas = (Resolve-Path "dashboard/atlas").Path
Get-ChildItem -LiteralPath $atlas -Directory | Where-Object { $_.Name -like ".data.backup-*" -or $_.Name -like ".downloads.backup-*" } | Select-Object FullName, LastWriteTime
```

Os dois destinos formam um conjunto: `data` e `downloads` devem voltar juntos à
mesma versão. Os passos abaixo valem para **cada pasta separadamente**; defina
`$nome` como `data` ou `downloads` e repita o procedimento para a outra. Se houver
mais de um backup da mesma pasta, trate cada um individualmente e preserve o mais
recente até concluir a recuperação.

```powershell
$nome = "data"   # depois repita com "downloads"
$destino = Join-Path $atlas $nome
$backup = Get-ChildItem -LiteralPath $atlas -Directory | Where-Object { $_.Name -like ".$nome.backup-*" } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Test-Path -LiteralPath $destino
$backup.FullName
```

## Validar destino e backup

Valide o conjunto atual (dados e ZIPs): confere o contrato, o tamanho, a integridade
e a contagem de linhas de cada ZIP.

```powershell
.venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'dashboard/atlas/data', r'dashboard/atlas/downloads'); print('dados e downloads válidos')"
```

Para validar a versão anterior, monte o par de backups (`.data.backup-*` com
`.downloads.backup-*`) e passe os dois caminhos exatos:

```powershell
.venv\Scripts\python -c "from painel_dados.contracts.atlas_site import validar_diretorio_site; validar_diretorio_site(r'<backup de data>', r'<backup de downloads>'); print('backups válidos')"
```

Para comparar as árvores de uma pasta (`$destino` e `$backup` do passo anterior) por
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
como na preparação.

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
