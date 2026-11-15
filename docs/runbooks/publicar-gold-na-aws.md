# Publicar a Gold na AWS

Este procedimento publica uma execução da camada Gold em
`s3://<bucket>/gold/<id-execucao>/`. A publicação usa uma sessão temporária do
AWS CLI, começa sempre com simulação e não remove objetos já existentes.

## Pré-requisitos

- AWS CLI v2 instalado e acesso autorizado à conta do laboratório;
- pacote do projeto instalado na `.venv`;
- Gold validada em `data/gold/`;
- nome do bucket criado pelo Terraform;
- PowerShell aberto na raiz do repositório.

Não crie access keys de longa duração. Não registre credenciais, identificador
da conta ou saída sensível no repositório.

## 1. Abrir uma sessão temporária

Autentique o perfil local e confirme a identidade antes de publicar:

```powershell
aws login --profile painel-lab
aws sts get-caller-identity --profile painel-lab
```

Defina o bucket e um identificador imutável para a execução. Se o estado local
do Terraform estiver disponível, o nome do bucket pode ser consultado com
`terraform -chdir=infra/terraform output -raw bucket_name`.

```powershell
$bucket = "NOME-DO-BUCKET"
$execucao = "{0:yyyyMMddTHHmmssZ}-{1}" -f `
  (Get-Date).ToUniversalTime(), (git rev-parse --short HEAD)
$env:PAINEL_BUCKET = $bucket
$env:PAINEL_EXECUCAO = $execucao
```

## 2. Simular a publicação

O modo padrão é dry-run. Ele cria `data/gold/manifesto.json`, com tamanho e
SHA-256 de cada artefato, e apenas mostra o que o AWS CLI enviaria:

```powershell
.venv\Scripts\python -c "import os; from pathlib import Path; from painel_dados.s3_sync import sincronizar_gold; r = sincronizar_gold(Path('data/gold'), os.environ['PAINEL_BUCKET'], os.environ['PAINEL_EXECUCAO'], perfil='painel-lab'); print(r.processo.stdout)"
```

Confira se o destino exibido é exatamente
`s3://$bucket/gold/$execucao/`. O comando gerado nunca usa `--delete`. Pare se
a origem, o bucket ou o prefixo não forem os esperados.

## 3. Publicar

Após revisar o dry-run, execute a mesma operação com `simulacao=False`:

```powershell
.venv\Scripts\python -c "import os; from pathlib import Path; from painel_dados.s3_sync import sincronizar_gold; r = sincronizar_gold(Path('data/gold'), os.environ['PAINEL_BUCKET'], os.environ['PAINEL_EXECUCAO'], perfil='painel-lab', simulacao=False); print(r.processo.stdout)"
```

Não reutilize um identificador de execução. Um prefixo novo preserva a versão
anterior e simplifica a reversão.

## 4. Verificar a publicação

Liste os objetos e confirme a presença do manifesto:

```powershell
aws s3 ls "s3://$bucket/gold/$execucao/" --recursive --profile painel-lab
$verificacao = Join-Path $env:TEMP "painel-gold-$execucao"
New-Item -ItemType Directory -Force -Path $verificacao | Out-Null
aws s3 cp "s3://$bucket/gold/$execucao/manifesto.json" `
  "$verificacao\manifesto.json" --profile painel-lab
Get-FileHash data/gold/manifesto.json, "$verificacao\manifesto.json" `
  -Algorithm SHA256
```

Os dois hashes do manifesto devem ser iguais. Confira também no JSON a
quantidade de arquivos, o total de bytes e os SHA-256 dos artefatos. Guarde
como evidência apenas o identificador da execução, o URI do prefixo, a listagem
sem dados sensíveis e o hash do manifesto.

## 5. Reverter uma publicação

Enquanto consumidores ainda não apontarem para a execução nova, basta manter
ou restaurar a referência ao prefixo da última execução válida. Se uma chave
tiver sido sobrescrita, localize as versões preservadas pelo versionamento do
bucket:

```powershell
aws s3api list-object-versions --bucket $bucket `
  --prefix "gold/$execucao/" --profile painel-lab --output table
```

Recupere cada versão necessária em um diretório temporário, valide-a contra o
manifesto correspondente e só então envie-a novamente:

```powershell
aws s3api get-object --bucket $bucket --key "CAMINHO-DA-CHAVE" `
  --version-id "ID-DA-VERSAO" "$verificacao\artefato-restaurado" `
  --profile painel-lab
```

Nunca use `--delete` para reverter. Se a publicação nova estiver inválida,
registre o incidente antes de removê-la.

## 6. Limpar e encerrar

Para remover somente um prefixo de execução comprovadamente inválido:

```powershell
aws s3 rm "s3://$bucket/gold/$execucao/" --recursive --profile painel-lab
Remove-Item -LiteralPath data/gold/manifesto.json -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $verificacao -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item Env:PAINEL_BUCKET, Env:PAINEL_EXECUCAO -ErrorAction SilentlyContinue
```

O versionamento pode manter versões não atuais, que serão tratadas pela
política de ciclo de vida. A sessão de `aws login` é temporária e deve expirar;
não a substitua por credenciais permanentes.

Quando o laboratório não for mais necessário, siga o runbook
[Desligar o laboratório AWS](desligar-laboratorio-aws.md).
