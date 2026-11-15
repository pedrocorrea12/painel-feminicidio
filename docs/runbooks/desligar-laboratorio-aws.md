# Runbook: desligar o laboratório AWS

Use ao fim de cada experimento, ao estourar um alerta de orçamento ou antes de
ficar sem acompanhar a conta. O módulo está em `infra/terraform/`.

## Sintomas que pedem desligamento

- alerta de orçamento (50%, 80%, 100% ou previsão acima de 100%);
- custo inesperado em Billing / Cost Explorer;
- fim do experimento, sem necessidade do laboratório;
- credencial ou configuração suspeita.

## Estado atual do laboratório (14/11/2026)

O laboratório está **parcial**: existem bucket, grupo de logs e orçamento. Não existem
provedor OIDC, papel nem política (a organização bloqueia o OIDC; ver ADR 0002).
Assim, os passos de revogação do papel (1.3) e de verificação do provedor (3) não se
aplicam enquanto `habilitar_federacao_github = false`. O estado do Terraform está
em `infra/terraform/terraform.tfstate` do worktree de integração; sem ele use o
passo 5 (estado perdido).

## 1. Parar novas execuções

1. Desabilite **inteiramente** qualquer workflow que assuma o papel do laboratório
   (Actions > o workflow > Disable workflow), incluindo o disparo manual.
2. Confirme na aba Actions que nenhuma execução está em andamento; cancele as ativas.
3. Se a suspeita for de credencial ou configuração, **revogue já** o acesso, sem esperar
   o destroy (um plano não revoga nada): apague a política inline e o papel,
   `aws iam delete-role-policy --role-name <projeto>-github-pipeline --policy-name <projeto>-pipeline`
   e `aws iam delete-role --role-name <projeto>-github-pipeline`. O `terraform destroy`
   seguinte reconcilia o estado, pois o recurso já ausente é tratado como removido.

## 2. Destruir

```powershell
cd infra\terraform
# Credenciais temporárias do aws login (ver infra/terraform/README.md)
terraform plan -destroy -out destruir.tfplan   # confira a lista: bucket, papel, logs, orçamento
terraform apply destruir.tfplan
```

O bucket tem `force_destroy`, portanto objetos e versões são removidos. Se a Gold
publicada no bucket for necessária, **copie antes** (`aws s3 sync`); o site público
não depende dela.

## 3. Verificar que nada restou

```powershell
aws s3 ls | Select-String "dados-violencia-sc-lab"
aws iam list-roles --query "Roles[?starts_with(RoleName,'dados-violencia-sc-lab')].RoleName"
aws logs describe-log-groups --log-group-name-prefix "/dados-violencia-sc-lab"
aws budgets describe-budgets --account-id <ID_DA_CONTA> `
  --query "Budgets[?Name=='dados-violencia-sc-lab-mensal'].Name"
aws iam list-open-id-connect-providers   # só relevante se a federação estiver ligada
```

Os quatro primeiros devem voltar vazios (ajuste o prefixo se mudou `project`). Seus
outros orçamentos da conta não são do laboratório e devem permanecer. O provedor
OIDC só deve ter sumido se o módulo o criou (`create_oidc_provider = true`); se ele já
existia, permanece de propósito.

## 4. Confirmar custo

No Billing, abra Cost Explorer do mês e filtre por tag `projeto=dados-violencia-sc-lab`.
O custo pode aparecer com atraso de até 24 horas. Registre em `docs/costs.md`:
data, duração, volume processado, custo observado e a confirmação de que os
recursos foram removidos.

## 5. Se o destroy falhar

- **Erro de permissão:** confira o perfil ativo e o MFA.
- **Bucket não vazio:** rode novamente; o `force_destroy` esvazia o bucket antes.
- **Recurso criado fora do Terraform:** liste e remova à mão apenas o que tem a tag
  `projeto=dados-violencia-sc-lab`, depois execute `terraform state list` para
  checar divergência.
- **Estado perdido:** remova manualmente, nesta ordem: (1) a política inline do papel
  (`aws iam delete-role-policy`) e depois o papel; (2) o provedor OIDC, só se foi criado
  aqui; (3) o bucket, **esvaziando antes todas as versões e delete markers** (a
  exclusão manual não tem o `force_destroy` do Terraform); (4) o grupo de logs;
  (5) o orçamento do laboratório. Registre o incidente.

## Evidências a guardar

Saída do `terraform apply` de destruição, saída das verificações do passo 3 e o
registro em `docs/costs.md`. Não inclua o ID da conta nem credenciais.
