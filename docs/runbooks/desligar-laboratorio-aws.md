# Runbook: desligar o laboratório AWS

Use ao fim de cada experimento, ao estourar um alerta de orçamento ou antes de
ficar sem acompanhar a conta. O módulo está em `infra/terraform/`.

## Sintomas que pedem desligamento

- alerta de orçamento (50%, 80%, 100% ou previsão acima de 100%);
- custo inesperado em Billing / Cost Explorer;
- fim do experimento, sem necessidade do laboratório;
- credencial ou configuração suspeita.

## 1. Parar novas execuções

Desative ou remova qualquer workflow agendado que assuma o papel do laboratório
(`workflow_dispatch` manual não precisa ser removido). Confirme na aba Actions que
nenhuma execução está em andamento.

## 2. Destruir

```powershell
cd infra\terraform
$env:AWS_PROFILE = "painel-lab"
terraform plan -destroy -out destruir.tfplan   # confira a lista: bucket, papel, logs, orçamento
terraform apply destruir.tfplan
```

O bucket tem `force_destroy`, portanto objetos e versões são removidos. Se a Gold
publicada no bucket for necessária, **copie antes** (`aws s3 sync`); o site público
não depende dela.

## 3. Verificar que nada restou

```powershell
aws s3 ls | Select-String "painel-feminicidio-lab"
aws iam list-roles --query "Roles[?starts_with(RoleName,'painel-feminicidio-lab')].RoleName"
aws logs describe-log-groups --log-group-name-prefix "/painel-feminicidio-lab"
aws budgets describe-budgets --account-id <ID_DA_CONTA>
```

Todos devem voltar vazios. O provedor OIDC só é removido se o módulo o criou
(`create_oidc_provider = true`); se ele já existia, permanece de propósito.

## 4. Confirmar custo

No Billing, abra Cost Explorer do mês e filtre por tag `projeto=painel-feminicidio-lab`.
O custo pode aparecer com atraso de até 24 horas. Registre em `docs/costs.md`:
data, duração, volume processado, custo observado e a confirmação de que os
recursos foram removidos.

## 5. Se o destroy falhar

- **Erro de permissão:** confira o perfil ativo e o MFA.
- **Bucket não vazio:** rode novamente; o `force_destroy` esvazia o bucket antes.
- **Recurso criado fora do Terraform:** liste e remova à mão apenas o que tem a tag
  `projeto=painel-feminicidio-lab`, depois execute `terraform state list` para
  checar divergência.
- **Estado perdido:** remova manualmente na ordem papel → provedor OIDC (se criado
  aqui) → bucket → logs → orçamento, e registre o incidente.

## Evidências a guardar

Saída do `terraform apply` de destruição, saída das verificações do passo 3 e o
registro em `docs/costs.md`. Não inclua o ID da conta nem credenciais.
