# Contrato de dados: site do atlas

Implementação: `src/painel_dados/contracts/atlas_site.py`. Testes:
`tests/contracts/test_atlas_site.py` (diretório sintético montado em `tmp_path`).

`validar_diretorio_site(diretorio)` roda sobre o diretório **temporário** gerado por
`pipeline/build_atlas_site_data.py`, antes de ele substituir `dashboard/atlas/data`
via `painel_dados.publish.publicar_diretorio`. Falha levanta `ValueError` e a versão
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
- cada ZIP listado em `downloads` existe ao lado do diretório de dados.

## Comportamento do pipeline

- `malha_sc.json` não é gerado pelo script: é copiado da versão publicada para o
  diretório temporário, como antes (o script já o preservava).
- **Fora do escopo:** os ZIPs em `dashboard/atlas/downloads` continuam escritos
  diretamente (são gerados antes do manifesto, que registra tamanhos e linhas).
  Uma falha de validação não os reverte.
- Um backup órfão (`.data.backup-*`) bloqueia a próxima publicação até limpeza
  manual (ver T05).
- Evidência: a execução sobre os dados reais reproduz o diretório versionado, exceto
  `atualizado_em` no manifesto; os ZIPs têm o mesmo conteúdo (CRC) e só mudam o
  carimbo interno.
