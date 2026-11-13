# SINAN no Panorama Territorial da Violência

## Fonte

Sistema de Informação de Agravos de Notificação, ficha de violência
interpessoal e autoprovocada. Os arquivos nacionais anuais foram obtidos no
FTP público do DataSUS e permanecem no cache local em formato Parquet.

## Colunas principais

| Coluna | Uso |
| --- | --- |
| `DT_OCOR` | data e mês da ocorrência |
| `CS_SEXO` | sexo da pessoa notificada |
| `CS_RACA` | raça ou cor da pessoa notificada |
| `NU_IDADE_N` | idade e grupo etário |
| `ID_MN_RESI` | município de residência usado nas taxas |
| `LES_AUTOP` | separa violência autoprovocada e interpessoal |
| `VIOL_FISIC` | marcação de violência física |
| `VIOL_PSICO` | marcação de violência psicológica |
| `VIOL_SEXU` | marcação de violência sexual |
| `VIOL_FINAN` | marcação de violência financeira |
| `VIOL_NEGLI` | marcação de negligência |
| `VIOL_TORT` | marcação de tortura |
| `VIOL_TRAF` | marcação de tráfico de pessoas |

## Regras

Violência interpessoal:

`LES_AUTOP igual a 2`

Violência autoprovocada:

`LES_AUTOP igual a 1`

Cada tipo de violência exige a marcação do campo correspondente igual a 1 e
`LES_AUTOP igual a 2`.

## Unidade e cálculo

A unidade é a notificação. O SINAN não identifica pessoas únicas para esta
análise. Tipos de violência podem coexistir no mesmo registro e não devem ser
somados entre si.

Taxa por 100 mil habitantes:

`notificações de residentes / população residente x 100.000`

As taxas são calculadas de 2015 a 2025. Até 2024 o denominador é a população
publicada por sexo (`tipo_denominador = publicado`). Em 2025, que continua
preliminar, o total usa a estimativa oficial do IBGE para 1º de julho de 2025
(`publicado`) e os recortes feminino e masculino aplicam a proporção municipal
de 2024 a esse total (`estimado_proporcao_2024`), conforme
`pipeline/build_populacao_2025.py`. Linhas de sexo não informado não têm
denominador nem taxa em nenhum ano.

## Saídas

- `data/silver/sinan_atlas_violencia.parquet`
- `data/gold/atlas/sinan_violencia_territorio_ano.csv`
- `data/gold/atlas/sinan_violencia_idade_ano.csv`
- `data/gold/atlas/sinan_violencia_metodologia.json`

## Controles

1. A série deve cobrir 2015 a 2025.
2. Violência interpessoal e autoprovocada devem permanecer separadas.
3. O recorte feminino interpessoal deve coincidir com as duas Silver anteriores
   em cada ano.
4. Brasil, UFs e municípios de Santa Catarina não podem ter chave duplicada.
5. Tipos de violência não podem ser somados.
6. Taxa, população e `tipo_denominador` existem juntos, só para sexo total,
   feminino e masculino. Até 2024 o denominador é `publicado`; em 2025 é
   `publicado` para o total e `estimado_proporcao_2024` por sexo.
7. O ano de 2025 permanece `preliminar`, mesmo com taxa.
