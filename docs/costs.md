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
