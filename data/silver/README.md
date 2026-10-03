# Silver

Dados tratados, tipados e filtrados para uso analítico.

O arquivo principal é `sinan_viol_mulheres_interpessoal.parquet`, contendo mulheres com `LES_AUTOP == '2'`, isto é, violência interpessoal e não autoprovocada.

`populacao_feminina_municipio.parquet` contém a população feminina anual dos
5.570 municípios brasileiros entre 2015 e 2024, pronta para junção pelas chaves
`ano` e `id_municipio`.

`indicadores_territorio_ano.parquet` é a Silver consolidada. Reúne Brasil, 27
UFs e 5.570 municípios por ano, com notificações, vínculo com parceiro ou
ex-parceiro, ocorrências na residência, população feminina, percentuais, taxas
por 100 mil mulheres e uma flag de suficiência para pequenos números.

