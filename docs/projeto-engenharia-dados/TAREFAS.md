# Quadro de tarefas

Fonte de verdade da divisão de trabalho entre agentes. Regras em `AGENTS.md`.
Status: `a fazer`, `em andamento`, `em revisão`, `aprovada`, `integrada`.
Todas as branches partem de `engenharia-dados`. Sem push sem aprovação do dono.

Backlog de origem: `README.md` desta pasta (entregas 1 a 8).

| ID | Entrega | Dono | Branch | Status | Depende de |
| --- | --- | --- | --- | --- | --- |
| T00 | Base: pacote, config, checagens (entrega 2) | Codex | engenharia-dados | integrada (53a05c1) | |
| T01 | Baseline do pipeline atual (entrega 1) | Claude | tarefa/t01-baseline | em revisão | |
| T02 | Contratos e testes SINAN (entregas 3 e 4) | Codex | tarefa/t02-contratos-sinan | a fazer | |
| T03 | Contratos e testes SINESP (entregas 3 e 4) | Claude | tarefa/t03-contratos-sinesp | a fazer | |
| T04 | CI: lint, testes e validação (entrega 5) | a definir | tarefa/t04-ci | a fazer | T02, T03, T08 |
| T05 | Publicação Gold segura e atômica (entrega 6) | a definir | tarefa/t05-publicacao-segura | a fazer | T02, T03, T08 |
| T08 | Atualizar o validador do projeto e a documentação de taxas 2025 (achado da T01) | Claude | tarefa/t08-validador | a fazer (aguarda T02) | T01, T02; aprovação do dono para tocar `pipeline/` |
| T06 | Laboratório AWS (entrega 7) | a definir | tarefa/t06-aws | bloqueada | Gate A e Gate B, aprovação do dono |
| T07 | Demo profissional (entrega 8) | a definir | tarefa/t07-demo | bloqueada | Gate C |

T02 e T03 são independentes e podem rodar em paralelo: não compartilham nenhum
arquivo. T01 também é independente.

## T01 Baseline do pipeline atual

- **Dono:** Claude. **Branch:** `tarefa/t01-baseline`.
- **Arquivos permitidos:** `docs/baseline/**` (novo). Somente leitura em
  `pipeline/`, `data/` e `dashboard/`.
- **Escopo:** registrar como o pipeline roda hoje: ordem dos scripts, comandos,
  entradas e saídas, contagens de linhas e colunas por artefato Silver/Gold,
  hash dos Gold publicados, tempo observado. Nada é refatorado.
- **Aceite:** `docs/baseline/README.md` com comandos reproduzíveis e tabela de
  contagens/hashes; `validate_project.py` executado e seu resultado registrado;
  nenhum arquivo fora de `docs/baseline/` modificado.

## T02 Contratos e testes SINAN

- **Dono:** Codex. **Branch:** `tarefa/t02-contratos-sinan`.
- **Arquivos permitidos:** `src/painel_dados/contracts/__init__.py`,
  `src/painel_dados/contracts/sinan.py`, `tests/contracts/test_sinan.py`,
  `tests/fixtures/sinan/**`, `docs/contracts/sinan.md`.
- **Não tocar:** `pipeline/`, `pyproject.toml`, `quality/`. Reutilize
  `assert_required_columns` e `assert_unique`; se faltar uma checagem, registre em
  "Pedidos".
- **Escopo:** descrever o contrato do SINAN lido de `pipeline/extract_sinan.py`,
  `pipeline/build_sinan_atlas.py` e `docs/SINAN_ATLAS.md`: colunas, tipos, chave
  de granularidade, periodicidade e tratamento de ano preliminar. Funções de
  validação que levantam `ValueError` com mensagem estável.
- **Aceite:** testes falham com coluna removida, tipo alterado e chave duplicada
  e passam com a fixture sintética válida; `pytest` e `ruff check src tests`
  verdes; `docs/contracts/sinan.md` descreve o contrato; nenhum dado real
  versionado.

## T03 Contratos e testes SINESP

- **Dono:** Claude. **Branch:** `tarefa/t03-contratos-sinesp`.
- **Arquivos permitidos:** `src/painel_dados/contracts/sinesp.py`,
  `tests/contracts/test_sinesp.py`, `tests/fixtures/sinesp/**`,
  `docs/contracts/sinesp.md`.
- **Atenção:** `contracts/__init__.py` é criado em T02. Em T03 crie-o vazio, também;
  como o conteúdo é idêntico, o merge não conflita. Se T02 já tiver mudado
  o arquivo, rebase antes de commitar.
- **Não tocar:** `pipeline/`, `pyproject.toml`, `quality/`.
- **Escopo:** contrato do SINESP a partir de `pipeline/extract_sinesp.py`,
  `pipeline/build_sinesp_atlas.py` e `docs/SINESP_VDE.md`: esquema, mudanças de
  planilha entre anos, cobertura mensal, séries parciais, chave e granularidade.
- **Aceite:** mesmo critério de T02, aplicado ao SINESP; inclui teste de série
  mensal incompleta.

## T04 CI

- **Arquivos permitidos:** `.github/workflows/ci.yml`. Python 3.11, `pip install -e
  ".[dev]"`, `ruff check src tests`, `pytest`. Sem deploy.
- **Aceite:** workflow falha quando um teste de contrato falha. Só inicia após
  T02, T03 e T08 integradas.

## T05 Publicação segura

- **Arquivos permitidos:** `src/painel_dados/publish.py`, `tests/test_publish.py`.
  Mudanças em `pipeline/` ou `.github/` exigem aprovação do dono.
- **Aceite:** Gold inválida não substitui a versão válida; escrita em caminho
  temporário seguida de troca atômica; teste simula falha no meio.

## T08 Validador e documentação das taxas de 2025

- **Dono:** Claude. **Branch:** `tarefa/t08-validador`. Só inicia depois que a T02
  definir o contrato do SINAN para 2025 e com **aprovação do dono** para alterar
  `pipeline/`.
- **Origem:** achado da T01 (`docs/baseline/README.md`): o commit `e7dc7ed` passou a
  publicar taxas de 2025 e `pipeline/validate_project.py` ainda exige que elas
  fiquem vazias, o que o faz falhar hoje (linhas 327 e 360).
- **Arquivos permitidos:** `pipeline/validate_project.py`, `docs/SINAN_ATLAS.md`
  e, se mencionar a taxa de 2025, `docs/SINESP_VDE.md`. Nenhum construtor,
  dado ou arquivo do dashboard.
- **Escopo:** trocar as duas asserções por verificações do estado real, alinhadas
  ao contrato da T02 (por exemplo: 2025 continua `preliminar`; a taxa só existe
  onde há denominador, com `tipo_denominador` válido); corrigir a documentação
  que ainda diz que a taxa de 2025 fica vazia. Sem mudar nenhum valor publicado.
- **Aceite:** `validate_project.py` passa nos dados atuais; falha numa cópia em que
  a taxa de 2025 tem `tipo_denominador` inválido ou em que a situação de 2025 deixa
  de ser `preliminar`; documentação coerente com a Gold; nenhum arquivo fora da
  lista alterado.

## T06 e T07

Bloqueadas pelos Gates B e C e por aprovação explícita do dono. Não iniciar.

## Pedidos e entregas

Cada agente anota abaixo, em sua tarefa, pedidos de arquivos extras e o resumo
da entrega.

- T01: entregue em `docs/baseline/`: inventário (390 artefatos, contagens e SHA-256), cadeia do pipeline, reprodução dos 9 construtores offline numa cópia (Parquets e CSV idênticos; só carimbos de data mudam, e o protótipo local estava desatualizado), `validador.json` e resultado do `validate_project.py`. Achado principal: o validador **falha hoje** por 2 asserções desatualizadas (taxa 2025 do SINAN, linha 327, e do SINESP, linha 360) depois do commit `e7dc7ed`; sem elas, o restante passa. Não reexecutados por exigirem rede ou Bronze: extract_*, fetch_*, build_populacao_2025, build_sinan_atlas, build_sim_atlas, build_rais. **Pedido:** registrar a T08 (validador e taxas de 2025), aprovada pelo dono, em branch própria. Revisão cruzada do Codex reprovou a 1ª versão; corrigidos escopo do quadro, cadeia, cobertura do coletor e evidências.
- T02: (vazio)
- T03: (vazio)
