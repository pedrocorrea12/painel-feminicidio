# Baseline do pipeline atual (T01)

Registro do estado do pipeline em 12 de novembro de 2026, commit-base `e70609d`
(branch `engenharia-dados`), antes de qualquer refatoração. Nada em `pipeline/`,
`data/` ou `dashboard/` foi alterado: toda execução abaixo foi somente leitura
ou numa cópia descartável.

Arquivos desta pasta:

| Arquivo | Conteúdo |
| --- | --- |
| `coletar_baseline.py` | coletor reproduzível (inventário, reprodução e validador) |
| `inventario.json` | 390 artefatos com bytes e SHA-256; linhas e colunas para os 17 Parquets e os 39 CSV |
| `reproducao.json` | reconstrução dos construtores offline numa cópia, com o que mudou em cada arquivo |
| `validador.json` | asserções do `validate_project.py` que falham hoje e resultado do restante |

## Ambiente usado

Anaconda Python 3.12.7 com pandas 2.2.2, pyarrow 16.1.0 e duckdb 1.5.6, em
Windows 11. É o ambiente que o `README.md` do projeto indica
(`C:\Users\User\anaconda3\python.exe`).

Divergências em relação ao pacote novo (`pyproject.toml`):

- o pipeline importa **duckdb** em `build_sinan_atlas.py`, `fetch_populacao_geral.py`
  e `validate_project.py`, mas `pyproject.toml` e `requirements.txt` não o declaram;
- `pyproject.toml` fixa `pandas==2.2.2` e `pyarrow==16.1.0` (igual ao Anaconda),
  mas esses pins não têm build para Python 3.13; o ambiente de desenvolvimento
  dos agentes usa Python 3.11.

## Cadeia do pipeline

Ordem lógica reconstruída a partir dos scripts e da documentação. Não há
orquestrador: cada script é rodado à mão.

| Etapa | Scripts | Rede | Lê | Escreve |
| --- | --- | --- | --- | --- |
| 1. Extração | `extract_sinan.py`, `extract_sim.py`, `extract_sinesp.py` | sim | fontes públicas | Bronze e Silver; `extract_sinesp.py` também escreve a Gold `data/gold/sinesp` |
| 2. Dimensões | `fetch_ibge.py`, `fetch_malha_sc.py`, `fetch_populacao_feminina.py`, `fetch_populacao_geral.py` | sim | IBGE, MS | Bronze, Silver, malha do site |
| 3. Silver e Gold por fonte | `build_populacao_2025.py`, `build_sinan_atlas.py`, `build_sim_atlas.py`, `build_rais.py` | só `build_populacao_2025.py` e `build_sim_atlas.py` referenciam URLs | Bronze | Silver; `build_sinan_atlas.py` e `build_sim_atlas.py` também escrevem a Gold do atlas, `build_rais.py` a Gold da RAIS |
| 4. Silver territorial e Gold do painel | `build_silver.py`, `build_gold.py` (importa e executa `build_silver`) | não | Silver; `build_gold.py` também lê a Gold de `raca` e `rais` | `indicadores_territorio_ano.parquet`, `sinan_preliminar_territorio_ano.parquet`, `data/gold/painel.json`, cópia em `dashboard/dist/data` |
| 5. Gold analítico | `build_dashboard_analysis.py`, `build_integrated_analysis.py`, `build_sinesp_analysis.py`, `build_race_analysis.py`, `build_sinesp_atlas.py` | não | Silver; `build_race_analysis.py` lê `data/gold/ibge` e `build_sinesp_atlas.py` lê `data/gold/integrado/validacao_municipios_sinesp_sc.csv` | `data/gold/{analise.json,integrado,raca,atlas}` e relatórios em `docs/` |
| 6. Catálogo, protótipo e site | `build_atlas_catalog.py`, `build_atlas_prototype_data.py`, `build_atlas_site_data.py` | não | Silver e Gold | `data/gold/atlas` (catálogo), `dashboard/prototipos/atlas-violencia/data.json`, `dashboard/atlas/data` e os ZIPs de `dashboard/atlas/downloads` |
| 7. Validação | `validate_project.py` | não | Silver, Gold, site | nada |

A coluna "Rede" e as entradas e saídas vêm da leitura estática dos scripts
(imports e constantes de caminho); só as etapas 4 a 6 foram executadas. Há
dependências entre etapas que a ordem alfabética não revela: `build_gold.py`
precisa da Gold de `raca` e `rais`, e `build_sinesp_atlas.py` precisa de um CSV
gerado em `data/gold/integrado`.

Não existe nenhum teste automatizado dos construtores nem verificação de que as
etapas rodam na ordem certa.

## Contagens por camada

Totais do inventário: 17 Silver (18,98 milhões de linhas, 106 MB), 49 arquivos
Gold (297 mil registros CSV, 34,8 MB), 318 JSONs do site do atlas (33,4 MB), 3
ZIPs de download (1,8 MB), 2 JSONs do painel antigo (`dashboard/dist/data`) e o
`data.json` do protótipo local (16,4 MB, ignorado pelo Git). Bronze (1,4 GB) não
foi inventariada: é cache de fontes externas e não é versionada.

| Silver | linhas | colunas | bytes | sha256 (12) |
| --- | ---: | ---: | ---: | --- |
| `indicadores_territorio_ano.parquet` | 55.980 | 15 | 1.258.553 | `300bd0980ba9` |
| `populacao_feminina_municipio.parquet` | 55.700 | 5 | 465.591 | `985846f6597a` |
| `populacao_municipio_2025.parquet` | 5.571 | 8 | 194.160 | `0cccb0f1f162` |
| `populacao_municipio_ano.parquet` | 55.700 | 5 | 488.597 | `3a8c8822d36e` |
| `populacao_municipio_idade_ano.parquet` | 4.511.700 | 9 | 18.381.569 | `d51a6704d895` |
| `populacao_municipio_sexo_ano.parquet` | 111.400 | 6 | 851.309 | `0bdc958c206c` |
| `rais_escolaridade_raca_sexo.parquet` | 28.064 | 21 | 929.436 | `c883d1f15ee5` |
| `rais_movimentacao_mensal.parquet` | 30.900 | 18 | 387.099 | `96ac6c46202f` |
| `rais_vinculos_raca_sexo.parquet` | 26.036 | 21 | 831.957 | `8f7902f0db7b` |
| `sim_atlas_mortalidade.parquet` | 1.101.514 | 14 | 8.920.182 | `8a45923b27e4` |
| `sim_mulheres_agressao.parquet` | 44.831 | 11 | 485.164 | `0fe253d97106` |
| `sinan_atlas_violencia.parquet` | 4.292.317 | 18 | 23.350.495 | `9890299e4685` |
| `sinan_preliminar_territorio_ano.parquet` | 5.213 | 6 | 53.291 | `00481a81e14a` |
| `sinan_viol_mulheres_interpessoal.parquet` | 1.863.727 | 74 | 37.113.302 | `81c4830aa186` |
| `sinan_viol_mulheres_interpessoal_2025_preliminar.parquet` | 294.188 | 74 | 5.905.649 | `9f2757e2219d` |
| `sinesp_feminicidio.parquet` | 518.123 | 7 | 920.731 | `e2e652e28602` |
| `sinesp_vde_ocorrencias.parquet` | 5.975.255 | 17 | 5.875.579 | `4f69660af139` |

| Pasta Gold | arquivos | bytes | linhas CSV |
| --- | ---: | ---: | ---: |
| `data/gold` (raiz: `painel.json`, `analise.json`) | 2 | 4.804.288 | n/a |
| `data/gold/atlas` | 14 | 24.976.997 | 243.187 |
| `data/gold/ibge` | 2 | 26.185 | 323 |
| `data/gold/integrado` | 11 | 861.611 | 4.682 |
| `data/gold/raca` | 5 | 547.419 | 4.716 |
| `data/gold/rais` | 10 | 524.488 | 8.194 |
| `data/gold/sinesp` | 5 | 3.054.729 | 36.328 |

Hash de cada arquivo individual em `inventario.json`. A Silver é derivada de
Bronze e não é versionada; seus hashes só valem para esta máquina e servem para
detectar mudança, não para reprodução bit a bit entre máquinas.

Valores de controle verificados pelo `validate_project.py` (todos conferem na
carga atual): SINAN SC 2024 = 9.647 notificações; parceiro/ex-parceiro SC 2024 =
2.918; população feminina SC 2024 = 4.071.859; taxa SC 2024 = 236,92; SIM
agressão SC 2024 = 90; Silver territorial = 55.980 linhas (10 Brasil, 270 UF,
55.700 municípios); SINESP com os 12 meses de 2019 a 2025 e 8 meses em 2026.

## Resultado de `validate_project.py`

```powershell
C:\Users\User\anaconda3\python.exe pipeline\validate_project.py
```

**Falha hoje**, em cerca de 4 segundos, por duas asserções desatualizadas, não
por dado inválido:

| Linha | Asserção | Por que falha |
| --- | --- | --- |
| 327 | taxa SINAN 2025 (`sinan_violencia_territorio_ano.csv`) toda vazia | o commit `e7dc7ed` (6 nov) passou a publicar taxas de 2025: 8.721 de 11.628 linhas têm taxa (`tipo_denominador` = `estimado_proporcao_2024` ou `publicado`) |
| 360 | taxa SINESP de 2025 em diante toda vazia | mesmo motivo, na Gold `sinesp_prioridade_territorio_ano.csv` |

O modo `validador` do coletor roda uma cópia temporária do script, fora do
projeto e com o original intacto, e neutraliza uma a uma as asserções que
falham. Resultado em `validador.json`: só essas duas falham e **todas as demais
asserções passam** (4,5 s). O contrato do
SINAN da T02 deve decidir explicitamente o que vale para a taxa de 2025;
`docs/SINAN_ATLAS.md` ainda diz que a taxa de 2025 permanece vazia.

Conclusão: o validador atual não é um gate confiável para CI (T04) nem para
publicação segura (T05) enquanto não for atualizado.

## Reprodutibilidade dos construtores offline

Nove construtores que não precisam de rede nem de Bronze foram executados numa
cópia (`coletar_baseline.py reproduzir`) e 390 artefatos foram comparados antes
e depois. `build_gold.py` executa `build_silver` internamente, então a Silver
territorial também foi reconstruída.

| Script | Saída | Tempo |
| --- | --- | ---: |
| `build_gold.py` (inclui `build_silver`) | ok | 5,4 s |
| `build_dashboard_analysis.py` | ok | 1,9 s |
| `build_integrated_analysis.py` | ok | 2,6 s |
| `build_sinesp_analysis.py` | ok | 7,9 s |
| `build_race_analysis.py` | ok | 2,0 s |
| `build_sinesp_atlas.py` | ok | 39,6 s |
| `build_atlas_catalog.py` | ok | 0,9 s |
| `build_atlas_prototype_data.py` | ok | 2,3 s |
| `build_atlas_site_data.py` | ok | 10,6 s |

Resultado, com o detalhe de cada arquivo em `reproducao.json`:

- **Os 17 Parquets, os 39 CSV e 322 dos 331 JSON saíram idênticos byte a byte.**
- **8 JSONs** mudam em um único campo, o carimbo de data (`atualizado_em`,
  `meta.atualizado`, `meta.gerado_em` ou `gerado_em`): `manifesto.json`,
  `painel.json`, `analise.json`, `resumo_analises_sinesp.json`,
  `resumo_integracao.json`, `resumo_raca.json` e os dois espelhos em
  `dashboard/dist/data`.
- **Os 3 ZIPs de download** mudam de hash, mas o conteúdo (nomes, CRC e tamanho
  dos membros) é igual: a diferença é a data de modificação gravada no ZIP.
- **O `data.json` do protótipo local estava desatualizado**: 38.278 valores
  mudam, com taxas que passam de vazias a preenchidas. O arquivo é de 26 de
  outubro, anterior à publicação das taxas de 2025. Ele é ignorado pelo Git e
  não é publicado.

Os dois relatórios Markdown que os construtores escrevem em `docs/` também são
comparados com os originais (`relatorios_docs` em `reproducao.json`): em cada um
só muda a linha "Atualizado em".

Consequências para a publicação:

- a Gold é determinística dado o mesmo Silver; a data de geração é o único
  ruído, e ela faz o Git acusar mudança mesmo sem mudança de dado;
- os ZIPs precisam ser comparados por conteúdo, não por hash do arquivo;
- `build_integrated_analysis.py` e `build_sinesp_analysis.py` escrevem relatórios
  em `docs/` e falham se a pasta não existir.

## O que não foi reexecutado

Por exigirem rede ou o Bronze de 1,4 GB, ficam só inventariadas e **sem tempo
nem reprodução medidos**: `extract_*`, `fetch_*`, `build_populacao_2025.py`,
`build_sinan_atlas.py`, `build_sim_atlas.py` e `build_rais.py`. A Silver e a
Gold que elas produzem estão no inventário. O benchmark de tempo e memória dessas etapas
é insumo do Gate B.

## Como repetir

```powershell
$py = "C:\Users\User\anaconda3\python.exe"
$raiz = "C:\portfolio\painel-feminicidio"   # projeto com Silver e Gold materializadas
$saida = "C:\temp\baseline"                 # fora da raiz; C:\temp\copia deve estar vazia
$py docs\baseline\coletar_baseline.py inventario $raiz --saida $saida\inventario.json
$py docs\baseline\coletar_baseline.py reproduzir $raiz C:\temp\copia --saida $saida\reproducao.json
$py docs\baseline\coletar_baseline.py validador $raiz --saida $saida\validador.json
```

O coletor recusa `--saida` e `COPIA` dentro da raiz, para que a raiz nunca seja
escrita. Os JSON desta pasta foram gerados num worktree separado da raiz.

## Achados para as próximas tarefas

1. **T02/T03/T04/T05:** atualizar o `validate_project.py` (taxa 2025) antes de
   usá-lo como gate; o contrato deve decidir o que é esperado para 2025.
2. **Dependências:** declarar `duckdb` no `pyproject.toml` quando os scripts
   migrarem; definir um único Python (3.11) para desenvolvimento e CI.
3. **Publicação segura (T05):** ignorar ou normalizar os carimbos de data ao
   comparar Gold, para que "sem mudança de dado" signifique "sem diff".
4. **Caminhos pessoais:** o `README.md` do projeto referencia
   `C:\Users\User\anaconda3\python.exe`; os scripts usam `ROOT` relativo ao
   arquivo e são portáteis, mas escrevem em `docs/` sem criar a pasta.
