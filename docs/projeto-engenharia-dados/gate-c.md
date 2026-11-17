# Gate C: situação e evidências

Resumo para o dono confirmar, item a item, antes de liberar a T07 (demo). Posição em
17/11/2026, na `develope` em `8e8d989`. Este documento não confirma nada: a confirmação
do Gate C é do dono (regra 5 do `AGENTS.md`).

## Resumo

| Item do Gate C | Evidência | Pendência | Confirmação do dono |
| --- | --- | --- | --- |
| CI visível e aprovado | Workflows `CI` e `Publicar Atlas` com sucesso em `8e8d989` | nenhuma | a fazer |
| Incidentes simulados e recuperação demonstrada | `docs/runbooks/incidentes-simulados.md` e `docs/runbooks/publicacao-gold.md` | `incidentes-simulados.md` ainda mostra os comandos antigos de restauração | a fazer |
| Métricas reais, limitações e custos observados | `docs/benchmark/`, `docs/costs.md` | custo observado registrado em 17/11 (US$ 0,00); reconferir quando a fatura fechar | a fazer |
| Nenhum segredo ou dado pessoal desnecessário | `docs/auditoria/varredura-segredos.md` | um achado de gravidade baixa (e-mail nos metadados Git), aceito pelo dono em 17/11/2026 | a fazer |

Nenhum item depende de novo trabalho dos agentes. Depende do dono: a confirmação final.
A decisão sobre o e-mail nos metadados Git foi tomada em 17/11/2026 (aceitar).

## 1. CI visível e aprovado

- Os workflows `CI` (lint, testes, validação do projeto e Terraform sem credenciais) e `Publicar Atlas` concluíram com
  sucesso no merge `8e8d989`. O mesmo vale para os três últimos merges (PRs 4, 5 e 6), conferidos pela
  API do GitHub; os PRs 1 a 3 não foram conferidos neste resumo.
- Como conferir: aba Actions do repositório no GitHub, ramo `develope`.
- O que a CI não cobre: nada que use credenciais AWS. O `terraform apply` e a publicação no bucket são manuais e do dono.

## 2. Incidentes simulados e recuperação demonstrada

- **O que foi feito (T21):** cinco incidentes reproduzidos numa raiz de simulação, nunca no repositório: Gold inválida na
  validação, ZIP corrompido, backup órfão que bloqueia a publicação, falha na segunda troca do `publicar_conjunto` e falha na
  restauração com backups preservados. O relatório traz o roteiro, a saída real da reexecução de 16/11/2026 e as lacunas
  encontradas no runbook.
- **Correções do runbook (T23 e T26):** as lacunas viraram correção em `docs/runbooks/publicacao-gold.md`. A restauração agora
  usa uma movimentação que renomeia a pasta inteira ou falha sem mover nada, e cada mensagem de erro tem orientação.
- **Limites declarados:** a colagem dos blocos num console interativo real (PSReadLine) e o PowerShell 7 não foram testados por
  ninguém. Os testes foram feitos no Windows PowerShell 5.1.
- **Pendência:** `docs/runbooks/incidentes-simulados.md` ainda cita os comandos antigos com `Move-Item`. Quem for repetir a
  simulação deve seguir o `publicacao-gold.md`, que é o texto vigente.

## 3. Métricas reais, limitações e custos observados

- **Métricas:** `docs/benchmark/` (T12): pipeline completo sem rede em cerca de 183 s, pico de memória de 5,2 GB, 13 estágios
  medidos em 3 repetições. É medição local; não representa o tempo em um executor remoto.
- **Custo estimado:** `docs/costs.md` traz a estimativa preliminar do benchmark e o custo esperado do laboratório (centavos de
  armazenamento e requisições).
- **Custo observado:** registrado em `docs/costs.md` em 17/11/2026, lido no painel de faturamento: US$ 0,00 devido e no
  mês, créditos restantes US$ 120,00. É leitura manual do painel; a primeira fatura fechada só existe em dezembro.
- **Prazo:** o laboratório deve ser desligado antes de 14/05/2027, pelo roteiro `docs/runbooks/desligar-laboratorio-aws.md`.
- **Limitações conhecidas:** a federação OIDC do GitHub ficou desligada por uma SCP da organização da conta (ADR 0002), então a
  publicação na AWS é por login local temporário.

## 4. Nenhum segredo ou dado pessoal desnecessário

- **O que foi feito (T22):** varredura mascarada de 506 arquivos rastreados e 152 commits (relatório em
  `docs/auditoria/varredura-segredos.md`). Sem achados de gravidade alta ou média: nenhuma credencial, token, chave privada,
  `.env`, estado Terraform, CPF ou dado pessoal individual.
- **Achado de gravidade baixa:** um e-mail pessoal aparece nos metadados de autoria de 145 commits (a auditoria o mascara;
  o dono deve confirmar se é o seu). Não é credencial.
  **Decisão do dono em 17/11/2026: aceitar a exposição**, sem reescrever o histórico. Reescrever o histórico é ação exclusiva do dono (regra 5) e
  muda todos os hashes; os commits novos já usam o endereço `noreply`.
- **Limite declarado pela auditoria:** a busca não prova a ausência de um segredo com formato novo, ofuscado ou criptografado.
- **Antes da demo:** repetir a varredura nos arquivos que mudaram desde 16/11/2026 (esta data é da auditoria).

## O que falta para liberar a T07

1. Dono: reconferir o custo quando a primeira fatura fechar (dezembro/2026); não bloqueia a T07.
2. ~~Decidir sobre o e-mail nos metadados Git~~: o dono aceitou em 17/11/2026.
3. Dono: confirmar os quatro itens e liberar a T07 no quadro.
4. Opcional, sem bloquear: alinhar `incidentes-simulados.md` ao runbook novo.
