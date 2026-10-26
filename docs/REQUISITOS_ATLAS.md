# Requisitos do Atlas Territorial da Violência

Documento de levantamento de requisitos, anterior à implementação.
Status: rascunho validado com o autor em 26/10/2026.

## 1. Propósito e público

Painel territorial sobre violência no Brasil, nas UFs e nos municípios de Santa Catarina.

- **Objetivo principal:** projeto de portfólio.
- **Uso público:** disponível para pesquisa e imprensa.
- **Consequência:** a confiabilidade pesa mais que a quantidade de indicadores. Menos telas, bem explicadas.

## 2. Decisões tomadas

| Tema | Decisão |
| --- | --- |
| Mulheres | Capítulo próprio do atlas geral, não destaque da home |
| Municípios | Apenas Santa Catarina; Brasil e UFs em nível nacional |
| Mapa | Coroplético dos municípios de SC (exige malha municipal do IBGE) |
| Publicação | O atlas substitui o painel publicado, que vira o capítulo de mulheres |

## 3. Perguntas que o painel responde

1. Qual o tamanho de cada tipo de violência no meu território e como evoluiu desde 2015?
2. Como SC e meu município se comparam com o Brasil e com outros municípios?
3. Quem é mais afetado, por sexo, idade e raça ou cor?
4. O que há de mais recente (2025 e 2026) sem confundir com dado consolidado?

## 4. Estrutura de telas

1. **Visão geral:** valor absoluto e taxa dos indicadores principais do território escolhido.
2. **Série histórica:** um indicador ao longo dos anos, comparando Brasil, SC e município.
3. **Comparação territorial:** mapa e ranking dos municípios de SC, com regra mínima para municípios pequenos.
4. **Desigualdades:** sexo, faixa etária e raça ou cor; depois emprego e remuneração (RAIS), como associação descritiva.
5. **Violência contra a mulher:** capítulo com SINAN, SIM e Sinesp.
6. **Monitoramento recente:** 2025 e 2026 (até agosto), separados dos anos consolidados.
7. **Fontes e metodologia:** origem de cada número e o que ele não mede.

## 5. Interação

- Seletores de território, indicador, período e sexo.
- Todo gráfico mostra número absoluto junto da taxa por 100 mil, com o denominador explícito.
- Dado ausente, parcial ou preliminar tem marcação visual própria.

## 6. Requisitos para pesquisa e imprensa

- Fonte, período e denominador visíveis em cada número.
- Download dos dados em CSV.
- Data de atualização e sugestão de citação.

## 7. Requisitos para o portfólio

- Navegação clara em poucos cliques e visual cuidado.
- Texto curto sobre decisões técnicas: arquitetura medalhão, validações e a regra de não somar fontes.

## 8. Regras de integridade

1. Não somar SINAN, SIM e Sinesp.
2. Informar se o território é residência (SIM, SINAN) ou local do fato (Sinesp).
3. Taxas somente até 2024; 2025 sem denominador populacional.
4. 2026 cobre janeiro a agosto e só se compara com o mesmo período de outros anos.
5. Estupro e estupro de vulnerável avaliados em conjunto (mudança de classificação em 2020).
6. Municípios pequenos: sinalizar, sem ranquear sem critério.
7. Tipos de violência do SINAN podem coexistir no mesmo registro e não são somáveis.
8. Relação entre trabalho e violência é associação territorial, sem inferência causal.

## 9. Fora desta versão

Medidas protetivas e processos judiciais, rede de acolhimento, sistema prisional, pesquisas de vitimização e mapas intramunicipais. Estupro, desaparecidos e localizados só existem por UF, não por município.

## 10. Requisitos não funcionais

- Site estático publicável no GitHub Pages.
- `data.json` atual tem 16 MB: dividir por fonte ou território, com carregamento sob demanda.
- Funcionar bem no celular; acessibilidade de contraste e teclado.

## 11. Pendências

- Obter a malha municipal de SC do IBGE para o mapa.
- Definir critério mínimo de casos e de população para ranking.
- Definir como o painel antigo é absorvido no capítulo de mulheres.
- Revisar o texto do título e da home.
