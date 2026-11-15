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
5. **Sem push, sem merge, sem PR.** Só o dono do projeto aprova push, merge em
   `develope` e qualquer custo ou recurso AWS.
6. **Não alterar o dashboard nem os scripts de `pipeline/`**, exceto se a tarefa
   disser. Dados em `data/bronze` e `data/silver` nunca vão para o git; os testes
   usam fixtures pequenas e sintéticas em `tests/fixtures/`.
7. **Sem segredos** nem dados pessoais no repositório.
8. **Ao terminar**: atualize o status da sua tarefa em `TAREFAS.md` (no mesmo
   branch, último commit), escreva em "Entrega" o que foi feito e o que ficou
   pendente, e pare. O dono decide o merge.
9. **Revisão cruzada**: o autor de uma tarefa não a aprova. A revisão é feita
   pelo outro agente em modo leitura.

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
