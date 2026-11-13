# Baseline do pipeline atual (T01)

Registro do estado do pipeline em 12 de novembro de 2026, commit-base `e70609d`
(branch `engenharia-dados`), antes de qualquer refatoração. Nada em `pipeline/`,
`data/` ou `dashboard/` foi alterado: toda execução abaixo foi somente leitura
ou numa cópia descartável.

Arquivos desta pasta:

| Arquivo | Conteúdo |
| --- | --- |
| `coletar_baseline.py` | coletor reproduzível (inventário e teste de reprodução) |
| `inventario.json` | 386 artefatos com bytes, linhas, colunas e SHA-256 |
| `reproducao.json` | resultado da reconstrução dos construtores offline numa cópia |

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
| 1. Extração | `extract_sinan.py`, `extract_sim.py`, `extract_sinesp.py` | sim | fontes públicas | Bronze e Silver |
| 2. Dimensões | `fetch_ibge.py`, `fetch_malha_sc.py`, `fetch_populacao_feminina.py`, `fetch_populacao_geral.py` | sim | IBGE, MS | Bronze, Silver, malha do site |
| 3. Silver | `build_silver.py`, `build_populacao_2025.py`, `build_sinan_atlas.py`, `build_sim_atlas.py`, `build_rais.py` | não | Bronze | Silver (e Gold da RAIS) |
| 4. Gold do painel | `build_gold.py` (chama `build_silver`) | não | Silver | `data/gold/painel.json`, cópia em `dashboard/dist/data` |
| 5. Gold analítico | `build_dashboard_analysis.py`, `build_integrated_analysis.py`, `build_sinesp_analysis.py`, `build_race_analysis.py`, `build_sinesp_atlas.py` | não | Silver | `data/gold/{analise.json,integrado,raca,atlas}` e relatórios em `docs/` |
| 6. Catálogo e site | `build_atlas_catalog.py`, `build_atlas_prototype_data.py`, `build_atlas_site_data.py` | não | Gold, Bronze (catálogo) | `data/gold/atlas`, `dashboard/atlas/data` |
| 7. Validação | `validate_project.py` | não | Silver, Gold, site | nada |

Não existe nenhum teste automatizado dos construtores nem verificação de que as
etapas rodam na ordem certa.

## Contagens por camada

Totais do inventário: 17 Silver (18,98 milhões de linhas, 106 MB), 49 arquivos
Gold (297 mil linhas CSV, 34,8 MB), 318 JSONs do site do atlas (33,4 MB) e 2 do
painel antigo (`dashboard/dist/data`). Bronze (1,4 GB) não foi inventariada: é
cache de fontes externas e não é versionada.

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

Rodando uma cópia do script sem essas duas asserções (copiada para fora do
projeto, original intacto), **todas as demais asserções passam**. O contrato do
SINAN da T02 deve decidir explicitamente o que vale para a taxa de 2025;
`docs/SINAN_ATLAS.md` ainda diz que a taxa de 2025 permanece vazia.

Conclusão: o validador atual não é um gate confiável para CI (T04) nem para
publicação segura (T05) enquanto não for atualizado.

## Reprodutibilidade dos construtores offline

Oito construtores que não precisam de rede nem de Bronze foram executados numa
cópia (`coletar_baseline.py reproduzir`) e os hashes de 386 artefatos foram
comparados antes e depois:

| Script | Saída | Tempo |
| --- | --- | ---: |
| `build_gold.py` | ok | 5,6 s |
| `build_dashboard_analysis.py` | ok | 2,0 s |
| `build_integrated_analysis.py` | ok | 2,7 s |
| `build_sinesp_analysis.py` | ok | 8,3 s |
| `build_race_analysis.py` | ok | 2,1 s |
| `build_sinesp_atlas.py` | ok | 40,4 s |
| `build_atlas_prototype_data.py` | ok | 2,3 s |
| `build_atlas_site_data.py` | ok | 10,6 s |

Resultado: **todos os CSV e a maior parte dos JSON saíram idênticos byte a
byte**. Mudaram apenas 8 arquivos, e em cada um a única diferença é um carimbo
de data (`atualizado_em`, `meta.atualizado`, `gerado_em`): `manifesto.json`,
`painel.json`, `analise.json`, `resumo_analises_sinesp.json`,
`resumo_integracao.json`, `resumo_raca.json` e os espelhos em `dashboard/dist`.
Os dois relatórios Markdown em `docs/` também só mudam a linha "Atualizado em".

Consequências para a publicação:

- a Gold é determinística dado o mesmo Silver; a data de geração é o único
  ruído, e ela faz o Git acusar mudança mesmo sem mudança de dado;
- `build_integrated_analysis.py` e `build_sinesp_analysis.py` escrevem relatórios
  em `docs/` e falham se a pasta não existir.

## O que não foi reexecutado

Por exigirem rede, Bronze de 1,4 GB ou escreverem fora de áreas isoladas, ficam
só inventariadas e **sem tempo nem reprodução medidos**: `extract_*`, `fetch_*`,
`build_silver.py`, `build_populacao_2025.py`, `build_sinan_atlas.py`,
`build_sim_atlas.py`, `build_rais.py` e `build_atlas_catalog.py`. A Silver
correspondente está no inventário. O benchmark de tempo e memória dessas etapas
é insumo do Gate B.

## Como repetir

```powershell
$py = "C:\Users\User\anaconda3\python.exe"
# a raiz do projeto com Silver e Gold materializadas; a pasta COPIA deve estar vazia
$py docs\baseline\coletar_baseline.py inventario C:\portfolio\painel-feminicidio --saida inventario.json
$py docs\baseline\coletar_baseline.py reproduzir C:\portfolio\painel-feminicidio C:\temp\copia --saida reproducao.json
$py pipeline\validate_project.py
```

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
