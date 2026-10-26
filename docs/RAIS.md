# RAIS vínculos por raça/cor e sexo

## Fonte

Tabela `obsref.rais.flat_vinculos_unificado` no Databricks do Observatório FIESC
(uma linha por vínculo, safras anuais). Os SQLs de extração estão em
`pipeline/sql/rais_obsref_raca_sexo.sql`. Os CSVs exportados ficam em
`data/bronze/rais/obsref/`, ignorados pelo Git:

| Bloco | Arquivo | Grão |
| --- | --- | --- |
| 1A | `rais_br_uf_sexo_raca.csv` | Brasil (`BR`) e UF × ano × sexo × raça |
| 1B | `rais_sc_municipio_sexo_raca.csv` | município de SC × ano × sexo × raça |
| 2 | `rais_br_uf_sexo_raca_escolaridade.csv` | Brasil e UF × ano × sexo × raça × escolaridade |
| 4 | `rais_br_uf_mes_sexo_raca_admissoes_desligamentos.csv` | Brasil e UF × mês × sexo × raça (admissões e desligamentos) |

O bloco 3 (município de SC × escolaridade × faixa etária) foi removido em
15/10/2026. O Brasil vem como linha `BR` via `GROUPING SETS`, com mediana
calculada sobre todos os vínculos; o grão municipal só existe para SC, porque
a versão Brasil inteiro passava de 65 mil linhas por ano e não cabia na
exportação.

Os blocos 0.x são conferência e não são exportados. O bloco 0.1 diz quais safras
existem; o 0.2 confirma os códigos; o 0.3 mede a fatia de raça não identificada
por UF e ano; o 0.4 verifica se o espelho do SIDRA no Databricks tem as tabelas
do Censo 2022 (9605, 10061, 10295), o que dispensaria a API do IBGE.

## Decisões de método

- **Território é o do estabelecimento** (`cd_municipio_6d`). A coluna
  `cd_municipio_trabalho` vem 999999 ou nula na base inteira. Não é residência:
  em região metropolitana, Florianópolis concentra empregos de São José e
  Palhoça. Preferir razões (salarial, participação) a taxas sobre população.
- **Estoque = vínculo ativo em 31/12.** Os blocos 1 a 3 são estoque. O bloco 4
  usa todos os vínculos do ano, de propósito, para contar admissões e
  desligamentos por mês.
- **Remuneração de dezembro, só valores positivos**, no numerador e no
  denominador. Média e mediana (`percentile_approx`) calculadas sobre o mesmo
  conjunto. Valores nominais: deflacionar antes de comparar anos.
- **Raça/cor é declarada pelo empregador**, não pela pessoa. Isso embranquece a
  base em relação ao Censo, ao SIM e ao SINAN. Por isso os indicadores comparam
  participações (RAIS contra Censo), nunca dividem vínculos por população por
  raça como se fosse taxa. A fatia "não identificada" (código 9) é reportada
  por UF e ano; acima de 10% a UF recebe flag de cautela.
- **Códigos RAIS** (confirmados no bloco 0.2 em 15/10/2026): raça 1 indígena,
  2 branca, 4 preta, 6 amarela, 8 parda, 9 "Nao ident" e 99 "Não informado",
  os dois últimos tratados como não identificada; sexo 1 masculino, 2 feminino
  (9 existe em 56 linhas, descartar); escolaridade 1 a 11, com 99 em 56 linhas.
- **Safras**: 2008 a 2025. Brasil 2019 = 46,7 milhões de vínculos ativos,
  SC 2025 = 2,95 milhões, coerentes com a RAIS pública. A série pode começar
  em 2015 se o painel precisar. O agregado "negra"
  (preta + parda) é calculado em pandas. Mapeamento para o padrão do projeto
  (SIM/SINAN: 1 branca, 2 preta, 3 amarela, 4 parda, 5 indígena) na Silver.
- **Só emprego formal.** Em estados pouco formalizados a RAIS cobre fatia
  pequena das mulheres negras. Comparar cada UF consigo mesma ao longo do tempo
  antes de comparar UFs entre si.

## Quebra de série em raça/cor (conferido em 15/10/2026, bloco 0.3)

Somando os códigos 9 e 99, a fatia de vínculos sem raça identificada é:

| Ano | SC | SP | Brasil, faixa entre UFs |
| --- | --- | --- | --- |
| 2019 | 30,0% | 18,2% | 18% a 64% (AC, AP, RR, TO acima de 53%) |
| 2022 | 36,8% | 22,8% | 23% a 64% |
| 2023 | 13,3% | 6,3% | 6% a 25% (código 99 some) |
| 2024 | 4,6% | 2,4% | 2% a 13% (PI, RN, AC, PB acima de 10%) |
| 2025 | 3,2% | 1,7% | 2% a 10% |

Consequências para o projeto:

- **Raça/cor na RAIS só é usável a partir de 2024**, com 2023 em cautela e
  2019 a 2022 descartados para qualquer recorte racial. A não identificação
  não é aleatória (concentra-se no Norte e Nordeste e muda com o porte e o
  setor da empresa), então filtrar os informados não corrige o viés.
- **Não há painel por raça.** Os indicadores raciais são corte transversal
  de 2024 e 2025 por UF, e pooled 2024–2025 por município de SC.
- **O painel 2019–2025 fica só por sexo**: participação feminina e razão
  salarial mulher/homem, que não dependem de raça. É a variável da hipótese
  de Aizer e continua válida.
- UFs com mais de 10% de não identificada em 2024 ou 2025 recebem flag.
- As extrações (blocos 1 a 4) não mudam: trazem `cd_raca` bruto por ano, e o
  corte é feito em pandas.

## Indicadores previstos (Gold)

Por sexo, 2019 a 2025 (painel):

1. Participação feminina no emprego formal e razão salarial mulher/homem, por
   UF e ano e por município de SC pooled.
2. Saldo mensal de admissões e desligamentos por UF e sexo, para cruzar com
   tentativa de feminicídio e feminicídio mensais do Sinesp.

Por raça, só 2024 e 2025 (corte transversal):

3. Participação das mulheres negras no emprego formal ÷ participação na
   população feminina (Censo 2022, tabela 9605): índice de inserção formal.
4. Razão salarial mulheres negras / homens brancos.
5. Distribuição de escolaridade das mulheres por raça, contra a tabela 10061.

## Conferência

O total de vínculos ativos por UF e ano nos CSVs deve bater com o bloco 0.1
(SC: 2,32 M em 2019, 2,95 M em 2025). O painel FIESC mostra 2,92 M para SC 2025
porque aplica regra própria de vínculo; a diferença é esperada.

## Espelho do SIDRA

`obsref.sidra.flat_unificado` guarda tabelas do SIDRA em formato longo
(`cd_tabela`, nove dimensões, nível territorial, `vl_resultado`). Território
fica em `nm_dimensao_1` (ex.: "Abadia de Goiás - GO"), indicador em
`nm_dimensao_2` e ano em `nm_dimensao_3` (conferido na 4714).

Conferido em 15/10/2026 (bloco 0.4a): **as tabelas do Censo 2022 de cor ou
raça (9605), instrução (10061) e renda (10295, 10296, 10289) não estão no
espelho.** Estão lá 4714 e 9514 (população 2022), 9542 (Censo 2022, 36 M
linhas, conteúdo a confirmar), 6579 (estimativas de população), 5938 (PIB
municipal) e tabelas anuais da PNAD Contínua (7109, 7113, 7126, 7141, 7206).
A 9542 é "Pessoas de 15 anos ou mais de idade, total e as alfabetizadas, por
sexo, cor ou raça e grupos de idade" (Censo 2022, universo, até município):
serve de denominador por raça e sexo para a RAIS (idade ativa) e para taxas de
mulheres de 15 anos ou mais. A 9606 do SIDRA (população por cor ou raça, sexo
e idade, todas as idades) é a referência para as taxas do SIM; a API funciona
no navegador, embora bloqueie scripts. O bloco 0.5 do SQL faz o teste de
embranquecimento da RAIS contra a 9542, por UF.

## Teste de embranquecimento (rodado em 15/10/2026)

Participação de mulheres negras entre as mulheres com raça identificada na RAIS
(vínculos ativos) contra a participação na população feminina do Censo 2022
(tabela 9606, todas as idades; o lado do Censo no bloco 0.5 veio nulo porque o
filtro não casou com a estrutura da 9542 no espelho, então a comparação foi
feita em pandas com `data/gold/ibge/censo2022_mulheres_cor_raca_uf.csv`).
Resultado em `data/gold/rais/teste_embranquecimento_rais_censo_uf.csv`.

| Recorte | Razão RAIS / Censo 2024 | Razão 2025 |
| --- | --- | --- |
| Santa Catarina | 0,94 | 1,01 |
| Brasil (agregado das UFs) | 0,89 | 0,92 |
| Mediana das UFs | 1,01 | 1,02 |
| Mínimo | 0,72 (RS) | 0,78 (RS) |
| Máximo | 1,24 (RR) | 1,23 (RR) |

Leitura:

- **A foto racial da RAIS 2024–2025 é usável em SC e no Brasil.** A composição
  por raça no emprego formal fica a poucos pontos do Censo, e a razão melhora
  de 2023 para 2025 à medida que a não identificação cai.
- **O viés não é só embranquecimento.** No Sul e Sudeste a RAIS tem menos
  negras do que o Censo (RS e PR abaixo de 0,8); no Norte e Nordeste tem mais
  (AM, AC, RR acima de 1,1). Isso mistura classificação pelo empregador com a
  seleção real de quem está no emprego formal. Por isso a comparação de
  participações é descritiva, não mede discriminação.
- Em 2024 e 2025, RS e PR ficam com flag de cautela pela razão; PI e RN pela
  fatia de não identificada acima de 10%.
- Use 2025 como ano principal (maior cobertura) e 2024 como conferência.

## Denominadores do Censo 2022 salvos no projeto

- `data/bronze/ibge/censo2022_9606_mulheres_cor_raca_br_uf.json` e
  `data/gold/ibge/censo2022_mulheres_cor_raca_uf.csv`: mulheres por cor ou raça,
  Brasil e UFs.
- `data/bronze/ibge/censo2022_9606_mulheres_cor_raca_municipios_sc.json` e
  `data/gold/ibge/censo2022_mulheres_cor_raca_municipios_sc.csv`: mulheres por
  cor ou raça nos 295 municípios de SC. Serve para o pooled municipal da RAIS e
  para as taxas municipais do SIM por raça.

## Exportação feita em 15/10/2026

Os quatro blocos foram exportados do Databricks em xlsx (originais em
`data/bronze/rais/obsref/xlsx_original/`) e convertidos para CSV em
`data/bronze/rais/obsref/`. Conferências:

| Arquivo | Linhas | Anos |
| --- | --- | --- |
| `rais_br_uf_sexo_raca.csv` | 2.588 | 2019–2025 |
| `rais_sc_municipio_sexo_raca.csv` | 23.464 (295 municípios) | 2019–2025 |
| `rais_br_uf_sexo_raca_escolaridade.csv` | 28.076 | 2019–2025 |
| `rais_br_uf_mes_sexo_raca_admissoes_desligamentos.csv` | 30.926 | 2019–2025 |

- A linha `BR` é igual à soma das UFs em todos os anos (diferença zero).
- SC: 2.319.210 vínculos em 2019 e 2.949.150 em 2025, iguais nos três
  arquivos de estoque e iguais ao bloco 0.1.
- Códigos presentes: raça 1, 2, 4, 6, 8, 9 e 99; sexo 1, 2 e 9.
- O saldo mensal do Brasil em 2025 tem o padrão esperado: positivo de
  janeiro a novembro e fortemente negativo em dezembro (desligamentos de
  fim de ano).

## Construção executada em 15/10/2026

`pipeline/build_rais.py` lê os quatro CSVs de `data/bronze/rais/obsref/` e gera:

1. Silver `rais_vinculos_raca_sexo.parquet`,
   `rais_movimentacao_mensal.parquet` e
   `rais_escolaridade_raca_sexo.parquet`.
2. Gold por sexo, 2019 a 2025: participação feminina, razão salarial
   mulher e homem com piso de 100 vínculos, painel municipal de Santa Catarina
   e movimentação mensal por sexo.
3. Gold por raça, 2024 e 2025: inserção formal de mulheres negras contra o
   Censo, razão salarial de mulheres negras em relação a homens brancos e
   mulheres brancas, escolaridade por raça e qualidade do preenchimento.
4. Mapeamento dos códigos de raça para o padrão do projeto. Os códigos 9 e 99
   ficam como não identificados. Sexo 9 e escolaridade 99 são descartados.
5. Código municipal convertido de seis para sete dígitos com o cadastro do
   IBGE. O rótulo municipal vem da Silver de população para corrigir a
   acentuação da exportação da RAIS.

Conferências executadas pelo script e por `pipeline/validate_project.py`:

1. Brasil é igual à soma das UFs em todos os anos.
2. Santa Catarina tem 2.319.210 vínculos em 2019 e 2.949.150 em 2025.
3. Admissões menos desligamentos são iguais ao saldo mensal.
4. Raça fica marcada como usável somente em 2024 e 2025.

Pendências opcionais: deflator INPC, caso o painel mostre nível salarial entre
anos, e extensão da série para 2015.
