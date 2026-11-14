# Laboratório AWS com Terraform

Módulo mínimo e removível do laboratório. **Escrito e revisado, nunca aplicado.**
Nada aqui cria recurso até o dono aprovar custo e escopo (tarefa T06) e rodar os
comandos abaixo com a própria conta. Preparação da conta: ver
`docs/projeto-engenharia-dados/AWS-PREPARACAO.md`. Estimativa de custo:
`docs/costs.md` e `docs/benchmark/README.md`.

## O que cria

| Recurso | Para quê |
| --- | --- |
| Bucket S3 `<projeto>-<conta>` | Gold publicada, manifestos e cache da Bronze. Privado, versionado, criptografado (SSE-S3), só TLS, sem acesso público |
| Regra de ciclo de vida | Expira versões antigas (30 dias) e uploads multipart incompletos |
| Provedor OIDC do GitHub (opcional) | Autenticação sem chave de longa duração |
| Papel IAM `<projeto>-github-pipeline` | Assumido só por execuções do repositório e das branches configurados; permite `ListBucket`, `GetObject`, `PutObject` no bucket e escrita no grupo de logs. **Sem** `DeleteObject` e sem permissões administrativas |
| Grupo de logs CloudWatch | Retenção de 14 dias |
| Orçamento mensal (AWS Budgets) | Alerta por e-mail a 50%, 80% e 100% do real e 100% do previsto |

Não cria Lambda, agendamento, rede nem banco. O executor recomendado do pipeline
é o GitHub Actions agendado (`docs/benchmark/README.md`); a AWS entra como
armazenamento durável, identidade federada e observabilidade.

## Pré-requisitos

- Conta AWS com MFA no usuário raiz, orçamento e alerta já configurados à mão
  (o orçamento deste módulo é adicional) e um perfil local de acesso, sem chaves
  no repositório (`aws configure sso`).
- Terraform >= 1.6.

## Uso

```powershell
cd infra\terraform
Copy-Item terraform.tfvars.example terraform.tfvars   # ajuste os valores
$env:AWS_PROFILE = "painel-lab"
terraform init
terraform fmt -check
terraform validate
terraform plan -out lab.tfplan     # leia o plano inteiro antes de aplicar
terraform apply lab.tfplan
```

Depois do `apply`, o workflow do GitHub usa o papel (sem segredo):

```yaml
permissions:
  id-token: write
  contents: read
steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: <saída papel_github_arn>
      aws-region: <saída regiao>
```

Observações sobre o OIDC:

- A condição aceita `repo:<dono/nome>:ref:refs/heads/<branch>`. Jobs que usam
  `environment:` ganham outro `sub` (`...:environment:<nome>`) e **não** assumem este
  papel; se precisar, acrescente o padrão em `main.tf` conscientemente.
- Cada conta só pode ter um provedor OIDC por URL: se já existir, use
  `create_oidc_provider = false`.

## Remoção

`terraform destroy` remove tudo (o bucket tem `force_destroy`, incluindo versões).
Procedimento completo e verificação em
`docs/runbooks/desligar-laboratorio-aws.md`.

## Regras

- Nunca versionar `terraform.tfvars`, estado (`*.tfstate`), planos ou credenciais.
  O `.gitignore` desta pasta já bloqueia esses arquivos.
- O estado fica local no início. Se o laboratório crescer, migrar para backend
  remoto numa tarefa própria e documentada.
- `.terraform.lock.hcl` deve ser gerado por `terraform init` e versionado na
  primeira execução real (não foi possível gerá-lo sem o binário).
- Registrar em `docs/costs.md` o custo observado de cada experimento.
