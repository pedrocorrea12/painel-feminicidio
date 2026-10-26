# Sinesp VDE: base de ocorrências do MJSP

## Fonte

Página oficial: https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023

Apesar do nome da URL ("2022 e 2023"), a página publica um arquivo por ano,
de 2015 a 2026, no padrão:

```text
https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-AAAA.xlsx/@@download/file
```

O portal `dados.mj.gov.br`, usado na versão anterior do extrator
(`basededadosvde.zip` e `indicadoressegurancapublicauf.xlsx`), saiu do ar em
2026 e o domínio não resolve mais. A página acima é a fonte oficial vigente.

## Estrutura do arquivo

Uma aba por ano, cerca de 765 mil linhas e 14 colunas:

| coluna | conteúdo |
| --- | --- |
| `uf`, `municipio` | UF e município do fato (`NÃO INFORMADO` quando o estado não informa) |
| `evento` | 31 indicadores (lista abaixo) |
| `data_referencia` | primeiro dia do mês de referência |
| `agente`, `arma`, `faixa_etaria` | desagregações exclusivas de alguns eventos (sem linha de total) |
| `feminino`, `masculino`, `nao_informado`, `total_vitima` | vítimas, para eventos contra a pessoa |
| `total` | contagem de ocorrências ou registros, para eventos patrimoniais e de produtividade |
| `total_peso` | quilos, para apreensões de cocaína e maconha |
| `abrangencia` | `Estadual`, `Polícia Federal` ou `Polícia Rodoviária Federal` |

Eventos: Feminicídio, Tentativa de feminicídio, Homicídio doloso, Tentativa de
homicídio, Lesão corporal seguida de morte, Roubo seguido de morte
(latrocínio), Estupro, Estupro de vulnerável, Morte por intervenção de Agente
do Estado, Morte de Agente do Estado, Suicídio, Suicídio de Agente do Estado,
Mortes no trânsito, Morte no trânsito ou em decorrência dele, Mortes a
esclarecer, Pessoa Desaparecida, Pessoa Localizada, Furto de veículo, Roubo de
veículo, Roubo de carga, Roubo a instituição financeira, Tráfico de drogas,
Apreensão de Cocaína, Apreensão de Maconha, Arma de Fogo Apreendida, Mandado
de prisão cumprido, Atendimento pré-hospitalar, Busca e salvamento, Combate a
incêndios, Realização de vistorias, Emissão de Alvarás de licença.

## Regras de leitura

- **Linhas repetidas no mesmo mês devem ser somadas.** A nota do MJSP cita
  Estupro e Tentativa de Homicídio, mas o padrão aparece em vários eventos:
  o DF, por exemplo, envia Brasília dividida em várias linhas por mês. Os
  valores são complementares, não cópias.
- **Zero é ausência de ocorrência, não ausência de dado** (nota dos gestores
  estaduais). Lacunas reais aparecem como meses sem linha.
- **Só a abrangência `Estadual` entra nos totais territoriais.** As linhas da
  PF e da PRF repetem eventos (tráfico, armas, mortes no trânsito) e dobrariam
  a contagem.
- Feminicídio é contado em vítimas (`total_vitima`); há registros residuais
  de vítimas masculinas em alguns estados (7 no Brasil em 2019), mantidos como
  publicados.
- O último ano publicado é parcial (em outubro de 2026, cobre janeiro a agosto).
- Dados de ocorrência policial, por local do fato. Não se comparam diretamente
  com SIM e SINAN, que usam residência da vítima e critérios de saúde.

## Conferência

Feminicídios por UF em 2019 batem com o Anuário Brasileiro de Segurança
Pública (Brasil 1.331; SC 58; SP 184; MG 149).

## Saídas no projeto

- Bronze: `data/bronze/sinesp/vde/bancovde-AAAA.xlsx` + cache parquet.
- Silver: `data/silver/sinesp_vde_ocorrencias.parquet` (base completa) e
  `data/silver/sinesp_feminicidio.parquet` (recorte usado pelo painel).
- Gold: `data/gold/sinesp/*.csv` com Brasil e Santa Catarina por mês, ano e
  evento, todas as UFs por ano e os municípios catarinenses por ano.

## Quebras de série conhecidas (conferir antes de comparar anos)

Os estados mudam sistemas e critérios de classificação, e o MJSP publica o que
recebe. Casos visíveis na série 2019 a 2026:

- **Estupro em SC**: 4.381 vítimas em 2019 contra 1.158 em 2020, enquanto
  Estupro de vulnerável segue estável (~3 mil/ano). Em 2019 SC parece ter
  somado as duas naturezas na linha de Estupro. Para comparar anos, use a soma
  Estupro + Estupro de vulnerável.
- **Estupro no ES** (2023 e 2025), **RO** (2025) e **MA** (2021): quedas de mais
  de 60% em um ano, sem contrapartida em outro evento. Tratar como lacuna de
  envio, não como queda real.
- **Feminicídio** não apresenta quebra visível em SC nem no Brasil no período.

## Validação para o atlas

O processo `pipeline/build_sinesp_atlas.py` verifica os nove eventos
prioritários do atlas. A presença mensal é avaliada pela existência das linhas,
e não pelo valor numérico. Assim, um mês com zero ocorrência continua sendo
considerado informado.

Resultados da carga atual:

- Todas as 27 UFs têm os 12 meses esperados de 2019 a 2025.
- Todas as 27 UFs têm os 8 meses esperados de janeiro a agosto de 2026.
- Feminicídio, tentativa de feminicídio, homicídio doloso, tentativa de
  homicídio e suicídio têm linhas para os 295 municípios de Santa Catarina.
- Estupro, estupro de vulnerável, pessoa desaparecida e pessoa localizada
  aparecem somente como total estadual e não suportam análise municipal.
- As taxas são calculadas somente até 2024, último ano com denominador
  populacional compatível.
- A série de 2026 permanece parcial e não deve ser comparada com anos cheios.

Saídas:

- `data/gold/atlas/sinesp_cobertura_evento_uf_ano.csv`
- `data/gold/atlas/sinesp_cobertura_evento_resumo.csv`
- `data/gold/atlas/sinesp_prioridade_territorio_ano.csv`
- `data/gold/atlas/sinesp_prioridade_mensal.csv`
- `data/gold/atlas/sinesp_prioridade_metodologia.json`
