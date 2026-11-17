# Demo profissional do pipeline de dados

Roteiro reproduzível de 10 a 15 minutos. A demonstração conta uma única história:
fontes públicas viram camadas rastreáveis, passam por contratos e checagens, são
publicadas com recuperação prevista e chegam a um painel estático. Não há execução
de coleta, alteração de dados, acesso à AWS nem dependência de serviços externos.

## Preparação (antes da apresentação)

Abra um PowerShell na raiz do repositório e deixe disponíveis estes arquivos:

- `docs/architecture.md`;
- `docs/contracts/sinan.md` e `docs/contracts/sinesp.md`;
- `docs/runbooks/publicacao-gold.md`;
- `docs/benchmark/README.md` e `docs/costs.md`;
- `docs/projeto-engenharia-dados/gate-c.md`;
- o painel público, se houver conexão.

Os comandos abaixo são somente leitura. Rode os testes antes da fala, para não
consumir o tempo da demo. Nunca mostre variáveis de ambiente, identidade da conta,
credenciais, nome real de bucket ou arquivos de estado Terraform.

## 0:00–2:00 — Da fonte ao produto

Mostre o diagrama de `docs/architecture.md` e diga:

> O pipeline coleta dados públicos em Bronze, padroniza em Silver e entrega
> agregados em Gold. O painel estático consome a publicação do atlas. A evolução
> preservou o pipeline e acrescentou contratos, testes, manifestos e publicação
> segura, separando código reutilizável em `src/painel_dados`.

```powershell
Get-Content docs/architecture.md | Select-Object -First 55
```

**Resultado esperado:** os diagramas do fluxo atual e do fluxo com checagens,
manifesto e publicação atômica, seguidos das fronteiras entre `pipeline/`, `src/`,
`data/`, `dashboard/`, `infra/` e `docs/`.

## 2:00–4:30 — Contratos e qualidade

Mostre que SINAN e SINESP têm contratos diferentes porque representam desafios
distintos: dados de saúde com ano preliminar e dados de segurança com cobertura
mensal e séries parciais.

```powershell
Get-Content docs/contracts/sinan.md | Select-Object -First 45
Get-Content docs/contracts/sinesp.md | Select-Object -First 45
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m ruff check src tests
```

**Resultado esperado:** os documentos apresentam esquema, granularidade e regras
temporais; o pytest termina sem falhas e o Ruff informa `All checks passed!`.
Explique que fixtures sintéticas provam falhas de esquema, tipo, chave e cobertura
sem versionar Bronze ou Silver reais.

## 4:30–7:00 — Publicar sem perder a última versão válida

Abra `docs/runbooks/publicacao-gold.md`, que é o **procedimento vigente** para
publicação e recuperação. Não execute os comandos de movimentação do runbook na
demo. Conte o fluxo: gerar em temporários irmãos, validar `data` e `downloads` como
conjunto, trocar as pastas e preservar backups quando a restauração automática não
consegue terminar.

```powershell
Select-String -Path docs/runbooks/publicacao-gold.md `
  -Pattern '^## (Preparação segura|Validar destino e backup|Recuperar|Janela sem destino no Windows|Encerramento e evidências)'
```

**Resultado esperado:** cinco marcos operacionais do runbook. Relacione-os aos
incidentes já simulados: Gold inválida, ZIP corrompido, backup órfão, falha na
segunda troca e falha na restauração. Ressalte que a versão inválida não substitui
a válida e que backups remanescentes bloqueiam a próxima publicação de propósito.

Limite importante: `docs/runbooks/incidentes-simulados.md` conserva a transcrição
histórica com comandos antigos. Para qualquer operação atual, vale
`docs/runbooks/publicacao-gold.md`.

## 7:00–9:00 — Medir antes de escolher infraestrutura

```powershell
Select-String -Path docs/benchmark/README.md `
  -Pattern 'Soma sequencial|Não medido|Executor do pipeline'
```

**Resultado esperado:** aparecem a soma sequencial medida, a seção do que não foi
medido e a recomendação de executor. Explique que o benchmark mediu 13 estágios sem
rede, em três repetições, e encontrou execução local de cerca de 3 minutos e pico
de aproximadamente 5,2 GB. Isso favorece GitHub Actions para o processamento; a
AWS foi usada como laboratório de armazenamento, versionamento, logs e orçamento,
não como justificativa artificial para migrar todo o pipeline.

Declare os limites: downloads e `fetch_*` não foram medidos; Linux e máquinas
menores não foram medidos; preços públicos mudam e precisam ser reconfirmados.

## 9:00–11:30 — Laboratório AWS, custo e decisão de segurança

```powershell
Select-String -Path docs/projeto-engenharia-dados/gate-c.md `
  -Pattern 'Custo observado|Limitações conhecidas|Nenhum segredo'
```

**Resultado esperado:** aparecem o registro do custo observado, a limitação da
federação e o resumo da auditoria. Diga que o laboratório criou armazenamento S3
privado, versionado e criptografado, logs com retenção curta e orçamento. A SCP da
organização impediu OIDC; a decisão foi não contornar a política e não criar chave
de longa duração. A publicação real ficou manual, por sessão temporária do dono.

O custo observado em 17/11/2026 foi zero, mas veio de leitura manual do painel e a
primeira fatura fechada ainda precisa ser reconferida. Não revele créditos, IDs,
nomes da conta, nomes de bucket ou identificadores de execução. O laboratório deve
ser desligado pelo runbook próprio dentro do prazo registrado no projeto.

## 11:30–13:30 — Painel público e fechamento

Se houver conexão, abra o painel público e mostre apenas três coisas: o recorte
territorial, a série temporal e a indicação de dado preliminar/parcial. Não refaça
o dashboard nem valide números ao vivo. Feche com:

> O valor não está só no painel final. Está na cadeia verificável: arquitetura
> explícita, contratos executáveis, testes sintéticos, publicação recuperável,
> desempenho medido, custo e limitações declarados. O painel continua independente
> da AWS e a última versão válida é preservada quando uma publicação falha.

**Resultado esperado:** o painel carrega e permite navegar pelos três elementos. Se
ele não carregar, use o plano alternativo abaixo; isso não invalida as evidências.

## Plano alternativo totalmente offline

Este plano não requer GitHub, AWS, fontes externas nem Silver local e cabe no mesmo
tempo:

1. Mostre os dois diagramas em `docs/architecture.md`.
2. Mostre os cabeçalhos dos contratos SINAN e SINESP.
3. Apresente o resultado já obtido de pytest e Ruff; se o ambiente local estiver
   pronto, rode-os, pois usam fixtures sintéticas.
4. Percorra os cinco títulos do `docs/runbooks/publicacao-gold.md` com o comando da
   seção de publicação; não execute recuperação.
5. Mostre em `docs/benchmark/README.md` a linha da soma sequencial e a seção
   `Não medido`.
6. Use `docs/projeto-engenharia-dados/gate-c.md` para fechar com CI, incidentes,
   custo, limitações e auditoria.

Se o painel público estiver indisponível, descreva-o a partir de
`docs/architecture.md`; não abra `dashboard/atlas/data`, não inicie servidor local
e não dependa de dados publicados. Se a `.venv` não estiver pronta, mostre o último
resultado registrado nesta entrega e diga explicitamente que os testes não foram
reexecutados naquele computador.

## Limites e pendências a declarar

- A demo reutiliza evidências existentes; não reproduz pipeline, benchmark,
  incidentes, publicação AWS nem varredura histórica.
- O `main()` integral do validador depende de dados locais não versionados; a CI
  cobre contratos e unidades desacopladas com fixtures sintéticas.
- A CI não usa credenciais AWS; `apply` e publicação no bucket continuam manuais e
  sob responsabilidade do dono.
- A auditoria reduz risco, mas não prova ausência de segredo ofuscado ou em formato
  desconhecido.
- A transcrição de incidentes é histórica; a recuperação vigente está somente em
  `docs/runbooks/publicacao-gold.md`.
- A primeira fatura fechada e os estágios de rede permanecem fora da evidência
  atual e devem ser reconferidos depois, sem bloquear esta demo.
