# Bronze

Camada de preservação das fontes originais. Os dados não são corrigidos nem agregados aqui.

- `sinan/cache_bruto`: arquivos nacionais anuais convertidos do DBC para parquet.
- `ibge/municipios_sc.json`: dimensão municipal obtida da API oficial de localidades do IBGE.
- `ibge/municipios_brasil.json`: dimensão nacional atual da mesma API, usada para
  converter com segurança os códigos municipais de seis para sete dígitos.
- `ibge/ripsa014dm.csv.zip`: população municipal por sexo e idade, obtida do portal
  de dados abertos do Ministério da Saúde.

Arquivos volumosos são mantidos localmente e ignorados pelo Git.

