# Retomada da integração dos dados

Registro salvo em 2026-10-14.

## Estado atual

1. As bases Silver de SINAN, SIM, Sinesp VDE e população feminina estão disponíveis no projeto.
2. A série integrada de 2019 a 2024 foi gerada para Brasil, Santa Catarina e 295 municípios catarinenses.
3. O monitoramento de 2025 e 2026 foi gerado com números absolutos e comparações de períodos equivalentes.
4. Os 295 municípios catarinenses do Sinesp receberam uma correspondência única com o código municipal usado na população.
5. O registro especial “NÃO INFORMADO” foi mantido na auditoria e não recebeu código municipal.
6. O relatório analítico e as limitações metodológicas foram documentados.
7. O painel não foi alterado nem publicado nesta etapa.
8. As análises derivadas do Sinesp foram concluídas para as 27 UFs, Brasil e municípios de Santa Catarina.
9. O validador foi atualizado para reconhecer SIM 2025 preliminar, SIM 2026 prévia e Sinesp 2026 parcial.

## Arquivos principais

1. `pipeline/build_integrated_analysis.py`: processo reproduzível de integração, validação e geração do relatório.
2. `data/gold/integrado/historico_integrado_2019_2024.csv`: série comum com números absolutos e taxas.
3. `data/gold/integrado/monitoramento_atual_2025_2026.csv`: acompanhamento recente sem taxas.
4. `data/gold/integrado/validacao_municipios_sinesp_sc.csv`: auditoria da correspondência municipal.
5. `data/gold/integrado/resumo_integracao.json`: controles compactos da execução.
6. `docs/RELATORIO_INTEGRACAO_DADOS.md`: resultados e limitações.
7. `pipeline/build_sinesp_analysis.py`: razão entre Sinesp e SIM, tentativas, taxas municipais, sazonalidade e homicídios.
8. `docs/RELATORIO_ANALISES_SINESP.md`: resultados das novas análises de segurança pública.

## Controles da execução

1. Histórico integrado: 1.782 linhas.
2. Monitoramento recente: 1.485 linhas.
3. Validação do Sinesp: 296 registros, sendo 295 municípios e um registro especial.
4. Municípios de Santa Catarina com pelo menos uma vítima de feminicídio em 2025: 32.
5. Taxas recalculadas de forma independente: nenhuma divergência acima de 0,01 ponto.
6. Chaves duplicadas nas tabelas finais: nenhuma.
7. Razão entre Sinesp e SIM para Brasil e 27 UFs: 168 linhas.
8. Tentativas e feminicídios consumados: 224 linhas.
9. Taxas municipais plurianuais: 295 linhas.
10. Série mensal de Brasil e Santa Catarina: 184 linhas.
11. Sazonalidade por mês: 24 linhas.
12. Homicídio doloso e feminicídio: 224 linhas.

## Regras já decididas

1. As taxas são calculadas somente até 2024 porque a população feminina disponível termina nesse ano.
2. O monitoramento de 2025 e 2026 usa números absolutos.
3. SINAN e SIM usam residência da vítima. Sinesp usa município do fato.
4. As três fontes aparecem em medidas separadas. Elas não são somadas.
5. O SIM de 2025 e 2026 é comparado até 26 de agosto, último dia comum entre os arquivos.
6. O Sinesp de 2026 é comparado com janeiro a agosto de 2025.
7. O SINAN preliminar de 2025 é comparado com o ano completo de 2024.
8. Variação percentual fica vazia quando o período anterior possui valor zero.
9. Taxas municipais de feminicídio com menos de cinco vítimas recebem indicação de dado insuficiente.
10. A definição oficial do Sinesp para homicídio doloso exclui feminicídio. A soma é permitida, mas os componentes permanecem separados.
11. O rótulo recomendado para a soma é “mulheres vítimas de homicídio doloso ou feminicídio”.
12. Tentativas registradas não são apresentadas como mortes evitadas.

## Como reproduzir

Na raiz do projeto, execute:

```text
python pipeline/build_integrated_analysis.py
python pipeline/build_sinesp_analysis.py
python pipeline/validate_project.py
```

Os scripts leem apenas as camadas Silver e substituem as saídas de `data/gold/integrado` e os relatórios correspondentes.

## Próximo ponto de decisão

O próximo trabalho deve começar pela revisão dos dois relatórios e das tabelas. Somente depois de aprovação deve ser criada uma proposta de interface para incorporar SINAN, SIM e Sinesp ao painel.

Se a incorporação for autorizada, a sequência recomendada é:

1. Definir quais indicadores entram na primeira tela comparativa.
2. Definir a apresentação dos dados preliminares e parciais.
3. Criar uma cópia de segurança da versão pública atual.
4. Alterar o painel usando as tabelas integradas.
5. Validar localmente antes de qualquer publicação.

## Observação sobre o repositório

O projeto já continha alterações locais anteriores a esta integração. Não limpar, restaurar ou sobrescrever essas alterações ao retomar o trabalho. Revisar o estado do Git antes de preparar qualquer commit.
