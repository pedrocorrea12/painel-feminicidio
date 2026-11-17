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
| T11 | Dependência `duckdb` e runbook de publicação (pendências da T05/T09) | Codex | tarefa/t11-duckdb-runbook | integrada | T05, T09 |
| T12 | Benchmark local do pipeline (Gate B) | Claude | tarefa/t12-benchmark | integrada | T09 |
| T13 | Declarar `xlrd` e registrar a estimativa de custo (pedidos da T12) | Claude | tarefa/t13-xlrd-custos | integrada | T12 |
| T14 | Terraform do laboratório AWS, só escrito e revisado, sem `apply` (preparação da T06) | Claude | tarefa/t14-terraform | integrada | T12; revisão estática do Codex |
| T15 | Terraform sem federação OIDC (a conta bloqueia por SCP), lock file e ADR | Claude | tarefa/t15-terraform-sem-oidc | integrada | T14; laboratório parcialmente aplicado pelo dono |
| T16 | Publicar a Gold no bucket pelo login local (código e runbook) | Codex | tarefa/t16-publicar-gold-s3 | integrada | nenhuma (segue a decisão do contexto acima) |
| T17 | CI: `terraform fmt -check` e `validate` sem credenciais | Codex | tarefa/t17-ci-terraform | integrada | T15 (lock file); ok do dono para tocar `.github/` |
| T18 | Marcar artefatos gerados no Git (`.gitattributes`) para o diff do PR ficar legível | Codex | tarefa/t18-artefatos-gerados | integrada | T17 |
| T19 | Analisar e rodar `pipeline/validate_project.py` na CI (hoje fora dela porque `data/silver` não é versionada) | Codex | tarefa/t19-validate-project-ci | integrada | T18; ok do dono para tocar `.github/` |
| T20 | Incluir os ZIPs de `dashboard/atlas/downloads` na publicação segura (geração, validação e troca com backup) | Claude | tarefa/t20-zips-publicacao-segura | integrada | T05 (publicação segura) |
| T21 | Simular incidentes da publicação (Gold inválida, ZIP corrompido, backup órfão, falha na troca) e registrar a recuperação | Claude | tarefa/t21-incidentes-simulados | integrada | T20 (publicação conjunta) |
| T22 | Varredura de segredos e dados pessoais no repositório e no histórico (somente leitura, relatório) | Codex | tarefa/t22-varredura-segredos | integrada | nenhuma |
| T23 | Corrigir `docs/runbooks/publicacao-gold.md` com os 5 defeitos achados na T21 (par de backups, restauração parcial, listagem truncada, backup nulo, vários backups por pasta) | Claude | tarefa/t23-corrige-runbook-publicacao | integrada | T21 |
| T24 | Atualizar as regras 5 e 9 do `AGENTS.md` (push de branches de tarefa; revisor independente) e versionar `.claude/agents/revisor-independente.md` | Claude | integracao/gate-c | aprovada pelo dono | decisão do dono em 16/11/2026 |
| T25 | Versionar o agente `executor-tarefa` (`.claude/agents/executor-tarefa.md`) para tarefas independentes rodarem em paralelo, cada uma no seu worktree | Claude | tarefa/t25-agente-executor | integrada | decisão do dono em 16/11/2026 |
| T26 | Corrigir `docs/runbooks/publicacao-gold.md` com os 4 achados da segunda rodada de revisão da T23 e acertar no quadro os status da T23 e da T25 | Claude (`executor-tarefa`) | tarefa/t26-runbook-achados-t23 | integrada | T23, T25 |
| T27 | Resumo do Gate C com evidências (`docs/projeto-engenharia-dados/gate-c.md`) e teto de 2 rodadas de revisão para tarefas só de documentação (regra 9 do `AGENTS.md`) | Claude | tarefa/t27-resumo-gate-c | em revisão | pedido do dono em 17/11/2026 |
| T06 | Laboratório AWS (entrega 7) | Claude | tarefa/t06-aws | integrada (parcial) | T12, estimativa de custo, aprovação do dono |
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

## T13 xlrd e estimativa de custo

- **Dono:** Claude. **Branch:** `tarefa/t13-xlrd-custos`.
- **Arquivos permitidos:** `pyproject.toml` (só `dependencies`), `docs/costs.md`.
- **Escopo:** declarar `xlrd` (versão fixa) e registrar em `docs/costs.md` a estimativa
  de `docs/benchmark/README.md` (volumes, serviços, orçamento de referência).
- **Aceite:** instalação limpa num venv novo; `build_populacao_2025.py` roda numa
  cópia; `pytest` e `ruff check src tests` verdes.

## T14 Terraform do laboratório (sem apply)

- **Dono:** Claude; revisão estática do Codex (modo leitura). **Branch:** `tarefa/t14-terraform`.
- **Arquivos permitidos:** `infra/terraform/**`, `docs/runbooks/desligar-laboratorio-aws.md`
  (novo), `docs/costs.md` (só se T13 já integrada).
- **Regras:** nenhum `terraform apply`, nenhuma credencial, nenhum state versionado,
  nenhum recurso criado. O código só é aplicado depois da aprovação do dono (T06).
- **Escopo:** módulo mínimo e removível: S3 privado (versionado, criptografado, sem
  acesso público, ciclo de vida), provedor OIDC do GitHub e papel de menor privilégio
  restrito ao repositório e à branch, grupo de logs com retenção curta e orçamento
  com alerta por e-mail. Variáveis para região, teto, e-mail e repositório. README
  com os passos de `init/plan/apply/destroy` e runbook de desligamento.
- **Aceite:** `terraform fmt -check` e `validate` documentados (execução local fica
  para quando o binário existir; a CI pode rodá-los sem credenciais), revisão
  estática do Codex aprovada, sem segredos.

## Contexto das T15 a T17: o laboratório AWS foi aplicado em parte

Em 14/11/2026 o dono aplicou o Terraform da T14 numa conta do plano gratuito
(região `us-east-2`, projeto `dados-violencia-sc-lab`). Foram criados: bucket S3,
grupo de logs e orçamento. **Falhou** a criação do provedor OIDC do GitHub: uma
política de controle de serviço (SCP) da organização nega
`iam:CreateOpenIDConnectProvider`. Por isso também não existem o papel e a
política que dependem dele. Não se tenta contornar a SCP nem criar chave de acesso
de longa duração. Decisão: publicar pela sessão local do dono (`aws login`,
credenciais temporárias) e manter o desenho OIDC no código, desligado por variável.
O estado do Terraform está em `infra/terraform/terraform.tfstate` do worktree de
integração (ignorado pelo Git; não apagar nem versionar).

## T15 Terraform sem federação OIDC

- **Dono:** Claude; revisão do Codex (modo leitura). **Branch:** `tarefa/t15-terraform-sem-oidc`.
- **Arquivos permitidos:** `infra/terraform/**` (inclui `.terraform.lock.hcl` e
  `.gitignore`), `docs/adr/0002-publicacao-aws-por-login-local.md` (novo),
  `docs/runbooks/desligar-laboratorio-aws.md`, `docs/costs.md` (só uma nota).
- **Escopo:** variável `habilitar_federacao_github` (padrão `true`) que liga ou desliga
  provedor OIDC, papel e política; saída `papel_github_arn` nula quando desligada;
  `terraform.tfvars.example` e README coerentes; versionar `.terraform.lock.hcl`;
  ignorar `tfplan`; ADR com problema, mensagem da SCP, alternativa descartada
  (chave fixa), consequências e caminho de volta; runbook de desligamento cobrindo o
  estado parcial.
- **Aceite:** `terraform fmt -check` e `validate` ok; com `habilitar_federacao_github =
  false` o `plan` contra a conta real mostra **0 a criar, 0 a alterar, 0 a destruir**;
  pytest e ruff verdes; nenhum segredo, estado ou plano versionado.

## T16 Publicar a Gold no bucket pelo login local

- **Dono:** Codex. **Branch:** `tarefa/t16-publicar-gold-s3`, a partir de
  `engenharia-dados`; **pode começar já, em paralelo com a T15** (não compartilham arquivos).
- **Arquivos permitidos:** `src/painel_dados/s3_sync.py` (novo),
  `tests/test_s3_sync.py` (novo), `docs/runbooks/publicar-gold-na-aws.md` (novo),
  `docs/runbooks/README.md` (só o índice). Não alterar `pyproject.toml` (sem boto3):
  usar a AWS CLI por `subprocess`.
- **Escopo:** função pura que monta o comando `aws s3 sync` da pasta Gold para
  `s3://<bucket>/gold/<id-da-execução>/`, **simulação (`--dryrun`) por padrão**, valida
  nome de bucket e prefixo, recusa caminhos fora de `data/gold`, não usa `--delete` e
  escreve um manifesto com tamanho e SHA-256 de cada arquivo. Runbook: login
  (`aws login`), credenciais temporárias, simulação, publicação, verificação por
  listagem e checagem do manifesto, rollback por versão do objeto, limpeza.
- **Aceite:** testes sem rede (comando montado, recusas, manifesto determinístico);
  pytest e `ruff check src tests` verdes; nenhuma credencial no código; o runbook
  cita `docs/runbooks/desligar-laboratorio-aws.md` para encerrar.

## T17 CI do Terraform sem credenciais

- **Dono:** Codex. **Branch:** `tarefa/t17-ci-terraform`, depois da T15 integrada.
  **Só começa com o ok do dono para tocar `.github/`.**
- **Arquivos permitidos:** `.github/workflows/ci.yml`.
- **Escopo:** job separado que roda `terraform fmt -check -recursive`, `terraform init
  -backend=false -input=false` e `terraform validate` em `infra/terraform`, sem
  credenciais e sem `plan`; versão do Terraform fixa; ações fixadas como no job atual.
- **Aceite:** YAML válido, job independente do job Python, nenhuma credencial ou
  permissão além de `contents: read`; CI verde no GitHub depois de o dono fazer push.

## T18 Marcar artefatos gerados no Git

- **Dono:** Codex. **Branch:** `tarefa/t18-artefatos-gerados`, a partir de `engenharia-dados`.
- **Arquivos permitidos:** `.gitattributes` (novo, na raiz). Nenhum outro (arquivo compartilhado:
  só esta tarefa o cria).
- **Contexto:** `dashboard/dist/data/painel.json` tem 4,4 MB e 122 mil linhas (conteúdo gerado
  pelo commit `484aaef`, anterior às tarefas T09 a T17), o que torna ilegível o diff de um PR
  para `develope`. O Pages publica só `dashboard/atlas`, então nada disso afeta o site.
- **Escopo:** marcar como `linguist-generated=true` (o GitHub recolhe o diff e não conta nas
  estatísticas) os artefatos gerados e grandes: `dashboard/dist/data/**`, `data/gold/**`,
  `dashboard/atlas/data/**` e `dashboard/atlas/downloads/**`. Não usar `-diff` nem `binary`,
  para o conteúdo continuar revisável quando alguém quiser. Não alterar normalização de
  fim de linha (nada de `text=auto` nem `eol`), para não reescrever arquivos.
- **Aceite:** `git check-attr linguist-generated` retorna `set` para amostras de cada caminho
  e `unspecified` para `src/`, `tests/`, `docs/` e `infra/`; `git status` sem outros arquivos
  modificados após a criação; pytest e `ruff check src tests` verdes. Sem push.
- **Fora do escopo (decisão do dono):** remover ou parar de versionar `dashboard/dist/`.

## T12 Benchmark local do pipeline (Gate B)

- **Dono:** Claude. **Branch:** `tarefa/t12-benchmark`. Sem custo, sem AWS.
- **Arquivos permitidos:** `docs/benchmark/**` (novo) e, se necessário, um script de
  medição em `tools/`. Somente leitura em `pipeline/`, `data/` e `dashboard/`.
- **Escopo:** medir, numa cópia, tempo, pico de memória e volume de entrada e saída
  dos estágios que rodam offline (os 9 construtores da T01) e, quando possível, dos
  que dependem de rede ou Bronze (extract/fetch), anotando o que não foi medido.
  Comparar executores (local, GitHub Actions, contêiner/Lambda) por limites de
  memória, duração e dependências (pyarrow, pandas, duckdb). Recomendar o executor.
- **Aceite:** `docs/benchmark/README.md` com comandos reproduzíveis, tabela de
  medições e recomendação; estimativa de custo mensal preliminar para `docs/costs.md`.

## T19 `validate_project.py` na CI

- **Dono:** Codex. **Branch:** `tarefa/t19-validate-project-ci`, a partir de `engenharia-dados`.
  **Só altera `.github/` com o ok do dono.**
- **Contexto:** o validador lê `data/silver` e `data/gold`, que não são versionadas, e por isso
  o job de CI não o executa (comentário em `.github/workflows/ci.yml`). Hoje a única garantia
  automática sobre os dados vem dos testes com fixtures.
- **Arquivos permitidos:** `.github/workflows/ci.yml`; `tests/test_validate_project.py` e
  fixtures novas em `tests/fixtures/validate_project/` (todas novas); `docs/runbooks/` apenas
  se criar um runbook novo para a validação. **Não alterar** `pipeline/validate_project.py`
  nem scripts de `pipeline/` sem registrar o pedido na seção "Pedidos e entregas".
- **Escopo:** primeiro **analisar** e registrar em "Entrega" quais asserções dependem de
  dados reais e quais dependem só de estrutura; depois propor e implementar o menor
  caminho que rode o validador na CI sem versionar dados reais nem pessoais (por exemplo,
  fixtures sintéticas pequenas, ou separar a parte estrutural da parte que exige a Silver).
  Se a solução exigir mudar o validador, registrar como pedido e parar.
- **Aceite:** a CI executa a validação e falha quando uma fixture é adulterada (teste que
  prova a falha, com mensagem estável); nenhum dado real, pessoal ou segredo no repositório;
  pytest e `ruff check src tests` verdes; CI verde no GitHub depois do push do dono. Sem push.

## T20 ZIPs na publicação segura

- **Dono:** Claude. **Branch:** `tarefa/t20-zips-publicacao-segura`, a partir de `engenharia-dados`.
- **Contexto:** `build_atlas_site_data.py` publica `dashboard/atlas/data` pela troca segura
  (`publicar_diretorio`), mas os ZIPs de `dashboard/atlas/downloads` são gravados direto, fora
  dela: uma falha no meio pode deixar um ZIP novo ao lado de dados antigos.
- **Arquivos permitidos:** `pipeline/build_atlas_site_data.py` (só a geração e a validação dos
  ZIPs; autorizado por esta tarefa), `src/painel_dados/publish.py` apenas se for indispensável
  (registrar o motivo em "Pedidos"), `tests/test_publish.py` e `tests/test_atlas_downloads.py`
  (novo), `docs/contracts/atlas_site.md` e `docs/runbooks/` para a documentação. Nada em
  `dashboard/atlas/` além do que o script regenera.
- **Escopo:** gerar os ZIPs no diretório temporário, validar (abre, contém o CSV esperado,
  linhas e bytes batem com o manifesto do site) e trocar com backup, mantendo a restauração
  em caso de falha. Descrever no contrato que `data/` e `downloads/` passam a ser publicados
  juntos, e o que acontece se um deles falhar.
- **Aceite:** testes sem rede cobrindo ZIP corrompido, CSV ausente e contagem divergente
  (a versão anterior permanece); site e ZIPs regenerados sem diferença de conteúdo além dos
  carimbos de data; pytest e `ruff check src tests` verdes. Sem push.
- **Fora do escopo:** mudar o formato dos ZIPs ou das colunas.

## T21 Incidentes simulados e recuperação

- **Dono:** Claude. **Branch:** `tarefa/t21-incidentes-simulados`, a partir da `develope`.
- **Contexto:** item do Gate C "incidentes simulados e recuperação demonstrada". Os testes
  cobrem as falhas em memória; falta um registro reproduzível, com o runbook seguido passo a passo.
- **Arquivos permitidos:** `docs/runbooks/incidentes-simulados.md` (novo), `tests/test_incidentes_publicacao.py`
  (novo, se útil), `docs/projeto-engenharia-dados/TAREFAS.md` (só a própria linha e Entrega).
  Não alterar `src/`, `pipeline/` nem dados reais; a simulação roda em cópia temporária.
- **Escopo:** simular Gold inválida, ZIP corrompido, backup órfão, falha na segunda troca e
  falha na restauração; seguir `docs/runbooks/publicacao-gold.md` em cada caso e registrar
  comando, saída, resultado e tempo. Se o runbook falhar, registrar o defeito como pedido.
- **Aceite:** documento com os cinco incidentes e a recuperação comprovada; nenhum dado real
  alterado; pytest e `ruff check src tests` verdes. Sem push.

**Entrega (Claude, 16/11/2026):**

- Feito: `docs/runbooks/incidentes-simulados.md` com os cinco incidentes (Gold inválida, ZIP
  corrompido em três variações, backup órfão, falha na segunda troca, falha na restauração),
  cada um com cenário, como provocar, comando, saída, resultado, tempo e se o runbook bastou.
  Tudo rodou em cópias temporárias fora do repositório; `dashboard/atlas`, `src/`, `pipeline/`
  e os dados reais não foram tocados. Nos incidentes 1, 2 e 4 o conjunto voltou idêntico (mesma
  impressão digital); nos 3 e 5 a recuperação seguiu o runbook e o conjunto restaurado também
  ficou idêntico e válido. O script de provocação está no apêndice do documento.
  Não foi criado `tests/test_incidentes_publicacao.py`: `tests/test_publish.py` já cobre as
  falhas em memória.
- **Revisão cruzada (Codex, leitura): reprovada com 4 achados, tratados:** (1) a impressão digital agora
  tem implementação reproduzível (`Get-Digital`, `Get-Residuos`, `Novo-Sim` e o roteiro `rodar_tudo.ps1`, apêndices B e C),
  considera caminho e conteúdo, e os cinco incidentes foram reexecutados com ela (digital do conjunto `528EDE06…`,
  321 arquivos, igual antes e depois, sem resíduos, validação passando); (2) `publicar_sim.py` recusa raiz sem
  `SIMULACAO.txt` ou com `.git`/`pyproject.toml`, e a trava foi testada contra a raiz do repositório; (3) registrada a
  lacuna E (vários backups por pasta) e o pedido 5; (4) "o runbook bastou" trocado por "em parte" nos incidentes 3 e 5.
- **Segunda rodada (Codex): reprovada, 1 achado ainda aberto e 1 novo, tratados:** o incidente 3 não imprimia
  "idêntico, válido e sem resíduos" para o estado recuperado; o roteiro ganhou a checagem `I3 depois da recuperacao`
  (321 arquivos, digital idêntico, sem resíduos, validação passando) antes da nova publicação. O bloco de saída do
  apêndice C agora é a transcrição literal das 27 linhas do roteiro (só o caminho da raiz abreviado). Os `.ps1`
  passaram a ser gravados com BOM UTF-8, para o PowerShell 5.1 não corromper os acentos. Itens 2 a 5 da primeira
  correção foram confirmados como resolvidos.
- **Terceira rodada (revisor independente, Claude em sessão nova, só leitura): aprovada com ressalvas.** O revisor
  reexecutou o roteiro `rodar_tudo.ps1` a partir dos apêndices (321 arquivos, digital `528EDE06…`, linhas iguais às do
  documento, só mudam UUIDs e caminho), confirmou a trava e as contagens e não achou lacuna nova no runbook. Duas
  ressalvas baixas, tratadas: as saídas citadas na recuperação do incidente 3 vêm da execução manual do runbook (agora
  dito no texto), e a transcrição passa a ser descrita como as 27 linhas rotuladas, com as quatro linhas de rastro do
  PowerShell por trava explicadas e omitidas.
- Pendente: o dono decide o merge.

**Pedidos** (defeitos do runbook `docs/runbooks/publicacao-gold.md`, não corrigidos aqui):

1. Validar backup de uma só pasta: dizer que se usa a outra pasta atual
   (`validar_diretorio_site(<backup de data>, 'dashboard/atlas/downloads')`).
2. Incluir o caso em que uma pasta ficou na versão nova e a outra ausente (restauração parcial):
   decidir pelo conjunto e pôr o destino novo em quarentena. Não foi simulado.
3. Trocar `Select-Object FullName, LastWriteTime` por `Format-List` (o caminho sai truncado).
4. Tratar a listagem sem backup (`$backup` nulo) com mensagem clara.
5. Vários backups por pasta: parear `data` e `downloads` pelos instantes de criação em vez de escolher o
   mais recente de cada uma de forma independente, e validar o par antes de qualquer `Move-Item`.

## T22 Varredura de segredos e dados pessoais

- **Dono:** Codex, **somente leitura**. **Branch:** `tarefa/t22-varredura-segredos`, a partir da `develope`.
- **Arquivos permitidos:** `docs/auditoria/varredura-segredos.md` (novo) e a própria linha do quadro.
  **Não alterar nenhum outro arquivo nem reescrever histórico.**
- **Escopo:** procurar na árvore e no histórico Git chaves AWS e tokens, senhas, `.env`, estado do
  Terraform, IDs de conta, e-mails, CPF e outros dados pessoais; conferir `.gitignore`, `data/` e as
  fixtures. Cada achado leva arquivo, commit, gravidade e ação sugerida, **sem copiar o valor do segredo**.
- **Aceite:** relatório com método, comandos, achados (ou "sem achados") e conclusão; nenhum valor
  sensível no relatório. Sem push.

## T23 Correção do runbook de publicação

- **Dono:** Claude. **Branch:** `tarefa/t23-corrige-runbook-publicacao`, a partir da `develope`. **Arquivos:** `docs/runbooks/publicacao-gold.md` e a própria linha e Entrega no quadro.
- **Escopo:** os 5 pedidos da T21 (par de backups com uma só pasta, restauração parcial, listagem truncada, backup nulo, vários backups por pasta).
- **Entrega (Claude):** (A) validação de backup de uma só pasta com a outra pasta atual; (B) caso "uma pasta na versão nova e a outra ausente": quarentena da pasta nova e restauração dos dois backups; (C) listagem com `Format-List`; (D) função `Get-Backup` que falha com mensagem clara quando não há backup e avisa quando há vários; (E) pareamento por proximidade de horário, com diferença impressa, parada obrigatória se for grande e validação do par como condição. **Verificado:** os comandos do runbook foram extraídos do próprio arquivo e executados em cópias temporárias (mesmos scripts da T21): dois backups pareados (0 s) e recuperados, conjunto idêntico ao original; backup só de `data` validado com o `downloads` atual; sem backup, mensagem clara; restauração parcial com a pasta nova em quarentena, conjunto válido e idêntico ao original, sem `.tmp-*` nem `.backup-*`; dois backups de `downloads` (3 s e 9 dias), escolhido o de 3 s. 130 testes e Ruff verdes. **Revisão independente (Claude, sessão nova, só leitura): aprovada com ressalvas, todas tratadas:** (1, média) com vários backups, o `$backup` da preparação podia não ser o do par validado; a seção Recuperar agora redefine `$backup` como `$bd`/`$bz` (o par validado) e proíbe `Move-Item` antes da validação; (2) `Format-List` da função `Get-Backup` vazava para o pipeline e `$bd` virava array; agora vai ao console por `Out-Host` e `$bd` é um único `DirectoryInfo`; (3) caso de backup de uma só pasta: o texto diz definir só a variável da pasta que tem backup; (4) a restauração parcial ganhou comandos próprios com `$nova`, `$bd` e `$bz`. Reexecutados os cinco cenários com os blocos extraídos do runbook: todos passam, conjunto idêntico ao original. **Integrada** à `develope` pelo PR #4 (merge `beaa953`); os achados da segunda rodada de revisão, feita depois do merge, ficaram para a T26.

## T24 Regras de convivência e revisor independente

- **Decisão do dono (16/11/2026), pedida em chat:** reduzir a participação manual do dono. (1) Regra 9: revisão cruzada por revisor
  independente (agente `revisor-independente`, Claude em sessão nova, só leitura); Codex como segundo olhar opcional. (2) Regra 5: push de
  branches de tarefa, abrir PR e fazer merge (com CI verde, revisor independente aprovado e sem tocar dados publicados, `infra/` ou `.github/`) delegados aos agentes; AWS, T07, Gate C, `--force`, segredos e mudanças nas regras 5 e 9 seguem com o dono. Abrir PR e fazer merge exigem o `gh` instalado e autenticado pelo dono. (3) Commits com e-mail `noreply` e sem `Co-Authored-By`
  de agentes. (4) Agente versionado em `.claude/agents/`.
- **Arquivos alterados:** `AGENTS.md`, `.claude/agents/revisor-independente.md` (novo), `docs/projeto-engenharia-dados/TAREFAS.md`.
- **Limite conhecido:** o `Bash` do revisor não é tecnicamente só leitura; a proteção é a instrução do agente, por isso o autor confere
  `git status` e o diff depois de cada revisão. O revisor é da mesma família do autor: tarefas de segurança, custo ou dados reais pedem a leitura do dono.

## T25 Agente executor de tarefas

- **Decisão do dono (16/11/2026), pedida em chat:** criar mais um agente para dar celeridade ao processo. **Dono:** Claude.
  **Branch:** `tarefa/t25-agente-executor`, a partir da `develope`. **Arquivos:** `.claude/agents/executor-tarefa.md` (novo) e a
  própria linha e esta seção no quadro. O `AGENTS.md` não muda: as regras 5 e 9 continuam como estão.
- **Papéis:** o coordenador (a sessão principal) escolhe a tarefa, cria a branch e o worktree, **escreve a linha e a seção da tarefa
  no quadro dessa branch** (o executor para se não as encontrar), chama o `executor-tarefa`, pede a revisão ao `revisor-independente` e
  cuida de push, PR e merge dentro da regra 5. O executor só escreve e commita na branch da tarefa e deixa o status em `em revisão`.
  Quem escreveu não aprova (regra 9): o revisor continua sendo uma sessão nova, sem o contexto de autoria.
- **Paralelismo:** um executor por tarefa, cada um no seu worktree, e só para tarefas cujos arquivos permitidos não se sobrepõem. O
  `TAREFAS.md` é a exceção inevitável: toda tarefa edita a própria linha e seção, então o segundo merge pode conflitar nele. Quem
  resolve é o coordenador, atualizando a branch antes do PR; o executor não faz `merge` nem `rebase`.
- **Entrega (Claude):** agente com travas de autoria: todo comando ancorado no worktree (`cd` na mesma chamada ou `git -C`), lista
  positiva de comandos `git` (correção é commit novo, sem `--amend`), `gh` proibido por inteiro, `git add` só com caminhos explícitos
  e conferência do que está preparado antes do commit, `dashboard/atlas`, `data/` e `infra/` intactos como no revisor, `.venv`
  próprio do worktree, pytest e ruff antes de cada commit e resposta com a linha final `ESTADO:`.
  **Verificado:** pytest e Ruff verdes (o diff só tem Markdown). **Não verificado:** o agente ainda não executou nenhuma tarefa; ele só
  fica disponível numa sessão aberta depois do merge.
  **Revisão independente (Claude, sessão nova, só leitura), 1ª rodada: aprovada com ressalvas, tratadas:** (1, média) nada ancorava
  os comandos ao worktree e um commit podia cair na `develope` do checkout principal: agora todo comando leva o worktree e o commit
  confere a branch na mesma chamada; (2, média) furos na lista de proibidos (`gh workflow run`, `commit --amend`, `pull`, `clean`,
  `config`): trocada por lista positiva; (3) sem trava contra `git add -A`: caminhos explícitos e conferência do índice; (4) trava de
  dados mais estreita que a do revisor: igualada, e `pipeline/` e `dashboard/` citados; (5) comandos em sintaxe PowerShell numa
  ferramenta que é o Git Bash: barras normais; (6) ninguém registrava a tarefa no quadro da branch: é o coordenador, e "pare" virou
  devolver `ESTADO: bloqueada`; (7) pedido de arquivo extra ia para a Entrega: vai para "Pedidos" (regra 2); (8) critério de
  paralelismo ignorava o `TAREFAS.md`: exceção descrita acima. O mesmo defeito do item 5 existe no `revisor-independente.md` e fica
  para outra tarefa. **2ª rodada: aprovada com ressalvas**, os 8 achados resolvidos e 5 novos, todos baixos, tratados no agente:
  comparação do caminho do worktree ignora o sentido das barras; pedido de arquivo extra é commitado; índice sujo após `add` errado
  fica para o coordenador limpar; remoção e renomeação por `git add`; `commit` sem `--no-verify` e `ESTADO: incompleta` definido.
  Estas últimas correções não passaram por nova rodada. **Pendente:** **leitura do dono antes do merge** (ressalva 9 do revisor: o arquivo
  define o que um agente com escrita pode fazer, o que toca segurança no sentido da regra 9) e a primeira tarefa real como teste.
- **Limite conhecido:** como no revisor, as travas são instrução, não bloqueio técnico; o coordenador confere `git status`, o diff e o
  `git log` da branch **e do checkout principal** depois de cada execução.

## T26 Achados da segunda rodada da T23 no runbook de publicação

- **Dono:** Claude, pelo agente `executor-tarefa` (primeira tarefa real dele). **Branch:** `tarefa/t26-runbook-achados-t23`, a partir
  da `develope`. **Pedido do dono em chat (16/11/2026).**
- **Arquivos permitidos:** `docs/runbooks/publicacao-gold.md`; e, em `docs/projeto-engenharia-dados/TAREFAS.md`, só: a linha da T26
  e esta seção, o status na linha da T23, o trecho "**Pendente:** merge." no fim da Entrega da T23, e o status na linha da T25.
- **Escopo, parte 1 (runbook):** os 4 achados da segunda rodada de revisão independente da T23, feita depois do merge do PR #4. Os
  números de linha são os do runbook na `develope` e servem de orientação.
  1. **(média) `Move-Item` sem guarda aninha o backup dentro do destino quando a quarentena falha** (bloco da restauração parcial,
     por volta das linhas 214-220; o mesmo padrão nas linhas 195-196 e 172). Cenário reproduzido pelo revisor: `data` na versão nova
     com um arquivo aberto por outro processo; o `Move-Item` da quarentena dá erro não terminante e move só parte da pasta; o comando
     seguinte encontra `data` ainda existente e move o backup para dentro dela (`data\.data.backup-*`), onde a listagem do runbook,
     que não é recursiva, não o encontra. Correção esperada: `-ErrorAction Stop` nos `Move-Item` e, antes de cada restauração, parar
     com mensagem clara se o destino ainda existir; e dizer no runbook o que fazer nesse caso.
  2. **(baixa/média) A comparação de árvores usa o `$backup` da preparação e a remoção usa o do par validado** (linhas 123, 138-140,
     159 e 183). Com vários backups de uma pasta, compara-se um e apaga-se outro, que nunca foi comparado. Correção esperada:
     comparar o mesmo backup que será removido (o do par, `$bd`/`$bz`).
  3. **(baixa) O bloco de pareamento, colado no console, não para no `throw`** (linhas 73-81): as linhas seguintes rodam com `$bd`
     nulo ou com um `$bd` antigo da mesma sessão. Correção esperada: zerar `$bd` e `$bz` no início do bloco e não seguir com valor
     nulo.
  4. **(baixa) Não há comando para conferir `.tmp-*`** (as linhas 222 e 250 pedem a conferência; a listagem das linhas 32-35 só
     filtra `.backup-*`). Correção esperada: dar o comando.
- **Verificação exigida:** extrair os blocos PowerShell do runbook corrigido e executá-los em cópias temporárias fora do
  repositório (Windows PowerShell 5.1), incluindo o cenário do achado 1 com um arquivo mantido aberto. Nunca sobre `dashboard/atlas`
  nem `data/` do repositório. Dizer na Entrega o que foi executado e o que não foi.
- **Escopo, parte 2 (quadro):** T23 e T25 já estão na `develope` (PRs #4 e #5, merges `beaa953` e `8001d93`): mudar o status das duas
  linhas para `integrada` e trocar o "**Pendente:** merge." da Entrega da T23 por uma frase dizendo que foi integrada pelo PR #4 e que
  os achados da segunda rodada ficaram para a T26.
- **Pedidos:** (nenhum até agora)
- **Entrega (Claude, `executor-tarefa`), primeira rodada** (commits `eb70a6c`, `03b6f42`, `530219f`; o que a segunda rodada mudou
  está logo abaixo e prevalece):
  - **Achado 1:** toda restauração passa pela função `Restore-Backup`, que para com `Destino ainda existe: ...` sem mover nada e
    usa `Move-Item -ErrorAction Stop`; os `Move-Item` de quarentena também levam `-ErrorAction Stop`. Os blocos de mais de um passo
    ("Destino inválido e backup válido" e a restauração parcial) vêm dentro de `& { ... }` e conferem o backup antes de mover, para
    pararem no primeiro erro mesmo colados no console. Seção nova "Se a restauração parar" diz o que fazer: fechar o processo e
    repetir o bloco (o resto do destino vai para uma segunda quarentena).
  - **Achado 2:** o passo 4 virou só inspeção e não define mais `$backup`; a comparação de árvores define `$backup` a partir do par
    (`$bd`/`$bz`), o mesmo que "Recuperar" restaura ou remove.
  - **Achado 3:** o bloco de pareamento zera `$bd` e `$bz`, só calcula `$bz` com `$bd` definido e só imprime o par com os dois
    definidos; senão avisa `Par de backups incompleto`. O `throw` de "Nenhum backup de 'downloads'" saiu: esse caso cai no aviso.
  - **Achado 4:** comando em "Encerramento e evidências" que lista `.tmp-*`, `.backup-*` e quarentenas das duas pastas,
    recursivo (acha também backup aninhado); a restauração parcial aponta para ele.
  - **Parte 2:** T23 e T25 como `integrada`; "Pendente: merge." da T23 trocado pela frase do PR #4.
  - **Executado** (Windows PowerShell 5.1, blocos extraídos do próprio runbook, em cópias de `data` e `downloads` numa pasta
    temporária fora do repositório; "colado" = linhas entregues uma a uma por `powershell -Command -`, que segue depois de um erro):
    (a) controle com os blocos do runbook antigo e um arquivo de `data` aberto por outro processo: reproduziu o defeito
    (quarentena parcial e `data\.data.backup-*` aninhado); o comando novo de resíduos acha esse backup aninhado e a listagem da
    preparação não; (b) o mesmo cenário com os blocos novos, na restauração parcial e em "Destino inválido": a primeira tentativa
    para na quarentena, backups intactos, nada aninhado, `downloads` não restaurado; liberado o arquivo, a repetição do bloco
    restaura, o conjunto valida e fica idêntico ao original, com duas quarentenas; (c) sem backups e com `$bd`/`$bz` antigos na
    sessão, todos os blocos colados em sequência: variáveis zeradas, aviso de par incompleto, nada movido nem removido; (d) backup
    só de `data`: validação de "uma só pasta", comparação vazia, `Restore-Backup` recusado com destino existente, remoção
    (com backup só de `downloads`, apenas o pareamento e a validação de "uma só pasta"); (e) dois backups de `downloads` (3 s e 9 dias): o passo 4 mostra o de 9 dias, a comparação e a
    remoção usam o de 3 s, e o outro fica; (f) as duas pastas ausentes: restauradas, conjunto válido e idêntico ao original, sem
    resíduos; (g) restauração parcial sem arquivo aberto, como script (`-File`). 130 testes e Ruff verdes.
  - **Não executado:** colagem num console interativo de verdade (com PSReadLine): o "colado" foi simulado pela entrada padrão;
    PowerShell 7; o caso "Quarentena já existe" (bloco repetido no mesmo segundo); nada sobre `dashboard/atlas` nem `data/` do
    repositório. O arquivo aberto foi sempre `data\manifesto.json`; arquivo aberto em subpasta ou em `downloads` não foi testado.
  - **Limite da primeira rodada, resolvido na segunda:** com `-ErrorAction Stop` a quarentena ainda podia ficar parcial (o
    `Move-Item` do PowerShell 5.1 movia os outros arquivos antes de falhar no que estava aberto); o runbook parava e explicava,
    não evitava.
- **Revisão independente da primeira rodada: aprovada com ressalvas.** Os 4 achados originais foram dados como resolvidos; a
  revisão trouxe 5 achados novos, tratados na segunda rodada (commit `5979a59`):
  - **Achado 1 (média), arquivo aberto dentro do backup deixava o destino incompleto sem erro:** a causa era o `Move-Item`, que
    move arquivo por arquivo. Quarentena e restauração passaram a usar a função nova `Move-Pasta`
    (`[System.IO.Directory]::Move`), que renomeia a pasta inteira ou falha sem mover nada; não existe mais estado parcial para o
    operador repetir por cima. Cada etapa tem mensagem própria (`Quarentena de '...' falhou e nada foi movido` e `Restauração de
    ... falhou e nada foi movido`), e a função confere o estado depois da falha (se não for "origem inteira, alvo ausente", manda
    não repetir e acionar o dono). Os blocos ficaram repetíveis: com o destino já em quarentena, a repetição avisa e só restaura,
    sem criar outra quarentena. "Se a restauração parar" foi reescrita por mensagem, incluindo a saída da restauração parcial que
    para em `downloads` com `data` já restaurada (repetição responde `Backup ausente` e aponta para "Destino ausente e backup
    válido").
  - **Achado 2 (baixa), bloco da restauração parcial:** antes de mover qualquer coisa, o bloco agora valida `$nova`, confere cada
    backup do par e para com `A pasta '...' existe: este não é o caso de restauração parcial. Nada foi movido.` se a outra pasta
    existir. A repetição depois de uma restauração bem-sucedida não refaz nada: responde `Backup ausente` com a saída indicada.
  - **Achado 3 (baixa), "param no primeiro erro":** cada bloco `& { ... }` e as duas funções começam com
    `$ErrorActionPreference = 'Stop'`; a atribuição é local ao bloco e a preferência da sessão não muda (conferido). O texto diz
    isso.
  - **Achado 4 (baixa), "segunda quarentena":** o texto saiu; como a quarentena não fica mais parcial, há no máximo uma por pasta.
  - **Achado 5 (só registro):** sem correção; segue declarado abaixo como não executado.
  - **Executado nesta rodada** (Windows PowerShell 5.1.26100, blocos extraídos do próprio runbook, árvores sintéticas de 3
    arquivos por pasta numa pasta temporária fora do repositório; colagem simulada invocando cada instrução de topo do bloco
    separadamente na mesma sessão; arquivo mantido aberto por outro processo `powershell.exe`): 55 verificações, 0 falhas
    (o número vem de um roteiro do executor que ficou na pasta temporária e **não está no repositório**; não é reproduzível a
    partir dele).
    Achado 1: "Destino inválido" com arquivo aberto em `.data.backup-*\municipio\a.json` (erro de restauração, destino ausente,
    backup e quarentena inteiros; repetição com o arquivo ainda aberto não muda nada; liberado, `data` volta completa e idêntica
    ao backup, uma quarentena); "Destino ausente" (mesmo comportamento); restauração parcial com falha em `downloads` depois de
    `data` restaurada (`downloads` ausente e backup inteiro; repetição responde `Backup ausente`; a saída indicada conclui o
    conjunto anterior completo), com falha já em `data`, e com `$nova = "downloads"`. Achado 2: `downloads` presente, nada
    movido, também na repetição; `$nova` inválida recusada. Achado 3: controle sem a preferência segue adiante; com ela para;
    "Destino inválido" e restauração parcial com `$atlas` nulo dão um único erro e não movem nada; preferência da sessão continua
    `Continue`. Regressão: arquivo aberto no destino (para na quarentena sem mover nada; liberado, restaura), dois backups de
    `downloads` (3 s e 9 dias: par usa o de 3 s, o outro fica), sessão com `$bd`/`$bz`/`$backup` antigos e nenhum backup (nada
    movido), `Restore-Backup` com destino existente, "Quarentena já existe" e as duas pastas ausentes. Sonda à parte: com um
    arquivo aberto em subpasta, `Directory.Move` falhou sem mover nada com compartilhamento `None`, `ReadWrite` e
    `ReadWrite, Delete`; o `Move-Item` no mesmo cenário deixou 2 arquivos de cada lado. 130 testes e Ruff verdes.
  - **Não executado nesta rodada:** colagem num console interativo de verdade (com PSReadLine) e PowerShell 7 (não instalado na
    máquina), como na primeira rodada; os comandos Python de validação do contrato e a comparação de árvores (não mudaram e as
    árvores desta rodada são sintéticas, não passam no contrato); volumes diferentes entre backup e destino; nada sobre
    `dashboard/atlas` nem `data/` do repositório.
  - **Pendente ao fim da segunda rodada:** `incidentes-simulados.md` cita os comandos antigos (`Move-Item`) e não foi tocado (fora
    dos arquivos permitidos).
- **Revisão independente da segunda rodada: aprovada com ressalvas.** Os 5 achados da primeira rodada foram dados como resolvidos
  e a atomicidade do `Move-Pasta` foi confirmada pelo revisor (12 casos dele, incluindo `FileShare.None` e processo com diretório
  de trabalho dentro da pasta). Ficaram 4 ressalvas baixas, tratadas na terceira rodada (commit `90f747d`), **só em texto**: os 14
  blocos PowerShell do runbook são idênticos aos de `ceb703e` e a primitiva de movimentação não mudou.
  - **Ressalva 1, `Backup ausente` afirmava uma causa que o código não confere:** a entrada diz agora que a mensagem não prova que
    a pasta foi restaurada. A saída por "Destino ausente e backup válido" só vale se a execução anterior do mesmo bloco parou em
    `Restauração de ... falhou e nada foi movido` na outra pasta, com conferência do estado (pasta do backup ausente no lugar,
    outra pasta ausente com backup intacto, quarentena `.<nova>.quarentena-*` se a pasta nova existia). Na primeira execução, ou se
    a conferência não fecha, o texto manda não restaurar só uma pasta (conjunto misto), refazer o passo 5 e a validação do par e,
    sem backup das duas, parar. O passo 2 da restauração parcial aponta para essa entrada.
  - **Ressalva 2, "nada foi movido" sempre atribuído a arquivo aberto:** parágrafo novo manda ler a `Causa:` antes de repetir;
    repetir só quando for acesso negado ou arquivo em uso, citando o terminal ou programa com a pasta como diretório atual;
    qualquer outra causa (caminho inválido, permissão, volumes diferentes) é parar e acionar o dono. As entradas de quarentena e de
    restauração e a nota de "Destino ausente e backup válido" foram reescritas nesse sentido.
  - **Ressalva 3, mensagens sem entrada própria:** "Se a restauração parar" tem agora uma entrada para cada mensagem emitida pelas
    funções e blocos de "Recuperar": além das que já existiam, `Defina $nova` (corrigir e repetir), `Par de backups não definido`,
    `Backup não definido para`, `Backup de '...' não definido ou ausente` (na repetição depois do sucesso significa "já
    restaurado"; na primeira execução, variável nula ou antiga), `A pasta '...' existe` e o aviso `Destino ausente (já está em
    quarentena?)`. "Qualquer outro erro" continua como regra final.
  - **Ressalva 4, volumes diferentes:** o runbook diz que quarentena, backup e destino ficam sob `$atlas`, no mesmo volume, e que
    entre volumes `Directory.Move` falha sem mover nada, com o motivo na `Causa:`. Esse comportamento foi **verificado pelo
    revisor, não pelo executor**. A origem do número "55 verificações" está registrada acima.
  - **Verificado nesta rodada:** como só o texto mudou, nenhum bloco foi reexecutado (o cenário da ressalva 1 não foi rodado: o
    código que responde `Backup ausente` é o mesmo já exercitado). Conferência por comparação de cadeias, com um roteiro
    temporário fora do repositório: os 14 blocos PowerShell são idênticos aos de `ceb703e`; as 12 mensagens distintas (14 instruções `throw` e
    `Write-Warning`) dos blocos de "Recuperar" têm entrada na seção, e as 12 entradas casam literalmente com o texto emitido
    (trechos separados por `...` conferidos em ordem). 130 testes e Ruff verdes.
  - **Não verificado:** o comportamento entre volumes diferentes e as causas alternativas de "nada foi movido" (diretório de
    trabalho dentro da pasta, permissão, caminho inválido) não foram reproduzidos pelo executor; a orientação apoia-se no relato
    do revisor. Continuam sem execução: console interativo com PSReadLine e PowerShell 7.
  - **Terceira rodada de revisão independente (curta, só o diff `ceb703e..2d54aa7`): aprovada com ressalvas.** As quatro ressalvas
    estão resolvidas e os 14 blocos são idênticos (conferido pelo revisor por SHA-256). Dois achados baixos, de redação, corrigidos
    pelo coordenador no commit seguinte: a contagem de mensagens acima (era "13"; são 12 distintas em 14 instruções) e a frase do
    runbook sobre onde a mensagem diz que nada foi movido. Essa última correção não passou por nova rodada.
  - **Pendente:** `docs/runbooks/incidentes-simulados.md` segue citando os comandos antigos com `Move-Item` (fora dos arquivos
    permitidos; pede tarefa própria). Sem execução por ninguém: console interativo com PSReadLine e PowerShell 7.

## T27 Resumo do Gate C e teto de rodadas de revisão

- **Pedido do dono (17/11/2026), em chat:** depois de 6 rodadas de revisão num único runbook (T23 e T26), fechar o Gate C com um
  resumo de evidências e limitar as rodadas de revisão de documentação. **Dono:** Claude. **Branch:** `tarefa/t27-resumo-gate-c`, a
  partir da `develope`.
- **Arquivos:** `docs/projeto-engenharia-dados/gate-c.md` (novo), `AGENTS.md` (só o acréscimo à regra 9, por decisão do dono), e
  nesta `TAREFAS.md` a linha e a seção da T27 e o status das linhas da T21, T22 e T26 (já integradas na `develope`: `1088c3b`,
  `87c7e1f` e `8e8d989`).
- **Entrega (Claude):** `gate-c.md` lista, para cada item do Gate C, a evidência no repositório, a pendência e o campo de
  confirmação do dono; não confirma nada. Pendências que são do dono: custo da primeira fatura AWS em `docs/costs.md` e a decisão
  sobre o e-mail nos metadados Git (achado baixo da T22). Teto: 2 rodadas para tarefa só de documentação; depois, só achado médio
  ou alto reabre; esta tarefa altera o `AGENTS.md`, então pela definição nova não está sob o teto; seguiu 2 rodadas por decisão do dono. **Verificado:** as afirmações do `gate-c.md` foram conferidas contra os arquivos
  citados e contra o resultado da CI em `8e8d989`. **Não verificado:** a data da última varredura de segredos (16/11/2026) é a da
  auditoria; nenhuma varredura nova foi feita. **Revisão independente, 1ª rodada: aprovada com ressalvas** (1 média: "só documentação" sem definição, que deixaria
  `AGENTS.md`, `.github/` e `infra/` escaparem; 6 baixas: gravidade atribuída por quem?, "reabre" ambíguo, registro dos achados
  baixos, e três exageros do `gate-c.md`). Todos corrigidos; o médio reabriu a revisão, como a própria regra manda.
  **2ª rodada: aprovada com ressalvas**, os 7 achados resolvidos e 3 novos, todos baixos e corrigidos pelo autor **sem nova
  rodada**, como a regra manda: (N1) a frase sobre o teto valer para esta tarefa; (N2) documentação de runbooks, custos e auditoria
  entra no teto, com leitura do dono mantida (**decisão que o dono deve confirmar ao ler a regra**); (N3) risco aceito: a correção
  sem revisão de um achado baixo pode tocar mais que o achado, mitigado por este registro. **Pendente:** **leitura do dono** (a mudança na regra 9 e o
  resumo do Gate C são dele).

## T06 e T07

T06: **aplicada em parte** com aprovação do dono (S3 privado, logs e orçamento);
a federação OIDC do GitHub ficou desligada por variável porque uma SCP da
organização da conta a bloqueia (ver `docs/adr/0002-publicacao-aws-por-login-local.md`).
A primeira publicação da Gold foi feita por login local temporário. O trabalho
foi integrado à `develope` pelo PR #1 (merge `def2685`). Pendente: registrar o
custo observado em `docs/costs.md` após a primeira fatura e desligar o
laboratório (`docs/runbooks/desligar-laboratorio-aws.md`) antes de 14/05/2027.

T07 continua **bloqueada**. Só o dono a libera, depois de confirmar **todos** os itens do
Gate C (`docs/projeto-engenharia-dados/README.md`). Situação em 16/11/2026, sem nenhum
item confirmado ainda:

| Item do Gate C | Situação | O que falta |
| --- | --- | --- |
| CI visível e aprovado | CI verde nos PRs 1 e 2 e na `develope` | confirmar; T19 amplia o que a CI valida |
| Incidentes simulados e recuperação demonstrada | não feito | simular falhas (Gold inválida, ZIP corrompido, backup órfão) e registrar; T20 cobre os ZIPs |
| Métricas reais, limitações e custos observados | parcial: benchmark e estimativa existem | registrar o custo da primeira fatura AWS em `docs/costs.md` |
| Nenhum segredo ou dado pessoal desnecessário | não confirmado | varredura final do repositório antes da demo |

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
- T11: **Entrega:** `duckdb==1.5.6`, versão usada pelo ambiente atual do
  pipeline, foi declarada nas dependências do projeto e instalada pelo comando
  `pip install -e ".[dev]"` num venv Python 3.11. O novo runbook
  `docs/runbooks/publicacao-gold.md` descreve diagnóstico, validação por
  contrato, comparação por SHA-256, restauração, quarentena e remoção segura de
  `.data.backup-*`, além de `RuntimeWarning` e da janela sem destino no Windows;
  referencia `docs/contracts/atlas_site.md` e registra que os ZIPs ainda ficam
  fora da troca. Validação final: 82 testes e Ruff verdes; `validate_project.py`
  passou com os dados locais. **Pedidos:** nenhum. **Revisão cruzada (Claude):** aprovada; instalação limpa em venv novo com `duckdb==1.5.6`, 82 testes e Ruff verdes; comandos do runbook (validar destino e backup, comparar por SHA-256, remover) executados numa cópia, sem diferenças.
- T12: **Entrega:** `tools/medir_estagios.py` e `docs/benchmark/` (README, `medicoes.json`). 13 estágios sem rede, 3 repetições: pipeline completo em cerca de 183 s, pico de 5,2 GB (`build_sinan_atlas`); `build_sim_atlas` é o mais lento (76 s). Recomendação: GitHub Actions agendado como executor; AWS no laboratório para armazenamento durável, OIDC e logs; custo de ordem de grandeza abaixo de US$ 1 por mês. **Pedidos:** (1) declarar `xlrd` em `pyproject.toml` (estágio `build_populacao_2025` falha sem ele); (2) registrar a estimativa do benchmark em `docs/costs.md`. **Revisão cruzada (Codex):** 1ª passada reprovou (`--saida` ambíguo, memória só por processo, variação e executor local; corrigidos e medição refeita); 2ª aprovou. **Pendente:** medir os estágios de rede.
- T13: `xlrd==2.0.2` declarado em `pyproject.toml`; estimativa preliminar (menos de US$ 1 por mês, preços de referência não verificados) em `docs/costs.md`. Verificado: venv novo com `pip install -e ".[dev]"` instala `xlrd`; `build_populacao_2025.py` roda numa cópia com a Bronze real (5.571 municípios); 82 testes e Ruff verdes. **Pedidos:** nenhum. **Revisão cruzada (Codex):** aprovada, sem achados.
- T14: módulo Terraform em `infra/terraform/` (S3 privado versionado e criptografado, OIDC do GitHub com papel de menor privilégio por repositório e branch, grupo de logs de 14 dias, orçamento com alerta), README de uso, `terraform.tfvars.example`, `.gitignore` do estado e runbook `docs/runbooks/desligar-laboratorio-aws.md`. **Nada foi aplicado e nenhum recurso existe.** Limite da verificação: o binário do Terraform não está instalado, então só a sintaxe HCL foi conferida (parser em Python); `fmt` e `validate` ficam para o Codex ler e para a CI. **Pedidos:** (1) job de CI com `terraform fmt -check` e `validate` sem credenciais (`.github/` fora da lista); (2) `.terraform.lock.hcl` na primeira execução real. **Revisão estática (Codex):** 1ª passada reprovou (4 médios, 3 baixos: `StringLike` aceitava curingas, runbook incompleto, `bucket_key_enabled` inócuo, provedor OIDC existente sem checagem de audiência); corrigidos; 2ª passada confirmou os 7 e achou 1 médio no runbook (revogar acesso), corrigido. Aprovada para integração. `fmt` e `validate` ainda não rodaram (sem binário).
- T15: variável `habilitar_federacao_github` (padrão `true`) liga ou desliga provedor OIDC, papel e política; saída `papel_github_arn` nula quando desligada; `.terraform.lock.hcl` versionado (provedor aws 5.100.0) e `tfplan` ignorado; ADR 0002; runbook de desligamento com o estado parcial; nota em `docs/costs.md`; README e exemplo de variáveis atualizados; nome padrão do projeto agora `dados-violencia-sc-lab`. **Verificado:** `terraform fmt -check` e `validate` ok; com a federação desligada, `terraform plan` contra a conta real (cópia temporária do estado, já removida) deu **No changes** (0 criar, 0 alterar, 0 destruir); 82 testes e ruff verdes. **Revisão cruzada (Codex, leitura): aprovada, sem achados** (a 1ª e a 2ª tentativas travaram sem conclusão; a 3ª, com mensagem final gravada em arquivo, concluiu). **Pendente:** acrescentar `habilitar_federacao_github = false` ao `terraform.tfvars` do worktree de integração, onde está o estado.
- T16: **Entrega:** `src/painel_dados/s3_sync.py` monta e executa `aws s3 sync` sem shell, restrito a `data/gold`, com dry-run por padrão, validação de bucket, prefixo e identificador e sem `--delete`; gera `manifesto.json` determinístico com tamanho e SHA-256 de cada artefato. Os testes cobrem o comando, as recusas, o manifesto e a execução simulada sem rede. O runbook `docs/runbooks/publicar-gold-na-aws.md` documenta `aws login`, sessão temporária, simulação, publicação, verificação, reversão por versão de objeto, limpeza e desligamento do laboratório. **Verificado:** 99 testes e Ruff verdes. Nenhuma credencial foi criada ou registrada e nenhuma chamada à AWS foi feita. **Pedidos:** nenhum. **Pendente:** revisão cruzada e primeira publicação real pelo dono com sua sessão temporária; como ressalvas, a simulação grava `manifesto.json` e o manifesto não possui marca de conclusão.
- T16 (fechamento): **Revisão cruzada (Claude, leitura): reprovada na 1ª passada** (2 médios no runbook: saída `bucket_name` em vez de `bucket_dados` e perfil `painel-lab` em vez de `lab-painel`; 1 baixo: links simbólicos); corrigidos, **aprovada com ressalvas** (simulação grava `manifesto.json`; manifesto sem marca de conclusão). Integrada; 99 testes e ruff verdes. Falta a primeira publicação real pelo dono.
- T17: **Entrega:** job `terraform` separado e independente do job Python em `.github/workflows/ci.yml`, com `actions/checkout@v6`, `hashicorp/setup-terraform@v4` e Terraform 1.17.1. Em `infra/terraform`, executa `fmt -check -recursive`, `init -backend=false -input=false` e `validate`, sem credenciais, segredos ou `plan`; as permissões continuam limitadas a `contents: read`. **Verificado:** YAML carregado localmente, 99 testes e Ruff verdes. Nenhuma chamada à AWS foi feita. **Pedidos:** nenhum. **Pendente:** a CI só poderá ficar verde no GitHub depois do push pelo dono.
- T17 (fechamento): **Revisão cruzada (Claude, leitura): aprovada, sem achados** (ações por tag como no job existente; `setup-terraform@v4` e `checkout@v6` existem; permissões `contents: read`). Integrada localmente; **a CI do job `terraform` só roda no GitHub depois do push**, que depende do dono.
- T18: **Entrega:** `.gitattributes` na raiz marca `dashboard/dist/data/**`, `data/gold/**`, `dashboard/atlas/data/**` e `dashboard/atlas/downloads/**` com o atributo booleano `linguist-generated`, sem desabilitar diff, declarar arquivos binários ou alterar normalização de fim de linha. **Verificado:** `git check-attr linguist-generated` retorna `set` para amostras dos quatro caminhos e `unspecified` para amostras de `src/`, `tests/`, `docs/` e `infra/`; status da tarefa sem outros arquivos modificados; 99 testes e Ruff verdes. **Pedidos:** nenhum. **Pendente:** revisão cruzada.
- T18 (fechamento): **Revisão cruzada (Claude, leitura): aprovada, sem achados** (`git check-attr` confirmou `set` nos quatro caminhos e `unspecified` em `src/`, `tests/`, `docs/`, `infra/` e nos HTML do dashboard). Integrada localmente.
- T20: ZIPs de `dashboard/atlas/downloads` agora entram na publicação segura. **Entrega:** nova `publicar_conjunto` em `src/painel_dados/publish.py` (gera e valida vários diretórios em temporários irmãos e troca todos como uma unidade; falha em qualquer etapa devolve todos à versão anterior; falha na restauração preserva os backups e lista os caminhos); `validar_diretorio_site(diretorio, diretorio_downloads=None)` ganhou validação a fundo dos ZIPs (caminho, tamanho, ZIP íntegro, CSV esperado, linhas e arquivos fora do manifesto; mensagens estáveis); `build_atlas_site_data.py` publica `data/` e `downloads/` juntos. Contrato (`docs/contracts/atlas_site.md`) e runbook (`docs/runbooks/publicacao-gold.md`) atualizados. **Verificado:** 120 testes e Ruff verdes antes da revisão (21 novos: troca conjunta com falha na geração, na validação, na segunda troca, na restauração e com backup órfão; ZIP corrompido, sem CSV, contagem e tamanho divergentes, arquivo sobrando e caminho inválido); execução sobre os dados reais regenerou o site e os 3 ZIPs com o mesmo conteúdo (CSV com o mesmo SHA-256; só mudam `atualizado_em` e o carimbo interno dos ZIPs), e a regeneração foi descartada; o comando novo do runbook valida os arquivos reais. **Pedidos (arquivos fora da lista inicial, justificados):** (1) `src/painel_dados/publish.py` (previsto como condicional): `publicar_diretorio` só troca um diretório, e trocar `data/` e `downloads/` separadamente deixaria uma falha entre as duas trocas com versões misturadas; a função nova não altera a existente. (2) `src/painel_dados/contracts/atlas_site.py`: o teste da validação de ZIP precisa de código importável de `src/` (o `pipeline/` não é pacote) e o contrato do site é o lugar natural; a assinatura antiga continua valendo. Os dois pedem a aprovação do dono na revisão. **Revisão cruzada (Codex, modo leitura): reprovada com 6 achados, todos tratados:** (1) destinos aninhados agora são rejeitados ("Destinos aninhados na publicação conjunta"); (2) falha ao remover a versão nova de um destino que não existia antes, durante a reversão, agora vira `RuntimeError` listando o caminho ("versão nova não removida em"); (3) `backup_remanescente` é atribuído só ao destino dono do backup; (4) CSV só com cabeçalho é rejeitado ("Download sem registros"); (5) runbook reescrito para tratar `data` e `downloads` como conjunto, com `$nome` por pasta e validação do par de backups; (6) introdução do contrato corrigida para `publicar_conjunto`. O Codex aprovou os dois pedidos (publish.py e contracts/atlas_site.py). Testes novos para os achados 1 a 4; 124 testes e Ruff verdes. **Segunda rodada (Codex): aprovada com ressalvas;** os 7 itens resolvidos, com 1 achado novo baixo (a seção final do runbook só citava `.data.*`), corrigido no último commit. **Pedidos aprovados pelo dono (publish.py e contracts/atlas_site.py).** **Integrada na `develope` pelo PR #2 (merge `40faa5d`, CI e Publicar Atlas verdes).**
- T19: **Entrega:** análise do `pipeline/validate_project.py`: dependem dos dados reais a presença da Silver e da Gold, a igualdade entre a Gold e a cópia do dashboard, os controles exatos do `painel.json`, contagens, domínios, chaves, totais, cobertura temporal, taxas e situações de SINAN, SIM, Sinesp, população, raça e RAIS, as consistências entre Parquets/CSVs, a reconciliação dos municípios com SC e o confronto final do site com a Gold. Dependem somente de estrutura ou arquivos versionados a presença de `dashboard/dist/{index.html,styles.css,app.js}` e, na parte estrutural de `validar_dados_site`, o manifesto, os 295 JSONs municipais, o limite de tamanho, a relação indicador/mapa e a igualdade dos IDs da malha; essa função ainda mistura no final o confronto com a Gold. O menor caminho sem editar `pipeline/` usa as unidades já desacopladas: a CI executa `tests/test_validate_project.py` sobre três CSVs sintéticos mínimos, sem municípios reais; a reconciliação válida passa e adulterações parametrizadas de SIM, SINAN e Sinesp falham com o prefixo estável `<arquivo>: municípios não fecham com SC:`. A estrutura completa do site, inclusive uma Gold sintética mínima para atravessar o confronto final, é gerada em `tmp_path`: o caso válido percorre manifesto, 295 JSONs, limite de tamanho, relação indicador/mapa e IDs da malha, e a malha adulterada falha com `malha não casa com municípios`. Nenhum dos 295 arquivos é versionado. **Verificado:** 105 testes e Ruff verdes; nenhum dado real, pessoal ou segredo foi acrescentado. **Pedidos:** nenhum, pois não foi necessário separar `validar_estrutura_dados_site`. **Pendente:** o `main()` integral continua fora da CI porque exige toda a Silver e controles reais; a CI só poderá ficar verde no GitHub depois do push do dono. Revisão cruzada: Claude (aprovada). **Integrada na `develope` pelo PR #2 (merge `40faa5d`).**
- T22: **Entrega:** relatório `docs/auditoria/varredura-segredos.md` com varredura mascarada de 506 arquivos rastreados e 152 commits por `git grep` em todos os snapshots, `git log -p`, nomes históricos, mensagens e metadados de commit. Foram conferidos chaves e tokens conhecidos, atribuições de segredo, chaves privadas, `.env`, `*.tfstate`, ARNs/IDs de conta AWS, e-mails, CPF com dígitos verificadores, outros campos pessoais, `.gitignore`, `data/` e `tests/fixtures/`. **Achados:** nenhum de gravidade alta ou média; um achado baixo, o e-mail pessoal mascarado `p***@g***.com` nos metadados de autoria de 145 commits. Não há credencial ativa e não foi feita reescrita de histórico. Candidatos em documentação, teste, Gold agregada e inventário foram classificados como referências variáveis, placeholders ou falsos positivos. `.env`, estado Terraform, Bronze e Silver estão ignorados e não apareceram por nome no histórico. **Verificado:** relatório sem valor sensível não mascarado; 130 testes e Ruff verdes. **Pedidos:** nenhum. **Pendente:** revisão cruzada pelo Claude e decisão do dono sobre usar endereço `noreply` nos commits futuros. **Revisão cruzada (Claude, leitura): aprovada.** Refeitas as buscas críticas no histórico de todas as referências (chaves AWS, chaves privadas, tokens, `.tfstate`/`.env`/`.tfvars`, ARNs com conta): zero ocorrências, como no relatório; os três e-mails de autoria e commit (dois `noreply`, um pessoal) conferem com o achado de baixa gravidade. Decisão do dono em 16/11/2026: usar e-mail `noreply` nos commits futuros (configurado) e ligar no GitHub o bloqueio de push que expõe o e-mail (confirmado); o histórico não é reescrito.
