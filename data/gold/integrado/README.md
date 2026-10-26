# Dados integrados

Esta pasta reúne saídas analíticas que não são consumidas pelo painel atual.

## Arquivos

1. `historico_integrado_2019_2024.csv`: Brasil, Santa Catarina e 295 municípios catarinenses, com população feminina, números absolutos e taxas de SINAN, SIM e Sinesp.
2. `monitoramento_atual_2025_2026.csv`: números absolutos recentes e comparação com o mesmo período anterior.
3. `validacao_municipios_sinesp_sc.csv`: correspondência entre o nome publicado pelo Sinesp e o código municipal do cadastro populacional.
4. `resumo_integracao.json`: controles usados no relatório e na retomada do trabalho.
5. `razao_sim_sinesp_uf_2019_2024.csv`: razão contextual entre feminicídios do Sinesp e mortes de mulheres por agressão no SIM para Brasil e 27 UFs.
6. `tentativa_feminicidio_2019_2026.csv`: tentativas e feminicídios consumados, com cobertura e situação da publicação.
7. `taxa_municipal_feminicidio_sc_2019_2024.csv`: taxa plurianual dos 295 municípios catarinenses.
8. `sinesp_serie_mensal_2019_2026.csv`: série mensal de Brasil e Santa Catarina.
9. `sinesp_sazonalidade_mes_2019_2025.csv`: médias mensais e índices sazonais dos anos completos.
10. `homicidio_doloso_feminicidio_2019_2026.csv`: componentes separados e soma metodologicamente permitida.
11. `resumo_analises_sinesp.json`: controles das análises de segurança pública.

## Regras centrais

1. As taxas são calculadas apenas entre 2019 e 2024, período com população feminina disponível.
2. SINAN e SIM usam residência da vítima. Sinesp usa município do fato.
3. Números das três fontes não são somados.
4. Comparações recentes usam o mesmo período de cada fonte.

## Atualização

Execute `python pipeline/build_integrated_analysis.py` depois de atualizar as camadas Silver.

Depois, execute `python pipeline/build_sinesp_analysis.py` para gerar as análises derivadas do Sinesp.
