# Bronze

Camada de preservação das fontes originais. Os dados não são corrigidos nem agregados aqui.

- `sinan/cache_bruto`: arquivos nacionais anuais convertidos do DBC para parquet.
- `ibge/municipios_sc.json`: dimensão municipal obtida da API oficial de localidades do IBGE.
- `ibge/municipios_brasil.json`: dimensão nacional atual da mesma API, usada para
  converter com segurança os códigos municipais de seis para sete dígitos.
- `sinesp/vde/bancovde-AAAA.xlsx`: base anual Sinesp VDE publicada pelo MJSP
  (ocorrências e vítimas por UF, município, mês e evento), com cache `.parquet`
  idêntico ao lado de cada xlsx para evitar releitura.
- `rais/obsref/*.csv`: extrações da RAIS de vínculos por raça/cor e sexo feitas no
  Databricks do Observatório FIESC com `pipeline/sql/rais_obsref_raca_sexo.sql`.
  Ver `docs/RAIS.md`.
- `ibge/censo2022_9606_mulheres_cor_raca_br_uf.json`: resposta bruta da API do SIDRA,
  tabela 9606 do Censo 2022 (população residente por cor ou raça), mulheres, todas as
  idades, Brasil e 27 UFs. Obtida em 15/10/2026 pelo navegador, porque a API recusa
  scripts (403).
- `ibge/ripsa014dm.csv.zip`: população municipal por sexo e idade, obtida do portal
  de dados abertos do Ministério da Saúde.

Arquivos volumosos são mantidos localmente e ignorados pelo Git.

