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
| T19 | Analisar e rodar `pipeline/validate_project.py` na CI (hoje fora dela porque `data/silver` não é versionada) | Codex | tarefa/t19-validate-project-ci | em revisão | T18; ok do dono para tocar `.github/` |
| T20 | Incluir os ZIPs de `dashboard/atlas/downloads` na publicação segura (geração, validação e troca com backup) | Claude | tarefa/t20-zips-publicacao-segura | pendente | T05 (publicação segura) |
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

## T06 e T07

T06: **aplicada em parte** com aprovação do dono (S3 privado, logs e orçamento);
a federação OIDC do GitHub ficou desligada por variável porque uma SCP da
organização da conta a bloqueia (ver `docs/adr/0002-publicacao-aws-por-login-local.md`).
A primeira publicação da Gold foi feita por login local temporário. O trabalho
foi integrado à `develope` pelo PR #1 (merge `def2685`). Pendente: registrar o
custo observado em `docs/costs.md` após a primeira fatura e desligar o
laboratório (`docs/runbooks/desligar-laboratorio-aws.md`) antes de 14/05/2027.

T07 continua **bloqueada**. Só o dono a libera, depois de confirmar **todos** os itens do
Gate C (`docs/projeto-engenharia-dados/README.md`). Situação em 15/11/2026, sem nenhum
item confirmado ainda:

| Item do Gate C | Situação | O que falta |
| --- | --- | --- |
| CI visível e aprovado | CI verde no PR 1 e na `develope` | confirmar; T19 amplia o que a CI valida |
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
- T19: **Entrega:** análise do `pipeline/validate_project.py`: dependem dos dados reais a presença da Silver e da Gold, a igualdade entre a Gold e a cópia do dashboard, os controles exatos do `painel.json`, contagens, domínios, chaves, totais, cobertura temporal, taxas e situações de SINAN, SIM, Sinesp, população, raça e RAIS, as consistências entre Parquets/CSVs, a reconciliação dos municípios com SC e o confronto final do site com a Gold. Dependem somente de estrutura ou arquivos versionados a presença de `dashboard/dist/{index.html,styles.css,app.js}` e, na parte estrutural de `validar_dados_site`, o manifesto, os 295 JSONs municipais, o limite de tamanho, a relação indicador/mapa e a igualdade dos IDs da malha; essa função ainda mistura no final o confronto com a Gold. O menor caminho sem editar `pipeline/` usa as unidades já desacopladas: a CI executa `tests/test_validate_project.py` sobre três CSVs sintéticos mínimos, sem municípios reais; a reconciliação válida passa e adulterações parametrizadas de SIM, SINAN e Sinesp falham com o prefixo estável `<arquivo>: municípios não fecham com SC:`. A estrutura completa do site, inclusive uma Gold sintética mínima para atravessar o confronto final, é gerada em `tmp_path`: o caso válido percorre manifesto, 295 JSONs, limite de tamanho, relação indicador/mapa e IDs da malha, e a malha adulterada falha com `malha não casa com municípios`. Nenhum dos 295 arquivos é versionado. **Verificado:** 105 testes e Ruff verdes; nenhum dado real, pessoal ou segredo foi acrescentado. **Pedidos:** nenhum, pois não foi necessário separar `validar_estrutura_dados_site`. **Pendente:** o `main()` integral continua fora da CI porque exige toda a Silver e controles reais; a CI só poderá ficar verde no GitHub depois do push do dono. Revisão cruzada: Claude.
