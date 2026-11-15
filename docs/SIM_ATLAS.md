# SIM no Panorama Territorial da Violência

## Fonte

Sistema de Informações sobre Mortalidade, SIM, do Ministério da Saúde.

Arquivos anuais usados: `data/bronze/sim/Mortalidade_Geral_AAAA_csv.zip`.

Dicionário oficial:

https://svs.aids.gov.br/daent/cgiae/coesv/sistemas-informacao/sim/documentacao/dicionario-de-dados-SIM-tabela-DO.pdf

## Colunas utilizadas

| Coluna | Uso |
| --- | --- |
| `DTOBITO` | data e mês do óbito |
| `SEXO` | masculino, feminino ou não informado |
| `RACACOR` | branca, preta, amarela, parda, indígena ou não informada |
| `IDADE` | idade em anos e grupo etário |
| `CODMUNRES` | município de residência, usado nas taxas |
| `CODMUNOCOR` | município onde ocorreu o óbito, preservado para comparação |
| `CAUSABAS` | causa básica segundo a CID-10 |

## Grupos de causa

| Indicador | Regra |
| --- | --- |
| Óbitos por agressão | CID-10 X85 a Y09 |
| Óbitos por suicídio | CID-10 X60 a X84 |
| Óbitos por acidentes de transporte | CID-10 V01 a V99 |

Os três grupos são exclusivos pela causa básica do óbito.

## Cálculos

Taxa territorial por 100 mil habitantes:

`óbitos de residentes / população residente x 100.000`

Taxa por sexo por 100 mil habitantes do mesmo sexo:

`óbitos de residentes do sexo / população residente do sexo x 100.000`

Taxa por idade por 100 mil habitantes do mesmo grupo etário:

`óbitos de residentes do grupo etário / população residente do grupo etário x 100.000`

As taxas são calculadas de 2015 a 2024. Os denominadores locais não cobrem
2025 e 2026. Nesses anos, o projeto exibe somente valores absolutos e informa a
situação do dado.

## Situação dos anos

| Período | Situação |
| --- | --- |
| 2015 a 2024 | definitivo |
| 2025 | preliminar |
| 2026 | prévia |

## Saídas

- `data/silver/sim_atlas_mortalidade.parquet`
- `data/gold/atlas/sim_mortalidade_territorio_ano.csv`
- `data/gold/atlas/sim_mortalidade_idade_ano.csv`
- `data/gold/atlas/sim_mortalidade_metodologia.json`

## Controles

1. A cobertura anual deve incluir 2015 a 2026.
2. Os três grupos de causa devem estar presentes.
3. O recorte de mulheres mortas por agressão deve coincidir com
   `sim_mulheres_agressao.parquet` em cada ano.
4. Brasil, UFs e municípios de Santa Catarina não podem ter chave duplicada.
5. Taxas de 2025 e 2026 devem permanecer vazias.
6. Sexo e idade não são cruzados porque os denominadores populacionais são
   recortes separados.
