# Arquitetura do pipeline de dados

## Estado atual

O projeto coleta fontes públicas, preserva arquivos e caches na Bronze, produz
Parquet padronizado na Silver e materializa CSV e JSON agregados na Gold. O
dashboard estático consome artefatos copiados para `dashboard/atlas/data` e é
publicado pelo GitHub Pages.

```text
DataSUS e MJSP
      |
pipeline/extract_*.py
      |
data/bronze -> data/silver -> data/gold
                                  |
                         dashboard/atlas/data
                                  |
                            GitHub Pages
```

## Arquitetura alvo

O fluxo de dados permanece. A evolução adiciona contratos, componentes
reutilizáveis, testes, manifestos e execução controlada.

```text
sources -> ingestion -> bronze -> transform -> silver -> model -> gold
              |                     |                    |
          retries/logs          schema checks       reconciliation
              \_____________________|____________________/
                                    |
                              run manifest
                                    |
                         atomic site publication
```

## Fronteiras

- `pipeline/`: entrada compatível durante a migração.
- `src/painel_dados/`: código reutilizável e testável.
- `data/`: artefatos organizados por estágio de processamento.
- `dashboard/atlas/`: produto público independente da AWS.
- `infra/terraform/`: laboratório AWS posterior ao Gate A.
- `docs/`: contratos, decisões, operação e evidências.

## Pilotos

SINAN representa saúde e exercita download nacional, cache anual, dados
preliminares e padronização territorial. SINESP representa segurança e exercita
download de planilhas, mudanças de esquema, cobertura mensal e séries parciais.

## Publicação

O artefato Gold deverá ser escrito primeiro em caminho temporário, validado e
movido atomicamente para o destino público. Uma falha de extração ou qualidade
não poderá substituir a última versão válida do dashboard.
