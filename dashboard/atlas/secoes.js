// Seções de conteúdo: cartões da Visão geral e gráfico de Evolução.
// Reagem ao evento "atlas:estado" disparado por app.js.

import { criarDados } from "./dados.js?v=20261106c";
import { fmtInteiro, fmtTaxa, graficoLinhas, mapaMunicipal, miniatura } from "./graficos.js?v=20261106c";

const CARTOES = [
  { id: "sinesp_homicidio_doloso", titulo: "Homicídio doloso" },
  { id: "sim_agressao", titulo: "Mortes por agressão" },
  { id: "sinesp_tentativa_de_homicidio", titulo: "Tentativa de homicídio" },
  { id: "sinesp_violencia_sexual_policial_soma_das_classificacoes", titulo: "Estupro e estupro de vulnerável" },
  { id: "sim_suicidio", titulo: "Mortes por suicídio" },
  { id: "sinesp_pessoa_desaparecida", titulo: "Pessoas desaparecidas" },
];

const SEXOS = [
  ["total", "Todos"],
  ["feminino", "Feminino"],
  ["masculino", "Masculino"],
];
const MEDIDAS = [
  ["taxa", "Taxa por 100 mil"],
  ["absoluto", "Valor absoluto"],
];
const UFS = {
  AC: "Acre", AL: "Alagoas", AM: "Amazonas", AP: "Amapá", BA: "Bahia",
  CE: "Ceará", DF: "Distrito Federal", ES: "Espírito Santo", GO: "Goiás",
  MA: "Maranhão", MG: "Minas Gerais", MS: "Mato Grosso do Sul",
  MT: "Mato Grosso", PA: "Pará", PB: "Paraíba", PE: "Pernambuco", PI: "Piauí",
  PR: "Paraná", RJ: "Rio de Janeiro", RN: "Rio Grande do Norte",
  RO: "Rondônia", RR: "Roraima", RS: "Rio Grande do Sul", SC: "Santa Catarina",
  SE: "Sergipe", SP: "São Paulo", TO: "Tocantins",
};
const INDICADORES_IDADE = [
  "sim_agressao", "sim_suicidio", "sim_acidente_transporte",
  "sinan_notificacoes_interpessoais", "sinan_notificacoes_autoprovocadas",
  "sinan_violencia_fisica", "sinan_violencia_psicologica", "sinan_violencia_sexual",
];
const INDICADORES_MONITOR = [
  "sinesp_homicidio_doloso", "sinesp_tentativa_de_homicidio",
  "sinesp_feminicidio", "sinesp_tentativa_de_feminicidio",
  "sinesp_suicidio", "sinesp_violencia_sexual_policial_soma_das_classificacoes",
];

const $ = (id) => document.getElementById(id);

function tag(nome, classe, texto) {
  const e = document.createElement(nome);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

function notaDenominador2025(tipo) {
  if (tipo === "estimado_proporcao_2024") {
    return "A população de 2025 por sexo foi estimada aplicando a proporção de 2024 à população total oficial de 2025.";
  }
  if (tipo === "publicado") {
    return "A taxa de 2025 usa a população total oficial do IBGE.";
  }
  return "";
}

export function iniciarSecoes({ manifesto, territorioPorId, definirEstado, obterEstado }) {
  const dados = criarDados(manifesto);
  let rodada = 0;
  let janelaMapa = "3a";
  let ufComparacao = "SP";
  let indicadorIdade = "sim_agressao";
  let indicadorMonitoramento = "sinesp_homicidio_doloso";

  /* Controles segmentados (sexo e medida) */
  function segmentado(opcoes, atual, chave, rotulo) {
    const grupo = tag("div", "segmented");
    grupo.setAttribute("role", "group");
    grupo.setAttribute("aria-label", rotulo);
    for (const [valor, texto] of opcoes) {
      const b = tag("button", "", texto);
      b.type = "button";
      b.setAttribute("aria-pressed", String(valor === atual));
      b.addEventListener("click", () => definirEstado({ [chave]: valor }));
      grupo.append(b);
    }
    return grupo;
  }

  function desenharControles(estado) {
    $("controles-sexo-geral").replaceChildren(segmentado(SEXOS, estado.s, "s", "Sexo"));
    $("controles-evolucao").replaceChildren(
      campoIndicador(estado),
      segmentado(SEXOS, estado.s, "s", "Sexo"),
      segmentado(MEDIDAS, estado.m, "m", "Medida"),
    );
  }

  function campoIndicador(estado) {
    const rotulo = tag("label", "select-field");
    rotulo.append(tag("span", "", "Indicador"));
    const seletor = document.createElement("select");
    const eixos = new Map();
    for (const ind of manifesto.indicadores) {
      if (!eixos.has(ind.eixo)) eixos.set(ind.eixo, []);
      eixos.get(ind.eixo).push(ind);
    }
    for (const [eixo, lista] of eixos) {
      const grupo = document.createElement("optgroup");
      grupo.label = eixo;
      for (const ind of lista) {
        const o = tag("option", "", `${ind.rotulo} (${ind.fonte})`);
        o.value = ind.id;
        o.selected = ind.id === estado.i;
        grupo.append(o);
      }
      seletor.append(grupo);
    }
    seletor.addEventListener("change", () => definirEstado({ i: seletor.value }));
    rotulo.append(seletor);
    return rotulo;
  }

  function campoIndicadorMapa(estado) {
    const rotulo = tag("label", "select-field");
    rotulo.append(tag("span", "", "Indicador do mapa"));
    const seletor = document.createElement("select");
    const municipais = manifesto.indicadores.filter((ind) => ind.municipal && ind.arquivo_mapa);
    if (!municipais.some((ind) => ind.id === estado.i)) {
      const atual = dados.indicador(estado.i);
      const opcao = tag("option", "", `${atual.rotulo}: sem detalhe municipal`);
      opcao.value = atual.id;
      opcao.selected = true;
      seletor.append(opcao);
    }
    const eixos = new Map();
    for (const ind of municipais) {
      if (!eixos.has(ind.eixo)) eixos.set(ind.eixo, []);
      eixos.get(ind.eixo).push(ind);
    }
    for (const [eixo, lista] of eixos) {
      const grupo = document.createElement("optgroup");
      grupo.label = eixo;
      for (const ind of lista) {
        const opcao = tag("option", "", `${ind.rotulo} (${ind.fonte})`);
        opcao.value = ind.id;
        opcao.selected = ind.id === estado.i;
        grupo.append(opcao);
      }
      seletor.append(grupo);
    }
    seletor.addEventListener("change", () => definirEstado({ i: seletor.value }));
    rotulo.append(seletor);
    return rotulo;
  }

  function campoAnoMapa(estado) {
    const rotulo = tag("label", "select-field map-year-field");
    rotulo.append(tag("span", "", "Ano de referência"));
    const seletor = document.createElement("select");
    const atual = Math.min(2025, Math.max(janelaMapa === "3a" ? 2017 : 2015, Number(estado.a)));
    for (let ano = 2025; ano >= (janelaMapa === "3a" ? 2017 : 2015); ano -= 1) {
      const opcao = tag("option", "", String(ano));
      opcao.value = String(ano);
      opcao.selected = ano === atual;
      seletor.append(opcao);
    }
    seletor.addEventListener("change", () => definirEstado({ a: seletor.value }));
    rotulo.append(seletor);
    return rotulo;
  }

  function controleJanelaMapa(estado) {
    const grupo = tag("div", "segmented map-window");
    grupo.setAttribute("role", "group");
    grupo.setAttribute("aria-label", "Período do mapa");
    for (const [valor, texto] of [["3a", "Três anos"], ["ano", "Um ano"]]) {
      const botao = tag("button", "", texto);
      botao.type = "button";
      botao.setAttribute("aria-pressed", String(valor === janelaMapa));
      botao.addEventListener("click", () => {
        janelaMapa = valor;
        atualizar(estado);
      });
      grupo.append(botao);
    }
    return grupo;
  }

  function campoAno(estado, rotuloTexto = "Ano") {
    const rotulo = tag("label", "select-field compact-field");
    rotulo.append(tag("span", "", rotuloTexto));
    const seletor = document.createElement("select");
    for (let ano = 2025; ano >= 2015; ano -= 1) {
      const opcao = tag("option", "", String(ano));
      opcao.value = String(ano);
      opcao.selected = ano === Math.min(2025, Number(estado.a));
      seletor.append(opcao);
    }
    seletor.addEventListener("change", () => definirEstado({ a: seletor.value }));
    rotulo.append(seletor);
    return rotulo;
  }

  function campoUfComparacao(estado) {
    if (estado.t in UFS && estado.t !== "SC") ufComparacao = estado.t;
    const rotulo = tag("label", "select-field");
    rotulo.append(tag("span", "", "Outro estado"));
    const seletor = document.createElement("select");
    for (const [sigla, nome] of Object.entries(UFS)) {
      if (sigla === "SC") continue;
      const opcao = tag("option", "", `${nome} (${sigla})`);
      opcao.value = sigla;
      opcao.selected = sigla === ufComparacao;
      seletor.append(opcao);
    }
    seletor.addEventListener("change", () => {
      ufComparacao = seletor.value;
      atualizar(obterEstado());
    });
    rotulo.append(seletor);
    return rotulo;
  }

  function seletorLocal(rotuloTexto, ids, atual, aoMudar) {
    const rotulo = tag("label", "select-field");
    rotulo.append(tag("span", "", rotuloTexto));
    const seletor = document.createElement("select");
    for (const id of ids) {
      const ind = dados.indicador(id);
      const opcao = tag("option", "", `${ind.rotulo} (${ind.fonte})`);
      opcao.value = id;
      opcao.selected = id === atual;
      seletor.append(opcao);
    }
    seletor.addEventListener("change", () => aoMudar(seletor.value));
    rotulo.append(seletor);
    return rotulo;
  }

  /* Cartões */
  function variacao(pontos, campo) {
    const validos = pontos.filter((p) => p[campo] != null && p[campo] > 0);
    if (validos.length < 2) return null;
    const ini = validos[0];
    const fim = validos[validos.length - 1];
    return { de: ini.ano, pct: ((fim[campo] - ini[campo]) / ini[campo]) * 100 };
  }

  async function montarCartao(config, estado, territorio) {
    const ind = dados.indicador(config.id);
    const { territorio: efetivo, substituido } = dados.resolver(territorio, config.id);
    const serie = await dados.serie(efetivo, config.id, estado.s);
    const consolidados = serie.filter((p) => p.situacao === "consolidado");
    const comTaxa = consolidados.filter((p) => p.taxa != null);
    const alvo = comTaxa.length ? comTaxa[comTaxa.length - 1] : consolidados[consolidados.length - 1];

    const botao = tag("button", "card");
    botao.type = "button";
    botao.append(
      tag("p", "card-source", `${ind.fonte} · ${ind.base_territorial}`),
      tag("h3", "card-title", config.titulo),
    );
    if (!alvo) {
      botao.append(tag("p", "card-empty", "Sem dados para este recorte."));
      return botao;
    }
    const campo = alvo.taxa != null ? "taxa" : "valor";
    const ate = serie.filter((p) => p.ano <= alvo.ano && p.situacao === "consolidado");
    botao.append(
      tag("p", "card-value", fmtInteiro.format(alvo.valor)),
      tag("p", "card-year", `${ind.unidade} em ${alvo.ano}`),
    );
    if (alvo.taxa != null) botao.append(tag("p", "card-rate", `${fmtTaxa.format(alvo.taxa)} por 100 mil`));
    else botao.append(tag("p", "card-rate", "Taxa indisponível"));

    const insuficiente = efetivo.tipo === "municipio" && !alvo.suficiente;
    const v = insuficiente ? null : variacao(ate, campo);
    if (insuficiente) botao.append(tag("p", "card-flag", "Poucos casos: interpretar com cautela"));
    else if (v) {
      const sinal = v.pct > 0 ? "+" : "";
      botao.append(tag("p", "card-var", `${sinal}${fmtInteiro.format(Math.round(v.pct))}% desde ${v.de}`));
    }
    botao.append(miniatura(ate.filter((p) => p[campo] != null).map((p) => ({ ano: p.ano, y: p[campo] }))));
    if (substituido) botao.append(tag("p", "card-flag", "Total de Santa Catarina: sem detalhe municipal"));
    botao.addEventListener("click", () => {
      definirEstado({ i: config.id });
      $("evolucao").scrollIntoView();
    });
    botao.setAttribute("aria-label", `${config.titulo}: ver evolução`);
    return botao;
  }

  async function desenharCartoes(estado, territorio, minhaRodada) {
    const cartoes = await Promise.all(CARTOES.map((c) => montarCartao(c, estado, territorio)));
    if (minhaRodada !== rodada) return;
    $("cartoes").replaceChildren(...cartoes);
    $("nota-cartoes").textContent = estado.s === "total"
      ? ""
      : notaDenominador2025("estimado_proporcao_2024");
  }

  /* Evolução */
  function pontosDaSerie(serie, medida) {
    return serie
      .filter((p) => (medida === "taxa" ? p.taxa != null : p.valor != null))
      .map((p) => ({
        ano: p.ano,
        y: medida === "taxa" ? p.taxa : p.valor,
        valor: p.valor,
        taxa: p.taxa,
        tipoDenominador: p.tipoDenominador,
        situacao: p.situacao,
        oco: !p.suficiente,
      }));
  }

  async function desenharEvolucao(estado, territorio, minhaRodada) {
    const ind = dados.indicador(estado.i);
    const { territorio: efetivo, substituido } = dados.resolver(territorio, estado.i);
    const alvos = [efetivo];
    if (estado.m === "taxa") {
      for (const extra of [dados.SC, dados.BRASIL]) {
        if (!alvos.some((t) => t.id === extra.id)) alvos.push(extra);
      }
    }
    const series = [];
    for (const [i, t] of alvos.entries()) {
      const bruta = await dados.serie(t, estado.i, estado.s);
      series.push({ id: t.id, nome: t.nome, classe: i === 0 ? "s-a" : t.id === "SC" ? "s-b" : "s-c", pontos: pontosDaSerie(bruta, estado.m), bruta });
    }
    if (minhaRodada !== rodada) return;

    $("titulo-grafico").textContent = `${ind.rotulo}: ${efetivo.nome}`;
    const area = $("grafico");
    const comDados = series.filter((s) => s.pontos.length);
    if (!comDados.length) {
      area.replaceChildren(tag("p", "chart-empty", "Não há dados deste indicador para o recorte escolhido."));
    } else {
      const unidade = estado.m === "taxa" ? "por 100 mil" : ind.unidade;
      graficoLinhas(area, comDados, {
        formatoY: (v) => (estado.m === "taxa" ? fmtTaxa.format(v) : fmtInteiro.format(v)),
        descricao: `Gráfico de linhas: ${ind.rotulo} (${unidade}) em ${alvos.map((t) => t.nome).join(", ")}`,
      });
    }

    const notas = [];
    if (substituido) notas.push(`Este indicador não tem detalhe municipal. Mostrando o total de ${efetivo.nome}.`);
    if (estado.m === "absoluto" && alvos.length === 1) {
      notas.push("Valores absolutos de territórios de tamanhos diferentes não se comparam no mesmo eixo. Escolha a taxa para comparar com Santa Catarina e o Brasil.");
    }
    if (estado.m === "taxa") {
      const pontos2025 = series.flatMap((s) => s.pontos).filter((p) => p.ano === 2025);
      const tipos2025 = new Set(pontos2025.map((p) => p.tipoDenominador).filter(Boolean));
      if (tipos2025.has("estimado_proporcao_2024")) notas.push(notaDenominador2025("estimado_proporcao_2024"));
      else if (tipos2025.has("publicado")) notas.push(notaDenominador2025("publicado"));
      else notas.push("Este indicador não possui taxa de 2025 com período anual completo.");
    }
    if (efetivo.tipo === "municipio") {
      notas.push("Pontos vazados indicam anos com menos de 5 casos: a taxa oscila muito em municípios pequenos.");
    }
    if (series.some((s) => s.pontos.some((p) => p.situacao !== "consolidado"))) {
      notas.push("Trechos tracejados: 2025 é preliminar e 2026 é parcial, até agosto.");
    }
    notas.push(ind.ressalva);
    $("notas-grafico").replaceChildren(...notas.map((n) => tag("li", "", n)));

    desenharTabela(comDados, estado, ind);
  }

  function desenharTabela(series, estado, ind) {
    const tabela = tag("table", "data-table");
    const cabeca = document.createElement("tr");
    cabeca.append(tag("th", "", "Ano"));
    for (const s of series) {
      cabeca.append(tag("th", "", `${s.nome}: ${ind.unidade}`), tag("th", "", `${s.nome}: taxa por 100 mil`));
    }
    const thead = document.createElement("thead");
    thead.append(cabeca);
    tabela.append(thead);
    const anos = [...new Set(series.flatMap((s) => s.bruta.map((p) => p.ano)))].sort((a, b) => a - b);
    const corpo = document.createElement("tbody");
    for (const ano of anos) {
      const tr = document.createElement("tr");
      tr.append(tag("th", "", String(ano)));
      for (const s of series) {
        const p = s.bruta.find((q) => q.ano === ano);
        tr.append(
          tag("td", "", p ? fmtInteiro.format(p.valor) : "n.d."),
          tag("td", "", p && p.taxa != null ? fmtTaxa.format(p.taxa) : "n.d."),
        );
      }
      corpo.append(tr);
    }
    tabela.append(corpo);
    $("tabela-grafico").replaceChildren(tabela);
  }

  function legendaMapa(limites) {
    const itens = [];
    for (let indice = 0; indice < 5; indice += 1) {
      const inicio = indice === 0 ? 0 : limites[indice - 1];
      const fim = indice === 4 ? null : limites[indice];
      let texto;
      if (indice === 0) texto = `até ${fmtTaxa.format(fim)}`;
      else if (fim == null) texto = `acima de ${fmtTaxa.format(inicio)}`;
      else texto = `${fmtTaxa.format(inicio)} a ${fmtTaxa.format(fim)}`;
      const item = tag("span", "map-legend-item");
      item.append(tag("i", `map-q${indice}`), document.createTextNode(texto));
      itens.push(item);
    }
    const insuficiente = tag("span", "map-legend-item");
    insuficiente.append(tag("i", "map-insuficiente"), document.createTextNode("dado insuficiente"));
    itens.push(insuficiente);
    return itens;
  }

  async function desenharMapa(estado, territorio, minhaRodada) {
    $("controles-mapa").replaceChildren(
      campoIndicadorMapa(estado),
      campoAnoMapa(estado),
      segmentado(SEXOS, estado.s, "s", "Sexo"),
      controleJanelaMapa(estado),
    );
    const ind = dados.indicador(estado.i);
    const aviso = $("aviso-mapa");
    const conteudo = $("conteudo-mapa");
    if (!ind.municipal || !ind.arquivo_mapa) {
      aviso.hidden = false;
      aviso.textContent = `${ind.rotulo} não possui identificação municipal na fonte. Escolha outro indicador para comparar os municípios.`;
      conteudo.hidden = true;
      return;
    }
    aviso.hidden = true;
    conteudo.hidden = false;

    const anoMinimo = janelaMapa === "3a" ? 2017 : 2015;
    const ano = Math.min(2025, Math.max(anoMinimo, Number(estado.a)));
    const [tabela, malha] = await Promise.all([dados.mapa(estado.i), dados.malha()]);
    if (minhaRodada !== rodada) return;
    const base = tabela.filter((linha) => linha.ano === ano && linha.sexo === estado.s);
    const nota2025 = ano === 2025
      ? notaDenominador2025(base.find((linha) => linha.taxa != null)?.tipoDenominador)
      : "";
    aviso.hidden = !nota2025;
    aviso.textContent = nota2025;
    const linhas = base.map((linha) => janelaMapa === "3a"
      ? { ...linha, valor: linha.valor3a, taxa: linha.taxa3a, suficiente: linha.suficiente3a }
      : linha);
    const periodo = janelaMapa === "3a" ? `${ano - 2} a ${ano}` : String(ano);
    $("titulo-mapa").textContent = `${ind.rotulo}: ${periodo}`;
    $("titulo-ranking").textContent = `Ranking municipal, ${periodo}`;

    const resumo = mapaMunicipal($("mapa-sc"), malha, linhas, {
      selecionado: territorio.tipo === "municipio" ? territorio.id : null,
      descricao: `Mapa de Santa Catarina para ${ind.rotulo}, ${periodo}, taxa por 100 mil habitantes`,
      aoSelecionar: (id) => definirEstado({ t: id }, "push"),
    });
    $("legenda-mapa").replaceChildren(
      tag("strong", "", "Taxa por 100 mil"),
      ...legendaMapa(resumo.limites),
    );

    const ranking = linhas
      .filter((linha) => linha.suficiente && linha.taxa != null)
      .sort((a, b) => b.taxa - a.taxa || b.valor - a.valor)
      .slice(0, 10);
    $("ranking-mapa").replaceChildren(...ranking.map((linha) => {
      const item = document.createElement("li");
      const botao = tag("button", "ranking-row");
      botao.type = "button";
      botao.append(
        tag("span", "ranking-name", linha.nome),
        tag("strong", "ranking-rate", fmtTaxa.format(linha.taxa)),
        tag("span", "ranking-count", `${fmtInteiro.format(linha.valor)} ${ind.unidade}`),
      );
      botao.addEventListener("click", () => definirEstado({ t: linha.id }, "push"));
      item.append(botao);
      return item;
    }));
  }

  function mediana(valores) {
    const ordenados = valores.filter((v) => v != null).sort((a, b) => a - b);
    if (!ordenados.length) return null;
    const meio = Math.floor(ordenados.length / 2);
    return ordenados.length % 2 ? ordenados[meio] : (ordenados[meio - 1] + ordenados[meio]) / 2;
  }

  function resumoMetrica(rotulo, valor, detalhe, classe = "") {
    const bloco = tag("article", `summary-metric ${classe}`.trim());
    bloco.append(
      tag("p", "summary-label", rotulo),
      tag("strong", "summary-value", valor),
      tag("p", "summary-detail", detalhe),
    );
    return bloco;
  }

  async function desenharComparacao(estado, territorio, minhaRodada) {
    const ano = Math.min(2025, Number(estado.a));
    $("controles-comparacao").replaceChildren(
      campoIndicador(estado),
      campoAno(estado, "Ano"),
      segmentado(SEXOS, estado.s, "s", "Sexo"),
      campoUfComparacao(estado),
    );
    const [linhas, serieMunicipio] = await Promise.all([
      dados.comparacao(estado.i, estado.s, ano),
      territorio.tipo === "municipio" ? dados.serie(territorio, estado.i, estado.s) : Promise.resolve([]),
    ]);
    if (minhaRodada !== rodada) return;
    if (!linhas.length) {
      $("resumo-comparacao").replaceChildren(tag("p", "chart-empty", "Este indicador não possui taxa para o ano selecionado."));
      $("barras-comparacao").replaceChildren();
      $("tabela-comparacao").replaceChildren();
      $("nota-comparacao").textContent = "Escolha outro ano para realizar a comparação.";
      return;
    }
    const ufs = linhas.filter((linha) => linha.nivel_territorial === "uf");
    const brasil = linhas.find((linha) => linha.id_territorio === "BR");
    const sc = ufs.find((linha) => linha.id_territorio === "SC");
    const outro = ufs.find((linha) => linha.id_territorio === ufComparacao);
    const taxaMediana = mediana(ufs.map((linha) => linha.taxa));
    const municipio = serieMunicipio.find((p) => p.ano === ano && p.taxa != null);
    const ind = dados.indicador(estado.i);

    const resumos = [];
    if (brasil) resumos.push(resumoMetrica("Brasil", fmtTaxa.format(brasil.taxa), `${fmtInteiro.format(brasil.valor)} ${ind.unidade}`));
    if (taxaMediana != null) resumos.push(resumoMetrica("Mediana dos estados", fmtTaxa.format(taxaMediana), "referência não ponderada"));
    if (sc) {
      const posicao = [...ufs].sort((a, b) => b.taxa - a.taxa).findIndex((linha) => linha.id_territorio === "SC") + 1;
      resumos.push(resumoMetrica("Santa Catarina", fmtTaxa.format(sc.taxa), `${posicao}ª posição entre 27 UFs`, "summary-focus"));
    }
    if (municipio) resumos.push(resumoMetrica(territorio.nome, fmtTaxa.format(municipio.taxa), `${fmtInteiro.format(municipio.valor)} ${ind.unidade}`));
    else if (outro) resumos.push(resumoMetrica(UFS[ufComparacao], fmtTaxa.format(outro.taxa), `${fmtInteiro.format(outro.valor)} ${ind.unidade}`));
    $("resumo-comparacao").replaceChildren(...resumos);

    const ordenadas = [...ufs].sort((a, b) => b.taxa - a.taxa);
    const exibidas = ordenadas.slice(0, 10);
    if (sc && !exibidas.includes(sc)) exibidas.push(sc);
    if (outro && !exibidas.includes(outro)) exibidas.push(outro);
    exibidas.sort((a, b) => b.taxa - a.taxa);
    const maximo = Math.max(1, ...exibidas.map((linha) => linha.taxa));
    $("titulo-comparacao").textContent = `${ind.rotulo}: posição entre os estados em ${ano}`;
    $("barras-comparacao").replaceChildren(...exibidas.map((linha) => {
      const item = tag("div", `comparison-bar${linha.id_territorio === "SC" ? " comparison-bar-focus" : ""}`);
      item.append(
        tag("span", "comparison-bar-name", UFS[linha.id_territorio] ?? linha.territorio),
        tag("span", "comparison-bar-track"),
        tag("strong", "comparison-bar-value", fmtTaxa.format(linha.taxa)),
      );
      item.querySelector(".comparison-bar-track").style.setProperty("--bar", `${linha.taxa / maximo * 100}%`);
      return item;
    }));

    const tabela = tag("table", "data-table comparison-table");
    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    for (const texto of ["Referência", "Taxa", ind.unidade]) trh.append(tag("th", "", texto));
    thead.append(trh);
    const corpo = document.createElement("tbody");
    const referencias = [
      brasil && ["Brasil", brasil.taxa, brasil.valor],
      taxaMediana != null && ["Mediana das UFs", taxaMediana, null],
      sc && ["Santa Catarina", sc.taxa, sc.valor],
      outro && [UFS[ufComparacao], outro.taxa, outro.valor],
      municipio && [territorio.nome, municipio.taxa, municipio.valor],
    ].filter(Boolean);
    for (const [nome, taxa, valor] of referencias) {
      const tr = document.createElement("tr");
      tr.append(tag("th", "", nome), tag("td", "", fmtTaxa.format(taxa)), tag("td", "", valor == null ? "n.d." : fmtInteiro.format(valor)));
      corpo.append(tr);
    }
    tabela.append(thead, corpo);
    $("tabela-comparacao").replaceChildren(tabela);
    const nota2025 = ano === 2025
      ? notaDenominador2025(linhas.find((linha) => linha.taxa != null)?.tipo_denominador)
      : "";
    $("nota-comparacao").textContent = `Taxa por 100 mil. A taxa Brasil usa o total nacional e sua população. A mediana representa o ponto central das 27 taxas estaduais. ${nota2025} ${ind.ressalva}`.trim();
  }

  function barraIdade(rotulo, sc, br, maximo) {
    const linha = tag("div", "age-row");
    const valores = tag("div", "age-row-values");
    const barraSc = tag("span", "age-bar age-bar-sc");
    const barraBr = tag("span", "age-bar age-bar-br");
    barraSc.style.setProperty("--bar", `${(sc ?? 0) / maximo * 100}%`);
    barraBr.style.setProperty("--bar", `${(br ?? 0) / maximo * 100}%`);
    barraSc.textContent = sc == null ? "n.d." : fmtTaxa.format(sc);
    barraBr.textContent = br == null ? "n.d." : fmtTaxa.format(br);
    valores.append(barraSc, barraBr);
    linha.append(tag("strong", "age-label", rotulo), valores);
    return linha;
  }

  function tabelaRacaParaTerritorio(base, territorio) {
    if (territorio.tipo === "municipio") {
      return base.sim_raca_municipios.filter((linha) => String(linha.id_municipio) === territorio.id);
    }
    const ufs = territorio.tipo === "brasil" ? Object.keys(UFS) : [territorio.id];
    const linhas = base.sim_raca_uf_ano.filter((linha) => ufs.includes(linha.sigla_uf));
    const resultado = [];
    const ultimoAno = Math.max(...linhas.map((linha) => linha.ano));
    const percentuaisNaoInformados = linhas
      .filter((linha) => linha.ano === ultimoAno && linha.percentual_raca_nao_informada != null)
      .map((linha) => linha.percentual_raca_nao_informada);
    const percentualNaoInformado = percentuaisNaoInformados.length
      ? percentuaisNaoInformados.reduce((soma, valor) => soma + valor, 0) / percentuaisNaoInformados.length
      : null;
    for (const raca of ["Negra", "Branca"]) {
      const recorte = linhas.filter((linha) => linha.raca === raca);
      const anos = new Set(recorte.map((linha) => linha.ano)).size;
      const porUf = new Map();
      for (const linha of recorte) {
        if (!porUf.has(linha.sigla_uf)) porUf.set(linha.sigla_uf, linha.populacao_feminina_raca);
      }
      const populacao = [...porUf.values()].reduce((soma, valor) => soma + (valor ?? 0), 0);
      const obitos = recorte.reduce((soma, linha) => soma + linha.obitos_mulheres_agressao, 0);
      resultado.push({
        raca,
        obitos_mulheres_agressao: obitos,
        taxa_anual_media_100mil_mulheres_censo2022: populacao && anos ? obitos / populacao / anos * 100000 : null,
        percentual_raca_nao_informada: percentualNaoInformado,
        dado_suficiente: obitos >= 5,
      });
    }
    return resultado;
  }

  function desenharResumoRaca(base, territorio) {
    const recorte = tabelaRacaParaTerritorio(base, territorio);
    const negra = recorte.find((linha) => linha.raca === "Negra");
    const branca = recorte.find((linha) => linha.raca === "Branca");
    if (!negra || !branca) {
      $("resumo-raca").replaceChildren(tag("p", "chart-empty", "Recorte racial indisponível para este território."));
      return;
    }
    const taxaNegra = negra.taxa_anual_media_100mil_mulheres_censo2022;
    const taxaBranca = branca.taxa_anual_media_100mil_mulheres_censo2022;
    const razao = taxaNegra != null && taxaBranca > 0 ? taxaNegra / taxaBranca : null;
    const diferenca = taxaNegra != null && taxaBranca != null ? taxaNegra - taxaBranca : null;
    const percentualNaoInformado = negra.percentual_raca_nao_informada ?? branca.percentual_raca_nao_informada;
    const bloco = tag("div", "evidence-metrics");
    bloco.append(
      resumoMetrica("Mulheres negras", taxaNegra == null ? "n.d." : fmtTaxa.format(taxaNegra), `${fmtInteiro.format(negra.obitos_mulheres_agressao)} mortes no período`),
      resumoMetrica("Mulheres brancas", taxaBranca == null ? "n.d." : fmtTaxa.format(taxaBranca), `${fmtInteiro.format(branca.obitos_mulheres_agressao)} mortes no período`),
      resumoMetrica("Razão entre taxas", razao == null ? "n.d." : `${fmtTaxa.format(razao)} vezes`, "negra dividida pela branca", "summary-focus"),
      resumoMetrica("Diferença entre taxas", diferenca == null ? "n.d." : `${diferenca > 0 ? "+" : ""}${fmtTaxa.format(diferenca)}`, "pontos por 100 mil"),
      resumoMetrica("Raça não informada", percentualNaoInformado == null ? "n.d." : `${fmtTaxa.format(percentualNaoInformado)}%`, "qualidade do preenchimento"),
    );
    const leitura = razao == null
      ? "A diferença entre os grupos não pode ser estimada com segurança."
      : razao >= 1
        ? `A taxa de mulheres negras é ${fmtInteiro.format((razao - 1) * 100)}% maior que a taxa de mulheres brancas.`
        : `A taxa de mulheres negras é ${fmtInteiro.format((1 - razao) * 100)}% menor que a taxa de mulheres brancas.`;
    $("resumo-raca").replaceChildren(bloco, tag("p", "analysis-note", leitura));
  }

  function desenharResumoTrabalho(base, territorio) {
    let linha;
    if (territorio.tipo === "municipio") {
      linha = base.trabalho_municipios.find((item) => String(item.id_territorio) === territorio.id);
    } else {
      linha = base.trabalho_ano.find((item) => item.ano === 2025 && String(item.id_territorio) === territorio.id);
    }
    if (!linha) {
      $("resumo-trabalho").replaceChildren(tag("p", "chart-empty", "Dados da RAIS indisponíveis para este território."));
      return;
    }
    const bloco = tag("div", "evidence-metrics");
    const periodo = territorio.tipo === "municipio" ? "2019 a 2025" : "2025";
    const diferencaSalarial = (linha.razao_salarial_mulher_homem - 1) * 100;
    bloco.append(
      resumoMetrica("Participação feminina", `${fmtTaxa.format(linha.participacao_feminina_pct)}%`, `${fmtInteiro.format(linha.vinculos_total)} vínculos formais, ${periodo}`),
      resumoMetrica("Razão salarial", `${fmtInteiro.format(linha.razao_salarial_mulher_homem * 100)}%`, "remuneração média feminina em relação à masculina", "summary-focus"),
      resumoMetrica("Remuneração feminina", `R$ ${fmtInteiro.format(linha.remuneracao_media_mulheres)}`, `média nominal, ${periodo}`),
      resumoMetrica("Diferença salarial", `${diferencaSalarial > 0 ? "+" : ""}${fmtInteiro.format(diferencaSalarial)}%`, diferencaSalarial <= 0 ? "abaixo da remuneração masculina" : "acima da remuneração masculina"),
    );
    if (territorio.tipo === "municipio") {
      const racial = base.salario_raca_municipios.find((item) => String(item.id_territorio) === territorio.id);
      if (racial?.razao_mulheres_negras_homens_brancos != null) {
        bloco.append(resumoMetrica("Mulheres negras e homens brancos", `${fmtInteiro.format(racial.razao_mulheres_negras_homens_brancos * 100)}%`, "razão da remuneração média"));
      }
    }
    const leitura = diferencaSalarial < 0
      ? `A remuneração média feminina é ${fmtInteiro.format(Math.abs(diferencaSalarial))}% menor que a masculina.`
      : `A remuneração média feminina é ${fmtInteiro.format(diferencaSalarial)}% maior que a masculina.`;
    $("resumo-trabalho").replaceChildren(bloco, tag("p", "analysis-note", leitura));
  }

  async function desenharDesigualdades(estado, territorio, minhaRodada) {
    $("controles-idade").replaceChildren(seletorLocal("Indicador", INDICADORES_IDADE, indicadorIdade, (id) => {
      indicadorIdade = id;
      atualizar(obterEstado());
    }));
    const [idade, desigualdades] = await Promise.all([
      dados.idade(indicadorIdade, 2024),
      dados.desigualdades(),
    ]);
    if (minhaRodada !== rodada) return;
    const sc = idade.filter((linha) => linha.territorio === "Santa Catarina" && linha.taxa != null);
    const br = idade.filter((linha) => linha.territorio === "Brasil" && linha.taxa != null);
    const ordemIdade = ["0 a 4 anos", "5 a 9 anos", "10 a 14 anos", "15 a 19 anos", "20 a 29 anos", "30 a 39 anos", "40 a 49 anos", "50 a 59 anos", "60 a 69 anos", "70 a 79 anos", "80 anos e mais"];
    const gruposDisponiveis = new Set(sc.map((linha) => linha.grupo_etario));
    const grupos = ordemIdade.filter((grupo) => gruposDisponiveis.has(grupo));
    const maximo = Math.max(1, ...idade.map((linha) => linha.taxa ?? 0));
    const maiorSc = [...sc].sort((a, b) => b.taxa - a.taxa)[0];
    const brMesmaFaixa = br.find((linha) => linha.grupo_etario === maiorSc?.grupo_etario);
    const relacaoComBrasil = maiorSc?.taxa != null && brMesmaFaixa?.taxa > 0 ? maiorSc.taxa / brMesmaFaixa.taxa * 100 : null;
    const distancias = grupos.map((grupo) => {
      const taxaSc = sc.find((linha) => linha.grupo_etario === grupo)?.taxa;
      const taxaBr = br.find((linha) => linha.grupo_etario === grupo)?.taxa;
      return { grupo, distancia: taxaSc == null || taxaBr == null ? null : Math.abs(taxaSc - taxaBr) };
    }).filter((item) => item.distancia != null).sort((a, b) => b.distancia - a.distancia);
    const maiorDistancia = distancias[0];
    $("resumo-idade").replaceChildren(
      resumoMetrica("Maior taxa em SC", maiorSc ? fmtTaxa.format(maiorSc.taxa) : "n.d.", maiorSc?.grupo_etario ?? "sem faixa disponível", "summary-focus"),
      resumoMetrica("Brasil na mesma faixa", brMesmaFaixa ? fmtTaxa.format(brMesmaFaixa.taxa) : "n.d.", "taxa por 100 mil"),
      resumoMetrica("SC em relação ao Brasil", relacaoComBrasil == null ? "n.d." : `${fmtInteiro.format(relacaoComBrasil)}%`, maiorSc?.grupo_etario ?? ""),
      resumoMetrica("Maior distância", maiorDistancia ? fmtTaxa.format(maiorDistancia.distancia) : "n.d.", maiorDistancia?.grupo ?? "pontos por 100 mil"),
    );
    const legenda = tag("div", "age-legend");
    legenda.append(tag("span", "age-key age-key-sc", "Santa Catarina"), tag("span", "age-key age-key-br", "Brasil"));
    $("grafico-idade").replaceChildren(
      legenda,
      ...grupos.map((grupo) => barraIdade(
        grupo,
        sc.find((linha) => linha.grupo_etario === grupo)?.taxa,
        br.find((linha) => linha.grupo_etario === grupo)?.taxa,
        maximo,
      )),
    );
    desenharResumoRaca(desigualdades, territorio);
    desenharResumoTrabalho(desigualdades, territorio);
  }

  async function desenharMulheres(territorio, minhaRodada) {
    const configuracoes = [
      ["sinan_notificacoes_interpessoais", "Violência interpessoal notificada"],
      ["sim_agressao", "Mortes por agressão"],
      ["sinesp_feminicidio", "Feminicídio"],
      ["sinesp_tentativa_de_feminicidio", "Tentativa de feminicídio"],
    ];
    const [paineis, simSc, feminicidioSc, simBrasil, feminicidioBrasil, tentativaSc] = await Promise.all([
      Promise.all(configuracoes.map(async ([id, titulo]) => {
      const ind = dados.indicador(id);
      const { territorio: efetivo, substituido } = dados.resolver(territorio, id);
      const serie = await dados.serie(efetivo, id, "feminino");
      const alvo = [...serie].reverse().find((p) => p.taxa != null);
      const recente = [...serie].reverse().find((p) => alvo && p.ano > alvo.ano);
      const painel = tag("article", "women-panel");
      painel.append(tag("p", "card-source", `${ind.fonte} · ${ind.base_territorial}`), tag("h3", "", titulo));
      if (alvo) painel.append(
        tag("strong", "women-value", fmtInteiro.format(alvo.valor)),
        tag("p", "women-rate", `${fmtTaxa.format(alvo.taxa)} por 100 mil em ${alvo.ano}${alvo.situacao === "preliminar" ? ", dado preliminar" : ""}`),
      );
      else painel.append(tag("p", "chart-empty", "Sem taxa consolidada."));
      if (recente) painel.append(tag("p", "women-recent", `${recente.ano}: ${fmtInteiro.format(recente.valor)} ${ind.unidade}, ${recente.situacao}`));
      if (substituido) painel.append(tag("p", "card-flag", "Sem detalhe municipal. Mostrando Santa Catarina."));
      painel.append(tag("p", "small", ind.ressalva));
      return painel;
      })),
      dados.serie(dados.SC, "sim_agressao", "feminino"),
      dados.serie(dados.SC, "sinesp_feminicidio", "feminino"),
      dados.serie(dados.BRASIL, "sim_agressao", "feminino"),
      dados.serie(dados.BRASIL, "sinesp_feminicidio", "feminino"),
      dados.serie(dados.SC, "sinesp_tentativa_de_feminicidio", "feminino"),
    ]);
    if (minhaRodada !== rodada) return;
    $("resumo-mulheres").replaceChildren(...paineis);

    const ponto = (serie, ano) => serie.find((item) => item.ano === ano);
    const razaoClassificacao = (ano, sim, feminicidio) => {
      const mortes = ponto(sim, ano)?.valor;
      const casos = ponto(feminicidio, ano)?.valor;
      return mortes > 0 && casos != null ? { ano, mortes, casos, razao: casos / mortes } : null;
    };
    const historico = [2019, 2020, 2021, 2022, 2023, 2024]
      .map((ano) => razaoClassificacao(ano, simSc, feminicidioSc))
      .filter(Boolean);
    const sc2024 = razaoClassificacao(2024, simSc, feminicidioSc);
    const br2024 = razaoClassificacao(2024, simBrasil, feminicidioBrasil);
    const topoClassificacao = tag("div", "women-analysis-summary");
    topoClassificacao.append(
      resumoMetrica("Santa Catarina, 2024", sc2024 ? `${fmtTaxa.format(sc2024.razao * 100)}%` : "n.d.", sc2024 ? `${fmtInteiro.format(sc2024.casos)} de ${fmtInteiro.format(sc2024.mortes)} mortes` : "sem dados", "summary-focus"),
      resumoMetrica("Brasil, 2024", br2024 ? `${fmtTaxa.format(br2024.razao * 100)}%` : "n.d.", br2024 ? `${fmtInteiro.format(br2024.casos)} de ${fmtInteiro.format(br2024.mortes)} mortes` : "sem dados"),
    );
    const linhasClassificacao = tag("div", "classification-list");
    for (const item of historico) {
      const linha = tag("div", "classification-row");
      const trilho = tag("span", "classification-track");
      const barra = tag("i", "");
      barra.style.setProperty("--bar", `${Math.min(100, item.razao * 100)}%`);
      trilho.append(barra);
      linha.append(
        tag("strong", "", String(item.ano)),
        trilho,
        tag("span", "classification-value", `${fmtTaxa.format(item.razao * 100)}%`),
        tag("small", "", `${fmtInteiro.format(item.casos)} de ${fmtInteiro.format(item.mortes)}`),
      );
      linhasClassificacao.append(linha);
    }
    const notaTerritorial = territorio.tipo === "municipio"
      ? `A comparação usa Santa Catarina porque SIM registra residência e Sinesp registra local do fato. Não é uma razão municipal para ${territorio.nome}.`
      : "SIM registra residência e Sinesp registra local do fato. A razão deve ser lida como aproximação de classificação.";
    $("mulheres-classificacao").replaceChildren(topoClassificacao, linhasClassificacao, tag("p", "analysis-note", notaTerritorial));

    const tabelaTentativas = tag("table", "data-table women-attempt-table");
    const cabecaTentativas = document.createElement("thead");
    const linhaCabeca = document.createElement("tr");
    for (const texto of ["Ano", "Tentativas", "Feminicídios", "Por consumado"]) linhaCabeca.append(tag("th", "", texto));
    cabecaTentativas.append(linhaCabeca);
    const corpoTentativas = document.createElement("tbody");
    for (const ano of [2024, 2025, 2026]) {
      const tentativas = ponto(tentativaSc, ano)?.valor;
      const consumados = ponto(feminicidioSc, ano)?.valor;
      const razao = consumados > 0 && tentativas != null ? tentativas / consumados : null;
      const linha = document.createElement("tr");
      linha.append(
        tag("th", "", ano === 2026 ? "2026 parcial" : String(ano)),
        tag("td", "", tentativas == null ? "n.d." : fmtInteiro.format(tentativas)),
        tag("td", "", consumados == null ? "n.d." : fmtInteiro.format(consumados)),
        tag("td", "", razao == null ? "n.d." : fmtTaxa.format(razao)),
      );
      corpoTentativas.append(linha);
    }
    tabelaTentativas.append(cabecaTentativas, corpoTentativas);
    const tentativa2024 = ponto(tentativaSc, 2024)?.valor;
    const feminicidio2024 = ponto(feminicidioSc, 2024)?.valor;
    const razao2024 = feminicidio2024 > 0 && tentativa2024 != null ? tentativa2024 / feminicidio2024 : null;
    const rolagemTentativas = tag("div", "table-scroll");
    rolagemTentativas.append(tabelaTentativas);
    $("mulheres-tentativas").replaceChildren(
      resumoMetrica("Tentativas por feminicídio", razao2024 == null ? "n.d." : fmtTaxa.format(razao2024), "Santa Catarina, 2024", "summary-focus"),
      rolagemTentativas,
      tag("p", "analysis-note", "Os valores de 2026 cobrem janeiro a agosto. A razão compara eventos policiais no mesmo período de referência."),
    );
  }

  async function desenharMonitoramento(estado, territorio, minhaRodada) {
    $("controles-monitoramento").replaceChildren(
      seletorLocal("Indicador", INDICADORES_MONITOR, indicadorMonitoramento, (id) => {
        indicadorMonitoramento = id;
        atualizar(obterEstado());
      }),
      segmentado(SEXOS, estado.s, "s", "Sexo"),
    );
    const linhas = await dados.mensal(indicadorMonitoramento, estado.s);
    if (minhaRodada !== rodada) return;
    const sc = linhas.filter((linha) => linha.territorio === "Santa Catarina" && linha.mes <= 8 && [2024, 2025, 2026].includes(linha.ano));
    const total = (ano) => sc.filter((linha) => linha.ano === ano).reduce((soma, linha) => soma + linha.valor, 0);
    const totais = [2024, 2025, 2026].map((ano) => [ano, total(ano)]);
    const variacao = totais[1][1] ? (totais[2][1] - totais[1][1]) / totais[1][1] * 100 : null;
    const ind = dados.indicador(indicadorMonitoramento);
    $("resumo-monitoramento").replaceChildren(
      ...totais.map(([ano, valor]) => resumoMetrica(`${ano}, janeiro a agosto`, fmtInteiro.format(valor), ind.unidade, ano === 2026 ? "summary-focus" : "")),
      resumoMetrica("Variação 2026 e 2025", variacao == null ? "n.d." : `${variacao > 0 ? "+" : ""}${fmtTaxa.format(variacao)}%`, "mesmo período"),
    );
    const tabela = tag("table", "data-table monitor-table");
    const meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago"];
    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    trh.append(tag("th", "", "Ano"), ...meses.map((mes) => tag("th", "", mes)), tag("th", "", "Total"));
    thead.append(trh);
    const corpo = document.createElement("tbody");
    for (const [ano, valor] of totais) {
      const tr = document.createElement("tr");
      tr.append(tag("th", "", String(ano)));
      for (let mes = 1; mes <= 8; mes += 1) tr.append(tag("td", "", fmtInteiro.format(sc.find((linha) => linha.ano === ano && linha.mes === mes)?.valor ?? 0)));
      tr.append(tag("td", "", fmtInteiro.format(valor)));
      corpo.append(tr);
    }
    tabela.append(thead, corpo);
    const nota = tag("p", "small", territorio.tipo === "municipio"
      ? `A série mensal não identifica município. Mostrando Santa Catarina para ${territorio.nome}.`
      : "Série mensal de Santa Catarina. Taxas não são usadas porque 2025 e 2026 não têm denominador populacional compatível.");
    $("tabela-monitoramento").replaceChildren(tabela, nota);
  }

  async function atualizar(estado) {
    const minhaRodada = ++rodada;
    const territorio = territorioPorId(estado.t);
    desenharControles(estado);
    try {
      await Promise.all([
        desenharCartoes(estado, territorio, minhaRodada),
        desenharEvolucao(estado, territorio, minhaRodada),
        desenharMapa(estado, territorio, minhaRodada),
        desenharComparacao(estado, territorio, minhaRodada),
        desenharDesigualdades(estado, territorio, minhaRodada),
        desenharMulheres(territorio, minhaRodada),
        desenharMonitoramento(estado, territorio, minhaRodada),
      ]);
    } catch (erro) {
      console.error(erro);
      $("cartoes").replaceChildren(tag("p", "chart-empty", "Não foi possível carregar os dados deste território."));
    }
  }

  document.addEventListener("atlas:estado", (e) => atualizar(e.detail));
  matchMedia("(max-width: 599px)").addEventListener("change", () => atualizar(obterEstado()));
}
