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
| `mes` | inteiro | entre 1 e 12 |
| `data_ocorrencia` | data | deve pertencer ao mesmo `ano` |
| `sexo` | texto | classificação da pessoa notificada |
| `raca` | texto | classificação de raça ou cor |
| `idade_anos` | inteiro anulável | idade derivada de `NU_IDADE_N` |
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

## Gold territorial

O arquivo `data/gold/atlas/sinan_violencia_territorio_ano.csv` contém:

| Coluna | Tipo lógico |
| --- | --- |
| `ano`, `notificacoes` | inteiro |
| `nivel_territorial`, `id_territorio`, `territorio` | texto |
| `indicador`, `sexo` | texto |
| `populacao`, `taxa_100mil` | numérico anulável |
| `tipo_denominador`, `situacao_dado` | texto anulável |

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

`validar_silver_atlas` verifica colunas, tipos, intervalo anual, mês, coerência
da data, natureza da violência e situação do dado.

`validar_gold_territorial` verifica colunas, tipos, chave única, cobertura anual
de cada série e situação do dado. As duas funções levantam `ValueError` com
mensagens estáveis.

As fixtures em `tests/fixtures/sinan/` são pequenas e inteiramente sintéticas.
Elas não reproduzem registros individuais do DataSUS.
