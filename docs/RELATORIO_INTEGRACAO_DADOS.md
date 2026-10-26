# Relatório de integração dos dados

Atualizado em 2026-10-14.

## Escopo concluído

1. A série histórica comum reúne SINAN, SIM, Sinesp VDE e população feminina para 2019 a 2024.
2. O monitoramento recente usa números absolutos e compara períodos equivalentes em 2025 e 2026.
3. Os municípios do Sinesp foram associados ao cadastro populacional de Santa Catarina.
4. As limitações de conceito, território, cobertura e situação dos dados foram registradas.

O painel não foi alterado nem publicado durante este trabalho.

## Resultados principais

1. O SINAN preliminar de 2025 contém 294.188 notificações no Brasil e 11.773 em Santa Catarina. Em relação a 2024, as variações são +1,7% no Brasil e +22,0% em Santa Catarina.
2. O Sinesp registra 1.578 vítimas de feminicídio no Brasil e 52 em Santa Catarina em 2025. As variações sobre 2024 são +5,1% e +2,0%, respectivamente.
3. Entre janeiro e agosto de 2026, o Sinesp registra 983 vítimas no Brasil e 38 em Santa Catarina. Contra janeiro a agosto de 2025, as variações são -2,6% e +26,7%.
4. O SIM registra 1.606 mortes de mulheres por agressão no Brasil e 49 em Santa Catarina entre 1 de janeiro e 26 de agosto de 2026. As comparações com o mesmo período de 2025 são -12,8% e 0,0%.
5. Em 2025, 32 municípios catarinenses possuem pelo menos uma vítima de feminicídio registrada no Sinesp.

## Leitura das taxas históricas

1. No Brasil, a taxa de notificações do SINAN passou de 174,77 em 2019 para 265,53 por 100 mil mulheres em 2024.
2. Em Santa Catarina, a taxa de notificações passou de 147,19 para 236,92 por 100 mil mulheres no mesmo período.
3. A taxa de mortes de mulheres por agressão no SIM passou de 3,51 para 3,33 no Brasil e de 3,05 para 2,21 em Santa Catarina.
4. A taxa de vítimas de feminicídio do Sinesp passou de 1,25 para 1,38 no Brasil e de 1,55 para 1,25 em Santa Catarina.

Cada taxa permanece acompanhada de seu número absoluto na tabela histórica.

## Validação territorial

1. Foram encontrados 295 municípios do Sinesp com correspondência única no cadastro populacional.
2. O Sinesp contém 1 registro adicional chamado “NÃO INFORMADO”. Ele permanece na auditoria, mas não recebe código IBGE e não entra nas taxas municipais.
3. Os 295 municípios aparecem em todos os arquivos anuais de 2019 a 2026. Cada município possui 92 combinações de ano e mês, considerando 2026 até agosto.
4. O total estadual do Sinesp continua incluindo registros sem município quando houver valor publicado nessa categoria. No conjunto atual, essa categoria tem valor zero para feminicídio em Santa Catarina.

## Limitações para interpretação

1. SINAN mede notificações de violência atendidas pela saúde. Uma pessoa pode aparecer em mais de uma notificação.
2. SIM mede mortes de mulheres cuja causa básica pertence ao grupo de agressões. Esse conceito é mais amplo que feminicídio.
3. Sinesp mede vítimas classificadas como feminicídio pelos órgãos de segurança pública.
4. SINAN e SIM usam residência da vítima na consolidação atual. Sinesp usa município do fato.
5. As três fontes não devem ser somadas e não formam uma sequência direta.
6. As taxas usam a população feminina oficial disponível até 2024. O monitoramento de 2025 e 2026 apresenta números absolutos.
7. SINAN 2025 é preliminar. SIM 2025 é preliminar e SIM 2026 é prévia. Sinesp 2026 possui janeiro a agosto.
8. Taxas municipais de feminicídio com menos de cinco vítimas recebem indicação de dado insuficiente para comparação.
9. O Sinesp publica o total de vítimas classificadas no evento Feminicídio. Registros residuais informados com sexo masculino permanecem no total oficial.

## Arquivos produzidos

1. `data/gold/integrado/historico_integrado_2019_2024.csv`
2. `data/gold/integrado/monitoramento_atual_2025_2026.csv`
3. `data/gold/integrado/validacao_municipios_sinesp_sc.csv`
4. `data/gold/integrado/resumo_integracao.json`

## Reprodução

Execute `python pipeline/build_integrated_analysis.py` na raiz do projeto depois de atualizar as camadas Silver.
