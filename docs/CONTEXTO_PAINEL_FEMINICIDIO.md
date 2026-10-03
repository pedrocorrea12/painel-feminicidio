# Painel de Indicadores — Violência contra a Mulher e Feminicídio

**Documento mestre de contexto.** Registra decisões, fontes validadas, armadilhas descobertas e o que falta fazer.

---

## 1. Objetivo

Painel de tela única (HTML estático) com indicadores de feminicídio e violência contra a mulher, com contexto **Brasil / UF / município**.

**Gancho temporal:** 7 de agosto de 2026 — 20 anos da Lei Maria da Penha (Lei 11.340/2006).

**Recorte territorial de interesse:** Santa Catarina e Florianópolis, com Brasil como referência.

---

## 2. Status das fontes

| Fonte | Status | Cobertura | Onde está |
|---|---|---|---|
| **SIM** (óbitos) | Validado | 2015–2024 | BigQuery / Base dos Dados |
| **População MS** | **Baixado e tratado** | 2015–2024 no Silver | Dados Abertos do SUS / DEMAS |
| **Diretório municípios** | OK | Atual | API de Localidades do IBGE |
| **SINAN Violência** | **Validado via FTP** | 2009–2024 (consolidado) + 2025 (preliminar) | FTP DataSUS via PySUS — ver `SINAN_FTP.md` |
| **Sinesp-VDE** (feminicídio) | Não iniciado | 2015–2026 | CSV gov.br |
| **CNJ** (medidas protetivas) | Não iniciado | — | Painel CNJ |

**Base dos Dados está encerrada.** Não há Sinesp, CNJ, FBSP nem dataset de segurança pública no catálogo. O que faltar vem de fora.

**Atualização 2026-08-24:** o SINAN via BigQuery/BD parava em 2019 (limitação da BD, não da fonte). Investigado o caminho direto pelo FTP do DataSUS via PySUS — vai até 2024 consolidado + 2025 preliminar, cobrindo todo o período do SIM. Ver §5.

---

## 3. Decisões metodológicas tomadas

### 3.1 Fonte principal
**BigQuery / Base dos Dados**, não PySUS — para SIM e população.
- Microdados com `data_obito` real (DATE), municípios de residência **e** ocorrência separados, valores já decodificados (`feminino`, `parda`, `via publica`).
- PySUS fica como backup e caminho de atualização quando o DataSUS publicar antes da BD sincronizar.
- **Exceção: SINAN.** Para violência não letal, a BD para em 2019 — o FTP via PySUS é a fonte principal aqui, não backup (ver §5).

### 3.2 Definição do indicador de letalidade
Óbitos de **mulheres por agressão**, CID-10 **X85–Y09**.

Feminicídio **não existe no DataSUS** — é categoria jurídico-policial. O SIM registra "agressão", sem distinguir razão de gênero. O contraste entre os dois é em si um indicador (ver §7).

### 3.3 Residência vs. ocorrência
**Residência é o padrão.**
- Teste SC/2023: 105 por residência, 103 por ocorrência — diferença irrelevante em nível estadual.
- Em nível municipal importa: cidades com hospital de referência (Florianópolis, Joinville) atraem óbitos de fora.
- Residência é o padrão do TabNet, o que facilita conferência externa.
- Mesmo critério aplicado ao SINAN: chave territorial = `ID_MN_RESI` (residência), não `ID_MN_OCOR` (ver §5.3).

### 3.4 Denominador
`br_ms_populacao.municipio` — população do **Ministério da Saúde**, com sexo e faixa etária.
- Mesma fonte que o TabNet usa para calcular taxas do SIM: numerador e denominador coerentes.
- Cobre 2000–2025.
- Taxas sempre **por 100 mil mulheres**, nunca número absoluto em comparações territoriais.

### 3.5 Tratamento de 2025
População existe, óbitos não.
- `obitos` = **NULL** (não zero — zero significaria "nenhuma morreu").
- Flag `sim_disponivel` = FALSE.
- `taxa_100mil` = NULL.
- A população de 2025 fica na base porque serve de denominador para indicadores futuros com outra janela temporal.
- O SINAN 2025 (PRELIM) segue a mesma lógica: existe mas é dado sujeito a revisão — sinalizar como preliminar se usado.

### 3.6 Municípios sem óbito
Preservados com **zero explícito** dentro da janela de cobertura do SIM.
- A query parte da **população** (todos os municípios, todos os anos) e traz óbitos via LEFT JOIN.
- Se partisse dos óbitos, ~4.600 municípios sumiriam e o mapa teria buracos em vez de áreas claras.

### 3.7 Granularidade dos recortes
- **Brasil e UF:** série anual e mensal, recortes por raça/idade/meio.
- **Município:** apenas total anual. Cruzamentos (raça × idade × meio) em nível municipal geram células com 1–2 casos — sem valor analítico e com risco de identificação.
- Ranking municipal por taxa: usar **agregação plurianual** (3 ou 5 anos). Um único caso em cidade de 5 mil habitantes gera taxa de 40/100 mil e distorce o mapa.

### 3.8 Chave territorial do SINAN
`id_municipio` = `ID_MN_RESI` do SINAN, que já sai do pysus 2.10 com 7 dígitos
(dígito verificador aplicado automaticamente por `download_to_parquet`,
parâmetro `add_dv=True` por padrão). `ID_MUNICIP` (notificação) e `ID_MN_OCOR`
(ocorrência, vem com **6 dígitos**, sem DV) são preservados como colunas
extras no parquet, mas não usados como chave — ver §5.3 e §6 item 4 corrigido.

---

## 4. Validações realizadas

### Validação cruzada (crítica)
**SC / 2023 / mulheres / X85–Y09 = 105 óbitos**

Confirmado por dois caminhos independentes:
1. PySUS → FTP DataSUS → `DOSC2023.dbc` → filtro em pandas
2. BigQuery → `br_ms_sim.microdados` → filtro em SQL

**105 = 105.** O filtro está provado.

### Completude de 2024
2024 é **definitivo**, não preliminar. Óbitos por mês em SC:

| Ano | Jan–Dez | Total |
|---|---|---|
| 2022 | 13,4,3,15,6,3,6,10,7,8,8,10 | 93 |
| 2023 | 12,6,11,6,11,7,8,6,9,11,8,10 | 105 |
| 2024 | 8,7,13,5,10,12,2,8,5,6,5,9 | 90 |

Dezembro/2024 (9) está em linha com 2022 (10) e 2023 (10). Não há queda progressiva nos últimos meses — padrão típico de base preliminar. Pode usar 2024 sem ressalva.

### Perfil SC/2023 (105 óbitos)
- **Meio:** X99 (objeto cortante) 24, X95 (arma de fogo) 11+8, X93/X94 presentes
- **Raça:** 84 brancas, 14 pardas, 5 pretas, 1 indígena
- **Municípios:** Joinville (420910) 9, Blumenau (420820) 6, Criciúma (420420) 5, Florianópolis (420540) 3

### SINAN / SC / 2024 (violência não letal, ver §5)
9.647 mulheres residentes em SC notificadas com violência interpessoal
(exclui autoprovocada) em 2024. Desse total, 2.918 com autor parceiro ou
ex-parceiro, das quais 120 residentes em Florianópolis.

---

## 5. SINAN via FTP — violência não letal (resolvido em 2026-08-24)

Investigação completa documentada em detalhe técnico em **`SINAN_FTP.md`**
(mesma pasta deste documento) — inclui exploração passo a passo da API do
pysus, todo o dicionário de colunas mapeado e os logs de execução. Resumo
executivo abaixo.

### 5.1 API funcionando (pysus 2.10)

```python
import pysus
pysus.disable_progress_bars()

client = pysus.api.PySUSClient()
ftp = await client.get_ftp()              # corrotina
datasets = await ftp.datasets()
sinan = [d for d in datasets if d.name == 'SINAN'][0]

contents = await sinan.content             # lista achatada de TODOS os arquivos do SINAN
viol_files = [f for f in contents if f.name.upper().startswith('VIOL')]

f2024 = [f for f in viol_files if f.year == 2024][0]
parquet = await client.download_to_parquet(f2024)   # TAMBÉM é corrotina no 2.10
load_result = parquet.load()
df = await load_result if inspect.iscoroutine(load_result) else load_result  # .load() as vezes e coroutine
```

Pegadinhas de instalação/ambiente:
- `pip install pysus` **não** puxa `pyyaml`, mas `import pysus` quebra sem ele — instalar manual.
- `pysus.disable_progress_bars()` é obrigatório em script/log não interativo (tqdm floodava o log).
- A API de alto nível (`pysus.sinan(...)`, `pysus.list_files(...)`) depende de
  um catálogo "DuckLake" hospedado que **não conectou neste ambiente**
  (`httpx.ConnectError`). Usar sempre a rota de baixo nível acima, que fala
  direto com o FTP público e funcionou de ponta a ponta.

### 5.2 Achado decisivo: cobertura do grupo VIOL

Código do grupo: **`VIOL`** ("Violência doméstica, sexual e/ou outras violências").

**Arquivos nacionais por ano** (não particionados por UF — diferente do
SIM/SINASC): `VIOLBR<AA>.dbc`, de **2009 a 2024** em
`/dissemin/publicos/SINAN/DADOS/FINAIS`, mais **2025** (preliminar) em
`/dissemin/publicos/SINAN/DADOS/PRELIM`.

**Consequência prática:** o loop de extração é só por **ANO**, não "UF × ano"
— um único arquivo por ano já traz o Brasil inteiro. O filtro de UF/município
acontece depois, dentro dos dados (colunas `SG_UF` / `SG_UF_NOT` / `SG_UF_OCOR`).

### 5.3 Mapeamento de campos principais (nomes ORIGINAIS no .dbc)

| Campo de interesse | Coluna original | Observação |
|---|---|---|
| sexo do paciente | `CS_SEXO` | `'F'`/`'M'`/`'I'` — literal, **sem** a inversão contraintuitiva da tabela traduzida da BD |
| lesão autoprovocada | `LES_AUTOP` | `1`=Sim, `2`=Não, `9`=Ignorado — filtrar sempre `== '2'` para violência interpessoal |
| autor cônjuge / ex-cônjuge / namorado(a) / ex-namorado(a) | `REL_CONJ` / `REL_EXCON` / `REL_NAMO` / `REL_EXNAM` | binário 1/2/9 |
| violência física/psicológica/sexual/tortura | `VIOL_FISIC` / `VIOL_PSICO` / `VIOL_SEXU` / `VIOL_TORT` | binário 1/2/9 |
| meio (ameaça/enforcamento/arma de fogo/força/objeto cortante) | `AG_AMEACA` / `AG_ENFOR` / `AG_FOGO` / `AG_FORCA` / `AG_CORTE` | binário 1/2/9 |
| encaminhamento (DEAM/atendimento mulher/defensoria) | `ENC_DEAM` / `ATEND_MULH` / `DEFEN_PUBL` | binário 1/2/9 |
| local de ocorrência | `LOCAL_OCOR` | `'01'` = Residência (maioria dos casos) |
| município notificação / residência / ocorrência | `ID_MUNICIP` / `ID_MN_RESI` / `ID_MN_OCOR` | ver §3.8 — só `ID_MN_RESI` usado como chave |
| UF notificação / residência / ocorrência | `SG_UF_NOT` / `SG_UF` / `SG_UF_OCOR` | código IBGE 2 dígitos, SC = `'42'` |

Todas as colunas binárias seguem `1=Sim, 2=Não, 9=Ignorado` como **string**, não int.

### 5.4 Número-alvo SC/Florianópolis 2024

Filtro: mulher + violência interpessoal + residente em SC + autor parceiro/ex-parceiro.

| Etapa do funil | N (2024) |
|---|---|
| Total notificações VIOL (Brasil) | 616.548 |
| Mulheres | 437.828 |
| + interpessoal (exclui autoprovocada) | 289.220 |
| + residentes em SC | 9.647 |
| **+ autor parceiro/ex-parceiro** | **2.918** |

Composição do autor: cônjuge 1.773, ex-cônjuge 575, namorado(a) 433, ex-namorado(a) 152.
**Florianópolis isolada: 120** notificações.

### 5.5 Extração final (pipeline local, 2015–2024)

Script: `pipeline/extract_sinan.py` — loop por ano com cache em disco
(`data/bronze/sinan/cache_bruto/viol_<ano>_bruto.parquet`, dados nacionais sem
filtro), filtra mulher + interpessoal, preserva `id_municipio` (=`ID_MN_RESI`)
+ `ano` sem agregar, salva parquet único.

**Saída:** `data/silver/sinan_viol_mulheres_interpessoal.parquet`
- 1.863.727 linhas × 73 colunas, 2015–2024, 5.585 municípios distintos, 36,1 MB
- Checagem: `ano==2024 & SG_UF=='42'` → 9.647 linhas, bate com §5.4

Esse parquet ainda não foi cruzado com população/SIM — falta decidir se ele
entra no pipeline via join direto em pandas/Colab ou se primeiro sobe pra
algum storage intermediário. Ver §9 "Próximos passos".

---

## 6. Armadilhas descobertas (não repetir)

1. **`sexo_paciente = 0` é FEMININO no SINAN (tabela traduzida da Base dos Dados).** Contraintuitivo — só se aplica à BD, não ao .dbc original do FTP, onde `CS_SEXO` já vem como `'F'`/`'M'` literal (ver §5.3).

2. **Tipos mistos no SINAN (BD).** `lesao_autoprovocada` e `sexo_paciente` são INT64; `ocorreu_*` e `autor_*` são STRING. Comparar com aspas ou sem, conforme o campo. No .dbc via pysus, **todas** as colunas binárias (`LES_AUTOP`, `REL_*`, `VIOL_*`, `AG_*` etc.) vêm como string — comparar sempre com `'1'`/`'2'`.

3. **SINAN mistura violência interpessoal e autoprovocada.** Sem filtrar `lesao_autoprovocada = 0` (BD) / `LES_AUTOP == '2'` (FTP), tentativas de suicídio entram no indicador de agressão. Em 2019: 126.666 de 405.441/405.497 notificações eram autoprovocadas (~31% — confirmado em ambas as fontes, BD e FTP).

4. **Código de município sem dígito verificador — depende do campo, não é regra geral.** No SIM (`CODMUNRES`) e no SINAN via FTP, **`ID_MN_OCOR`** (ocorrência) vem com 6 dígitos, sem DV. Mas **`ID_MUNICIP`** (notificação) e **`ID_MN_RESI`** (residência) do SINAN **já saem com 7 dígitos** no pysus 2.10 — o `download_to_parquet` aplica o DV automaticamente para esses dois campos (`add_dv=True` por padrão). Sempre conferir `.astype(str).str.len().value_counts()` por campo antes de assumir — não generalizar de um campo pro outro.

5. **A antiga extração por UF da Base dos Dados repetia 2022 em 2023.** A fonte
   direta DEMAS/RIPSA usada na pipeline atual possui valores distintos para os
   dois anos; não reutilizar o artefato antigo no cálculo das taxas.

6. **Tabela `br_ms_sim.municipio_causa_idade_sexo_raca` para em 2019.** Não usar. A tabela certa é `br_ms_sim.microdados`.

7. **A API DEMAS (`apidadosabertos.saude.gov.br`) NÃO expõe SIM nem SINAN.** Só CNES, SISAGUA, SISVAN, vacinação COVID, e-SUS Notifica. Não perder tempo ali.

8. **Metadados da BD mostram cobertura da FONTE, não da tabela.** A página do SINAN diz 2026; a tabela `br_ms_sinan.microdados_violencia` vai até 2019. Sempre confirmar com `SELECT DISTINCT ano`. **O FTP não tem essa limitação** — vai até 2024 consolidado (ver §5.2).

9. **Custo BigQuery.** `br_ms_sim.microdados` é o Brasil desde 1979. Sempre filtrar por `ano` (particionada) e nunca `SELECT *`. A query auto-gerada da BD com 11 LEFT JOINs é armadilha de custo.

10. **`pysus.list_files()` e `pysus.sinan()` (API de alto nível) dependem de um catálogo hospedado que pode não conectar.** Falhou com `httpx.ConnectError` neste ambiente. Usar a rota de baixo nível (`client.get_ftp()` → `sinan.content` → `client.download_to_parquet()`), que não depende desse catálogo.

11. **`download_to_parquet()` e `.load()` são corrotinas no pysus 2.10** — precisam de `await`, mesmo quando o arquivo já está em cache local. Sem isso o erro é silencioso até tentar usar o resultado (`AttributeError: 'coroutine' object has no attribute ...`).

---

## 7. Cruzamentos que contam história

- **Taxa de feminicídio × medidas protetivas per capita** — a proteção chega onde se morre mais?
- **SIM × Sinesp** — "mulheres mortas por agressão" vs. "classificadas como feminicídio". A razão varia entre UFs e revela diferença de **classificação**, não de realidade.
- **Notificações (SINAN/Ligue 180) × feminicídios** — município com morte alta e denúncia baixa sugere silêncio, não segurança. Agora viável com dados reais até 2024 (§5).
- **Raça/cor via SIM** — a queda (ou estabilidade) da violência é desigual entre mulheres brancas e negras.
- **Linha do tempo 2006–2026** com marcos legais: Lei Maria da Penha (2006), Lei do Feminicídio (2015), feminicídio como crime autônomo (2024).

---

## 8. Arquitetura definida

```
BigQuery (SIM + população + municípios)  ──┐
                                            ├──> pandas (Colab) ──> fato única ──> painel.json
SINAN (FTP DataSUS via PySUS, local)     ──┤
Sinesp-VDE (CSV gov.br)                  ──┘
```

- Joins acontecem no **Colab** (SIM/população/Sinesp), não no navegador.
- SINAN é extraído localmente (pysus não roda bem em Colab sem ajustes de
  async — ver §9) e entra no pipeline como parquet já filtrado, pronto pra
  upload/join junto com as outras fontes.
- O JSON é o **produto final** da pipeline, não a matéria-prima.
- Chave universal: `id_municipio` (7 dígitos) + `ano` (inteiro) — mesma chave
  em todas as fontes, incluindo SINAN (§3.8).
- Painel: **HTML único** (HTML+CSS+JS, D3 ou Plotly). Sem framework — não há login, backend nem múltiplas páginas.
- Atualização = rodar o Colab de novo (+ reexecutar `extract_sinan_viol.py` se o ano mudou) e trocar o JSON.

### Estrutura sugerida do JSON
```json
{
  "meta":       { "atualizado": "...", "fontes": [...], "notas": [...] },
  "brasil":     [ {"ano": 2015, "obitos": 4621, "taxa": 4.4} ],
  "ufs":        { "SC": [ {...} ] },
  "municipios": { "4205407": {"nome": "Florianópolis", "uf": "SC", "serie": [...]} },
  "recortes":   { "raca": {...}, "faixa_etaria": {...}, "meio": {...} }
}
```

**Mapa:** 5.570 polígonos municipais pesam 2–5 MB e travam em celular. Alternativa: mapa por UF (27 polígonos) com drill-down só para SC, ou UF + tabela ranqueada de municípios.

**Flag `dado_suficiente`:** municípios com menos de ~5 casos acumulados devem exibir "dado insuficiente" em vez de taxa sem sentido.

---

## 9. Query final validada (fato municipal — SIM)

```sql
WITH obitos AS (
  SELECT
    ano,
    id_municipio_residencia AS id_municipio,
    COUNT(*) AS obitos
  FROM `basedosdados.br_ms_sim.microdados`
  WHERE ano BETWEEN 2015 AND 2024
    AND sexo = 'feminino'
    AND (causa_basica BETWEEN 'X85' AND 'X99Z'
      OR causa_basica BETWEEN 'Y00' AND 'Y09Z')
  GROUP BY 1,2
),
pop AS (
  SELECT ano, id_municipio, SUM(populacao) AS pop_feminina
  FROM `basedosdados.br_ms_populacao.municipio`
  WHERE sexo = 'feminino' AND ano >= 2015
  GROUP BY 1,2
)
SELECT
  p.ano,
  p.id_municipio,
  m.nome AS municipio,
  m.sigla_uf,
  p.pop_feminina,
  o.obitos,
  (p.ano <= 2024) AS sim_disponivel,
  CASE WHEN p.ano <= 2024
       THEN ROUND(SAFE_DIVIDE(COALESCE(o.obitos, 0), p.pop_feminina) * 100000, 2)
       ELSE NULL END AS taxa_100mil
FROM pop p
LEFT JOIN obitos o
  ON p.id_municipio = o.id_municipio AND p.ano = o.ano
LEFT JOIN (SELECT DISTINCT id_municipio, nome, sigla_uf
           FROM `basedosdados.br_bd_diretorios_brasil.municipio`) m
  ON p.id_municipio = m.id_municipio
ORDER BY p.ano, m.sigla_uf, m.nome;
```

**Saída:** `obitos_brasil.json` — ~61 mil linhas (5.570 municípios × 11 anos).

### SINAN — filtro equivalente (agora via FTP, não mais BD)

A query BD abaixo (histórico 2009–2019, `br_ms_sinan.microdados_violencia`)
está **superada** pelo pipeline local via FTP (§5), que cobre até 2024.
Mantida aqui só como referência do filtro conceitual (a versão viva, em
pandas, está em `dados_sinan/extract_sinan_viol.py`):

```sql
-- HISTÓRICO / SUPERADO — usar dados_sinan/sinan_viol_filtrado.parquet
SELECT
  COUNT(*) AS total_notificacoes,
  COUNTIF(ocorreu_violencia_fisica = '1')        AS fisica,
  COUNTIF(ocorreu_violencia_psicologica = '1')   AS psicologica,
  COUNTIF(ocorreu_violencia_sexual = '1')        AS sexual,
  COUNTIF(encaminhamento_delegacia_mulher = '1') AS enc_deam,
  COUNTIF(local_ocorrencia = 1)                  AS na_residencia
FROM `basedosdados.br_ms_sinan.microdados_violencia`
WHERE ano = 2019
  AND id_uf_residencia = 42
  AND sexo_paciente = 0
  AND lesao_autoprovocada = 0
  AND (autor_conjugue = '1' OR autor_ex_conjugue = '1'
    OR autor_namorado_a = '1' OR autor_ex_namorado_a = '1');
```

Equivalente em pandas (dados de `sinan_viol_mulheres_interpessoal.parquet`, já filtrado
para mulher + interpessoal — só falta UF e autor):
```python
alvo = df[
    (df["SG_UF"] == "42") &
    ((df["REL_CONJ"] == "1") | (df["REL_EXCON"] == "1") |
     (df["REL_NAMO"] == "1") | (df["REL_EXNAM"] == "1"))
]
```

---

## 10. Setup do PySUS (funcionando — pysus 2.10)

A API mudou entre versões. O que funciona hoje (confirmado em 2026-08-24,
ver detalhamento completo em `SINAN_FTP.md`):

```python
!pip install pysus nest_asyncio pyyaml -q   # pyyaml NAO e dependencia automatica, mas e obrigatorio
import nest_asyncio; nest_asyncio.apply()
import pysus, inspect

pysus.disable_progress_bars()               # essencial fora de notebook interativo

client = pysus.api.PySUSClient()
ftp = await client.get_ftp()                # corrotina
datasets = await ftp.datasets()
sim = [d for d in datasets if d.name == 'SIM'][0]

# search NAO aceita 'group' — so state e year (e so funciona p/ bases particionadas por UF, tipo SIM/SINASC)
arquivos = await sim.search(state="SC", year=2023)

parquet = await client.download_to_parquet(arquivos[0])   # TAMBEM e corrotina
load_result = parquet.load()                                # TAMBEM pode ser corrotina
df = await load_result if inspect.iscoroutine(load_result) else load_result
```

**Notas:**
- `download` espera caminho de **arquivo**, não pasta.
- SIM no FTP: CID-10 de 1996 a 2024, 27 UFs + arquivo `BR` agregado (particionado por UF).
- **SINAN não é particionado por UF** — arquivos nacionais por ano (`VIOLBR<AA>.dbc`). `sinan.search(state=...)` não funciona pra ele; usar `sinan.content` + filtro por nome/ano (ver §5.1-5.2).
- `pysus.list_files()` / `pysus.sinan()` de alto nível existem mas dependem
  de um catálogo hospedado ("DuckLake") que não conectou neste ambiente —
  preferir a rota de baixo nível acima até confirmar em outro ambiente.

---

## 11. Próximos passos

1. ~~**SINAN via PySUS/FTP**~~ — **concluído em 2026-08-24.** VIOL vai até 2024
   consolidado + 2025 preliminar. Parquet filtrado pronto em
   `data/silver/sinan_viol_mulheres_interpessoal.parquet`. A camada Gold é gerada
   por `pipeline/build_gold.py` e consumida pelo painel estático.
   O parquet entra no join final com SIM/população.
2. ~~**População feminina municipal**~~ — **concluído em 2026-10-01.** Fonte
   oficial do Ministério da Saúde baixada diretamente e recortada para
   2015–2024 em `data/silver/populacao_feminina_municipio.parquet`. O cruzamento
   com o SINAN está materializado em `data/silver/indicadores_territorio_ano.parquet`,
   e as taxas por 100 mil mulheres já são exportadas para a Gold.
3. **Sinesp-VDE** — baixar CSV do gov.br, checar granularidade (municipal? mensal?), testar join por `id_municipio`. Maior risco técnico: formatos variam por UF.
4. **Recortes agregados** — segunda tabela com raça × idade × meio por UF/Brasil. Agora dá pra fazer o mesmo recorte pro SINAN (colunas `CS_RACA`, `NU_IDADE_N`, `VIOL_FISIC`/`_PSICO`/`_SEXU` já mapeadas — ver §5.3).
5. **Protótipo HTML** — layout e narrativa antes de plugar o dado real.
6. **CNJ** (opcional) — medidas protetivas por comarca. Exige tabela de correspondência comarca → município.

**Fonte do Sinesp:**
https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023

---

## 12. Notas metodológicas para o painel

Devem aparecer no produto final:

- SIM registra **agressões**, não feminicídios. Categorias diferentes, fontes diferentes.
- SINAN registra **notificações de violência não letal** — não é o mesmo universo do SIM (que é óbito). Cruzar os dois mostra o funil violência→morte, não uma soma.
- Critérios de classificação **variam entre UFs**; nem toda polícia segue as diretrizes nacionais de classificação de feminicídio.
- Monitores independentes (Lesfem/UEL) apontaram números **38,8% acima** do Sinesp em 2025 — indício de subnotificação oficial.
- Municípios pequenos: taxas instáveis. Usar agregação plurianual.
- Dados de residência, não de ocorrência (SIM e SINAN).
- 2015 como início da série coincide com a Lei do Feminicídio.
- Recorte racial exige denominador por raça — a proporção populacional muda a leitura.

---

## Estrutura de arquivos do projeto

```
C:\portfolio\painel-feminicidio\
├── CONTEXTO_PAINEL_FEMINICIDIO.md      (este arquivo — documento mestre)
├── SINAN_FTP.md                        (detalhamento técnico da investigação do FTP)
├── pipeline\                           (extração, transformação e validação)
├── data\bronze\sinan\                 (cache bruto e log de extração)
├── data\silver\                       (microdados tratados)
├── data\gold\                         (agregados consumidos pelo painel)
└── dashboard\dist\                    (site estático)
```
