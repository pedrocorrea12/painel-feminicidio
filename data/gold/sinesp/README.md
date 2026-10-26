# Sinesp VDE — Brasil e Santa Catarina

Gerado por `pipeline/extract_sinesp.py` em 2026-10-14 a partir dos arquivos `bancovde-AAAA.xlsx` publicados pelo MJSP.

Fonte: https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023

Arquivos:

- `sinesp_sc_brasil_mensal.csv`: Brasil e SC por ano, mês e evento.
- `sinesp_sc_brasil_anual.csv`: mesma base agregada por ano, com `meses_informados`.
- `sinesp_uf_anual.csv`: todas as UFs por ano e evento, para comparação.
- `sinesp_sc_municipios_anual.csv`: municípios catarinenses por ano e evento.
- `sinesp_feminicidio_sc_brasil_anual.csv`: vítimas de feminicídio, Brasil × SC, por ano.

Leitura das medidas:

- Eventos contra a pessoa (Feminicídio, Homicídio doloso, Estupro, Estupro de vulnerável, Lesão corporal seguida de morte, Latrocínio, Tentativas, Suicídio, Mortes no trânsito, Pessoa Desaparecida/Localizada) são medidos em vítimas: `vitimas_feminino`, `vitimas_masculino`, `vitimas_nao_informado` e `total_vitimas`.
- Eventos patrimoniais e de produtividade (Furto e Roubo de veículo, Roubo de carga, Roubo a instituição financeira, Tráfico de drogas, Arma de Fogo Apreendida, Mandado de prisão cumprido, atividades de bombeiros) são contagens em `total_ocorrencias`.
- Apreensões de Cocaína e Maconha são medidas em quilos em `total_peso`.
- Só a abrangência `Estadual` entra nos totais. Linhas da Polícia Federal e da PRF ficam na Silver, separadas, para não dobrar a contagem.
- Linhas repetidas do mesmo mês (Estupro e Tentativa de Homicídio) são somadas, conforme nota do MJSP. Zero significa ausência de ocorrência, não ausência de dado.
- `situacao_dado = parcial` marca o último ano publicado com menos de 12 meses.
