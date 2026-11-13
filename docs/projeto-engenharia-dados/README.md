# Plano de evolução para engenharia de dados

Este documento salva no repositório o plano de evolução do Painel de Violência
contra a Mulher. O objetivo é transformar o pipeline existente em um case
reproduzível, testado e observável sem reescrever o dashboard ou interromper a
publicação atual no GitHub Pages.

O documento Word original está preservado neste mesmo diretório como referência
de planejamento. Esta versão Markdown registra o encaixe confirmado após a
leitura do repositório e passa a ser o plano operacional versionável.

## Estado inicial confirmado

- As camadas `data/bronze`, `data/silver` e `data/gold` já existem.
- O dashboard estático está em `dashboard/atlas` e possui publicação no GitHub
  Pages.
- Há 22 scripts Python em `pipeline/` e documentação específica das fontes.
- SINAN será a fonte piloto de saúde e SINESP será a fonte piloto de segurança.
- Existem validações embutidas nos scripts, mas ainda não havia suíte `pytest`,
  pacote Python, Docker, ADRs, runbooks ou Terraform.
- A AWS não é pré-requisito para o funcionamento público do painel.

## Princípios

1. Preservar o painel e os resultados atuais antes de refatorar.
2. Migrar uma fonte e uma responsabilidade por vez.
3. Testar esquema, granularidade, idempotência e reconciliação antes da nuvem.
4. Manter Bronze original e impedir a publicação de Gold inválida.
5. Registrar decisões e limites observados, sem declarar como implementado o
   que ainda pertence ao roadmap.

## Arquitetura de transição

```text
fontes públicas
      |
      v
data/bronze -> data/silver -> data/gold -> dashboard/atlas/data
      |              |             |
 contratos       qualidade     publicação estática
      \______________|_____________/
                     |
              logs e manifestos
```

O pacote `src/painel_dados` receberá gradualmente as funções reutilizáveis. Os
scripts em `pipeline/` permanecem compatíveis e canônicos até que cada migração
tenha teste de equivalência.

## Portões de qualidade

### Gate A antes da AWS

- execução local documentada e portátil;
- testes de esquema, chave, idempotência e reconciliação aprovados;
- fixtures públicas ou sintéticas pequenas;
- publicação Gold atômica;
- arquitetura, dicionário e recuperação mínima documentados.

### Gate B antes do agendamento

- benchmark de tempo, memória e volume;
- executor escolhido a partir das medições;
- IAM de menor privilégio e federação OIDC;
- logs, diagnóstico de falha e política de desligamento;
- estimativa de custo e região registradas.

### Gate C antes da demonstração

- CI visível e aprovado;
- incidentes simulados e recuperação demonstrada;
- métricas reais, limitações e custos observados;
- nenhum segredo ou dado pessoal desnecessário no repositório.

## Primeiro backlog

| Ordem | Entrega | Aceite |
| --- | --- | --- |
| 1 | Baseline do pipeline atual | comandos, contagens e artefatos registrados |
| 2 | Pacote e configuração central | diagnóstico executável sem caminho pessoal |
| 3 | Contratos SINAN e SINESP | colunas, tipos, chaves, periodicidade e falhas |
| 4 | Testes automatizados | falham com esquema alterado e chave duplicada |
| 5 | CI | lint, testes e validação antes da publicação |
| 6 | Publicação segura | Gold inválida não substitui dados válidos |
| 7 | Laboratório AWS | infraestrutura implantável e removível |
| 8 | Demo profissional | arquitetura, ADRs, métricas e runbook |

## Decisões ainda abertas

- Lambda só será adotada se dependências, memória e duração forem compatíveis.
- Um job em contêiner ou GitHub Actions continua sendo alternativa válida para
  cargas pesadas do SINAN e do SINESP.
- PostgreSQL e dbt Core dependem de necessidade mensurável; Parquet permanece o
  padrão inicial.
- A agenda AWS será comparada com GitHub Actions por custo, simplicidade e
  observabilidade.

## Próximo marco

Concluir o Gate A local para SINAN e SINESP mantendo o dashboard publicável.
Somente depois disso será criado o primeiro recurso AWS.
