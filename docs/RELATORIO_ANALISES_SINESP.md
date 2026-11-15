# Análises do Sinesp integradas ao SIM

Atualizado em 2026-10-14.

O painel não foi alterado nem publicado nesta etapa.

## Razão entre Sinesp e SIM

1. No Brasil, a razão entre feminicídios publicados pelo Sinesp e mortes de mulheres por agressão no SIM passou de 0,36 em 2019 para 0,41 em 2024.
2. Em Santa Catarina, a razão passou de 0,51 para 0,57.
3. A tabela inclui as 27 UFs, Brasil, valores absolutos, taxas e ranking anual.
4. A razão deve ser lida como indicador contextual. O SIM usa residência da vítima e o Sinesp usa município do fato.

## Tentativas e feminicídios consumados

1. O Brasil registrou 2.340 tentativas em 2019 e 4.188 em 2025.
2. Santa Catarina registrou 225 tentativas e 52 feminicídios em 2025, razão de 4,33 tentativas por feminicídio.
3. O indicador representa registros classificados pela segurança pública. Ele não deve ser descrito como número de mortes evitadas.

## Taxas municipais plurianuais

1. A taxa usa feminicídios de 2019 a 2024 divididos pela soma da população feminina dos mesmos seis anos.
2. A tabela contém os 295 municípios de Santa Catarina.
3. Municípios com menos de cinco vítimas não recebem ranking de taxa.
4. Os cinco maiores números absolutos entre os municípios com dado suficiente são: Joinville (19), Chapecó (17), Florianópolis (16), Blumenau (15), Lages (9).

## Sazonalidade

1. A série mensal cobre 2019 a 2025 completos e janeiro a agosto de 2026.
2. O maior índice sazonal de feminicídio do Brasil ocorre em Dezembro, com índice 112,5.
3. Em Santa Catarina, o maior índice ocorre em Novembro, com índice 164,3.
4. O índice compara a média de cada mês com a média mensal geral de 2019 a 2025. Ele descreve a série e não identifica causas.
5. Em Santa Catarina, os números mensais são pequenos e o índice pode variar muito com poucos casos.

## Homicídio doloso e feminicídio

1. A documentação oficial define homicídio doloso com exclusão explícita de feminicídio.
2. A soma das duas categorias é metodologicamente permitida no conjunto atual: sim.
3. O rótulo recomendado é “mulheres vítimas de homicídio doloso ou feminicídio”. Os dois componentes devem permanecer visíveis.
4. A soma não inclui todas as mortes violentas intencionais. Latrocínio, lesão corporal seguida de morte e outras categorias permanecem separadas.

Fonte metodológica oficial: https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023

## Arquivos produzidos

1. `data/gold/integrado/razao_sim_sinesp_uf_2019_2024.csv`
2. `data/gold/integrado/tentativa_feminicidio_2019_2026.csv`
3. `data/gold/integrado/taxa_municipal_feminicidio_sc_2019_2024.csv`
4. `data/gold/integrado/sinesp_serie_mensal_2019_2026.csv`
5. `data/gold/integrado/sinesp_sazonalidade_mes_2019_2025.csv`
6. `data/gold/integrado/homicidio_doloso_feminicidio_2019_2026.csv`

## Reprodução

Execute `python pipeline/build_sinesp_analysis.py` depois de atualizar as camadas Silver.
