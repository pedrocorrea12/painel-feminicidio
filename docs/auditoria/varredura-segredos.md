# Varredura de segredos e dados pessoais

Data da auditoria: 16/11/2026. Referência inicial:
`tarefa/t19-fechamento-pr2` no commit `9ba8345`.

## Conclusão

Não foram encontrados segredos ativos, credenciais AWS, tokens, senhas, chaves
privadas, arquivos `.env`, estados Terraform, IDs reais de conta AWS, CPF ou
dados pessoais em nível individual nos arquivos versionados. Foi encontrado um
e-mail pessoal nos metadados Git de autoria e commit, classificado como baixa
gravidade.

## Método

A auditoria cobriu 506 arquivos rastreados e 152 commits alcançáveis por todas
as referências locais. Os valores candidatos foram processados em memória; a
saída de trabalho e este relatório contêm somente categoria, caminho, commit e
valores mascarados.

Comandos e técnicas usados:

```powershell
git ls-files
git status --ignored --short --untracked-files=all
git rev-list --all
git grep -I -i -l -E "<expressão por categoria>" HEAD --
git grep -I -i -l -E "<expressão por categoria>" (git rev-list --all) --
git log --all -p --no-color
git log --all --name-only --pretty=format:
git cat-file commit <commit>
git check-ignore -v --no-index <caminho de teste>
```

O conteúdo de `git log -p`, `git grep` e dos metadados foi filtrado antes da
exibição. Foram procurados:

- chaves AWS com prefixos `AKIA` e `ASIA`, segredos e tokens de sessão;
- tokens GitHub, Slack, OpenAI, JWT e literais genéricos de senha/token/secret;
- chaves privadas e URLs com credenciais embutidas;
- arquivos `.env`, `*.tfstate`, variáveis locais e planos Terraform;
- ARNs e sequências de 12 dígitos em contexto de conta AWS;
- e-mails, CPF com validação dos dígitos verificadores, telefones e nomes de
  campos normalmente associados a dados pessoais;
- conteúdo rastreado em `data/` e `tests/fixtures/`, inclusive cabeçalhos dos
  CSVs.

## Achados

### Alta

Sem achados.

### Média

Sem achados.

### Baixa

| Local | Commit | Evidência mascarada | Ação sugerida |
| --- | --- | --- | --- |
| Metadados Git (`author`/`committer`) | `9ba8345` como amostra; presente em 145 commits | `p***@g***.com` | Confirmar se a exposição é intencional. Para commits futuros, configurar um endereço `noreply` e a privacidade de e-mail no provedor Git. O histórico existente não foi alterado; qualquer decisão de reescrita deve ser uma tarefa separada e explícita do dono. |

O e-mail é dado pessoal, mas não é credencial e não exige revogação de acesso.

## Candidatos revisados e descartados

- `infra/terraform/README.md:55`: referências a variáveis de uma sessão
  temporária AWS; nenhum valor literal foi encontrado.
- `infra/terraform/terraform.tfvars.example:5`: endereço em domínio reservado
  para exemplos, não pertencente a uma pessoa.
- `tests/test_s3_sync.py`: identificador de 12 dígitos canônico de exemplo,
  repetido apenas em nomes sintéticos de bucket.
- `data/gold/**` e `dashboard/dist/data/**`: sequências de 11 e 12 dígitos são
  contagens, populações ou outros valores agregados; não há campos de CPF,
  e-mail, telefone ou identificação individual.
- `docs/baseline/inventario.json`: a única sequência com dígitos verificadores
  compatíveis com CPF está dentro de um SHA-256 mascarado, portanto é falso
  positivo.
- mensagens de commit: somente endereço `noreply` do agente; nenhum e-mail
  pessoal adicional, token ou segredo.

## Regras de exclusão e dados

- `.gitignore` exclui `.env`, `.env.*`, `.venv/`, `data/bronze/**` e
  `data/silver/**`, preservando apenas os respectivos READMEs.
- `infra/terraform/.gitignore` exclui `*.tfstate`, backups de estado,
  `.terraform/`, `*.tfvars`, planos e logs de falha; mantém somente o exemplo de
  variáveis.
- nenhum `.env` ou `*.tfstate` foi encontrado por nome na árvore ou no
  histórico.
- `data/` tem 54 arquivos rastreados: 52 artefatos Gold agregados e dois
  READMEs de Bronze/Silver. As 10 fixtures rastreadas são pequenas e sintéticas.

## Limitações

A busca combina expressões conhecidas, validação de CPF, inspeção de nomes e
revisão contextual. Ela não prova a ausência de um segredo com formato novo,
ofuscado ou criptografado. Nenhum valor candidato foi copiado para o relatório,
e nenhum arquivo ou histórico foi removido ou reescrito.
