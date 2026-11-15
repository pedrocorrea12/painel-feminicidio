# Panorama Territorial da Violência

## Objetivo

Ampliar o painel atual para um produto territorial sobre violência, preservando o recorte de violência contra a mulher como capítulo próprio.

Abrangência inicial:

- Brasil, unidades da federação e municípios de Santa Catarina.
- Série consolidada até 2025, conforme disponibilidade de cada fonte.
- Dados de 2026 separados como monitoramento parcial.
- Valores absolutos e taxas, sempre com denominador e período explícitos.

## Situação em 26 de outubro de 2026

O catálogo contém 48 indicadores provenientes de seis fontes:

- 30 eventos do Sinesp VDE e 1 indicador derivado de violência sexual policial.
- 4 indicadores do SIM.
- 9 indicadores do SINAN.
- 2 bases de denominadores do IBGE.
- 1 base racial do Censo 2022.
- 1 conjunto socioeconômico da RAIS.

Classificação de prontidão:

- 18 indicadores prontos.
- Nenhum indicador limitado somente às mulheres por falta de processamento.
- 30 indicadores prontos com ressalvas de cobertura ou comparabilidade.
- Nenhum indicador exige reprocessamento das bases já disponíveis.

Arquivos gerados:

- `data/gold/atlas/catalogo_indicadores.csv`
- `data/gold/atlas/matriz_disponibilidade_fontes.csv`
- `data/gold/atlas/resumo_catalogo.json`
- `data/gold/atlas/sinesp_cobertura_evento_uf_ano.csv`
- `data/gold/atlas/sinesp_cobertura_evento_resumo.csv`
- `data/gold/atlas/sinesp_prioridade_territorio_ano.csv`
- `data/gold/atlas/sinesp_prioridade_mensal.csv`
- `data/gold/atlas/sinesp_prioridade_metodologia.json`

O catálogo é reproduzível por `pipeline/build_atlas_catalog.py`.

## Primeira versão recomendada

### Visão geral

- Homicídio doloso.
- Mortes por agressão no SIM.
- Tentativa de homicídio.
- Feminicídio e tentativa de feminicídio.
- Estupro e estupro de vulnerável.
- Suicídio.
- Pessoas desaparecidas e localizadas.

### Violência contra a mulher

O painel atual permanece como capítulo do produto maior, com SINAN, SIM, Sinesp, Censo e RAIS.

### Desigualdades

- Sexo.
- Faixa etária.
- Raça ou cor.
- Inserção no emprego formal.
- Remuneração.

## Regras obrigatórias

1. Não somar registros de SINAN, SIM e Sinesp.
2. Informar se o território corresponde à residência ou ao local do fato.
3. Separar anos consolidados, preliminares e parciais.
4. Mostrar número absoluto junto da taxa.
5. Aplicar critérios mínimos antes de ranquear municípios pequenos.
6. Manter tipos de violência do SINAN como marcações que podem coexistir no mesmo registro.
7. Tratar a relação entre trabalho e violência como associação territorial descritiva, sem inferência causal.
8. Para a série de violência sexual em Santa Catarina, avaliar em conjunto estupro e estupro de vulnerável por causa da mudança de classificação observada em 2020.

## Próxima etapa

1. Prototipar a navegação do atlas usando apenas as camadas validadas.
2. Manter o painel publicado sem alteração durante a avaliação do protótipo.
3. Definir critérios editoriais de ranking e comparação antes da publicação.

## Denominadores populacionais concluídos

O arquivo bruto do Ministério da Saúde contém três recortes independentes:

- População total.
- População por sexo.
- População por idade simples, incluindo 80 anos e mais.

O processo `pipeline/fetch_populacao_geral.py` gera três bases Silver para os
5.570 municípios, de 2015 a 2024. A soma dos sexos e a soma das idades são
validadas contra a população total em cada município e ano.

O processo `pipeline/build_populacao_2025.py` acrescenta a população total
municipal oficial do IBGE para 2025. A população por sexo de 2025 é estimada
aplicando a proporção municipal de 2024 à população total oficial de 2025. O
arquivo registra o método usado no denominador.

A fonte não cruza sexo e idade. Assim, o atlas poderá calcular taxas gerais,
taxas por sexo e taxas por idade, mas não taxas conjuntas por sexo e idade com
esta base. As taxas por idade permanecem limitadas a 2024.

## Mortalidade concluída

O processo `pipeline/build_sim_atlas.py` lê os arquivos locais do SIM e gera:

- Agressões, CID-10 X85 a Y09.
- Suicídios, CID-10 X60 a X84.
- Acidentes de transporte, CID-10 V01 a V99.

A Silver preserva sexo, raça, idade, causa básica, residência e ocorrência.
A Gold territorial contém Brasil, 27 UFs e os 295 municípios de Santa Catarina.
A Gold etária contém Brasil e Santa Catarina. As taxas utilizam residência e
ficam limitadas a 2015 a 2024. As contagens de 2025 e 2026 continuam disponíveis
com a situação do dado explícita.

## Notificações concluídas

O processo `pipeline/build_sinan_atlas.py` separa violência interpessoal e
autoprovocada para todos os sexos. Também preserva as marcações de violência
física, psicológica, sexual, financeira, negligência, tortura e tráfico de
pessoas.

A unidade é a notificação, não a pessoa. Um mesmo registro pode conter mais de
um tipo de violência. Por isso, os tipos não podem ser somados. As Gold cobrem
Brasil, 27 UFs e os 295 municípios de Santa Catarina. Em 2025, as taxas usam a
população total oficial e a população por sexo estimada. O numerador de 2025 é
preliminar e deve permanecer identificado dessa forma.

## Registros policiais concluídos

O processo `pipeline/build_sinesp_atlas.py` validou os nove eventos
prioritários do Sinesp entre 2019 e agosto de 2026. Todos apresentam os meses
esperados nas 27 UFs: 12 meses de 2019 a 2025 e 8 meses em 2026.

As Gold incluem Brasil, todas as UFs e séries mensais para Brasil e Santa
Catarina. Feminicídio, tentativa de feminicídio, homicídio doloso, tentativa
de homicídio e suicídio também possuem cobertura dos 295 municípios
catarinenses. Estupro, estupro de vulnerável, pessoa desaparecida e pessoa
localizada aparecem somente como total estadual no arquivo atual e não devem
ser apresentados por município.

As taxas usam população total ou do sexo correspondente. Em 2025, a população
total é oficial e a população por sexo é estimada com a proporção de 2024. O
ano de 2026 cobre janeiro a agosto, não recebe taxa anual e deve ser comparado
somente com o mesmo período de anos anteriores.

A camada inclui o indicador derivado `Violência sexual policial, soma das
classificações`. Ele facilita a leitura conjunta de estupro e estupro de
vulnerável, mas não elimina mudanças de classificação entre UFs e anos. A
quebra de Santa Catarina entre 2019 e 2020 permanece sinalizada.

## Fora da primeira versão

- Medidas protetivas e processos judiciais.
- Chamadas policiais e atendimentos de emergência locais.
- Rede de acolhimento e serviços municipais.
- Sistema prisional.
- Pesquisas de vitimização.
- Mapas intramunicipais sem dados georreferenciados confiáveis.
