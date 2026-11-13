# ADR 0001 Evolução incremental do pipeline

## Status

Aceita em 12 de novembro de 2026.

## Contexto

O repositório já possui fontes, camadas Bronze, Silver e Gold, validações de
domínio e um dashboard publicado. Uma reescrita aumentaria o risco de alterar
indicadores já reconciliados e atrasaria a criação de evidências de engenharia.

## Decisão

Preservar o dashboard e os scripts atuais. Extrair gradualmente configuração,
observabilidade, contratos e checagens para `src/painel_dados`, mantendo wrappers
compatíveis em `pipeline/`. Cada etapa deverá possuir teste de equivalência ou
critério de aceite verificável antes da substituição do caminho anterior.

SINAN e SINESP serão os primeiros pilotos. A infraestrutura AWS será criada
somente depois que o pipeline local cumprir o Gate A.

## Alternativas consideradas

- Reescrever todo o pipeline: rejeitada por risco e ausência de ganho imediato.
- Migrar primeiro para AWS: rejeitada porque acrescentaria custo e operação
  antes de existir uma baseline automatizada.
- Manter apenas scripts independentes: rejeitada porque dificulta testes,
  configuração e reaproveitamento.

## Consequências

- A transição terá temporariamente dois pontos de organização: `pipeline/` e
  `src/painel_dados/`.
- O painel continuará demonstrável sem conta AWS.
- Novas ferramentas dependerão de requisito e medição, não apenas de valor de
  portfólio.
