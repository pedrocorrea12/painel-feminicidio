# Silver

Dados tratados, tipados e filtrados para uso analítico.

O arquivo principal é `sinan_viol_mulheres_interpessoal.parquet`, contendo mulheres com `LES_AUTOP == '2'`, isto é, violência interpessoal e não autoprovocada.

`sinan_viol_mulheres_interpessoal_2025_preliminar.parquet` contém a extração
preliminar de 2025 com o mesmo recorte. A tabela agregada correspondente é
`sinan_preliminar_territorio_ano.parquet`.

`sinan_atlas_violencia.parquet` amplia o SINAN para todos os sexos e separa
violência interpessoal de violência autoprovocada. A base cobre 2015 a 2025 e
preserva sexo, raça, idade, residência e sete marcações de tipo de violência.
As marcações podem coexistir no mesmo registro.

`sim_mulheres_agressao.parquet` contém óbitos femininos por agressão segundo o
SIM. Os anos de 2015 a 2024 estão marcados como definitivos, 2025 como
preliminar e 2026 como prévia. Os dois anos mais recentes possuem cobertura
parcial observada até agosto.

`sim_atlas_mortalidade.parquet` amplia o SIM para todos os sexos e preserva
sexo, raça, idade, município de residência, município de ocorrência e causa
básica. A base contém agressões, suicídios e acidentes de transporte de 2015 a
2026. A validação confirma que o recorte feminino de agressões coincide com a
série anterior em todos os anos.

`populacao_feminina_municipio.parquet` contém a população feminina anual dos
5.570 municípios brasileiros entre 2015 e 2024, pronta para junção pelas chaves
`ano` e `id_municipio`.

`populacao_municipio_ano.parquet`, `populacao_municipio_sexo_ano.parquet` e
`populacao_municipio_idade_ano.parquet` contêm os denominadores gerais de 2015
a 2024. As três bases cobrem os 5.570 municípios e reconciliam seus totais por
município e ano. Sexo e idade são recortes independentes da fonte, portanto não
há denominador combinado de sexo por idade. A base de idade preserva 81 idades
simples e também informa o grupo etário analítico.

`populacao_municipio_2025.parquet` contém a população total municipal oficial
do IBGE para 2025. A população por sexo é estimada aplicando a proporção de
2024 à população total de 2025. O campo `tipo_denominador_sexo` identifica o
método.

`indicadores_territorio_ano.parquet` é a Silver consolidada. Reúne Brasil, 27
UFs e 5.570 municípios por ano, com notificações, vínculo com parceiro ou
ex-parceiro, ocorrências na residência, população feminina, percentuais, taxas
por 100 mil mulheres e uma flag de suficiência para pequenos números.


`sinesp_vde_ocorrencias.parquet` contém a base Sinesp VDE completa desde 2019:
todas as UFs e municípios, por ano, mês e evento, com vítimas por sexo
(`vitimas_feminino`, `vitimas_masculino`, `vitimas_nao_informado`, `total_vitimas`),
contagem de ocorrências (`total_ocorrencias`) e peso apreendido (`total_peso`).
A coluna `abrangencia` separa Estadual, Polícia Federal e PRF; só a Estadual
entra nos totais da Gold. O último ano publicado com menos de 12 meses recebe
`situacao_dado = parcial`.

`sinesp_feminicidio.parquet` é o recorte de Feminicídio (abrangência Estadual)
dessa base, por UF, município, ano e mês, consumido por `build_gold.py`.

`rais_vinculos_raca_sexo.parquet` contém o estoque de vínculos formais ativos
em 31 de dezembro, por território, sexo e raça. A série por sexo cobre 2019 a
2025. A coluna `raca_usavel` restringe o recorte racial a 2024 e 2025.

`rais_movimentacao_mensal.parquet` contém admissões, desligamentos e saldo por
mês, território, sexo e raça. `rais_escolaridade_raca_sexo.parquet` preserva o
grão adicional de escolaridade para a análise racial de 2024 e 2025.
