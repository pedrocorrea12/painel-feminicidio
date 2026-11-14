# ADR 0002 Publicação na AWS por login local, sem federação OIDC

## Status

Aceita em 14 de novembro de 2026.

## Contexto

O laboratório AWS (`infra/terraform/`, tarefa T14) foi desenhado para que o
GitHub Actions publicasse a Gold no S3 por federação OIDC: um provedor de
identidade do GitHub, um papel de menor privilégio restrito ao repositório e à
branch, e nenhuma chave de acesso guardada no GitHub.

Ao aplicar o plano numa conta do plano gratuito (região `us-east-2`), a criação do
provedor falhou com `AccessDenied` e a mensagem "explicit deny in a service control
policy": a organização que contém a conta nega `iam:CreateOpenIDConnectProvider`.
O papel e a política dependem do provedor e também não foram criados. O restante
(bucket S3 privado, versionado e criptografado; grupo de logs; orçamento) foi
criado normalmente. A SCP é definida pela organização, não pelo dono da conta, e
não pode ser alterada por ele.

## Decisão

1. Não contornar a SCP.
2. Não criar chave de acesso de longa duração para o GitHub Actions: isso
   reintroduz o risco que a federação existia para evitar e provavelmente também
   seria bloqueado.
3. Publicar pela sessão local do dono, com credenciais temporárias (`aws login`),
   usando o bucket já criado. O procedimento fica no runbook
   `docs/runbooks/publicar-gold-na-aws.md` (tarefa T16).
4. Manter o desenho OIDC no Terraform, desligado pela variável
   `habilitar_federacao_github = false`. Com ela desligada o plano contra a conta
   real não propõe nenhuma mudança.
5. A CI do GitHub continua rodando testes e lint, sem acesso à AWS.

## Alternativas consideradas

- Usuário IAM com chave de acesso no GitHub: rejeitada por segurança (credencial
  fixa) e porque a mesma SCP pode bloqueá-la.
- Pedir a remoção da SCP: fora do controle do dono em conta do plano gratuito.
- Desfazer o laboratório inteiro: rejeitada; perderia a evidência de nuvem real
  (bucket privado com controles de segurança, orçamento e runbook de desligamento).
- Trocar de provedor de nuvem: sem ganho; o problema é a política da conta.

## Consequências

- A publicação na AWS passa a ser um passo manual do dono, deliberado e
  registrado, com credencial que expira.
- O GitHub Actions não escreve na AWS; o que a CI prova continua valendo (testes,
  contratos, lint, e, na T17, `fmt` e `validate` do Terraform).
- O código de federação permanece testado por `validate`, mas **não foi
  aplicado**; só uma conta sem a restrição confirmaria o fluxo completo.
- A conta do plano gratuito expira em 14/05/2027: o laboratório deve ser
  desligado (`docs/runbooks/desligar-laboratorio-aws.md`) ou documentado como
  encerrado antes disso.

## Caminho de volta

Em uma conta sem a SCP: `habilitar_federacao_github = true` (e
`create_oidc_provider = false` se o provedor já existir), `terraform plan`,
revisar e aplicar; depois usar `role-to-assume` com a saída `papel_github_arn`.
