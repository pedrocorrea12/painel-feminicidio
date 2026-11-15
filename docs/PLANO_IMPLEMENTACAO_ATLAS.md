# Plano de implementação do Atlas

Complementa `REQUISITOS_ATLAS.md` e `DESENHO_TELAS_ATLAS.md`. Status: rascunho, sem código.

## Ponto de partida

- Gold do atlas pronta e validada em `data/gold/atlas/` (SIM, SINAN, Sinesp, catálogo).
- `pipeline/build_atlas_prototype_data.py` gera um `data.json` de 16 MB, grande demais para publicar.
- Painel atual em `dashboard/dist/` (HTML, CSS e JS puros, sem build).
- Protótipo antigo em `dashboard/prototipos/monitoramento-atual/`.
- Alterações do repositório ainda sem commit.

## Decisões técnicas propostas

| Tema | Proposta | Motivo |
| --- | --- | --- |
| Stack | HTML, CSS e JS sem build, módulos ES | Mantém o padrão atual e o deploy no GitHub Pages |
| Gráficos | SVG próprio ou uma biblioteca pequena via CDN | Evita dependência pesada |
| Mapa | GeoJSON simplificado dos 295 municípios de SC | Leve, sem biblioteca de mapas |
| Dados | Arquivos JSON pequenos por fonte e território, carregados sob demanda | Substitui o `data.json` de 16 MB |
| Estado | Território, indicador e período na URL | Permite linkar uma visão específica |

## Etapas

### Etapa 0 — Organizar o repositório
- Commitar o trabalho acumulado em commits separados por assunto: pipeline, Gold, documentação.
- Decidir o que não versionar (parquets pesados já ignorados, `outputs/`, `__pycache__`).
- Criar uma branch para o atlas.
- **Pronto quando:** `git status` limpo e histórico legível.

### Etapa 1 — Dados para o site
- Reescrever a geração do JSON: um índice, um arquivo por fonte e indicador, e um por município, em `dashboard/atlas/data/`.
- Incluir em cada registro: valor, taxa, denominador, fonte, tipo de território (residência ou local do fato) e situação do dado.
- Gerar os CSVs para download e um manifesto com data de atualização.
- Definir o critério mínimo de casos e de população e gravar a flag `dado_suficiente` na Gold.
- **Pronto quando:** nenhum arquivo passa de cerca de 1 MB e o validador confere o conteúdo gerado.

### Etapa 2 — Malha do mapa
- Baixar a malha municipal de SC do IBGE e guardá-la em `data/bronze/ibge/`.
- Simplificar a geometria e gerar o GeoJSON final, ligado pelo código de 7 dígitos do município.
- **Pronto quando:** os 295 municípios têm geometria e casam com os IDs da Gold.

### Etapa 3 — Esqueleto do site
- Estrutura de pastas, menu fixo, seletor global de território, rodapé, tema e paleta.
- Leitura e escrita do estado na URL.
- **Pronto quando:** navegação entre seções funciona no desktop e no celular, ainda com conteúdo de exemplo.

### Etapa 4 — Visão geral e Evolução
- Cartões de indicadores, gráficos de linha, alternância entre absoluto e taxa e marcação de anos preliminares e parciais.
- **Pronto quando:** trocar o território atualiza todos os números, com fonte e ressalvas visíveis.

### Etapa 5 — Mapa e ranking
- Mapa coroplético, hachurado para municípios sem dado suficiente, ranking lateral e busca.
- **Pronto quando:** clicar num município muda o território global e indicadores só estaduais ficam bloqueados com aviso.

### Etapa 6 — Desigualdades
- Sexo, idade, raça ou cor e RAIS, com os avisos sobre denominadores.
- **Pronto quando:** cada gráfico tem nota do que não mede.

### Etapa 7 — Capítulo Mulheres e Recente
- Migrar o painel atual para o capítulo de mulheres, com os três blocos separados por fonte.
- Tela de monitoramento com comparação do mesmo período e série mensal do Sinesp.
- **Pronto quando:** nenhum número do painel antigo se perde e os valores batem com os controles da Gold.

### Etapa 8 — Metodologia, downloads e citação
- Tabela de fontes, fórmulas, seção técnica para portfólio, downloads e texto de citação.
- **Pronto quando:** todo indicador exibido tem entrada correspondente na metodologia.

### Etapa 9 — Qualidade
- Teste automático que confere os valores exibidos contra a Gold.
- Verificação no celular e por teclado, contraste e tabelas alternativas dos gráficos.
- Teste de carga: tamanho total transferido e tempo de abertura.
- **Pronto quando:** sem erros no console e a página abre rápido em conexão média.

### Etapa 10 — Publicação
- Atualizar o fluxo do GitHub Pages para o novo diretório, com redirecionamento da URL antiga.
- Gerar zip de entrega e backup do painel publicado antes da troca.
- **Pronto quando:** site publicado, conferido em produção e o painel antigo guardado como backup.

## Dependências entre etapas

- A 1 e a 2 vêm antes de 4 a 7.
- A 3 pode andar em paralelo com a 1 e a 2.
- As telas 4 a 7 são independentes entre si depois do esqueleto e podem entrar uma de cada vez.

## Riscos

- **Peso dos dados:** a granularidade por município, fonte, sexo e ano pode crescer. Mitigação: arquivos por território e carregamento sob demanda.
- **Falta de casos em municípios pequenos:** mapa com muito hachurado. Mitigação: critério mínimo ajustável e opção de agrupar anos.
- **Ressalvas demais:** a leitura pode ficar pesada. Mitigação: um aviso curto no gráfico e o detalhe na Metodologia.
- **Malha do IBGE:** formato ou código diferente do esperado. Mitigação: conferir o casamento dos IDs antes de desenhar.
- **Dados de 2025 e 2026 mudarem:** a Gold precisa ser regerada. Mitigação: fluxo único de atualização e data visível.

## Ordem sugerida de entrega

Primeiro um núcleo publicável (etapas 0 a 4), depois mapa e desigualdades (5 e 6), por fim mulheres, recente e publicação (7 a 10). O núcleo já serve como demonstração de portfólio.
