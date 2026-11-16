# AGENTS.md: regras de convivência entre agentes

Este repositório é trabalhado por mais de um agente (Claude e Codex) sob
orientação do dono do projeto. O repositório é o quadro de tarefas:
`docs/projeto-engenharia-dados/TAREFAS.md` diz quem faz o quê. Plano geral em
`docs/projeto-engenharia-dados/README.md`, arquitetura em `docs/architecture.md`
e decisões em `docs/adr/`.

## Regras

1. **Uma branch por tarefa**, criada a partir de `engenharia-dados`, com o nome
   indicado em `TAREFAS.md` (ex.: `tarefa/t03-contratos-sinan`). Nunca commitar
   direto em `engenharia-dados`, `develope` ou `atlas`.
2. **Arquivos permitidos**: altere só os arquivos listados na tarefa. Se precisar
   de outro, pare e registre o pedido na seção "Pedidos" da tarefa em vez de
   editar. Arquivos compartilhados (`pyproject.toml`, `AGENTS.md`, `TAREFAS.md`
   fora da própria linha de status, `.github/`) só mudam por tarefa que os cite.
3. **Commits pequenos**, em português, no imperativo, com um assunto por commit.
4. **Rodar antes de commitar**: `.venv\Scripts\python -m pytest` e
   `.venv\Scripts\python -m ruff check src tests`. Não commite com falha.
5. **Push só de branches de tarefa; merge, PR e AWS são do dono.** O dono autorizou
   (16/11/2026) o push de branches de tarefa e de integração, nunca de `develope`,
   `engenharia-dados` ou `atlas`. Merge em `develope`, abertura de PR, liberação da
   T07 e qualquer custo ou recurso AWS continuam dependendo do dono. Os commits
   usam o e-mail `noreply` do dono e não levam a linha `Co-Authored-By` de agentes,
   para não poluir o histórico nem a lista de contribuidores.
6. **Não alterar o dashboard nem os scripts de `pipeline/`**, exceto se a tarefa
   disser. Dados em `data/bronze` e `data/silver` nunca vão para o git; os testes
   usam fixtures pequenas e sintéticas em `tests/fixtures/`.
7. **Sem segredos** nem dados pessoais no repositório.
8. **Ao terminar**: atualize o status da sua tarefa em `TAREFAS.md` (no mesmo
   branch, último commit), escreva em "Entrega" o que foi feito e o que ficou
   pendente, e pare. O dono decide o merge.
9. **Revisão cruzada**: o autor de uma tarefa não a aprova. A revisão é feita em
   modo leitura por um revisor independente: o agente `revisor-independente`
   (`.claude/agents/revisor-independente.md`), numa sessão nova e sem o contexto
   de autoria. O Codex pode revisar como segundo olhar, a pedido do dono. O
   revisor só lê; quem escreveu corrige os achados e pede nova rodada. Tarefas
   que mexem em segurança, custo ou dados reais pedem também a leitura do dono.
   Decisão do dono em 16/11/2026.

## Ambiente

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest
.venv\Scripts\python -m ruff check src tests
```

Use Python 3.11: o `pyproject.toml` fixa `pandas==2.2.2` e `pyarrow==16.1.0`,
que não têm builds para 3.13. O `ruff` ainda não é limpo em `pipeline/` (legado),
por isso a checagem cobre só `src` e `tests`.

## Convenções de código

- Código novo em `src/painel_dados/`, testes em `tests/`, mesmo padrão de
  `quality/checks.py`: funções pequenas, determinísticas, com mensagens de erro
  estáveis (os testes verificam a mensagem).
- Contratos de dados: cada fonte em `src/painel_dados/contracts/<fonte>.py`,
  testes em `tests/contracts/test_<fonte>.py`.
- Docstrings e documentação em português.
