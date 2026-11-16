# Contrato de dados: site do atlas

Implementação: `src/painel_dados/contracts/atlas_site.py`. Testes:
`tests/contracts/test_atlas_site.py` (diretório sintético montado em `tmp_path`).

`validar_diretorio_site(diretorio, diretorio_downloads=None)` roda sobre os diretórios
**temporários** gerados por `pipeline/build_atlas_site_data.py`, antes de eles
substituírem `dashboard/atlas/data` e `dashboard/atlas/downloads` via
`painel_dados.publish.publicar_conjunto`. Falha levanta `ValueError` e a versão
publicada anterior é mantida.

## O que verifica

- arquivos obrigatórios: `manifesto.json`, `nacional.json`, `idade.json`,
  `mensal.json`, `desigualdades.json`, `malha_sc.json`;
- manifesto com as chaves `atualizado_em`, `periodo_consolidado`, `territorios`,
  `municipios`, `indicadores`, `downloads`, `arquivos`; indicadores sem duplicata;
- 295 municípios no manifesto e um arquivo `municipio/<id>.json` para cada um;
- cada indicador com `arquivo_mapa` tem o arquivo correspondente em `mapa/`;
- `desigualdades.json` com as seis tabelas esperadas, cada uma não vazia;
- estruturas malformadas no manifesto viram `ValueError` ("Estrutura inválida");
- tabelas (`colunas` + `linhas`) não vazias e com linhas da largura das colunas;
- `nacional.json` só referencia indicadores do manifesto;
- cada ZIP listado em `downloads` existe ao lado do diretório de dados (validação
  simples, sem o parâmetro `diretorio_downloads`);
- com `diretorio_downloads` (usado pelo pipeline sobre a versão ainda não publicada),
  cada ZIP é validado a fundo: o caminho é `downloads/<nome>.zip`; o arquivo existe;
  `bytes` do manifesto é o tamanho real; o ZIP abre e passa em `testzip`; contém só
  `<nome>.csv`; `linhas` do manifesto é o número de registros do CSV (sem o
  cabeçalho); e nenhum arquivo fora do manifesto sobra no diretório. As mensagens
  começam por `Download ausente`, `Download com caminho inválido`,
  `Download com tamanho divergente`, `Download corrompido`,
  `Download sem o CSV esperado`, `Download com contagem divergente`,
  `Download sem registros` (CSV só com cabeçalho) e `Download fora do manifesto`.
- a publicação conjunta rejeita destinos duplicados ou aninhados (um dentro do
  outro) e, na reversão, informa por exceção qualquer backup preservado ou versão
  nova que não pôde ser removida.

## Comportamento do pipeline

- `malha_sc.json` não é gerado pelo script: é copiado da versão publicada para o
  diretório temporário, como antes (o script já o preservava).
- Desde a T20, `dashboard/atlas/data` e `dashboard/atlas/downloads` são publicados
  **juntos** por `painel_dados.publish.publicar_conjunto`: os dois são gerados em
  diretórios temporários, validados entre si e trocados com backup. Se a validação
  ou a troca de qualquer um falhar, os dois voltam à versão anterior; não existe
  mais ZIP novo ao lado de dados antigos.
- Um backup órfão (`.data.backup-*` ou `.downloads.backup-*`) bloqueia a próxima
  publicação até limpeza manual (ver T05 e o runbook de publicação).
- Evidência: a execução sobre os dados reais reproduz o diretório versionado, exceto
  `atualizado_em` no manifesto; os ZIPs têm o mesmo conteúdo (CRC) e só mudam o
  carimbo interno.
