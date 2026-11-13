# Contrato de dados: Sinesp VDE

Implementação: `src/painel_dados/contracts/sinesp.py`. Testes:
`tests/contracts/test_sinesp.py`, com fixtures sintéticas em
`tests/fixtures/sinesp/`. Contexto da fonte em `docs/SINESP_VDE.md`.

Todas as funções levantam `ValueError` com mensagem estável. O contrato descreve
o que `pipeline/extract_sinesp.py` produz hoje e foi conferido contra a Silver e
a Gold atuais (somente leitura).

## Funções

| Função | Alvo | O que verifica |
| --- | --- | --- |
| `validar_bronze` | xlsx normalizado | colunas `uf`, `municipio`, `evento`, `data_referencia`; extras são aceitas |
| `validar_silver_ocorrencias` | `silver/sinesp_vde_ocorrencias.parquet` | colunas, tipos, `mes` 1 a 12, medidas não negativas, `abrangencia` e `situacao_dado` válidos |
| `validar_silver_feminicidio` | `silver/sinesp_feminicidio.parquet` | colunas, tipos, `mes`, medida, situação |
| `validar_gold_mensal` | `gold/sinesp/sinesp_sc_brasil_mensal.csv` | colunas, tipos, domínios, chave única |
| `validar_gold_anual` | `gold/sinesp/sinesp_sc_brasil_anual.csv` | idem, mais `meses_informados` entre 1 e 12 |
| `validar_cobertura_mensal` | Gold mensal | ano consolidado com 12 meses; ano parcial sem lacuna (1..N) |

## Granularidade e chaves

- **Silver (ocorrências):** uma linha por mês, UF, município, evento, abrangência
  e desagregações (agente, arma, faixa etária). **Sem chave única**: o MJSP envia
  mais de uma linha por mês para o mesmo evento e município (Estupro; DF dividido
  em várias linhas). Elas são somadas na Gold. Por isso o contrato não impõe
  unicidade na Silver.
- **Gold mensal:** `territorio, ano, mes, evento`.
- **Gold anual:** `territorio, ano, evento`.

## Domínios

- `abrangencia`: `Estadual`, `Polícia Federal`, `Polícia Rodoviária Federal`.
  Só `Estadual` entra nos totais.
- `situacao_dado`: `consolidado_publicacao` ou `parcial` (último ano publicado
  com menos de 12 meses).
- `territorio`: `Brasil` ou `Santa Catarina`.

## Periodicidade e séries parciais

- A série é mensal, com um arquivo `bancovde-AAAA.xlsx` por ano.
- Zero é ausência de ocorrência; lacuna real é mês sem linha. Por isso a cobertura
  é medida pela presença de linhas, não pelo valor.
- O ano `parcial` (hoje 2026, janeiro a agosto) deve ter meses contíguos a partir
  de janeiro. Anos consolidados exigem os 12 meses.
- `validar_cobertura_mensal` verifica por padrão só `Feminicídio`; outros eventos
  podem ser passados em `eventos_obrigatorios`. Eventos municipais parciais
  (Estupro, Pessoa Desaparecida) só existem no total estadual, então o padrão
  não os inclui.

## Limites conhecidos

- Quebras de série dos estados (Estupro em SC 2019, ES, RO, MA) são problema de
  conteúdo, não de esquema, e **não** são detectadas por este contrato.
- Não há checagem de reconciliação contra o Anuário (Brasil 2019 = 1.331
  feminicídios); fica para a tarefa de testes de reconciliação.
