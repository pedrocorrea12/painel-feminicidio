# Custos do laboratório AWS

Nenhum recurso AWS faz parte do estado inicial salvo neste repositório.

Antes do primeiro `terraform apply`, registrar nesta página:

- conta e elegibilidade do plano, sem identificadores sensíveis;
- região escolhida;
- serviços e quotas;
- volume estimado por execução;
- armazenamento, requisições, logs e transferência esperados;
- orçamento de referência e alertas configurados;
- data prevista para revisão e destruição dos recursos.

Após cada experimento, registrar custo observado, duração, volume processado e
confirmação de que agendamentos e recursos temporários foram removidos.

## Estimativa preliminar (benchmark local, Gate B)

Base: `docs/benchmark/README.md`. Os preços são de referência pública, **não
verificados**; confirmar na calculadora da AWS antes do primeiro `apply`.

| Item | Volume | Estimativa mensal |
| --- | --- | --- |
| S3 padrão (Bronze 1,4 GB + Silver e Gold ~0,14 GB, com versões) | ~2 a 3 GB | centavos |
| Requisições S3 e transferência | dezenas por execução | desprezível |
| Logs (CloudWatch, retenção de 14 dias) | poucos MB | centavos |
| Lambda (opcional, só se escolhido): 10 GB × ~183 s por execução completa | 1 execução por mês | ≈ US$ 0,03 |
| GitHub Actions agendado (executor recomendado) | ~3 min por execução | 0 em repositório público |
| **Total esperado** | | **menos de US$ 1** |

Controles obrigatórios antes de aplicar: orçamento mensal com alerta (referência:
US$ 5, alertas a 50%, 80% e 100%), região registrada (`us-east-1` sugerida), e data
prevista de revisão e destruição. Registrar aqui o custo observado após cada
experimento.

## Laboratório aplicado em parte (14/11/2026)

Conta do plano gratuito (créditos de US$ 100, válidos até 14/05/2027), região
`us-east-2`, projeto `dados-violencia-sc-lab`. Criados: bucket S3 (vazio), grupo
de logs e orçamento de US$ 5. Sem federação OIDC (bloqueada por SCP, ADR 0002).
Custo esperado nesta fase: zero a centavos. Registrar aqui o custo observado depois
da primeira publicação da Gold (T16).

## Primeira publicação da Gold (14/11/2026)

Execução `20261115T013546Z-c752be7` (commit c752be7), pelo runbook
`docs/runbooks/publicar-gold-na-aws.md` e login local temporário. 53 objetos
(52 arquivos da Gold e o manifesto), 34,8 MB, em `gold/<id-da-execução>/` do bucket
privado. Verificado: contagem de objetos, hash do manifesto igual ao local, objeto
criptografado e acesso público bloqueado.

## Custo observado (17/11/2026)

Painel de faturamento da conta, lido pelo dono em 17/11/2026: valor devido US$ 0,00;
custo acumulado do mês US$ 0,00; créditos restantes US$ 120,00 (o painel mostra mais
que os US$ 100 anotados em 14/11); plano gratuito, 180 dias restantes (até 14/05/2027).
Todo o uso é coberto pelos créditos. O painel agrupa por projeto da conta e mostra um
único projeto, com nome diferente de `dados-violencia-sc-lab`; o gasto é da conta toda.
Fonte: leitura manual do painel, sem exportação da fatura. A primeira fatura fechada
(dezembro/2026) ainda não existe: reconferir o valor quando fechar.
