# Gold

Agregações anonimizadas e compactas consumidas diretamente pelo painel.

`painel.json` é reconstruído por `pipeline/build_gold.py`. Nenhum microdado é enviado ao navegador.

As séries de Brasil, Santa Catarina e Florianópolis incluem contagens,
população feminina e taxas por 100 mil mulheres. O ranking municipal preserva
os valores absolutos e também carrega as taxas para evoluções futuras da
interface.

`integrado/` contém as tabelas analíticas de SINAN, SIM, Sinesp VDE e
população feminina. Esses arquivos ainda não são consumidos pelo painel.
O processo de geração está em `pipeline/build_integrated_analysis.py`.

`raca/` contém as taxas de mortes de mulheres por agressão segundo raça, os
índices de representação das notificações do SINAN e os recortes municipais de
Santa Catarina. O denominador é o Censo 2022. O processo de geração está em
`pipeline/build_race_analysis.py`.

`rais/` contém participação feminina, razões salariais, movimentação mensal,
inserção formal de mulheres negras, escolaridade e qualidade do preenchimento.
O processo de geração está em `pipeline/build_rais.py`.

`atlas/` contém o catálogo de indicadores, a matriz de disponibilidade por
fonte e o resumo de prontidão para a ampliação do projeto. O processo de
geração está em `pipeline/build_atlas_catalog.py`. Essas saídas não alteram o
painel publicado.

O mesmo diretório contém duas Gold do SIM geradas por
`pipeline/build_sim_atlas.py`. A primeira organiza contagens e taxas anuais por
território, causa e sexo. A segunda organiza Brasil e Santa Catarina por causa
e grupo etário. As taxas terminam em 2024 porque a população disponível termina
nesse ano.

As Gold do SINAN são geradas por `pipeline/build_sinan_atlas.py`. A visão
territorial organiza notificações por indicador e sexo. A visão etária compara
Brasil e Santa Catarina. Os tipos de violência não são somados entre si e 2025
permanece sem taxa.

As Gold prioritárias do Sinesp são geradas por
`pipeline/build_sinesp_atlas.py`. O conjunto inclui matriz de cobertura por UF
e ano, resumo metodológico, séries anuais territoriais e séries mensais para
Brasil e Santa Catarina. As taxas terminam em 2024. A cobertura municipal em
Santa Catarina existe para feminicídio, tentativa de feminicídio, homicídio
doloso, tentativa de homicídio e suicídio. Os demais eventos prioritários são
mantidos apenas nos níveis Brasil e UF quando o arquivo não identifica o
município.


## ibge/

`censo2022_mulheres_cor_raca_uf.csv`: mulheres por cor ou raça no Censo 2022, Brasil e
UFs, com participação de negras (preta + parda) e brancas sobre as identificadas.
Referência para o teste de embranquecimento da RAIS (bloco 0.5 do SQL) e denominador
estadual das taxas por raça do SIM.
