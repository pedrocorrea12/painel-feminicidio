-- =====================================================================
-- RAIS vínculos por raça/cor e sexo — extração no Databricks (obsref)
-- Tabela: obsref.rais.flat_vinculos_unificado (uma linha por vínculo, anual)
--
-- Como usar: rodar os blocos na ordem. Os blocos 0.x são conferência
-- (não exportar). Os blocos 1A, 1B, 2 e 4 geram as Pratas, já agregadas
-- (Brasil e UFs via GROUPING SETS; só SC no grão municipal); exportar
-- cada resultado como CSV (UTF-8, separador vírgula) para:
--   data/bronze/rais/obsref/<nome_do_bloco>.csv
--
-- Decisões (ver docs/RAIS.md):
--   * Território = cd_municipio_6d do estabelecimento. A coluna
--     cd_municipio_trabalho é 999999 / nula na base inteira.
--   * Só vínculo ativo em 31/12 (cd_vinculo_ativo_31_12 = 1): estoque.
--   * Remuneração = vl_remuneracao_dezembro_nominal, média e mediana
--     calculadas só sobre quem tem valor > 0 (numerador e denominador
--     com o mesmo conjunto de linhas).
--   * Raça/cor RAIS: 1 Indígena, 2 Branca, 4 Preta, 6 Amarela, 8 Parda,
--     9 "Nao ident" e 99 "Não informado" (confirmado no bloco 0.2: os dois
--     existem, com ~36 M e ~34 M linhas). Os dois são tratados como
--     não identificada. "negra" = preta + parda é calculada depois,
--     em pandas, a partir das linhas por raça.
--   * Escolaridade 99 e sexo 9 também existem (56 linhas): descartar.
--   * Safras: 2008 a 2025 (bloco 0.1). Brasil 2019 = 46,7 M ativos,
--     SC 2025 = 2,95 M; batem com a RAIS pública.
--   * Sexo RAIS: 1 Masculino, 2 Feminino.
--   * Anos: 2019 em diante. Confirmar no bloco 0.1 quais safras existem.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 0.1 Safras carregadas e volume por ano (conferência)
--     Esperado: SC 2025 ≈ 2,92 milhões de vínculos ativos (painel FIESC).
-- ---------------------------------------------------------------------
SELECT
  nr_ano_competencia                                   AS ano,
  COUNT(*)                                             AS vinculos_total,
  SUM(CASE WHEN cd_vinculo_ativo_31_12 = 1 THEN 1 ELSE 0 END) AS vinculos_ativos_3112,
  SUM(CASE WHEN cd_vinculo_ativo_31_12 = 1 AND sg_unidade_federativa = 'SC' THEN 1 ELSE 0 END) AS vinculos_ativos_sc
FROM obsref.rais.flat_vinculos_unificado
GROUP BY nr_ano_competencia
ORDER BY ano;


-- ---------------------------------------------------------------------
-- 0.2 Dicionário real de raça/cor, sexo e escolaridade (conferência)
--     Confirma os códigos antes de mapear em pandas.
-- ---------------------------------------------------------------------
SELECT 'raca_cor' AS campo, CAST(cd_raca_cor AS STRING) AS codigo, ds_raca_cor_vinculo AS descricao, COUNT(*) AS n
FROM obsref.rais.flat_vinculos_unificado
WHERE nr_ano_competencia >= 2019 AND cd_vinculo_ativo_31_12 = 1
GROUP BY cd_raca_cor, ds_raca_cor_vinculo
UNION ALL
SELECT 'sexo', CAST(cd_sexo_trabalhador AS STRING), ds_sexo_trabalhador, COUNT(*)
FROM obsref.rais.flat_vinculos_unificado
WHERE nr_ano_competencia >= 2019 AND cd_vinculo_ativo_31_12 = 1
GROUP BY cd_sexo_trabalhador, ds_sexo_trabalhador
UNION ALL
SELECT 'escolaridade', CAST(cd_escolaridade AS STRING), ds_escolaridade, COUNT(*)
FROM obsref.rais.flat_vinculos_unificado
WHERE nr_ano_competencia >= 2019 AND cd_vinculo_ativo_31_12 = 1
GROUP BY cd_escolaridade, ds_escolaridade
ORDER BY campo, codigo;


-- ---------------------------------------------------------------------
-- 0.3 Fatia de raça não identificada por UF e ano, separando os códigos
--     9 e 99. A primeira rodada contou só o 9 e mostrou uma queda forte
--     em 2023–2025 (SC: 26,9% em 2022 para 3,2% em 2025); é preciso ver
--     se o 99 explica a queda antes de aceitar a melhoria. Acima de 10%
--     no total a UF entra com flag de cautela.
-- ---------------------------------------------------------------------
SELECT
  nr_ano_competencia AS ano,
  sg_unidade_federativa AS sigla_uf,
  COUNT(*) AS vinculos,
  ROUND(100.0 * SUM(CASE WHEN cd_raca_cor = 9 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_cod9_nao_ident,
  ROUND(100.0 * SUM(CASE WHEN cd_raca_cor = 99 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_cod99_nao_informado,
  ROUND(100.0 * SUM(CASE WHEN cd_raca_cor IN (9, 99) OR cd_raca_cor IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_raca_nao_identificada,
  ROUND(100.0 * SUM(CASE WHEN cd_sexo_trabalhador = 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_mulheres
FROM obsref.rais.flat_vinculos_unificado
WHERE nr_ano_competencia >= 2019
  AND cd_vinculo_ativo_31_12 = 1
  AND sg_unidade_federativa IS NOT NULL
GROUP BY nr_ano_competencia, sg_unidade_federativa
ORDER BY ano, sigla_uf;


-- ---------------------------------------------------------------------
-- 0.4 Espelho do SIDRA no Databricks: obsref.sidra.flat_unificado
--     (colunas: cd_tabela, nm_tabela, nm_indicador, cd/nm_dimensao_1..9,
--     unidade, cd/nm_nivel_territorial, vl_resultado). Não há coluna de
--     território nem de período: devem estar nas dimensões. Três passos.
-- ---------------------------------------------------------------------
-- 0.4a Quais tabelas existem e quantas linhas. Interessam 9605 (cor ou
--      raça, universo 2022), 10061 (nível de instrução), 10295 (renda
--      domiciliar per capita), 10296 (classes de renda), 10289 (renda do
--      trabalho por sexo e cor), 4714 (população).
SELECT cd_tabela, sg_tabela, nm_tabela, COUNT(*) AS linhas,
       COUNT(DISTINCT nm_nivel_territorial) AS niveis
FROM obsref.sidra.flat_unificado
GROUP BY cd_tabela, sg_tabela, nm_tabela
ORDER BY cd_tabela;

-- 0.4b Para as tabelas de interesse presentes: níveis territoriais e
--      o que cada dimensão guarda (a estrutura varia por tabela).
SELECT cd_tabela, nm_nivel_territorial,
       MIN(nm_dimensao_1) AS ex_dim1, MIN(nm_dimensao_2) AS ex_dim2,
       MIN(nm_dimensao_3) AS ex_dim3, MIN(nm_dimensao_4) AS ex_dim4,
       MIN(nm_dimensao_5) AS ex_dim5, MIN(nm_dimensao_6) AS ex_dim6,
       COUNT(*) AS linhas
FROM obsref.sidra.flat_unificado
WHERE cd_tabela IN (9605, 10061, 10295, 10296, 10289, 4714)
GROUP BY cd_tabela, nm_nivel_territorial
ORDER BY cd_tabela, nm_nivel_territorial;

-- 0.4c Resultado de 15/10/2026: 9605, 10061, 10295, 10296 e 10289 NÃO
--      estão no espelho. Território fica em nm_dimensao_1, indicador em
--      nm_dimensao_2, ano em nm_dimensao_3 (visto na 4714).
--      Falta saber o que guardam 9542 (Censo 2022, 36 M linhas), 9514,
--      200/136 (Censo 2010), 6579 e as PNADC anuais 7109/7113/7126/7141/7206.
--      Se a 9542 for população por cor ou raça, sexo e idade, substitui a 9605.
SELECT cd_tabela, nm_nivel_territorial, nm_indicador,
       MIN(nm_dimensao_1) AS ex_dim1, MIN(nm_dimensao_2) AS ex_dim2,
       MIN(nm_dimensao_3) AS ex_dim3, MIN(nm_dimensao_4) AS ex_dim4,
       MIN(nm_dimensao_5) AS ex_dim5, MIN(nm_dimensao_6) AS ex_dim6,
       MIN(nm_dimensao_7) AS ex_dim7,
       COUNT(DISTINCT nm_dimensao_2) AS n_dim2, COUNT(DISTINCT nm_dimensao_3) AS n_dim3,
       COUNT(DISTINCT nm_dimensao_4) AS n_dim4, COUNT(DISTINCT nm_dimensao_5) AS n_dim5,
       COUNT(DISTINCT nm_dimensao_6) AS n_dim6, COUNT(DISTINCT nm_dimensao_7) AS n_dim7,
       COUNT(*) AS linhas
FROM obsref.sidra.flat_unificado
WHERE cd_tabela IN (9542, 9514, 200, 136, 6579, 7109, 7113, 7126, 7141, 7206)
GROUP BY cd_tabela, nm_nivel_territorial, nm_indicador
ORDER BY cd_tabela, nm_nivel_territorial, nm_indicador;

-- 0.4d Valores distintos das dimensões da 9542 (fora território), para
--      confirmar se há cor ou raça, sexo e idade.
SELECT 'dim2' AS dim, nm_dimensao_2 AS valor, COUNT(*) AS n FROM obsref.sidra.flat_unificado WHERE cd_tabela = 9542 GROUP BY nm_dimensao_2
UNION ALL
SELECT 'dim3', nm_dimensao_3, COUNT(*) FROM obsref.sidra.flat_unificado WHERE cd_tabela = 9542 GROUP BY nm_dimensao_3
UNION ALL
SELECT 'dim4', nm_dimensao_4, COUNT(*) FROM obsref.sidra.flat_unificado WHERE cd_tabela = 9542 GROUP BY nm_dimensao_4
UNION ALL
SELECT 'dim5', nm_dimensao_5, COUNT(*) FROM obsref.sidra.flat_unificado WHERE cd_tabela = 9542 GROUP BY nm_dimensao_5
UNION ALL
SELECT 'dim6', nm_dimensao_6, COUNT(*) FROM obsref.sidra.flat_unificado WHERE cd_tabela = 9542 GROUP BY nm_dimensao_6
ORDER BY dim, n DESC;


-- ---------------------------------------------------------------------
-- 0.5 TESTE DE EMBRANQUECIMENTO: participação de mulheres negras no
--     emprego formal (RAIS 2023–2025, só raça identificada) contra a
--     participação na população feminina de 15 anos ou mais do Censo 2022
--     (tabela 9542 do espelho obsref.sidra.flat_unificado), por UF.
--     Regra de decisão: se em SC a diferença for de poucos pontos, a foto
--     racial da RAIS 2024–2025 vale um bloco no painel; se a RAIS mostrar
--     metade do Censo, vira nota de rodapé.
--     O filtro do Censo não depende da ordem das dimensões: procura o
--     valor em qualquer nm_dimensao_N, exclui faixas etárias (padrão
--     "15 a 19 anos", "65 anos ou mais") e alfabetização.
-- ---------------------------------------------------------------------
WITH censo_base AS (
  SELECT
    CASE nm_dimensao_1
      WHEN 'Acre' THEN 'AC' WHEN 'Alagoas' THEN 'AL' WHEN 'Amapá' THEN 'AP'
      WHEN 'Amazonas' THEN 'AM' WHEN 'Bahia' THEN 'BA' WHEN 'Ceará' THEN 'CE'
      WHEN 'Distrito Federal' THEN 'DF' WHEN 'Espírito Santo' THEN 'ES'
      WHEN 'Goiás' THEN 'GO' WHEN 'Maranhão' THEN 'MA' WHEN 'Mato Grosso' THEN 'MT'
      WHEN 'Mato Grosso do Sul' THEN 'MS' WHEN 'Minas Gerais' THEN 'MG'
      WHEN 'Pará' THEN 'PA' WHEN 'Paraíba' THEN 'PB' WHEN 'Paraná' THEN 'PR'
      WHEN 'Pernambuco' THEN 'PE' WHEN 'Piauí' THEN 'PI' WHEN 'Rio de Janeiro' THEN 'RJ'
      WHEN 'Rio Grande do Norte' THEN 'RN' WHEN 'Rio Grande do Sul' THEN 'RS'
      WHEN 'Rondônia' THEN 'RO' WHEN 'Roraima' THEN 'RR' WHEN 'Santa Catarina' THEN 'SC'
      WHEN 'São Paulo' THEN 'SP' WHEN 'Sergipe' THEN 'SE' WHEN 'Tocantins' THEN 'TO'
    END AS sigla_uf,
    CASE
      WHEN 'Branca'   IN (nm_dimensao_2, nm_dimensao_3, nm_dimensao_4, nm_dimensao_5, nm_dimensao_6, nm_dimensao_7, nm_dimensao_8, nm_dimensao_9) THEN 'branca'
      WHEN 'Preta'    IN (nm_dimensao_2, nm_dimensao_3, nm_dimensao_4, nm_dimensao_5, nm_dimensao_6, nm_dimensao_7, nm_dimensao_8, nm_dimensao_9) THEN 'preta'
      WHEN 'Parda'    IN (nm_dimensao_2, nm_dimensao_3, nm_dimensao_4, nm_dimensao_5, nm_dimensao_6, nm_dimensao_7, nm_dimensao_8, nm_dimensao_9) THEN 'parda'
      WHEN 'Amarela'  IN (nm_dimensao_2, nm_dimensao_3, nm_dimensao_4, nm_dimensao_5, nm_dimensao_6, nm_dimensao_7, nm_dimensao_8, nm_dimensao_9) THEN 'amarela'
      WHEN 'Indígena' IN (nm_dimensao_2, nm_dimensao_3, nm_dimensao_4, nm_dimensao_5, nm_dimensao_6, nm_dimensao_7, nm_dimensao_8, nm_dimensao_9) THEN 'indigena'
    END AS raca,
    vl_resultado
  FROM obsref.sidra.flat_unificado
  WHERE cd_tabela = 9542
    AND nm_nivel_territorial = 'Unidade da Federação'
    AND 'Mulheres' IN (nm_dimensao_2, nm_dimensao_3, nm_dimensao_4, nm_dimensao_5, nm_dimensao_6, nm_dimensao_7, nm_dimensao_8, nm_dimensao_9)
    AND NOT ('Alfabetizadas' IN (nm_dimensao_2, nm_dimensao_3, nm_dimensao_4, nm_dimensao_5, nm_dimensao_6, nm_dimensao_7, nm_dimensao_8, nm_dimensao_9))
    AND NOT ('Não alfabetizadas' IN (nm_dimensao_2, nm_dimensao_3, nm_dimensao_4, nm_dimensao_5, nm_dimensao_6, nm_dimensao_7, nm_dimensao_8, nm_dimensao_9))
    AND NOT (COALESCE(nm_dimensao_2, '') RLIKE '^[0-9]+( a [0-9]+)? anos( ou mais)?$'
          OR COALESCE(nm_dimensao_3, '') RLIKE '^[0-9]+( a [0-9]+)? anos( ou mais)?$'
          OR COALESCE(nm_dimensao_4, '') RLIKE '^[0-9]+( a [0-9]+)? anos( ou mais)?$'
          OR COALESCE(nm_dimensao_5, '') RLIKE '^[0-9]+( a [0-9]+)? anos( ou mais)?$'
          OR COALESCE(nm_dimensao_6, '') RLIKE '^[0-9]+( a [0-9]+)? anos( ou mais)?$'
          OR COALESCE(nm_dimensao_7, '') RLIKE '^[0-9]+( a [0-9]+)? anos( ou mais)?$'
          OR COALESCE(nm_dimensao_8, '') RLIKE '^[0-9]+( a [0-9]+)? anos( ou mais)?$'
          OR COALESCE(nm_dimensao_9, '') RLIKE '^[0-9]+( a [0-9]+)? anos( ou mais)?$')
    AND LOWER(COALESCE(nm_indicador, '')) NOT LIKE '%percentual%'
    AND LOWER(COALESCE(nm_unidade_medida, '')) NOT LIKE '%percent%'
    AND COALESCE(nm_unidade_medida, '') <> '%'
),
censo AS (
  SELECT sigla_uf,
         SUM(vl_resultado) AS mulheres_15mais_identificadas,
         SUM(CASE WHEN raca IN ('preta', 'parda') THEN vl_resultado ELSE 0 END) AS negras_censo,
         SUM(CASE WHEN raca = 'branca' THEN vl_resultado ELSE 0 END) AS brancas_censo
  FROM censo_base
  WHERE raca IS NOT NULL AND sigla_uf IS NOT NULL
  GROUP BY sigla_uf
),
rais AS (
  SELECT
    nr_ano_competencia AS ano,
    sg_unidade_federativa AS sigla_uf,
    COUNT(*) AS mulheres_vinculos,
    SUM(CASE WHEN cd_raca_cor IN (1, 2, 4, 6, 8) THEN 1 ELSE 0 END) AS identificadas_rais,
    SUM(CASE WHEN cd_raca_cor IN (4, 8) THEN 1 ELSE 0 END) AS negras_rais,
    SUM(CASE WHEN cd_raca_cor = 2 THEN 1 ELSE 0 END) AS brancas_rais
  FROM obsref.rais.flat_vinculos_unificado
  WHERE nr_ano_competencia IN (2023, 2024, 2025)
    AND cd_vinculo_ativo_31_12 = 1
    AND cd_sexo_trabalhador = 2
    AND sg_unidade_federativa IS NOT NULL
  GROUP BY nr_ano_competencia, sg_unidade_federativa
)
SELECT
  r.ano, r.sigla_uf,
  r.mulheres_vinculos,
  ROUND(100.0 * (r.mulheres_vinculos - r.identificadas_rais) / r.mulheres_vinculos, 2) AS pct_nao_identificada_rais,
  ROUND(100.0 * r.negras_rais / NULLIF(r.identificadas_rais, 0), 2) AS pct_negras_rais,
  ROUND(100.0 * c.negras_censo / NULLIF(c.mulheres_15mais_identificadas, 0), 2) AS pct_negras_censo,
  ROUND(100.0 * r.negras_rais / NULLIF(r.identificadas_rais, 0)
      - 100.0 * c.negras_censo / NULLIF(c.mulheres_15mais_identificadas, 0), 2) AS dif_pontos_negras,
  ROUND((1.0 * r.negras_rais / NULLIF(r.identificadas_rais, 0))
      / NULLIF(1.0 * c.negras_censo / NULLIF(c.mulheres_15mais_identificadas, 0), 0), 3) AS razao_rais_censo_negras,
  ROUND(100.0 * r.brancas_rais / NULLIF(r.identificadas_rais, 0), 2) AS pct_brancas_rais,
  ROUND(100.0 * c.brancas_censo / NULLIF(c.mulheres_15mais_identificadas, 0), 2) AS pct_brancas_censo
FROM rais r
LEFT JOIN censo c ON c.sigla_uf = r.sigla_uf
ORDER BY r.ano, r.sigla_uf;

-- Se pct_negras_censo vier nulo, o filtro do Censo não casou com a
-- estrutura da 9542 no espelho: rodar 0.4d e ajustar.


-- =====================================================================
-- 1A. PRATA ESTADUAL: Brasil + UF × ano × sexo × raça
--     GROUPING SETS gera a linha do Brasil junto (sigla_uf = 'BR'), com
--     mediana calculada sobre todos os vínculos e não somada por UF.
--     Pequena: (27 + 1) × 2 × 7 × 7 anos ≈ 2,7 mil linhas.
--     Exportar como: rais_br_uf_sexo_raca.csv
-- =====================================================================
SELECT
  nr_ano_competencia                     AS ano,
  COALESCE(sg_unidade_federativa, 'BR')  AS sigla_uf,
  cd_sexo_trabalhador                    AS cd_sexo,
  cd_raca_cor                            AS cd_raca,
  COUNT(*)                               AS qt_vinculos,
  SUM(CASE WHEN nr_idade BETWEEN 18 AND 64 THEN 1 ELSE 0 END) AS qt_vinculos_18_64,
  SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN 1 ELSE 0 END) AS qt_com_remuneracao,
  SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN vl_remuneracao_dezembro_nominal ELSE 0 END) AS vl_rem_dez_soma,
  ROUND(SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN vl_remuneracao_dezembro_nominal ELSE 0 END)
        / NULLIF(SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN 1 ELSE 0 END), 0), 2) AS vl_rem_dez_media,
  ROUND(PERCENTILE_APPROX(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN vl_remuneracao_dezembro_nominal END, 0.5), 2) AS vl_rem_dez_mediana,
  ROUND(AVG(CASE WHEN vl_remuneracao_media_nominal > 0 THEN vl_remuneracao_media_nominal END), 2) AS vl_rem_media_ano_media
FROM obsref.rais.flat_vinculos_unificado
WHERE nr_ano_competencia >= 2019
  AND cd_vinculo_ativo_31_12 = 1
  AND sg_unidade_federativa IS NOT NULL
GROUP BY GROUPING SETS (
  (nr_ano_competencia, sg_unidade_federativa, cd_sexo_trabalhador, cd_raca_cor),
  (nr_ano_competencia, cd_sexo_trabalhador, cd_raca_cor)
)
ORDER BY ano, sigla_uf, cd_sexo, cd_raca;


-- =====================================================================
-- 1B. PRATA MUNICIPAL SC: município de SC × ano × sexo × raça
--     Só Santa Catarina no grão municipal. 295 × 2 × 7 × 7 ≈ 29 mil linhas.
--     Exportar como: rais_sc_municipio_sexo_raca.csv
-- =====================================================================
SELECT
  nr_ano_competencia                     AS ano,
  cd_municipio_6d                        AS id_municipio_6d,
  nm_municipio                           AS municipio,
  cd_sexo_trabalhador                    AS cd_sexo,
  cd_raca_cor                            AS cd_raca,
  COUNT(*)                               AS qt_vinculos,
  SUM(CASE WHEN nr_idade BETWEEN 18 AND 64 THEN 1 ELSE 0 END) AS qt_vinculos_18_64,
  SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN 1 ELSE 0 END) AS qt_com_remuneracao,
  SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN vl_remuneracao_dezembro_nominal ELSE 0 END) AS vl_rem_dez_soma,
  ROUND(SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN vl_remuneracao_dezembro_nominal ELSE 0 END)
        / NULLIF(SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN 1 ELSE 0 END), 0), 2) AS vl_rem_dez_media,
  ROUND(PERCENTILE_APPROX(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN vl_remuneracao_dezembro_nominal END, 0.5), 2) AS vl_rem_dez_mediana
FROM obsref.rais.flat_vinculos_unificado
WHERE nr_ano_competencia >= 2019
  AND cd_vinculo_ativo_31_12 = 1
  AND sg_unidade_federativa = 'SC'
GROUP BY
  nr_ano_competencia, cd_municipio_6d, nm_municipio,
  cd_sexo_trabalhador, cd_raca_cor
ORDER BY ano, id_municipio_6d, cd_sexo, cd_raca;


-- =====================================================================
-- 2. PRATA DE ESCOLARIDADE: Brasil + UF × ano × sexo × raça × escolaridade
--    Base da escolaridade por raça (comparação com Censo 10061).
--    Pequena: (27 + 1) × 2 × 7 × 12 × 7 anos ≈ 33 mil linhas.
--    Exportar como: rais_br_uf_sexo_raca_escolaridade.csv
-- =====================================================================
SELECT
  nr_ano_competencia                     AS ano,
  COALESCE(sg_unidade_federativa, 'BR')  AS sigla_uf,
  cd_sexo_trabalhador                    AS cd_sexo,
  cd_raca_cor                            AS cd_raca,
  cd_escolaridade                        AS cd_escolaridade,
  COUNT(*)                               AS qt_vinculos,
  SUM(CASE WHEN nr_idade BETWEEN 18 AND 64 THEN 1 ELSE 0 END) AS qt_vinculos_18_64,
  SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN 1 ELSE 0 END) AS qt_com_remuneracao,
  SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN vl_remuneracao_dezembro_nominal ELSE 0 END) AS vl_rem_dez_soma,
  ROUND(SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN vl_remuneracao_dezembro_nominal ELSE 0 END)
        / NULLIF(SUM(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN 1 ELSE 0 END), 0), 2) AS vl_rem_dez_media,
  ROUND(PERCENTILE_APPROX(CASE WHEN vl_remuneracao_dezembro_nominal > 0 THEN vl_remuneracao_dezembro_nominal END, 0.5), 2) AS vl_rem_dez_mediana
FROM obsref.rais.flat_vinculos_unificado
WHERE nr_ano_competencia >= 2019
  AND cd_vinculo_ativo_31_12 = 1
  AND sg_unidade_federativa IS NOT NULL
GROUP BY GROUPING SETS (
  (nr_ano_competencia, sg_unidade_federativa, cd_sexo_trabalhador, cd_raca_cor, cd_escolaridade),
  (nr_ano_competencia, cd_sexo_trabalhador, cd_raca_cor, cd_escolaridade)
)
ORDER BY ano, sigla_uf, cd_sexo, cd_raca, cd_escolaridade;
-- O rótulo da escolaridade (ds_escolaridade) foi conferido no bloco 0.2:
-- 1 Analfabeto, 2 Até 5ª incompleto, 3 5ª completo, 4 6ª a 9ª, 5 Fundamental
-- completo, 6 Médio incompleto, 7 Médio completo, 8 Superior incompleto,
-- 9 Superior completo, 10 Mestrado, 11 Doutorado, 99 Não informado.


-- =====================================================================
-- 3. (REMOVIDO) Município de SC × escolaridade × faixa etária.
--    Decisão de 15/10/2026: não exportar. O recorte racial por
--    escolaridade fica no nível UF (bloco 2) e o municipal de SC fica
--    sem escolaridade (bloco 1B), para não gastar esforço num pedaço que
--    não aguenta o viés de declaração de raça.
-- =====================================================================


-- =====================================================================
-- 4. PRATA DE CHOQUE: Brasil + UF × mês × sexo × raça, admissões e
--    desligamentos no ano, a partir dos próprios vínculos (mês de
--    admissão e de desligamento). Serve para o cruzamento mensal com o
--    Sinesp (tentativa de feminicídio e feminicídio por UF e mês).
--    Nota: inclui vínculos não ativos em 31/12, de propósito.
--    (27 + 1) × 12 × 2 × 7 × 7 anos ≈ 33 mil linhas.
--    Exportar como: rais_br_uf_mes_sexo_raca_admissoes_desligamentos.csv
-- =====================================================================
WITH adm AS (
  SELECT
    nr_ano_competencia AS ano,
    COALESCE(sg_unidade_federativa, 'BR') AS sigla_uf,
    CAST(nr_mes_admissao AS INT) AS mes,
    cd_sexo_trabalhador AS cd_sexo,
    cd_raca_cor AS cd_raca,
    COUNT(*) AS qt_admissoes
  FROM obsref.rais.flat_vinculos_unificado
  WHERE nr_ano_competencia >= 2019
    AND sg_unidade_federativa IS NOT NULL
    AND cd_admissao <> 0
    AND CAST(nr_mes_admissao AS INT) BETWEEN 1 AND 12
  GROUP BY GROUPING SETS (
    (nr_ano_competencia, sg_unidade_federativa, CAST(nr_mes_admissao AS INT), cd_sexo_trabalhador, cd_raca_cor),
    (nr_ano_competencia, CAST(nr_mes_admissao AS INT), cd_sexo_trabalhador, cd_raca_cor)
  )
),
des AS (
  SELECT
    nr_ano_competencia AS ano,
    COALESCE(sg_unidade_federativa, 'BR') AS sigla_uf,
    nr_mes_desligamento AS mes,
    cd_sexo_trabalhador AS cd_sexo,
    cd_raca_cor AS cd_raca,
    COUNT(*) AS qt_desligamentos,
    SUM(CASE WHEN cd_motivo_desligamento = 11 THEN 1 ELSE 0 END) AS qt_desligamentos_sem_justa_causa
  FROM obsref.rais.flat_vinculos_unificado
  WHERE nr_ano_competencia >= 2019
    AND sg_unidade_federativa IS NOT NULL
    AND nr_mes_desligamento BETWEEN 1 AND 12
  GROUP BY GROUPING SETS (
    (nr_ano_competencia, sg_unidade_federativa, nr_mes_desligamento, cd_sexo_trabalhador, cd_raca_cor),
    (nr_ano_competencia, nr_mes_desligamento, cd_sexo_trabalhador, cd_raca_cor)
  )
)
SELECT
  COALESCE(a.ano, d.ano) AS ano,
  COALESCE(a.sigla_uf, d.sigla_uf) AS sigla_uf,
  COALESCE(a.mes, d.mes) AS mes,
  COALESCE(a.cd_sexo, d.cd_sexo) AS cd_sexo,
  COALESCE(a.cd_raca, d.cd_raca) AS cd_raca,
  COALESCE(a.qt_admissoes, 0) AS qt_admissoes,
  COALESCE(d.qt_desligamentos, 0) AS qt_desligamentos,
  COALESCE(d.qt_desligamentos_sem_justa_causa, 0) AS qt_desligamentos_sem_justa_causa,
  COALESCE(a.qt_admissoes, 0) - COALESCE(d.qt_desligamentos, 0) AS saldo
FROM adm a
FULL OUTER JOIN des d
  ON a.ano = d.ano AND a.sigla_uf = d.sigla_uf AND a.mes = d.mes
 AND a.cd_sexo <=> d.cd_sexo AND a.cd_raca <=> d.cd_raca
ORDER BY ano, sigla_uf, mes, cd_sexo, cd_raca;


-- ---------------------------------------------------------------------
-- 5. Conferência cruzada depois da exportação: em 1A, a linha BR de cada
--    ano deve ser igual à soma das UFs em qt_vinculos (a mediana não
--    soma). O total por UF e ano deve bater com o bloco 0.1
--    (SC: 2.319.210 em 2019, 2.949.150 em 2025). Rodar em pandas.
-- ---------------------------------------------------------------------
