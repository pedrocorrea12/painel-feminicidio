# Benchmark local do pipeline (Gate B)

Medição de tempo, pico de memória e volume de cada estágio que roda sem rede.
Serve de base para escolher o executor (GitHub Actions, AWS) e estimar custo.
Dados brutos em [`medicoes.json`](medicoes.json).

## Como reproduzir

```powershell
.venv\Scripts\python -m pip install psutil xlrd   # só para a medição (ver "Achados")
.venv\Scripts\python tools\medir_estagios.py --copia C:\caminho\novo\vazio `
  --origem C:\caminho\do\checkout\com\data --repeticoes 3 --saida docs\benchmark\medicoes.json
```

O script copia `pipeline/`, `src/`, `data/` e as pastas do dashboard para uma pasta
**fora** do repositório e roda cada estágio num subprocesso: os estágios só gravam
na cópia. Apenas o JSON de resultados (`--saida`) é gravado onde você indicar. Pico de memória: o maior entre o pico do conjunto de trabalho de um processo
da árvore e a soma simultânea dos processos (amostragem a cada 20 ms; em Windows o `python` de um venv é um
lançador, por isso a árvore inteira é observada).

## Ambiente medido

Windows 11, Python 3.11.9, 16 CPUs, SSD local. Entrada: Bronze 1.414 MB, Silver
102 MB, Gold 33 MB. Três repetições por estágio. Nos estágios acima de 5 s a amplitude
entre repetições ficou em até 5,4%; nos de cerca de 1 s ela chega a 14%, o que são
centésimos de segundo. Usa-se a mediana.

## Resultados

| Grupo | Estágio | Tempo (mediana) | Pico de memória | Escrito |
| --- | --- | ---: | ---: | ---: |
| Bronze → Silver | `build_populacao_2025.py` | 1,1 s | 131 MB | 0,2 MB |
| Bronze → Silver | `build_sinan_atlas.py` | 30,4 s | **5.241 MB** | 34,1 MB |
| Bronze → Silver | `build_sim_atlas.py` | **76,6 s** | 1.370 MB | 12,6 MB |
| Bronze → Silver | `build_rais.py` | 1,5 s | 137 MB | 2,5 MB |
| Silver → Gold | `build_gold.py` | 5,9 s | 999 MB | 9,8 MB |
| Gold analítica | `build_dashboard_analysis.py` | 1,9 s | 684 MB | 0,6 MB |
| Gold analítica | `build_integrated_analysis.py` | 2,5 s | 670 MB | 0,6 MB |
| Gold analítica | `build_sinesp_analysis.py` | 8,2 s | 4.104 MB | 0,2 MB |
| Gold analítica | `build_race_analysis.py` | 2,0 s | 418 MB | 0,5 MB |
| Gold analítica | `build_sinesp_atlas.py` | 38,3 s | 4.281 MB | 7,9 MB |
| Site | `build_atlas_catalog.py` | 0,8 s | 94 MB | 0,02 MB |
| Site | `build_atlas_prototype_data.py` | 2,1 s | 149 MB | 15,7 MB |
| Site | `build_atlas_site_data.py` | 12,1 s | 261 MB | 33,2 MB |
| | **Soma sequencial** | **≈ 183 s (3 min)** | **máx. 5,2 GB** | |

Leitura rápida:

- O pipeline inteiro, depois que a Bronze existe, roda em **cerca de 3 minutos** e
  precisa de **até ~5,2 GB de memória** (picos em `build_sinan_atlas`,
  `build_sinesp_atlas` e `build_sinesp_analysis`). Os estágios não precisam rodar em
  paralelo, então o pico da execução é o do maior estágio.
- A Bronze (1,4 GB, 65% do SIM) não é versionada; qualquer executor precisa
  baixá-la ou restaurá-la de um cache.
- Dois estágios concentram o tempo: `build_sim_atlas` (42% do total) e
  `build_sinesp_atlas` (21%). Uma otimização futura (leitura por colunas, tipos
  menores) reduziria memória e tempo, mas não é pré-requisito.

## Não medido

- **Estágios de rede**: `extract_sinan.py`, `extract_sim.py`, `extract_sinesp.py`,
  `fetch_*`. Dependem da rede, do DataSUS (FTP via `pysus`) e do IBGE; o tempo é
  dominado pela fonte, e o tamanho da Bronze (SIM 917 MB, SINESP 186 MB, SINAN 165
  MB, IBGE 139 MB, RAIS 9 MB) é o único indicador local. Medir numa execução real
  antes de decidir o executor do **download**.
- Execução em Linux e em máquinas com menos núcleos. Os estágios são quase todos
  de um núcleo só (pandas); o ganho de CPUs extras é pequeno.

## Executores candidatos

| Critério | Local (máquina do dono) | GitHub Actions (agendado) | AWS Lambda | Contêiner (ECS/Fargate ou Batch) |
| --- | --- | --- | --- | --- |
| Memória | medido: 5,2 GB de pico | runner padrão de repositório público: 16 GB (privado: 8 GB), folga sobre os 5,2 GB | configurável até 10 GB; cabe, mas com folga curta e CPU proporcional | configurável |
| Duração | medido: ≈ 3 min | até 6 h por job; 3 min medidos, mais download | máximo 15 min; 3 min medidos mais download da Bronze pode estourar | sem teto prático |
| Disco | medido: Bronze + Silver + Gold ≈ 1,6 GB | ~14 GB livres; cabe Bronze + Silver + Gold (1,6 GB) | `/tmp` configurável até 10 GB; Bronze precisa vir do S3 | configurável |
| Dependências | venv local | `pip install` na hora (pyarrow, pandas, duckdb, pysus) | camada ou imagem; pacote grande | imagem própria |
| Custo estimado | 0, mas depende de a máquina estar ligada | 0 (repositório público) | ver abaixo | ver abaixo |
| Observabilidade | só o terminal | log por execução, histórico no GitHub | CloudWatch | CloudWatch |
| Esforço | nenhum, já é manual | menor: já existe `ci.yml` | médio | maior |

Os limites dos executores seguem a documentação pública do GitHub e da AWS, conferida na revisão cruzada;
confira os valores vigentes antes de decidir, pois mudam.

### Custo estimado (referência, confirmar nos preços vigentes)

Preços públicos de referência, não verificados nesta sessão; confirmar antes de usar.

- **Lambda, execução completa:** 10 GB × 183 s ≈ 1.830 GB·s, na faixa de US$ 0,03 por
  execução (arquitetura x86, preço de lista). Mensal com uma execução por mês:
  centavos.
- **S3:** Bronze 1,4 GB + Silver/Gold ~0,14 GB no padrão: poucos centavos por mês.
  Requisições e transferência são desprezíveis neste volume.
- **Logs:** retenção curta mantém o custo abaixo de centavos.
- Ordem de grandeza total do laboratório: **menos de US$ 1 por mês**, desde que
  agendamentos sejam desligados e o orçamento com alerta esteja ativo.

## Recomendação

1. **Executor do pipeline: GitHub Actions agendado.** Sem custo, 16 GB de memória
   sobra 3×, já temos CI e OIDC é possível. As medições não justificam Lambda ou
   contêiner para o processamento.
2. **O que a AWS acrescenta de valor no laboratório (T06):** armazenamento
   durável e versionado da Gold e dos manifestos de execução em S3, com acesso do
   GitHub por OIDC sem chave fixa, logs e destruição documentada. É o que ensina o
   padrão de nuvem a custo mínimo.
3. **Lambda/contêiner só se** a medição dos estágios de rede mostrar que eles
   passam de 15 minutos (aí contêiner) ou se quisermos demonstrar execução
   serverless de um estágio leve (por exemplo `build_atlas_site_data`, 261 MB,
   12 s) como exercício explícito de portfólio.
4. **Antes da T06:** medir uma execução real dos estágios `extract_*`/`fetch_*`,
   e decidir quanto da Bronze vale manter em cache (S3 ou `actions/cache`).

## Achados

- **Dependência não declarada:** `build_populacao_2025.py` lê `.xls` e exige
  `xlrd`, que não está em `pyproject.toml`; o estágio falha num ambiente limpo
  (`ImportError: Missing optional dependency 'xlrd'`). Também `pysus` só existe no
  extra `sinan`. Registrado como pedido na T12.
- A medição inicial de memória com o processo direto dava ~5 MB: no Windows o
  `python` do venv é um lançador. A versão final amostra a árvore de processos.
