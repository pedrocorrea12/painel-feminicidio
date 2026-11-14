# Preparação para o laboratório AWS

Roteiro para quando chegar a hora da T06. **Nada aqui cria recurso ou custo.**
Regra do projeto: qualquer custo ou recurso AWS exige aprovação explícita do dono.
Credenciais nunca entram no repositório nem no chat.

## 1. O que o dono pode adiantar (sem custo)

Confira os valores de oferta gratuita e créditos na página oficial da AWS antes
de abrir a conta; eles mudam e não foram verificados aqui.

1. **Conta dedicada.** Criar uma conta AWS só para o laboratório (e-mail próprio,
   por exemplo um alias). Não reutilizar conta de trabalho.
2. **Raiz protegida.** Ativar MFA no usuário raiz, guardar a recuperação e **não
   criar chave de acesso para a raiz**. A raiz só serve para a configuração inicial.
3. **Alerta de custo antes de tudo.** Em Billing: ativar alertas de cobrança e
   criar um orçamento (AWS Budgets) mensal baixo, por exemplo US$ 5, com alerta
   por e-mail a 50%, 80% e 100%. Sugestão: orçamento "de custo real" e "previsto".
4. **Acesso do dia a dia sem raiz.** Preferir IAM Identity Center (SSO) com um
   usuário administrador do laboratório e MFA; alternativa: um usuário IAM com
   MFA. Evitar chaves de acesso de longa duração.
5. **Região.** Escolher uma e anotar. Dados são públicos e sem dado pessoal, então
   a latência não importa: `us-east-1` costuma ser a mais barata; `sa-east-1`
   (São Paulo) costuma custar mais. Recomendo `us-east-1`, salvo preferência por
   residência dos dados no Brasil.
6. **Ferramentas locais (opcional).** AWS CLI v2 e Terraform instalados. Com SSO:
   `aws configure sso` cria um perfil local; as credenciais ficam fora do repositório.

### O que me informar depois (não sensível)

- região escolhida e nome do perfil local (por exemplo `painel-lab`);
- valor do orçamento configurado;
- se prefere SSO ou usuário IAM.

**Não** me envie: chaves de acesso, senhas, códigos MFA, nem o ID da conta em
documentos versionados. Não é necessário ID de conta no repositório.

## 2. O que fazemos antes de abrir qualquer recurso (Gate B, sem custo)

Tarefa **T12 (benchmark local)**: medir tempo, memória e volume de cada etapa do
pipeline e comparar executores (local, GitHub Actions, AWS). A decisão de usar ou
não Lambda, contêiner ou só GitHub Actions sai dessas medições, não do palpite.
Detalhes na seção T12 do quadro.

## 3. O que a T06 faz (proposta pequena e removível)

Só depois do Gate B e do seu "sim" ao custo estimado:

1. **Terraform em `infra/terraform/`**, estado local no início (sem segredos no git).
2. **S3 privado** com criptografia, bloqueio de acesso público e ciclo de vida,
   para guardar a Gold publicada e manifestos de cada execução.
3. **Federação OIDC do GitHub** com IAM de menor privilégio (sem chave de longa
   duração): o workflow assume um papel restrito à branch e ao repositório.
4. **Logs** com retenção curta (CloudWatch) e **manifesto por execução**
   (versões, contagens, hashes) para diagnosticar falha.
5. **Agendamento** só se o Gate B justificar (EventBridge Scheduler com Lambda ou
   job em contêiner); caso contrário, GitHub Actions agendado continua sendo a
   alternativa válida e mais barata.
6. **`terraform destroy` documentado** e testado; registrar em `docs/costs.md` o
   custo observado e a confirmação de remoção.

## 4. Ordem recomendada

| Passo | Quem | Custo |
| --- | --- | --- |
| Conta, MFA, orçamento, região, perfil | dono | zero |
| T12 benchmark local (Gate B) | Claude | zero |
| Registrar estimativa em `docs/costs.md` e pedir seu "sim" | Claude | zero |
| T06: Terraform, S3, OIDC, logs | Claude e Codex (revisão cruzada) | centavos |
| Experimento, medição, `destroy` | Claude | centavos |
| T07: demo com métricas reais | a definir | zero |

## 5. Decisões que ficam com o dono

- região e residência dos dados;
- teto de gasto e quem recebe os alertas;
- usar ou não agendamento na AWS (comparado com GitHub Actions);
- manter o laboratório ligado ou destruí-lo após cada experimento (recomendado:
  destruir).
