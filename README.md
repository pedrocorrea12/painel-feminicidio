# Painel de Violência contra a Mulher

Projeto de portfólio com indicadores de violência contra a mulher, mortes por agressão e contexto territorial para Brasil, Santa Catarina e Florianópolis.

## Arquitetura de dados

O projeto usa uma arquitetura medalhão enxuta:

- **Bronze:** arquivos brutos do DataSUS e dimensões oficiais, preservados sem transformação analítica.
- **Silver:** microdados filtrados e padronizados, com chaves e tipos consistentes.
- **Gold:** agregações pequenas e documentadas, prontas para o painel estático.

```text
data/bronze  ->  data/silver  ->  data/gold  ->  dashboard/dist/data
```

Os parquets Bronze e Silver são ignorados pelo Git por volume e sensibilidade operacional. Os JSONs Gold, pequenos e agregados, são versionáveis.

## Estrutura

```text
pipeline/                 extração, transformação e validação
data/bronze/              fontes preservadas
data/silver/              microdados tratados
data/gold/                agregados para consumo
dashboard/dist/           site estático publicável
docs/                     metodologia e investigação técnica
```

## Como atualizar

Com o Anaconda instalado:

```powershell
C:\Users\User\anaconda3\python.exe pipeline\build_gold.py
```

O comando valida os números de controle, gera `data/gold/painel.json` e copia o resultado para `dashboard/dist/data/painel.json`.
Ele também reconstrói antes a Silver consolidada
`data/silver/indicadores_territorio_ano.parquet`, cruzando SINAN e população.

Para atualizar o SINAN a partir do FTP, execute primeiro:

```powershell
C:\Users\User\anaconda3\python.exe pipeline\extract_sinan.py
```

O `pysus` precisa estar instalado para essa etapa. A construção da camada Gold usa apenas `pandas` e `pyarrow`.

Para atualizar a população feminina municipal diretamente das fontes oficiais
do Ministério da Saúde e do IBGE:

```powershell
C:\Users\User\anaconda3\python.exe pipeline\fetch_populacao_feminina.py
```

## Escopo atual

- SINAN consolidado: 2015–2024.
- Recortes disponíveis: Brasil, Santa Catarina e Florianópolis.
- Ranking municipal de SC por notificações e vínculo com parceiro/ex-parceiro.
- População feminina municipal: materializada para 2015–2024; o cruzamento com
  SINAN foi consolidado para Brasil, UFs e municípios, e as taxas já integram a
  camada Gold e o painel.
- SIM: metodologia validada, mas ainda não materializado no repositório.

O painel diferencia explicitamente notificações do SINAN, mortes por agressão do SIM e feminicídio jurídico-policial.


