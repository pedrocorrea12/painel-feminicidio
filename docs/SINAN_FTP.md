# SINAN — mapeamento no FTP do DataSUS via PySUS 2.10

## Ambiente
- Python 3.13.2, pysus 2.10.0 (`pip install pysus nest_asyncio pyyaml`).
  Atenção: a instalação do pysus 2.10.0 NÃO puxa `pyyaml` como dependência,
  mas `import pysus` falha sem ele (`ModuleNotFoundError: No module named 'yaml'`).
  Precisa instalar manualmente.
- Cache local do pysus: `C:\Users\User\pysus` (mudar com `pysus.set_cache(...)`).
- `pysus.disable_progress_bars()` é essencial em qualquer execução não interativa
  (script/CI/log) — a barra tqdm do download escreve uma linha nova a cada poucos
  KB e pode gerar dezenas de milhares de linhas de log num arquivo de ~45MB.

## 1. API que funciona (confirmado)

```python
import pysus
client = pysus.api.PySUSClient()
ftp = await client.get_ftp()          # corrotina
datasets = await ftp.datasets()       # lista de objetos Dataset
sinan = [d for d in datasets if d.name == 'SINAN'][0]
```

`sinan.group_definitions` retorna o dicionário completo de grupos de agravo do
SINAN (chave = código de 4 letras, valor = nome). Confirmado:

```
'VIOL': 'Violência doméstica, sexual e/ou outras violências'
```
(a string chega em latin-1/cp1252 quando impressa no terminal Windows —
acentos aparecem como `�`, mas o valor em si está correto).

`sinan.paths` retorna 2 diretórios remotos:
```
\dissemin\publicos\SINAN\DADOS\FINAIS   (dados consolidados/definitivos)
\dissemin\publicos\SINAN\DADOS\PRELIM   (dados preliminares do ano corrente)
```

## 2. IMPORTANTE — os arquivos do SINAN no FTP são NACIONAIS, não por UF

Diferente do que o roteiro original assumia (`sinan.search(state="SC", year=2023)`),
**os arquivos de VIOL no FTP não são particionados por estado**. Cada arquivo é
um único `.dbc` com o Brasil inteiro para aquele ano, nomeado
`VIOLBR<AA>.dbc` (BR = literal "Brasil", não um filtro de estado).

`sinan.content` (não `sinan.paths`) é quem retorna a lista achatada de todos os
arquivos (1097 no total, todos os agravos). Para achar os arquivos de violência:

```python
contents = await sinan.content
viol_files = [f for f in contents if f.name.upper().startswith('VIOL')]
```

O atributo `.state` desses arquivos vem `None` (não há informação de UF no nome
do arquivo — só existe para bases que de fato são particionadas por estado, como
SIM/SINASC/SIH). Portanto **o filtro de UF (SC) tem que ser feito depois do
download, dentro dos dados**, usando as colunas de município de residência/
ocorrência/notificação — não há como baixar "só SC" direto do FTP para o SINAN.

`sinan.search(**kwargs)` existe mas casa atributos direto no objeto do arquivo
(via `getattr`) — como `state` é sempre `None` para VIOL, `search(state="SC")`
nunca vai casar nada. Usar filtro por `name.startswith('VIOL')` em `sinan.content`
é o caminho certo, e depois filtrar por `.year`.

## 3. Ponto decisivo: até que ano existe VIOL no FTP?

**Resultado: 2024 consolidado (FINAIS) + 2025 preliminar (PRELIM).**
Lista completa de arquivos encontrados (17 arquivos, um por ano):

| Arquivo       | Ano  | Diretório |
|---------------|------|-----------|
| VIOLBR09.dbc  | 2009 | FINAIS |
| VIOLBR10.dbc  | 2010 | FINAIS |
| VIOLBR11.dbc  | 2011 | FINAIS |
| VIOLBR12.dbc  | 2012 | FINAIS |
| VIOLBR13.dbc  | 2013 | FINAIS |
| VIOLBR14.dbc  | 2014 | FINAIS |
| VIOLBR15.dbc  | 2015 | FINAIS |
| VIOLBR16.dbc  | 2016 | FINAIS |
| VIOLBR17.dbc  | 2017 | FINAIS |
| VIOLBR18.dbc  | 2018 | FINAIS |
| VIOLBR19.dbc  | 2019 | FINAIS |
| VIOLBR20.dbc  | 2020 | FINAIS |
| VIOLBR21.dbc  | 2021 | FINAIS |
| VIOLBR22.dbc  | 2022 | FINAIS |
| VIOLBR23.dbc  | 2023 | FINAIS |
| VIOLBR24.dbc  | 2024 | FINAIS |
| VIOLBR25.dbc  | 2025 | PRELIM (dado ainda preliminar/em atualização) |

**Conclusão para o painel:** o FTP tem 2009–2024 consolidado, cobrindo todo o
período alinhado ao SIM (2015–2024) e ainda estendendo para trás até 2009. O
recorte da Base dos Dados (parado em 2019) era uma limitação da BD, não do
SINAN em si — pelo FTP dá pra ir até 2024 (e usar 2025 como preliminar/parcial
se quiser sinalizar tendência recente, com aviso de que é dado sujeito a revisão).

## 4. API alternativa de alto nível (`pysus.sinan(...)` / `pysus.list_files(...)`)

O pacote também expõe funções síncronas de conveniência:

```python
pysus.sinan(disease="VIOL", year=2024, state="SC", as_dataframe=True)
pysus.list_files("SINAN", group="VIOL", state="SC")
```

**Essas funções NÃO funcionaram neste ambiente** — ambas passam por um catálogo
"DuckLake" hospedado (`PySUS.__aenter__` sempre chama `await self._ducklake.connect()`,
que tenta baixar um catálogo de um endpoint S3 via HTTPS) e falharam com
`httpx.ConnectError` / `httpcore.ConnectError` (falha de conexão TCP/TLS, não
erro de autenticação nem 404). Não deu para confirmar se é bloqueio de rede
neste ambiente específico ou instabilidade do serviço. **Usar a rota de baixo
nível (`client.get_ftp()` → `sinan.content` → `client.download_to_parquet()`),
que fala direto com o FTP público do DataSUS e funcionou de ponta a ponta.**

Se em outro ambiente o DuckLake conectar, `pysus.list_files` seria mais
conveniente para listar anos/arquivos sem precisar navegar `sinan.content`
manualmente — vale re-testar lá.

## 5. Download e conversão (rota que funciona)

```python
pysus.disable_progress_bars()
client = pysus.api.PySUSClient()
ftp = await client.get_ftp()
datasets = await ftp.datasets()
sinan = [d for d in datasets if d.name == 'SINAN'][0]
contents = await sinan.content
viol_files = [f for f in contents if f.name.upper().startswith('VIOL')]
f2024 = [f for f in viol_files if f.year == 2024][0]

parquet = await client.download_to_parquet(f2024)   # download_to_parquet TAMBÉM é corrotina
df = parquet.load()
```

Notas de assinatura (via `inspect.signature`):
```
download_to_parquet(file: BaseRemoteFile, token: str|None=None,
                     callback: Callable|None=None, timeout: float|None=None,
                     add_dv: bool=True) -> Parquet
```
`add_dv=True` por padrão — provavelmente adiciona o dígito verificador do
código de município nas colunas de município (a confirmar na seção 6/7).

Arquivo VIOLBR24.dbc = 46.4 MB compactado.

## 6. Shape e colunas do VIOLBR24.dbc (2024, nacional)

`df.shape = (616548, 159)` — 616.548 notificações de violência no Brasil em 2024,
159 colunas. Nomes de coluna vêm exatamente como no dicionário oficial do SINAN
(sem tradução), ex: `CS_SEXO`, `LES_AUTOP`, `VIOL_FISIC`, `REL_CONJ` etc.

## 7. Mapeamento de campos de interesse → nomes ORIGINAIS no .dbc

| Campo de interesse (nome traduzido na BD) | Coluna original no .dbc | Valores observados |
|---|---|---|
| sexo do paciente | `CS_SEXO` | `'F'` feminino (437.828), `'M'` masculino (178.558), `'I'` ignorado (162) — **literal, sem a inversão contraintuitiva que existe na tabela traduzida da Base dos Dados** |
| lesão autoprovocada | `LES_AUTOP` | `'1'` Sim (189.926 = 31%, bate com o achado de 2019), `'2'` Não (401.983), `'9'` Ignorado (20.032), branco (4.607) |
| autor_conjugue | `REL_CONJ` | `'1'` Sim (66.288), `'2'` Não, `'9'` Ignorado, branco |
| autor_ex_conjugue | `REL_EXCON` | idem (32.731 Sim) |
| autor_namorado_a | `REL_NAMO` | idem (17.516 Sim) |
| autor_ex_namorado_a | `REL_EXNAM` | idem (10.366 Sim) |
| ocorreu_violencia_fisica | `VIOL_FISIC` | binário 1/2/9 |
| ocorreu_violencia_psicologica | `VIOL_PSICO` | binário 1/2/9 |
| ocorreu_violencia_sexual | `VIOL_SEXU` | binário 1/2/9 |
| tortura | `VIOL_TORT` | binário 1/2/9 |
| meio_ameaca | `AG_AMEACA` | binário 1/2/9 |
| meio_enforcamento | `AG_ENFOR` | binário 1/2/9 |
| meio_arma_fogo | `AG_FOGO` | binário 1/2/9 |
| meio_forca | `AG_FORCA` (força corporal/espancamento) | binário 1/2/9 |
| meio_objeto_perfurante | `AG_CORTE` (objeto cortante/perfurante) — existe também `AG_OBJETO` (objeto contundente) | binário 1/2/9 |
| encaminhamento_delegacia_mulher | `ENC_DEAM` (Delegacia Especializada de Atendimento à Mulher) | binário 1/2/9 |
| encaminhamento_atendimento_mulher | `ATEND_MULH` (coluna separada, perto do fim do dataset) | binário 1/2/9 |
| encaminhamento_defensoria_publica | `DEFEN_PUBL` | binário 1/2/9 |
| local_ocorrencia | `LOCAL_OCOR` | `'01'` Residência (417.242 — maioria, confirma achado do usuário), `'06'`, `'99'` Ignorado, `'09'`, `'03'`, `'07'`, `'05'`, `'02'`, `'04'`, `'08'` |
| id_municipio_notificacao | `ID_MUNICIP` | string, **7 dígitos já com DV** (confirmado: 100% dos 616.548 registros com len==7) |
| id_municipio_residencia | `ID_MN_RESI` | string, 7 dígitos já com DV (mesmo padrão de `ID_MUNICIP`) |
| id_municipio_ocorrencia | `ID_MN_OCOR` | **ATENÇÃO — ver seção 7.1** |
| UF de notificação/residência/ocorrência | `SG_UF_NOT` / `SG_UF` / `SG_UF_OCOR` | código IBGE de 2 dígitos; **SC = `'42'`** (confirmado por volume: 23.798–23.808 notificações/ano em SC contam com esse código) |

Todas as colunas 1/2/9 seguem o padrão SINAN: `1=Sim, 2=Não, 9=Ignorado, ''=branco/não preenchido`.
**Padronizar sempre comparando com string `'1'`/`'2'`, não int** — as colunas vêm
como `object`/string do parquet gerado pelo pysus.

### 7.1 Município de OCORRÊNCIA pode vir com 6 dígitos (sem DV) — confirmar com step7

`ID_MUNICIP` e `ID_MN_RESI` já saem com 7 dígitos (o `add_dv=True` padrão do
`download_to_parquet` parece cobrir esses dois campos). **`ID_MN_OCOR` nas
amostras observadas veio com 6 dígitos** (ex.: `520870`, `355030` — falta o DV).
Isso bate com o aviso original do usuário sobre o .dbc trazer município sem
dígito verificador — só que aparentemente é específico do campo de ocorrência,
não dos outros dois. **Confirmando com contagem completa do dataset antes de
fechar esse ponto** (rodando `step7_muncode.py`).

**CONFIRMADO** com a contagem completa do dataset 2024 (`step7_muncode.py`):

| Coluna | Distribuição de tamanho (string) |
|---|---|
| `ID_MUNICIP` | 7 dígitos: 616.548 (100%) |
| `ID_MN_RESI` | 7 dígitos: 616.453 (99,98%) · vazio: 95 |
| `ID_MN_OCOR` | **6 dígitos: 595.591 (96,6%)** · vazio: 20.957 |

Confirmado também dentro do recorte SC: `ID_MN_RESI` 100% com 7 dígitos
(23.798 registros), `ID_MN_OCOR` 100% com 6 dígitos (23.766 registros,
ex.: `'420540'`, `'421190'`).

**Decisão do usuário:** usar `ID_MN_RESI` (residência, já vem pronto com 7
dígitos) como chave territorial principal (`id_municipio`) do pipeline.
`ID_MUNICIP` (notificação) e `ID_MN_OCOR` (ocorrência, 6 dígitos, sem DV) são
**preservados como colunas extras no parquet final, sem de/para por enquanto**
— não usar `ID_MN_OCOR` como chave até que exista um de/para 6→7 dígitos
(via tabela de municípios do IBGE) caso seja necessário no futuro.

## 8. Número-alvo: mulheres + violência interpessoal + autor parceiro/ex-parceiro, SC, 2024

Filtro: `CS_SEXO=='F' & LES_AUTOP=='2' & SG_UF=='42' & (REL_CONJ=='1' | REL_EXCON=='1' | REL_NAMO=='1' | REL_EXNAM=='1')`
(`SG_UF` = UF de **residência**, coerente com a decisão já tomada para o SIM —
ver `CONTEXTO_PAINEL_FEMINICIDIO.md` §3.3, "Residência é o padrão").

| Etapa do funil | N (Brasil 2024, salvo indicação) |
|---|---|
| Total notificações VIOL 2024 | 616.548 |
| Mulheres | 437.828 |
| Mulheres + interpessoal (exclui autoprovocada) | 289.220 |
| Mulheres + interpessoal + residentes em SC | 9.647 |
| **Mulheres + interpessoal + SC + autor parceiro/ex-parceiro** | **2.918** |

Composição do autor dentro desses 2.918:
- Cônjuge: 1.773
- Ex-cônjuge: 575
- Namorado(a): 433
- Ex-namorado(a): 152

Top municípios de residência (SC) nesse recorte: Joinville (4204608) 203,
São José (4209102) 149, Itajaí (4208203) 132, **Florianópolis (4205407) 120**,
Palhoça (4216602) 115.

**Florianópolis isolado: 120 notificações** de mulheres vítimas de violência
interpessoal por parceiro/ex-parceiro em 2024.

## 9. Função de extração em loop

**Ajuste importante em relação ao roteiro original:** como os arquivos VIOL do
FTP são NACIONAIS por ano (não particionados por UF — seção 2), o loop
correto é **só por ANO**, não "UF × ano". O filtro de UF acontece depois do
download, dentro dos dados (`SG_UF` / `SG_UF_NOT` / `SG_UF_OCOR`). Isso também
significa que baixar todos os anos já traz automaticamente todos os estados —
não há economia em restringir por UF no download.

Ver `pipeline/extract_sinan.py` na raiz do projeto.

## 10. Resultado da extração (rodada 2015–2024)

```
python pipeline/extract_sinan.py
```

| Ano | Notificações brutas (Brasil) | Após filtro mulher + interpessoal |
|---|---|---|
| 2015 | 227.901 | 117.295 |
| 2016 | 243.259 | 130.541 |
| 2017 | 307.367 | 155.773 |
| 2018 | 350.354 | 175.580 |
| 2019 | 405.497 | 185.868 |
| 2020 | 326.503 | 154.616 |
| 2021 | 373.262 | 175.303 |
| 2022 | 442.680 | 205.159 |
| 2023 | 588.388 | 274.372 |
| 2024 | 616.548 | 289.220 |

(2019 bruto = 405.497 aqui vs. 405.441 citado no contexto original — diferença
de 56 registros, provavelmente snapshot do FTP levemente diferente do
snapshot que gerou a tabela na Base dos Dados; irrelevante para o painel.)

**Saída final:** `data/silver/sinan_viol_mulheres_interpessoal.parquet`
- 1.863.727 linhas × 73 colunas (69 colunas originais do SINAN + `id_municipio` + `ano`, sem agregação)
- 5.585 municípios distintos em `id_municipio`
- 36,1 MB
- Checagem: filtrar `ano==2024 & SG_UF=='42'` dá 9.647 linhas — bate exatamente
  com o número do funil da seção 8.

**Cache bruto** (`dados_sinan/cache_bruto/viol_<ano>_bruto.parquet`, 1 arquivo
por ano, dados nacionais sem filtro): 140 MB. Reexecutar o script não baixa de
novo os anos já cacheados — só recalcula o filtro e reconcatena. Apagar essa
pasta força um novo download completo do FTP.

## 11. Contexto do projeto (achado durante a exploração)

Existe um documento mestre em `C:\Users\User\Downloads\CONTEXTO_PAINEL_FEMINICIDIO.md`
com as decisões já tomadas para o SIM/população (chave `id_municipio` 7
dígitos + `ano`, residência como padrão territorial, tratamento de municípios
sem óbito, etc.) — os critérios usados nesta extração do SINAN (residência
como chave, não agregar, preservar `id_municipio`) foram alinhados a esse
documento. Ele também lista "SINAN via FTP — a investigar" como próximo
passo; com o resultado deste documento, esse item pode ser marcado como
concluído (VIOL vai até 2024 consolidado + 2025 preliminar).

Esse mesmo Downloads tem `homicidios_feminicidios.ipynb`, mas é sobre outro
projeto (homicídios via Databricks/SSP), não SINAN — não precisa ser
consultado para este trabalho.
