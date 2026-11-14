# Quadro de tarefas

Fonte de verdade da divisão de trabalho entre agentes. Regras em `AGENTS.md`.
Status: `a fazer`, `em andamento`, `em revisão`, `aprovada`, `integrada`.
Todas as branches partem de `engenharia-dados`. Sem push sem aprovação do dono.

Backlog de origem: `README.md` desta pasta (entregas 1 a 8).

| ID | Entrega | Dono | Branch | Status | Depende de |
| --- | --- | --- | --- | --- | --- |
| T00 | Base: pacote, config, checagens (entrega 2) | Codex | engenharia-dados | integrada (53a05c1) | |
| T01 | Baseline do pipeline atual (entrega 1) | Claude | tarefa/t01-baseline | integrada | |
| T02 | Contratos e testes SINAN (entregas 3 e 4) | Codex | tarefa/t02-contratos-sinan | integrada (aprovada com ressalvas) | |
| T03 | Contratos e testes SINESP (entregas 3 e 4) | Claude | tarefa/t03-contratos-sinesp | integrada | |
| T04 | CI: lint, testes e validação (entrega 5) | Codex | tarefa/t04-ci | integrada | T02, T03, T08 |
| T05 | Publicação Gold segura e atômica (entrega 6) | Codex | tarefa/t05-publicacao-segura | integrada | T02, T03, T08 |
| T08 | Atualizar o validador do projeto e a documentação de taxas 2025 (achado da T01) | Claude | tarefa/t08-validador | integrada | T01, T02; aprovação do dono para tocar `pipeline/` |
| T09 | Ligar a publicação segura ao `build_atlas_site_data.py` (pendência da T05) | Claude | tarefa/t09-publicacao-atlas | integrada | T05, T01; aprovação do dono para tocar `pipeline/` |
| T10 | Endurecer o contrato SINAN (ressalvas da T02) | Codex | tarefa/t10-sinan-endurecimento | integrada (aprovada com ressalvas) | T02 |
| T11 | Dependência `duckdb` e runbook de publicação (pendências da T05/T09) | Codex | tarefa/t11-duckdb-runbook | a fazer | T05, T09 |
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

- **Dono:** Claude. **Branch:** `tarefa/t08-validador`. Exige **aprovação do dono**
  para alterar `pipeline/`.
- **Origem:** achado da T01 (`docs/baseline/README.md` e `validador.json`): o commit
  `e7dc7ed` passou a publicar taxas de 2025 e `pipeline/validate_project.py` ainda
  exige que elas fiquem vazias, o que o faz falhar hoje (linhas 327 e 360).
- **Arquivos permitidos:** `pipeline/validate_project.py`, `docs/SINAN_ATLAS.md`
  e, se mencionar a taxa de 2025, `docs/SINESP_VDE.md`. Nenhum construtor,
  dado ou arquivo do dashboard.
- **Escopo:** trocar as duas asserções por verificações do estado real, alinhadas
  aos contratos (por exemplo: 2025 continua `preliminar`; a taxa só existe onde há
  denominador, com `tipo_denominador` válido); corrigir a documentação que ainda
  diz que a taxa de 2025 fica vazia. Sem mudar nenhum valor publicado.
- **Aceite:** `validate_project.py` passa nos dados atuais; falha numa cópia em que
  a taxa de 2025 tem `tipo_denominador` inválido ou em que a situação de 2025 deixa
  de ser `preliminar`; documentação coerente com a Gold; nenhum arquivo fora da
  lista alterado.

## T09 Publicação segura do site do atlas

- **Dono:** Claude. **Branch:** `tarefa/t09-publicacao-atlas`. Exige **aprovação do dono**
  para alterar `pipeline/` (concedida em 2026-11-14).
- **Arquivos permitidos:** `pipeline/build_atlas_site_data.py`,
  `src/painel_dados/contracts/atlas_site.py`, `tests/contracts/test_atlas_site.py`,
  `tests/fixtures/atlas_site/**`, `docs/contracts/atlas_site.md`.
- **Escopo:** `dashboard/atlas/data` passa a ser gerado num diretório temporário e
  trocado por `publicar_diretorio` só após validação. `malha_sc.json` (não gerado
  pelo script) é preservado. Downloads (`dashboard/atlas/downloads`) ficam fora.
- **Aceite:** saída idêntica à baseline da T01 exceto carimbos de data; falha de
  validação mantém a versão anterior; testes cobrem o validador; `pytest` e
  `ruff check src tests` verdes.

## T10 Endurecer o contrato SINAN

- **Dono:** Codex. **Branch:** `tarefa/t10-sinan-endurecimento`.
- **Arquivos permitidos:** `src/painel_dados/contracts/sinan.py`,
  `tests/contracts/test_sinan.py`, `tests/fixtures/sinan/**`, `docs/contracts/sinan.md`.
- **Não tocar:** `pipeline/`, `pyproject.toml`, `quality/`, outros contratos.
- **Escopo:** fechar as ressalvas da revisão da T02: rejeitar `data_ocorrencia` fora
  de limites plausíveis (ex.: antes de 2000 ou depois do ano corrente), `idade_anos`
  negativa ou irreal, `sexo` fora do domínio; guarda de proporção de datas no ano da
  notificação (mínimo 90% das datas com o mesmo ano, calibrado nos dados reais).
- **Aceite:** um teste por regra nova (falha com valor inválido, passa com válido);
  a Silver e a Gold reais continuam aprovadas (só leitura, `id_territorio` como texto);
  `pytest` e `ruff check src tests` verdes; documentação atualizada.

## T11 Dependência duckdb e runbook de publicação

- **Dono:** Codex. **Branch:** `tarefa/t11-duckdb-runbook`.
- **Arquivos permitidos:** `pyproject.toml` (só `dependencies`), `docs/runbooks/publicacao-gold.md`
  (novo). Nada em `pipeline/`, `.github/` ou `src/`.
- **Escopo:** (1) declarar `duckdb` em `dependencies`, com versão fixa igual à usada nos
  scripts (`pip show duckdb` no venv; `build_sinan_atlas.py`, `fetch_populacao_geral.py`
  e `validate_project.py` o importam); confirmar que `pip install -e ".[dev]"` e os 82
  testes seguem verdes; (2) runbook curto em português sobre a publicação segura
  (`painel_dados.publish` e `build_atlas_site_data.py`): o que fazer com backup órfão
  `.data.backup-*` (identificar, comparar com o destino, restaurar ou remover) e com
  `RuntimeWarning`, e o que significa a janela sem destino entre as renomeações.
- **Aceite:** `pytest` e `ruff check src tests` verdes; runbook referencia
  `docs/contracts/atlas_site.md`; sem outras mudanças. **Fora do escopo:** colocar o
  `validate_project.py` na CI (depende da Silver, não versionada).

## T06 e T07

Bloqueadas pelos Gates B e C e por aprovação explícita do dono. Não iniciar.

## Pedidos e entregas

Cada agente anota abaixo, em sua tarefa, pedidos de arquivos extras e o resumo
da entrega.

- T01: entregue em `docs/baseline/`: inventário (390 artefatos, contagens e SHA-256), cadeia do pipeline, reprodução dos 9 construtores offline numa cópia (Parquets e CSV idênticos; só carimbos de data mudam, e o protótipo local estava desatualizado), `validador.json` e resultado do `validate_project.py`. Achado principal: o validador **falha hoje** por 2 asserções desatualizadas (taxa 2025 do SINAN, linha 327, e do SINESP, linha 360) depois do commit `e7dc7ed`; sem elas, o restante passa. Não reexecutados por exigirem rede ou Bronze: extract_*, fetch_*, build_populacao_2025, build_sinan_atlas, build_sim_atlas, build_rais. **Pedido:** registrar a T08 (validador e taxas de 2025), aprovada pelo dono, em branch própria. Revisão cruzada do Codex reprovou a 1ª versão; corrigidos escopo do quadro, cadeia, cobertura do coletor e evidências. Terceira passada do Codex aprovou.
- T02: **Entrega:** contratos da Silver do atlas e da Gold territorial, fixtures
  sintéticas, testes de esquema, tipo, chave, periodicidade e ano preliminar, e
  documentação do SINAN. O contrato foi ajustado à representação real de mês,
  idade e data anuláveis. Validação final: 16 testes aprovados, Ruff sem erros,
  Silver real com 4.292.317 linhas aprovada e Gold real com 127.908 linhas
  aprovada quando `id_territorio` é lido como texto. **Pedidos:** nenhum.
  **Revisão cruzada (Claude):** 1ª versão reprovada (rejeitava a Silver real); 2ª aprovada. **Ressalvas para tarefa futura:** o contrato ainda aceita `data_ocorrencia` fora de limites plausíveis (ex.: 1800 ou 2099), `idade_anos` negativa e `sexo` fora do domínio; falta guarda de proporção de datas no ano da notificação.
- T03: entregue em 5 commits. Contrato em `contracts/sinesp.py` (bronze, silver, gold mensal/anual, cobertura mensal), 26 testes de contrato, fixtures sintéticas, `docs/contracts/sinesp.md`. `pytest` (29 passando no total) e `ruff check src tests` verdes; validado também contra Silver e Gold reais, só leitura. Pendente: reconciliação contra o Anuário e detecção de quebras de série (fora do escopo). Obs.: `contracts/__init__.py` é vazio, como em T02. Revisão cruzada pelo Codex (read-only) reprovou a 1ª versão; corrigidos: série inteira ausente na cobertura, desagregações e `arquivo_origem` no esquema, coerência situação x meses no Gold anual. Nova passada do Codex aprovou, sem achados acima de baixo.
- T04: **Entrega:** workflow de CI para `push` e `pull_request` em
  `engenharia-dados` e `develope`, além de execução manual. Usa Ubuntu, Python
  3.11, cache pip, permissões somente de leitura, concorrência por referência,
  Ruff e pytest, sem deploy ou segredos. `pipeline/validate_project.py` fica fora
  porque depende da Silver não versionada. Sintaxe e estrutura YAML validadas
  localmente; 51 testes aprovados e Ruff sem erros. **Pedidos:** nenhum.
  **Revisão cruzada (Claude):** aprovada; rodada num checkout limpo (sem `data/`)
  com 51 testes e Ruff verdes. **Pendente:** a primeira execução real do workflow
  depende do push pelo dono; o `validate_project.py` continua fora da CI.
- T05: **Entrega:** módulo de publicação de diretórios com geração e validação
  em temporário no mesmo volume, troca com backup e restauração compatível com
  Windows. A revisão acrescentou retorno estruturado e aviso para backup não
  removido após publicação concluída, erro encadeado com o caminho do backup em
  falha dupla, detecção prévia de backups órfãos e documentação da janela sem
  destino entre as renomeações. Nove testes cobrem os fluxos de sucesso,
  falha e recuperação. Validação final: 51 testes aprovados e Ruff sem erros.
  **Pedidos:** nenhum. **Revisão cruzada (Claude):** 1ª versão reprovada (sucesso reportado como
  falha quando o backup não era removido; restauração falha sem apontar o
  backup); 2ª aprovada. **Ressalva:** um backup remanescente bloqueia as
  publicações seguintes até limpeza manual; registrar no runbook. **Pendente:**
  ligar o módulo ao pipeline e ao validador.
- T08: as duas asserções desatualizadas de `pipeline/validate_project.py` foram trocadas por `_validar_taxas_territoriais` (taxa, população e `tipo_denominador` juntos; `publicado` até 2024; em 2025 `publicado` no total e `estimado_proporcao_2024` por sexo; taxa recalculada com tolerância de 0,0051) e por checagens de situação (SINAN 2025 `preliminar`; SINESP parcial sem taxa). `docs/SINAN_ATLAS.md` e `docs/SINESP_VDE.md` corrigidos. Verificado: o validador passa nos dados reais e falha em 10 adulterações feitas numa cópia (denominador inválido, 2025 não preliminar, taxa apagada, taxa errada, estimado em 2024, taxa em ano parcial, parcial virando consolidado). Sem mudança em dados, construtores ou dashboard. Fora do escopo e ainda pendente: `docs/SIM_ATLAS.md` e a asserção do SIM continuam exigindo taxa vazia em 2025 e 2026, o que confere com a Gold atual do SIM. Revisão cruzada do Codex: 1ª passada reprovou (ano parcial do Sinesp não confrontado com o ano); corrigido sem fixar 2026 no código (`periodo_completo` equivale a 12 meses, só o maior ano pode ser parcial, `meses_observados` entre 1 e 12); 2ª passada aprovou.
- T09: `build_atlas_site_data.py` agora gera `dashboard/atlas/data` num diretório temporário (`gerar_dados`), valida com `validar_diretorio_site` (novo contrato `contracts/atlas_site.py`, 20 testes) e troca por `publicar_diretorio`; `malha_sc.json` é copiado da versão publicada. Execução sobre os dados reais: 318 arquivos idênticos aos versionados, exceto `atualizado_em`; ZIPs com mesmo CRC. 71 testes e Ruff verdes. **Pedidos:** nenhum. **Pendente:** ZIPs de `downloads` ainda são escritos fora da publicação segura; runbook do backup órfão; `validate_project.py` fora da CI.
- T10: **Entrega:** o contrato SINAN agora limita `data_ocorrencia` ao período
  1900-01-01 a 2025-12-31, `idade_anos` a 0–130, `sexo` ao domínio publicado e
  exige no mínimo 90% das datas no ano da notificação. Os limites foram
  calibrados na Silver real (95,70% no mesmo ano; mínimo 1900; idade máxima
  130), sem descartar os 6.094 registros anteriores a 2000 nem as 23 idades
  acima de 120. Foram acrescentados testes de falha e de fronteira válida para
  cada regra. Validação final: 62 testes e Ruff verdes; Silver real com
  4.292.317 linhas e Gold real com 127.908 linhas aprovadas. Documentação
  atualizada. **Pedidos:** nenhum. **Revisão cruzada (Claude):** aprovada; 62 testes e Ruff verdes, Silver real aprovada e regras provadas com valores adulterados. **Ressalva:** os limites de data (1900) e idade (130) foram calibrados nos extremos reais, então só barram valores absurdos; um recorte mais estreito exigiria tratar os 6.094 registros pré-2000.
