# Contrato de dados do SINAN

## Escopo

Este contrato cobre os artefatos SINAN usados pelo Panorama Territorial da
Violência. A fonte é o conjunto nacional anual de violência interpessoal e
autoprovocada do DataSUS. Os registros são notificações, não pessoas únicas, e
um registro pode marcar mais de um tipo de violência.

O contrato valida duas granularidades porque elas possuem regras de chave
distintas:

- Silver do atlas: uma linha por notificação classificada;
- Gold territorial: uma linha por combinação anual de território, indicador e
  sexo.

O extrator legado também materializa um recorte de mulheres com violência
interpessoal, usando `CS_SEXO = F`, `LES_AUTOP = 2`, município de residência e
separação entre anos definitivos e preliminares. Esse recorte é usado como
controle de reconciliação, mas não possui uma chave única por notificação.

## Silver do atlas

O arquivo `data/silver/sinan_atlas_violencia.parquet` segue o esquema abaixo.

| Coluna | Tipo lógico | Regra |
| --- | --- | --- |
| `ano` | inteiro | entre 2015 e 2025 |
| `mes` | numérico inteiro anulável | quando presente, entre 1 e 12 |
| `data_ocorrencia` | data anulável | entre 1900-01-01 e 2025-12-31; seu mês deve coincidir com `mes` |
| `sexo` | texto | `feminino`, `masculino` ou `não informado` |
| `raca` | texto | classificação de raça ou cor |
| `idade_anos` | numérico inteiro anulável | idade derivada de `NU_IDADE_N`, entre 0 e 130 |
| `grupo_etario` | texto | faixa derivada da idade |
| `natureza_violencia` | texto | `interpessoal` ou `autoprovocada` |
| `id_municipio_residencia` | texto anulável | código IBGE de residência |
| `sigla_uf_residencia` | texto anulável | UF derivada do município |
| `violencia_fisica` | booleano | campo original igual a 1 e natureza interpessoal |
| `violencia_psicologica` | booleano | mesma regra do tipo correspondente |
| `violencia_sexual` | booleano | mesma regra do tipo correspondente |
| `violencia_financeira` | booleano | mesma regra do tipo correspondente |
| `negligencia` | booleano | mesma regra do tipo correspondente |
| `tortura` | booleano | mesma regra do tipo correspondente |
| `trafico_pessoas` | booleano | mesma regra do tipo correspondente |
| `situacao_dado` | texto | `definitivo` até 2024 e `preliminar` em 2025 |

A Silver não declara uma chave única. `ano + id_municipio_residencia` representa
a dimensão territorial da análise, mas pode se repetir porque várias
notificações podem ocorrer no mesmo município e ano. Inventar uma chave com
esses campos eliminaria registros legítimos.

Na materialização observada, `mes` e `idade_anos` são armazenados como
`float64` por causa dos valores ausentes. O contrato aceita essa representação
somente quando todos os valores presentes são inteiros; valores fracionários,
como `3.5`, são rejeitados. `mes` e `data_ocorrencia` devem ser nulos juntos.
Quando presentes, o mês deve estar entre 1 e 12 e coincidir com o mês de
`data_ocorrencia`.

O campo `ano` identifica o arquivo anual ou ano de referência da notificação;
ele não é necessariamente o ano da ocorrência. Na Silver observada, 184.393
datas presentes têm ano diferente de `ano`, principalmente notificações de
ocorrências anteriores. Por isso o contrato não exige igualdade linha a linha,
mas exige que pelo menos 90% das datas presentes pertençam ao ano da
notificação. A proporção observada é 95,70%.

Os limites foram calibrados sem descartar a materialização real: há 6.094 datas
anteriores a 2000, com mínimo em 1900-01-01, e 23 idades acima de 120, com
máximo em 130. O contrato rejeita datas anteriores a 1900 ou posteriores ao fim
do período contratado (2025-12-31), idades fora de 0 a 130 e classificações de
sexo fora do domínio publicado.

No artefato validado durante a revisão, 467 de 4.292.317 notificações
(aproximadamente 0,0109%) possuem `mes` e `data_ocorrencia` nulos. Esses nulos
são preservados porque representam ausência conjunta da data de ocorrência, e
não uma quebra do contrato.

## Gold territorial

O arquivo `data/gold/atlas/sinan_violencia_territorio_ano.csv` contém:

| Coluna | Tipo lógico |
| --- | --- |
| `ano`, `notificacoes` | inteiro |
| `nivel_territorial`, `id_territorio`, `territorio` | texto |
| `indicador`, `sexo` | texto |
| `populacao`, `taxa_100mil` | numérico anulável |
| `tipo_denominador`, `situacao_dado` | texto anulável |

Ao carregar o CSV, `id_territorio` deve ser declarado como texto, por exemplo
com `pd.read_csv(..., dtype={"id_territorio": "string"})`. Sem essa declaração,
códigos municipais numéricos e identificadores como `BR` podem produzir uma
coluna de tipos mistos, que é rejeitada pelo contrato.

A chave de granularidade é:

```text
ano + nivel_territorial + id_territorio + indicador + sexo
```

Cada série definida por `nivel_territorial + id_territorio + indicador + sexo`
deve possuir exatamente um registro por ano de 2015 a 2025.

## Periodicidade e ano preliminar

Os arquivos de origem são nacionais e anuais. O período contratado é 2015 a
2025. Até 2024, `situacao_dado` deve ser `definitivo`; 2025 deve permanecer
`preliminar` porque está sujeito a atualização.

O contrato não obriga presença ou ausência da taxa de 2025. A implementação
atual calcula taxas quando existe denominador compatível, enquanto a
documentação histórica registra a publicação apenas de valores absolutos. A
regra estável nesta tarefa é a classificação explícita do ano como preliminar.

## Validação

`validar_silver_atlas` verifica colunas, tipos lógicos, intervalo anual, nulos
conjuntos de mês e data, coerência e limites da data, proporção mínima de datas
no ano da notificação, limites de idade, domínio de sexo, natureza da violência
e situação do dado.

`validar_gold_territorial` verifica colunas, tipos, chave única, cobertura anual
de cada série e situação do dado. As duas funções levantam `ValueError` com
mensagens estáveis.

As fixtures em `tests/fixtures/sinan/` são pequenas e inteiramente sintéticas.
Elas não reproduzem registros individuais do DataSUS.
