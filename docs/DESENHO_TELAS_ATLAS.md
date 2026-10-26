# Desenho textual das telas do Atlas

Descrição de como o site funciona e se parece, sem código.
Complementa `REQUISITOS_ATLAS.md`. Status: rascunho para revisão.

## Princípios

1. Uma página, várias seções navegáveis por menu fixo no topo.
2. O território escolhido (Brasil, UF ou município de SC) vale para o site inteiro e fica sempre visível.
3. Todo número aparece com valor absoluto, taxa por 100 mil e fonte.
4. Tom editorial e sóbrio. Sem alarmismo, sem ranking de "mais perigoso".

## Estrutura global

**Topo fixo:** nome do atlas à esquerda; ao centro, o seletor de território ("Santa Catarina", com busca de município); à direita, links Visão geral, Evolução, Mapa, Desigualdades, Mulheres, Recente, Metodologia.

**Rodapé:** fontes, data de atualização, como citar, link para os dados em CSV e para o repositório.

## Tela 1 — Visão geral

- **Título e subtítulo** do território escolhido e do período consolidado (2015–2024).
- **Faixa de cartões**, um por indicador principal: homicídio doloso, mortes por agressão, tentativa de homicídio, estupro (com estupro de vulnerável), suicídio, pessoas desaparecidas.
- **Cada cartão mostra:** valor absoluto do último ano consolidado, taxa por 100 mil, variação frente a 2015 e uma miniatura da série. Uma etiqueta informa a fonte (Sinesp, SIM ou SINAN) e se o território é residência ou local do fato.
- **Aviso fixo** sob a faixa: "As fontes medem coisas diferentes e não se somam."
- Clicar num cartão leva à Evolução com aquele indicador.

## Tela 2 — Evolução

- Seletor de indicador e de sexo (total, feminino, masculino).
- **Gráfico de linhas** com o território escolhido, SC e Brasil, para comparar. Alternância entre valor absoluto e taxa.
- Anos de 2025 e 2026 desenhados em tracejado, com legenda "preliminar" e "parcial até agosto".
- 2025 e 2026 não têm taxa (falta denominador): ao escolher taxa, o gráfico termina em 2024 e explica o motivo.
- Texto curto abaixo: o que a série mede e a ressalva de comparabilidade (por exemplo, a mudança de classificação de estupro em 2020 em SC).

## Tela 3 — Mapa

- **Mapa de SC por município**, colorido pela taxa por 100 mil do indicador e ano escolhidos.
- **Municípios sem massa suficiente** aparecem hachurados, com a legenda "casos insuficientes para comparar". Não entram no ranking.
- Passar o mouse mostra nome, valor absoluto, taxa, população e fonte.
- **Painel lateral:** ranking dos municípios com dado suficiente (dez primeiros e dez últimos) e busca por nome. Clicar num município define o território global.
- Indicadores só estaduais (estupro, desaparecidos) não são oferecidos no mapa, com aviso explicando por quê.

## Tela 4 — Desigualdades

- **Sexo:** barras lado a lado de feminino e masculino, em taxa e em valor absoluto.
- **Idade:** distribuição por faixa etária para Brasil e SC. Sem taxa conjunta de sexo e idade, porque a população da fonte não cruza as duas variáveis; um aviso diz isso.
- **Raça ou cor:** composição dos registros ao lado da composição da população (Censo 2022), com nota sobre dado ignorado.
- **Trabalho (RAIS):** emprego formal e remuneração por sexo e raça, apresentados como contexto territorial, com o texto "associação descritiva, não causalidade".

## Tela 5 — Violência contra a mulher

Capítulo que absorve o painel atual.
- Abertura com texto explicando a diferença entre notificação (SINAN), óbito por agressão (SIM) e feminicídio policial (Sinesp).
- **Três blocos, um por fonte,** lado a lado, nunca somados. Cada um com série própria e ressalva própria.
- **SINAN:** notificações de violência interpessoal contra mulheres, vínculo com parceiro ou ex-parceiro, tipos de violência (podem coexistir).
- **Municípios de SC:** a tabela do painel atual, com taxa e sinalização de cautela para números pequenos.

## Tela 6 — Recente

- Mostra apenas 2025 (preliminar) e 2026 (janeiro a agosto), em contagem, sem taxa.
- **Comparação com o mesmo período** de anos anteriores, por exemplo janeiro a agosto de 2026 contra janeiro a agosto de 2025.
- Gráfico mensal do Sinesp para Brasil e SC.
- Faixa de aviso permanente: "Dados provisórios; podem mudar."

## Tela 7 — Metodologia e fontes

- Tabela de fontes: nome, órgão, o que mede, unidade, território (residência ou local do fato), cobertura temporal e situação do dado.
- Seção "O que este painel não mede".
- Fórmula das taxas, critério mínimo de casos e de população para ranking.
- **Seção técnica para portfólio:** arquitetura bronze, silver e gold, validações automáticas e o motivo das regras de integridade.
- **Downloads** em CSV por fonte e **como citar**, com data de atualização.

## Comportamentos transversais

- **Estados vazios:** quando não há dado para o território ou indicador, a tela explica o motivo em vez de mostrar gráfico em branco.
- **Celular:** cartões em coluna única, mapa com toque, seletor de território em tela cheia.
- **Acessibilidade:** contraste adequado, navegação por teclado, tabela alternativa para cada gráfico.
- **Cores:** paleta única para fonte e outra para estados de dado (consolidado, preliminar, parcial), consistentes em todo o site.
- **Compartilhar:** o endereço da página guarda território, indicador e período, para a imprensa linkar uma visão específica.

## Questões abertas

1. Critério mínimo de casos e de população para o mapa e o ranking.
2. Nome final do atlas e texto da home.
3. Se o ranking mostra os dez primeiros e últimos ou só os primeiros.
4. Ordem do menu e se "Mulheres" aparece antes de "Desigualdades".
